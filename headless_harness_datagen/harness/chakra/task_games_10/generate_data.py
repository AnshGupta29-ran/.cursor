import os
import sqlite3
import json
from pathlib import Path

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript('''
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seed INTEGER NOT NULL,
    handle TEXT NOT NULL,
    cash INTEGER NOT NULL,
    tick INTEGER NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    tick INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    qty INTEGER NOT NULL,
    price INTEGER NOT NULL,
    fee INTEGER NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);
''')
    conn.commit()
    return conn

def price(seed, symbol, tick):
    # Simplified deterministic price: base = 1000 + (hash(symbol) % 900)
    base = 1000 + (hash(symbol) % 900)
    # price grows linearly with tick and seed influence
    return base + (tick * 2) + (seed % 10)

def fee_for_trade(price_cents, qty):
    total = price_cents * qty
    fee = total * 15 // 10000
    return max(fee, 100)

def main():
    root = Path(__file__).parent
    db_path = root / 'seedstreet.db'
    conn = init_db(db_path)
    cur = conn.cursor()
    # Insert a sample run
    seed = 42
    handle = 'DemoTrader'
    init_cash = 1_000_000  # cents
    cur.execute('INSERT INTO runs (seed, handle, cash, tick, status) VALUES (?,?,?,?,?)',
                (seed, handle, init_cash, 239, 'settled'))
    run_id = cur.lastrowid
    # Simulate some trades
    trades = [
        # (tick, symbol, side, qty)
        (0, 'KELP', 'buy', 40),
        (10, 'KELP', 'sell', 20),
        (50, 'BRINE', 'buy', 30),
        (100, 'AMBR', 'buy', 25),
        (150, 'SALTGLASS', 'sell', 15),
    ]
    cash = init_cash
    for tick, sym, side, qty in trades:
        p = price(seed, sym, tick)
        fee = fee_for_trade(p, qty)
        total = p * qty + fee if side == 'buy' else - (p * qty - fee)
        cash += -total if side == 'buy' else total
        cur.execute('INSERT INTO trades (run_id, tick, symbol, side, qty, price, fee) VALUES (?,?,?,?,?,?,?)',
                    (run_id, tick, sym, side, qty, p, fee))
    # Liquidate remaining holdings at final tick price
    holdings = {}
    for sym, side, qty in [(t[1], t[2], t[3]) for t in trades]:
        holdings.setdefault(sym, 0)
        holdings[sym] += qty if side == 'buy' else -qty
    for sym, qty in holdings.items():
        if qty > 0:
            p = price(seed, sym, 239)
            cash += qty * p
    # Update cash
    cur.execute('UPDATE runs SET cash = ? WHERE id = ?', (cash, run_id))
    conn.commit()
    conn.close()
    # Generate static HTML pages using simple templates.
    static_dir = root / 'static'
    static_dir.mkdir(exist_ok=True)
    # Load template files (same as Go templates) and perform minimal replacement.
    def render_template(tpl_path, ctx):
        txt = tpl_path.read_text()
        for k, v in ctx.items():
            txt = txt.replace('{{.'+k+'}}', str(v))
        return txt
    # Home page
    home_tpl = root / 'templates' / 'home.html'
    runs_data = [{'ID': run_id, 'Handle': handle, 'Cash': f"{cash/100:.2f}", 'Tick': 239, 'Status': 'settled'}]
    home_html = home_tpl.read_text().replace('{{range .Runs}}', '')
    # Very simple insertion – just list the run manually.
    run_row = f"<tr><td><a href='run/{run_id}'>{run_id}</a></td><td>{handle}</td><td>{cash/100:.2f}</td><td>239</td><td>settled</td></tr>"
    home_html = home_html.replace('{{end}}', run_row)
    (static_dir / 'home.html').write_text(home_html)
    # Floor page for run 1
    floor_tpl = root / 'templates' / 'floor.html'
    holdings_rows = []
    for sym, qty in holdings.items():
        price_now = price(seed, sym, 239)
        holdings_rows.append(f"<tr><td>{sym}</td><td>{qty}</td><td>{price_now/100:.2f}</td></tr>")
    holdings_html = '\n'.join(holdings_rows)
    floor_html = floor_tpl.read_text()
    floor_html = floor_html.replace('{{.Run.ID}}', str(run_id))
    floor_html = floor_html.replace('{{.Run.Handle}}', handle)
    floor_html = floor_html.replace('{{.Run.Tick}}', '239')
    floor_html = floor_html.replace('{{.Cash}}', f"{cash/100:.2f}")
    floor_html = floor_html.replace('{{range .Holdings}}', holdings_html)
    (static_dir / f'run_{run_id}.html').write_text(floor_html)
    # Leaderboard page
    lb_tpl = root / 'templates' / 'leaderboard.html'
    lb_html = lb_tpl.read_text().replace('{{range .Entries}}', '')
    entry_row = f"<tr><td>{run_id}</td><td>{handle}</td><td>{cash/100:.2f}</td><td>239</td></tr>"
    lb_html = lb_html.replace('{{end}}', entry_row)
    (static_dir / 'leaderboard.html').write_text(lb_html)
    # Tape page
    tape_tpl = root / 'templates' / 'tape.html'
    # Simple placeholder – list trades
    trade_rows = []
    for t in trades:
        tick, sym, side, qty = t
        p = price(seed, sym, tick)
        fee = fee_for_trade(p, qty)
        trade_rows.append(f"<tr><td>{tick}</td><td>{sym}</td><td>{side}</td><td>{qty}</td><td>{p/100:.2f}</td><td>{fee/100:.2f}</td></tr>")
    trades_html = '\n'.join(trade_rows)
    tape_html = tape_tpl.read_text().replace('{{range .Trades}}', trades_html)
    (static_dir / f'tape_{run_id}.html').write_text(tape_html)

if __name__ == '__main__':
    main()
