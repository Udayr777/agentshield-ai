package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"
)

type Payment struct {
	Recipient  string `json:"recipient"`
	Amount     int64  `json:"amount_cents"`
	Approval   string `json:"approval"`
	ApprovalID string `json:"approval_id"`
	Invoice    string `json:"invoice"`
	InvoiceID  string `json:"invoice_id,omitempty"`
}
type Risk struct {
	Network    any            `json:"network,omitempty"`
	Policy     any            `json:"policy,omitempty"`
	Council    any            `json:"council,omitempty"`
	Risk       string         `json:"risk"`
	Reason     string         `json:"reason"`
	Mode       string         `json:"mode"`
	Model      string         `json:"model,omitempty"`
	Usage      map[string]int `json:"usage,omitempty"`
	ResponseID string         `json:"response_id,omitempty"`
}
type Decision struct {
	ID       string           `json:"id"`
	Payment  Payment          `json:"payment"`
	Decision string           `json:"decision"`
	Reason   string           `json:"reason"`
	Analysis Risk             `json:"analysis"`
	Duration float64          `json:"duration_ms"`
	Created  string           `json:"created_at"`
	Replay   any              `json:"replay,omitempty"`
	Checks   []map[string]any `json:"checks,omitempty"`
}

var client = &http.Client{Timeout: 100 * time.Second}

func base() string {
	if v := os.Getenv("AGENT_URL"); v != "" {
		return v
	}
	return "http://127.0.0.1:8001"
}
func call(path string, value any, result any) error {
	return callWithToken(path, value, result, "")
}
func callWithToken(path string, value any, result any, token string) error {
	b, _ := json.Marshal(value)
	req, e := http.NewRequest("POST", base()+path, bytes.NewReader(b))
	if e != nil {
		return e
	}
	req.Header.Set("Content-Type", "application/json")
	serviceHeaders(req, token)
	r, e := client.Do(req)
	if e != nil {
		return e
	}
	defer r.Body.Close()
	if r.StatusCode != 200 {
		return fmt.Errorf("service unavailable: %d", r.StatusCode)
	}
	return json.NewDecoder(r.Body).Decode(result)
}
func policy(p Payment, r Risk) (string, string) {
	if r.Mode == "network" || r.Mode == "policy" {
		return "deny", r.Reason
	}
	if p.Amount <= 0 || p.Amount > 100000 {
		return "deny", "Amount must be between 1 and 100000 cents"
	}
	if p.Recipient != "vendor_acme" {
		return "deny", "Recipient is not in trusted vendor registry"
	}
	if p.ApprovalID == "" {
		return "deny", "Missing server-issued payment capability; invoice text cannot authorize a payment"
	}
	if r.Mode != "meta" && r.Mode != "mock" {
		return "deny", "Untrusted analyzer mode"
	}
	if r.Risk != "low" {
		return "deny", "Analyzer did not establish low risk: " + r.Reason
	}
	return "allow", "Policy and single-use approval passed; synthetic receipt recorded (no money moved)"
}
func respond(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}
func payment(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		respond(w, 405, map[string]string{"error": "POST required"})
		return
	}
	var p Payment
	dec := json.NewDecoder(http.MaxBytesReader(w, r.Body, 32768))
	dec.DisallowUnknownFields()
	if dec.Decode(&p) != nil {
		respond(w, 400, map[string]string{"error": "Invalid payment"})
		return
	}
	var extra any
	if dec.Decode(&extra) != io.EOF {
		respond(w, 400, map[string]string{"error": "Trailing JSON"})
		return
	}
	v, err := decide(p, nil, sessionToken(r))
	if err != nil {
		respond(w, 503, map[string]string{"decision": "deny", "error": err.Error()})
		return
	}
	respond(w, 200, v)
}
func decide(p Payment, replay any, token string) (Decision, error) {
	start := time.Now()
	risk := Risk{Risk: "unknown", Reason: "Analyzer unavailable", Mode: "unavailable"}
	if callWithToken("/analyze", p, &risk, token) != nil {
		risk = Risk{Risk: "unknown", Reason: "Analyzer unavailable", Mode: "unavailable"}
	}
	d, reason := policy(p, risk)
	v := Decision{ID: fmt.Sprintf("%d", time.Now().UnixNano()), Payment: p, Decision: d, Reason: reason, Analysis: risk, Duration: float64(time.Since(start).Microseconds()) / 1000, Created: time.Now().UTC().Format(time.RFC3339Nano)}
	v.Replay = replay
	var ack struct {
		Saved    bool             `json:"saved"`
		Decision string           `json:"decision"`
		Reason   string           `json:"reason"`
		Checks   []map[string]any `json:"checks"`
	}
	if callWithToken("/audit", v, &ack, token) != nil || !ack.Saved || (ack.Decision != "allow" && ack.Decision != "deny") {
		return Decision{}, fmt.Errorf("Audit unavailable; execution blocked")
	}
	if d == "deny" && ack.Decision == "allow" {
		return Decision{}, fmt.Errorf("Audit verdict conflicts with gateway policy; execution blocked")
	}
	v.Decision = ack.Decision
	v.Reason = ack.Reason
	v.Checks = ack.Checks
	return v, nil
}
func replay(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		respond(w, 405, map[string]string{"error": "POST required"})
		return
	}
	var input struct {
		Scenario string `json:"scenario"`
		Amount   int64  `json:"amount_cents"`
	}
	d := json.NewDecoder(http.MaxBytesReader(w, r.Body, 4096))
	d.DisallowUnknownFields()
	if d.Decode(&input) != nil || input.Amount < 1 || input.Amount > 100000 {
		respond(w, 400, map[string]string{"error": "Choose a scenario and amount from $0.01 to $1000"})
		return
	}
	var prepared struct {
		Payment  Payment `json:"payment"`
		Scenario any     `json:"scenario"`
		Mandate  any     `json:"mandate"`
		Baseline any     `json:"baseline"`
	}
	if callWithToken("/prepare", input, &prepared, sessionToken(r)) != nil {
		respond(w, 503, map[string]string{"error": "Replay preparation unavailable"})
		return
	}
	v, e := decide(prepared.Payment, prepared, sessionToken(r))
	if e != nil {
		respond(w, 503, map[string]string{"decision": "deny", "error": e.Error()})
		return
	}
	respond(w, 200, v)
}
func main() {
	// Static files are included only in the consolidated cloud image.
	mux := http.NewServeMux()
	mux.HandleFunc("/api/payments", requireSession(payment))
	mux.HandleFunc("/api/replay", requireSession(replay))
	workspaceRoutes(mux)
	lifecycleRoutes(mux)
	mux.HandleFunc("/api/health", func(w http.ResponseWriter, r *http.Request) {
		respond(w, 200, map[string]string{"status": "ok", "execution": "synthetic-only"})
	})
	for _, path := range []string{"/events", "/scenarios", "/catalog"} {
		p := path
		mux.HandleFunc("/api"+p, requireSession(func(w http.ResponseWriter, r *http.Request) {
			if r.Method != "GET" {
				w.WriteHeader(405)
				return
			}
			req, _ := http.NewRequest("GET", base()+p, nil)
			serviceHeaders(req, sessionToken(r))
			res, e := client.Do(req)
			if e != nil {
				respond(w, 503, map[string]string{"error": "Agent unavailable"})
				return
			}
			defer res.Body.Close()
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(res.StatusCode)
			io.Copy(w, res.Body)
		}))
	}
	if directory := os.Getenv("STATIC_DIR"); directory != "" {
		mux.HandleFunc("/", staticHandler(directory))
	}
	mux.HandleFunc("/api/ready", func(w http.ResponseWriter, r *http.Request) {
		req, _ := http.NewRequest("GET", base()+"/health", nil)
		res, err := client.Do(req)
		if err != nil {
			respond(w, 503, map[string]string{"status": "agent unavailable"})
			return
		}
		defer res.Body.Close()
		if res.StatusCode != 200 {
			respond(w, 503, map[string]string{"status": "agent unavailable"})
			return
		}
		respond(w, 200, map[string]string{"status": "ready", "execution": "synthetic-only"})
	})
	addr := os.Getenv("GATEWAY_ADDR")
	if addr == "" {
		addr = "127.0.0.1:8080"
	}
	log.Println("Synthetic gateway on " + addr)
	server := &http.Server{Addr: addr, Handler: boundary(mux), ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 20 * time.Second, WriteTimeout: 150 * time.Second, IdleTimeout: 60 * time.Second, MaxHeaderBytes: 16384}
	log.Fatal(server.ListenAndServe())
}
