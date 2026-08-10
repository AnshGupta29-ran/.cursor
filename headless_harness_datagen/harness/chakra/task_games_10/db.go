package main

import (
    "database/sql"
    "fmt"
    "log"
    _ "modernc.org/sqlite"
)

var db *sql.DB

// InitDB opens (or creates) the SQLite database and ensures the schema exists.
func InitDB(path string) error {
    var err error
    db, err = sql.Open("sqlite", path)
    if err != nil {
        return fmt.Errorf("open db: %w", err)
    }
    // Verify connection
    if err = db.Ping(); err != nil {
        return fmt.Errorf("ping db: %w", err)
    }
    // Create tables if not exist
    schema := []string{
        `CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seed INTEGER NOT NULL,
            handle TEXT NOT NULL,
            cash INTEGER NOT NULL,
            tick INTEGER NOT NULL,
            status TEXT NOT NULL
        );`,
        `CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            tick INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            qty INTEGER NOT NULL,
            price INTEGER NOT NULL,
            fee INTEGER NOT NULL,
            FOREIGN KEY(run_id) REFERENCES runs(id)
        );`,
    }
    for _, stmt := range schema {
        if _, err = db.Exec(stmt); err != nil {
            return fmt.Errorf("exec schema: %w", err)
        }
    }
    log.Println("Database initialized at", path)
    return nil
}
