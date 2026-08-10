package main

import (
    "fmt"
    "html/template"
    "log"
    "net/http"
    "path"
    "strconv"
    "strings"
)

var tmpl *template.Template

func init() {
    // Parse all templates in templates directory.
    var err error
    tmpl, err = template.ParseGlob("task_games_10/templates/*.html")
    if err != nil {
        log.Fatalf("Failed to parse templates: %v", err)
    }
}

// HomeHandler renders the home page with a run creation form and the leaderboard.
func HomeHandler(w http.ResponseWriter, r *http.Request) {
    if r.Method == http.MethodPost {
        // handle new run creation directly from home form.
        handle := strings.TrimSpace(r.FormValue("handle"))
        seedStr := strings.TrimSpace(r.FormValue("seed"))
        seedVal, _ := strconv.ParseInt(seedStr, 10, 64)
        if handle == "" {
            handle = "Trader"
        }
        run, err := NewRun(handle, seedVal)
        if err != nil {
            http.Error(w, "Failed to create run", http.StatusInternalServerError)
            return
        }
        http.Redirect(w, r, fmt.Sprintf("/run/%d", run.ID), http.StatusSeeOther)
        return
    }
    // GET: show form and recent leaderboard entries.
    rows, err := db.Query("SELECT id, handle, cash, tick, status FROM runs ORDER BY id DESC LIMIT 10")
    if err != nil {
        http.Error(w, "db error", http.StatusInternalServerError)
        return
    }
    defer rows.Close()
    type rowData struct{ ID int64; Handle string; Cash int64; Tick int; Status string }
    var data []rowData
    for rows.Next() {
        var rd rowData
        rows.Scan(&rd.ID, &rd.Handle, &rd.Cash, &rd.Tick, &rd.Status)
        data = append(data, rd)
    }
    tmpl.ExecuteTemplate(w, "home.html", map[string]interface{}{"Runs": data})
}

// NewRunHandler handles POST to create a run (alternative endpoint).
func NewRunHandler(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
        return
    }
    handle := strings.TrimSpace(r.FormValue("handle"))
    seedStr := strings.TrimSpace(r.FormValue("seed"))
    seedVal, _ := strconv.ParseInt(seedStr, 10, 64)
    if handle == "" { handle = "Trader" }
    run, err := NewRun(handle, seedVal)
    if err != nil {
        http.Error(w, "Failed to create run", http.StatusInternalServerError)
        return
    }
    http.Redirect(w, r, fmt.Sprintf("/run/%d", run.ID), http.StatusSeeOther)
}

// RunRouter dispatches sub‑paths under /run/{id}.
func RunRouter(w http.ResponseWriter, r *http.Request) {
    // Expected format: /run/{id} or /run/{id}/...
    parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/run/"), "/")
    if len(parts) == 0 || parts[0] == "" {
        http.NotFound(w, r)
        return
    }
    id, err := strconv.ParseInt(parts[0], 10, 64)
    if err != nil {
        http.NotFound(w, r)
        return
    }
    run, err := LoadRun(id)
    if err != nil {
        http.NotFound(w, r)
        return
    }
    // Determine sub‑path.
    sub := ""
    if len(parts) > 1 {
        sub = parts[1]
    }
    switch sub {
    case "":
        FloorHandler(w, r, run)
    case "trade":
        TradeHandler(w, r, run)
    case "advance":
        AdvanceHandler(w, r, run)
    case "settle":
        SettleHandler(w, r, run)
    case "tape":
        TapeHandler(w, r, run)
    default:
        http.NotFound(w, r)
    }
}

// FloorHandler renders the trading floor for a run.
func FloorHandler(w http.ResponseWriter, r *http.Request, run *Run) {
    // Prepare data for template.
    // Compute portfolio holdings.
    holdings := map[string]int{}
    rows, _ := db.Query("SELECT symbol, side, qty FROM trades WHERE run_id = ?", run.ID)
    for rows.Next() {
        var sym, side string
        var qty int
        rows.Scan(&sym, &side, &qty)
        if side == "buy" {
            holdings[sym] += qty
        } else {
            holdings[sym] -= qty
        }
    }
    rows.Close()
    // Build slice for display.
    type hold struct{ Symbol string; Qty int; Price string }
    var holdSlice []hold
    for _, instr := range run.Instruments {
        qty := holdings[instr.Symbol]
        price := formatCents(run.price(instr.Symbol, run.Tick))
        holdSlice = append(holdSlice, hold{Symbol: instr.Symbol, Qty: qty, Price: price})
    }
    // Dispatch events that occurred up to current tick.
    var events []string
    for _, ev := range run.Events {
        if ev <= run.Tick {
            // find sector of instrument at index ev%len
            sector := run.Instruments[ev%len(run.Instruments)].Sector
            events = append(events, fmt.Sprintf("Storm at tick %d – %s sector shock", ev, sector))
        }
    }
    // Snapshot mode: omit timestamps etc – our templates already have deterministic output.
    tmpl.ExecuteTemplate(w, "floor.html", map[string]interface{}{
        "Run": run,
        "Holdings": holdSlice,
        "Cash": formatCents(run.Cash),
        "Tick": run.Tick,
        "Events": events,
        "Snapshot": snapshotMode,
    })
}

// TradeHandler processes a POST trade.
func TradeHandler(w http.ResponseWriter, r *http.Request, run *Run) {
    if r.Method != http.MethodPost {
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
        return
    }
    symbol := strings.ToUpper(strings.TrimSpace(r.FormValue("symbol")))
    side := strings.ToLower(strings.TrimSpace(r.FormValue("side")))
    qty := parseInt(r.FormValue("qty"))
    if qty <= 0 {
        http.Error(w, "Invalid quantity", http.StatusBadRequest)
        return
    }
    price := run.price(symbol, run.Tick)
    if price == 0 {
        http.Error(w, "Unknown symbol", http.StatusBadRequest)
        return
    }
    fee := feeForTrade(price, qty)
    total := int64(qty)*price + fee
    // Validate based on side.
    if side == "buy" {
        if run.Cash < total {
            http.Error(w, "Insufficient cash", http.StatusBadRequest)
            return
        }
        run.Cash -= total
    } else if side == "sell" {
        // Check holdings.
        // Compute current holding.
        var holding int
        rows, _ := db.Query("SELECT SUM(qty) FROM trades WHERE run_id = ? AND symbol = ? AND side = 'buy'", run.ID, symbol)
        rows.Next()
        rows.Scan(&holding)
        rows.Close()
        rows2, _ := db.Query("SELECT SUM(qty) FROM trades WHERE run_id = ? AND symbol = ? AND side = 'sell'", run.ID, symbol)
        var sold int
        rows2.Next()
        rows2.Scan(&sold)
        rows2.Close()
        holding -= sold
        if holding < qty {
            http.Error(w, "Insufficient shares", http.StatusBadRequest)
            return
        }
        run.Cash += int64(qty)*price - fee
    } else {
        http.Error(w, "Invalid side", http.StatusBadRequest)
        return
    }
    // Insert trade record.
    _, err := db.Exec("INSERT INTO trades (run_id, tick, symbol, side, qty, price, fee) VALUES (?,?,?,?,?,?,?)", run.ID, run.Tick, symbol, side, qty, price, fee)
    if err != nil {
        http.Error(w, "Failed to record trade", http.StatusInternalServerError)
        return
    }
    // Update cash in DB.
    db.Exec("UPDATE runs SET cash = ? WHERE id = ?", run.Cash, run.ID)
    http.Redirect(w, r, fmt.Sprintf("/run/%d", run.ID), http.StatusSeeOther)
}

// AdvanceHandler advances ticks.
func AdvanceHandler(w http.ResponseWriter, r *http.Request, run *Run) {
    if r.Method != http.MethodPost {
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
        return
    }
    delta := parseInt(r.FormValue("delta"))
    if delta <= 0 {
        delta = 1
    }
    if err := run.Advance(delta); err != nil {
        http.Error(w, "Advance failed", http.StatusInternalServerError)
        return
    }
    // If we reached end, auto settle.
    if run.Tick >= 239 {
        run.Settle()
    }
    http.Redirect(w, r, fmt.Sprintf("/run/%d", run.ID), http.StatusSeeOther)
}

// SettleHandler forces settlement.
func SettleHandler(w http.ResponseWriter, r *http.Request, run *Run) {
    if r.Method != http.MethodPost {
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
        return
    }
    if err := run.Settle(); err != nil {
        http.Error(w, "Settle failed", http.StatusInternalServerError)
        return
    }
    http.Redirect(w, r, fmt.Sprintf("/run/%d", run.ID), http.StatusSeeOther)
}

// TapeHandler shows trade tape for a run.
func TapeHandler(w http.ResponseWriter, r *http.Request, run *Run) {
    rows, err := db.Query("SELECT tick, symbol, side, qty, price, fee FROM trades WHERE run_id = ? ORDER BY id", run.ID)
    if err != nil {
        http.Error(w, "db error", http.StatusInternalServerError)
        return
    }
    defer rows.Close()
    type tradeRec struct{ Tick int; Symbol string; Side string; Qty int; Price string; Fee string }
    var trades []tradeRec
    for rows.Next() {
        var t tradeRec
        var price, fee int64
        rows.Scan(&t.Tick, &t.Symbol, &t.Side, &t.Qty, &price, &fee)
        t.Price = formatCents(price)
        t.Fee = formatCents(fee)
        trades = append(trades, t)
    }
    tmpl.ExecuteTemplate(w, "tape.html", map[string]interface{}{"Run": run, "Trades": trades, "Snapshot": snapshotMode})
}

// LeaderboardHandler renders the global leaderboard (optional seed filter).
func LeaderboardHandler(w http.ResponseWriter, r *http.Request) {
    seedFilter := strings.TrimSpace(r.URL.Query().Get("seed"))
    query := "SELECT id, handle, cash, tick FROM runs WHERE status='settled'"
    var args []interface{}
    if seedFilter != "" {
        query += " AND seed = ?"
        seedVal, _ := strconv.ParseInt(seedFilter, 10, 64)
        args = append(args, seedVal)
    }
    query += " ORDER BY cash DESC, tick ASC, id ASC"
    rows, err := db.Query(query, args...)
    if err != nil {
        http.Error(w, "db error", http.StatusInternalServerError)
        return
    }
    defer rows.Close()
    type entry struct{ ID int64; Handle string; Cash string; Tick int }
    var entries []entry
    for rows.Next() {
        var e entry
        var cash int64
        rows.Scan(&e.ID, &e.Handle, &cash, &e.Tick)
        e.Cash = formatCents(cash)
        entries = append(entries, e)
    }
    tmpl.ExecuteTemplate(w, "leaderboard.html", map[string]interface{}{"Entries": entries, "Seed": seedFilter})
}

// Global flag indicating snapshot mode.
var snapshotMode bool

func InitGlobalState(seed int64, snapshot bool) {
    // Set the global seed for price generation (used per Run).
    // Not needed here as each Run stores its own seed.
    snapshotMode = snapshot
}
