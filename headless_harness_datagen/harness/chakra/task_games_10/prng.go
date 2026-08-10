package main

import (
    "encoding/binary"
    "math"
)

// SplitMix64 is a simple, fast, deterministic PRNG.
// It produces 64‑bit output; we expose 32‑bit ints for convenience.

type SplitMix64 struct {
    state uint64
}

func NewSplitMix64(seed int64) *SplitMix64 {
    // The original algorithm adds a constant to the seed.
    return &SplitMix64{state: uint64(seed) + 0x9e3779b97f4a7c15}
}

func (s *SplitMix64) Uint64() uint64 {
    z := s.state
    s.state += 0x9e3779b97f4a7c15
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9
    z = (z ^ (z >> 27)) * 0x94d049bb133111eb
    return z ^ (z >> 31)
}

func (s *SplitMix64) Uint32() uint32 {
    return uint32(s.Uint64() >> 32)
}

// Float64 returns a float in [0,1).
func (s *SplitMix64) Float64() float64 {
    // Use 53 bits of precision.
    return float64(s.Uint64()>>11) * (1.0 / (1 << 53))
}

// Helper to get deterministic int in [0, n).
func (s *SplitMix64) Intn(n int) int {
    if n <= 0 {
        return 0
    }
    return int(s.Uint64() % uint64(n))
}
