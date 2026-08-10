package main

import (
    "flag"
    "log"
    "net/http"
    "os"
    "path/filepath"
    "strconv"
)

func main() {
    // Command‑line flags
    seed := flag.Int64("seed", 42, "Seed for deterministic market")
    port := flag.Int("port", 8080, "Port to listen on")
    dbPath := flag.String("db", "seedstreet.db", "SQLite database file path")
    snapshot := flag.Bool("snapshot", false, "Enable snapshot mode (deterministic HTML output)")
    flag.Parse()

    // Ensure working directory is the task directory so relative paths work
    cwd, _ := os.Getwd()
    // If running from repository root, adjust path
    if !filepath.IsAbs(*dbPath) && !filepath.IsAbs("seedstreet.db") {
        // keep as is (relative to cwd)
    }

    // Initialize DB (creates tables if needed)
    if err := InitDB(*dbPath); err != nil {
        log.Fatalf("Failed to init DB: %v", err)
    }

    // Initialize global state
    InitGlobalState(*seed, *snapshot)

    // Register HTTP handlers
    http.HandleFunc("/", HomeHandler)
    http.HandleFunc("/run/new", NewRunHandler)
    http.HandleFunc("/run/", RunRouter) // will dispatch based on sub‑paths
    http.HandleFunc("/leaderboard", LeaderboardHandler)

    addr := ":" + strconv.Itoa(*port)
    log.Printf("Server starting on %s (seed=%d, db=%s, snapshot=%v)", addr, *seed, *dbPath, *snapshot)
    if err := http.ListenAndServe(addr, nil); err != nil {
        log.Fatalf("Server error: %v", err)
    }
}
