package main

import (
    "encoding/json"
    "fmt"
    "log"
    "math"
    "net/http"
    "os"
    "path/filepath"
    "strings"
    "time"
)

type FAQEntry struct {
    ID         string   `json:"id"`
    Question   string   `json:"question"`
    Answer     string   `json:"answer"`
    Category   string   `json:"category"`
    Tags       []string `json:"tags"`
    SourceRef  string   `json:"source_ref"`
    Status     string   `json:"status"`
    UpdatedAt  string   `json:"updated_at"`
}

type SearchResult struct {
    EntryID    string   `json:"entry_id"`
    Question   string   `json:"question"`
    Snippet    string   `json:"snippet"`
    Score      float64  `json:"score"`
    MatchedTerms []string `json:"matched_terms"`
    SourceRef  string   `json:"source_ref"`
}

type SearchResponse struct {
    Tier    string          `json:"tier"`
    Results []SearchResult  `json:"results"`
}

var (
    faqs      []FAQEntry
    idf       map[string]float64
    vectors   []map[string]float64 // tf-idf vectors for each FAQ
    // Simple threshold profile (hard‑coded for demo)
    autoAnswerMin = 0.7
    suggestMin    = 0.4
)

func tokenize(text string) []string {
    // lower‑case, split on non‑alphanum
    cleaned := strings.ToLower(text)
    cleaned = strings.ReplaceAll(cleaned, "-", " ")
    fields := strings.FieldsFunc(cleaned, func(r rune) bool {
        return !(r >= 'a' && r <= 'z' || r >= '0' && r <= '9')
    })
    return fields
}

func buildIndex() {
    // compute document frequencies
    df := make(map[string]int)
    for _, f := range faqs {
        seen := make(map[string]bool)
        tokens := tokenize(f.Question + " " + f.Answer)
        for _, t := range tokens {
            if !seen[t] {
                df[t]++
                seen[t] = true
            }
        }
    }
    N := float64(len(faqs))
    idf = make(map[string]float64)
    for term, freq := range df {
        idf[term] = math.Log(N / float64(freq))
    }
    // compute tf‑idf vector per FAQ
    vectors = make([]map[string]float64, len(faqs))
    for i, f := range faqs {
        tf := make(map[string]float64)
        tokens := tokenize(f.Question + " " + f.Answer)
        for _, t := range tokens {
            tf[t]++
        }
        // normalize tf
        length := float64(len(tokens))
        vec := make(map[string]float64)
        for term, cnt := range tf {
            vec[term] = (cnt / length) * idf[term]
        }
        vectors[i] = vec
    }
}

func cosine(a, b map[string]float64) float64 {
    var dot float64
    for term, av := range a {
        if bv, ok := b[term]; ok {
            dot += av * bv
        }
    }
    var magA, magB float64
    for _, v := range a {
        magA += v * v
    }
    for _, v := range b {
        magB += v * v
    }
    if magA == 0 || magB == 0 {
        return 0
    }
    return dot / (math.Sqrt(magA) * math.Sqrt(magB))
}

func search(query string, topK int) (string, []SearchResult) {
    qTokens := tokenize(query)
    tf := make(map[string]float64)
    for _, t := range qTokens {
        tf[t]++
    }
    length := float64(len(qTokens))
    qVec := make(map[string]float64)
    for term, cnt := range tf {
        if idfVal, ok := idf[term]; ok {
            qVec[term] = (cnt / length) * idfVal
        }
    }
    // compute scores
    type scored struct{ idx int; score float64 }
    scoredList := make([]scored, len(faqs))
    for i, vec := range vectors {
        s := cosine(qVec, vec)
        scoredList[i] = scored{i, s}
    }
    // simple sort descending
    sort.Slice(scoredList, func(i, j int) bool { return scoredList[i].score > scoredList[j].score })
    // pick topK
    var results []SearchResult
    for i := 0; i < topK && i < len(scoredList); i++ {
        idx := scoredList[i].idx
        entry := faqs[idx]
        score := scoredList[i].score
        // snippet: first 120 chars of answer
        snippet := entry.Answer
        if len(snippet) > 120 { snippet = snippet[:120] + "…" }
        // matched terms (intersection)
        matchSet := make(map[string]bool)
        for _, t := range qTokens { matchSet[t] = true }
        var matched []string
        for _, t := range tokenize(entry.Question + " " + entry.Answer) {
            if matchSet[t] { matched = append(matched, t) }
        }
        results = append(results, SearchResult{EntryID: entry.ID, Question: entry.Question, Snippet: snippet, Score: score, MatchedTerms: matched, SourceRef: entry.SourceRef})
    }
    // determine tier based on top score
    tier := "escalate"
    if len(results) > 0 {
        topScore := results[0].Score
        switch {
        case topScore >= autoAnswerMin:
            tier = "auto"
        case topScore >= suggestMin:
            tier = "suggest"
        default:
            tier = "escalate"
        }
    }
    return tier, results
}

func searchHandler(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
        return
    }
    var payload struct { Query string `json:"query"`; TopK int `json:"top_k"` }
    dec := json.NewDecoder(r.Body)
    if err := dec.Decode(&payload); err != nil {
        http.Error(w, "invalid json", http.StatusBadRequest)
        return
    }
    if strings.TrimSpace(payload.Query) == "" {
        http.Error(w, "query required", http.StatusBadRequest)
        return
    }
    if payload.TopK <= 0 { payload.TopK = 5 }
    tier, results := search(payload.Query, payload.TopK)
    resp := SearchResponse{Tier: tier, Results: results}
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(resp)
}

func main() {
    // load seed data
    exePath, _ := os.Executable()
    baseDir := filepath.Dir(exePath)
    dataPath := filepath.Join(baseDir, "data", "seed_faqs.json")
    f, err := os.Open(dataPath)
    if err != nil { log.Fatalf("cannot open seed data: %v", err) }
    defer f.Close()
    if err := json.NewDecoder(f).Decode(&faqs); err != nil { log.Fatalf("cannot decode seed data: %v", err) }
    buildIndex()
    // static files
    fs := http.FileServer(http.Dir(filepath.Join(baseDir, "web")))
    http.Handle("/", fs)
    http.HandleFunc("/api/search", searchHandler)
    // simple health endpoint
    http.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) { fmt.Fprint(w, `{"status":"ok"}`) })
    // server on 8080
    port := "8080"
    log.Printf("AnswerAtlas server listening on :%s", port)
    if err := http.ListenAndServe(":"+port, nil); err != nil {
        log.Fatalf("server error: %v", err)
    }
}
