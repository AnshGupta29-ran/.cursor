package main

import (
    "fmt"
    "strconv"
)

// formatCents returns a string like "123.45" for an amount in cents.
func formatCents(cents int64) string {
    dollars := cents / 100
    remainder := cents % 100
    return fmt.Sprintf("%d.%02d", dollars, remainder)
}

// feeForTrade computes the fee (0.15% of total, minimum 1 credit).
func feeForTrade(priceCents int64, qty int) int64 {
    total := priceCents * int64(qty)
    fee := total * 15 / 10000 // 0.15%
    if fee < 100 { // minimum 1 credit (100 cents)
        fee = 100
    }
    return fee
}

// parseInt parses a string into int, returning 0 on error.
func parseInt(s string) int {
    v, err := strconv.Atoi(s)
    if err != nil {
        return 0
    }
    return v
}
