package main

import (
    "database/sql"
    "fmt"
    "math"
    "strings"
)

// Instrument defines a tradable asset.
type Instrument struct {
    Symbol string
    Name   string
    Sector string
    Base   int64 // cents
    Drift  float64
    Vol    float64
}

// Global list of symbols – deterministic order.
var instrumentSymbols = []string{"KELP", "BRINE", "AMBR", "SALTGLASS", "CORAL"}

// Global PRNG seeded per run for instrument generation.
func generateInstruments(seed int64) []Instrument {
    rng := NewSplitMix64(seed)
    instruments := make([]Instrument, len(instrumentSymbols))
    sectors := []string{"Seafood", "Water", "Amber", "Glass", "Coral"}
    for i, sym := range instrumentSymbols {
        base := int64(1000 + rng.Intn(9000)) // 10.00 - 100.00 credits
        drift := rng.Float64()*0.001 - 0.0005 // small drift per tick
        vol := rng.Float64()*0.02 + 0.01    // volatility 1%‑3%
        instruments[i] = Instrument{Symbol: sym, Name: sym+" Corp", Sector: sectors[i%len(sectors)], Base: base, Drift: drift, Vol: vol}
    }
    return instruments
}

// Run represents a trading session.
type Run struct {
    ID     int64
    Seed   int64
    Handle string
    Cash   int64 // cents
    Tick   int   // 0‑239
    Status string // "active" or "settled"
    Instruments []Instrument
    Events []int // ticks when shocks occur
}

// NewRun creates a fresh run entry in the DB.
func NewRun(handle string, seed int64) (*Run, error) {
    // initial cash 10,000 credits = 1,000,000 cents
    const initCash = 1000000
    res, err := db.Exec("INSERT INTO runs (seed, handle, cash, tick, status) VALUES (?,?,?,?,?)", seed, handle, initCash, 0, "active")
    if err != nil {
        return nil, fmt.Errorf("insert run: %w", err)
    }
    id, _ := res.LastInsertId()
    run := &Run{ID: id, Seed: seed, Handle: handle, Cash: initCash, Tick: 0, Status: "active"}
    run.Instruments = generateInstruments(seed)
    run.Events = generateEventTicks(seed)
    return run, nil
}

// LoadRun fetches a run from DB.
func LoadRun(id int64) (*Run, error) {
    row := db.QueryRow("SELECT id, seed, handle, cash, tick, status FROM runs WHERE id = ?", id)
    var r Run
    if err := row.Scan(&r.ID, &r.Seed, &r.Handle, &r.Cash, &r.Tick, &r.Status); err != nil {
        return nil, fmt.Errorf("load run: %w", err)
    }
    r.Instruments = generateInstruments(r.Seed)
    r.Events = generateEventTicks(r.Seed)
    return &r, nil
}

// generateEventTicks creates 3 deterministic shock ticks from seed.
func generateEventTicks(seed int64) []int {
    rng := NewSplitMix64(seed + 12345)
    ticks := make([]int, 3)
    for i := 0; i < 3; i++ {
        ticks[i] = rng.Intn(200) + 20 // keep within 20‑219 range
    }
    // sort
    for i := 0; i < len(ticks)-1; i++ {
        for j := i + 1; j < len(ticks); j++ {
            if ticks[j] < ticks[i] {
                ticks[i], ticks[j] = ticks[j], ticks[i]
            }
        }
    }
    return ticks
}

// price returns deterministic price in cents for a symbol at a given tick.
func (r *Run) price(symbol string, tick int) int64 {
    // find instrument
    var instr *Instrument
    for i := range r.Instruments {
        if r.Instruments[i].Symbol == strings.ToUpper(symbol) {
            instr = &r.Instruments[i]
            break
        }
    }
    if instr == nil {
        return 0
    }
    // deterministic random walk using per‑symbol PRNG seeded with seed+symbol hash.
    // Combine seed, symbol, tick to get a reproducible normal variable.
    seedVal := r.Seed + int64(hashString(instr.Symbol))
    rng := NewSplitMix64(seedVal)
    // Advance rng to the required tick (skip previous draws).
    for i := 0; i < tick; i++ {
        _ = rng.Uint64()
    }
    // Normal via Box‑Muller (use two draws).
    u1 := rng.Float64()
    u2 := rng.Float64()
    z := math.Sqrt(-2.0*math.Log(u1)) * math.Cos(2*math.Pi*u2) // standard normal
    // price = base * exp(drift*tick + vol*z)
    priceFloat := float64(instr.Base) * math.Exp(instr.Drift*float64(tick)+instr.Vol*z)
    // round to nearest cent
    return int64(math.Round(priceFloat))
}

// ApplyShock modifies drift of instruments belonging to a sector at a given tick.
func (r *Run) applyShock(tick int) {
    // find which event triggers (if any)
    for _, ev := range r.Events {
        if ev == tick {
            // pick a sector based on tick value deterministic
            idx := tick % len(r.Instruments)
            sector := r.Instruments[idx].Sector
            // increase drift for all instruments in that sector for remaining ticks
            for i := range r.Instruments {
                if r.Instruments[i].Sector == sector {
                    r.Instruments[i].Drift += 0.001 // small bump
                }
            }
            break
        }
    }
}

// Advance advances the run by delta ticks (positive).
func (r *Run) Advance(delta int) error {
    if r.Status != "active" {
        return fmt.Errorf("run not active")
    }
    target := r.Tick + delta
    if target > 239 {
        target = 239
    }
    // apply shocks for any ticks crossed
    for t := r.Tick + 1; t <= target; t++ {
        r.applyShock(t)
    }
    r.Tick = target
    // persist tick
    _, err := db.Exec("UPDATE runs SET tick = ? WHERE id = ?", r.Tick, r.ID)
    return err
}

// Settle finalizes the run, liquidating holdings at final prices.
func (r *Run) Settle() error {
    if r.Status != "active" {
        return fmt.Errorf("already settled")
    }
    // compute holdings from trades
    holdings := map[string]int{}
    rows, err := db.Query("SELECT symbol, side, qty FROM trades WHERE run_id = ?", r.ID)
    if err != nil {
        return err
    }
    defer rows.Close()
    for rows.Next() {
        var sym, side string
        var qty int
        if err := rows.Scan(&sym, &side, &qty); err != nil {
            return err
        }
        if side == "buy" {
            holdings[sym] += qty
        } else if side == "sell" {
            holdings[sym] -= qty
        }
    }
    // liquidate
    for sym, qty := range holdings {
        if qty <= 0 {
            continue
        }
        price := r.price(sym, r.Tick)
        proceeds := int64(qty) * price
        r.Cash += proceeds
    }
    r.Status = "settled"
    // update DB
    _, err = db.Exec("UPDATE runs SET cash = ?, status = ? WHERE id = ?", r.Cash, r.Status, r.ID)
    return err
}

// hashString produces a simple deterministic hash for a string.
func hashString(s string) uint64 {
    var h uint64 = 1469598103934665603
    for i := 0; i < len(s); i++ {
        h ^= uint64(s[i])
        h *= 1099511628211
    }
    return h
}
