package main

import (
	"encoding/json"
	"net/http"
)

func lifecycleRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/api/public/help", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			w.WriteHeader(405)
			return
		}
		proxyAgent("/public/help")(w, r)
	})
	mux.HandleFunc("/api/invoices/chaos", requireSession(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			w.WriteHeader(405)
			return
		}
		var input struct {
			InvoiceID string `json:"invoice_id"`
			Scenario  string `json:"scenario"`
			Payload   string `json:"payload"`
		}
		d := json.NewDecoder(http.MaxBytesReader(w, r.Body, 8192))
		d.DisallowUnknownFields()
		if d.Decode(&input) != nil || len(input.InvoiceID) != 32 {
			respond(w, 400, map[string]string{"error": "Choose an owned invoice and a sandbox preset"})
			return
		}
		var prepared struct {
			Payment   Payment `json:"payment"`
			Scenario  any     `json:"scenario"`
			Mandate   any     `json:"mandate"`
			Baseline  any     `json:"baseline"`
			SourceSHA string  `json:"source_sha256"`
		}
		token := sessionToken(r)
		if callWithToken("/invoice-chaos", input, &prepared, token) != nil {
			respond(w, 404, map[string]string{"error": "Owned invoice unavailable or invalid sandbox request"})
			return
		}
		v, e := decide(prepared.Payment, prepared, token)
		if e != nil {
			respond(w, 503, map[string]string{"error": e.Error()})
			return
		}
		respond(w, 200, v)
	}))
	for _, path := range []string{"/decisions/insight", "/decisions/explain", "/documents", "/documents/upload", "/documents/segment", "/documents/explain-visual", "/documents/visual-clip", "/documents/visual-fixture", "/documents/confirm", "/threats/share", "/extension/pair", "/extension/revoke", "/arena/create", "/arena/inbox"} {
		p := path
		mux.HandleFunc("/api"+p, requireSession(proxyAgent(p)))
	}
	for _, path := range []string{"/threats", "/arena/state", "/arena/submit", "/extension/import"} {
		p := path
		mux.HandleFunc("/api"+p, proxyAgent(p))
	}
	mux.HandleFunc("/api/arena/run", requireSession(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			w.WriteHeader(405)
			return
		}
		var input struct {
			ArenaID     string `json:"arena_id"`
			Scenario    string `json:"scenario"`
			Payload     string `json:"payload"`
			ChallengeID string `json:"challenge_id"`
		}
		d := json.NewDecoder(http.MaxBytesReader(w, r.Body, 8192))
		d.DisallowUnknownFields()
		if d.Decode(&input) != nil {
			respond(w, 400, map[string]string{"error": "Invalid arena request"})
			return
		}
		var prepared struct {
			Payment     Payment `json:"payment"`
			Scenario    any     `json:"scenario"`
			Mandate     any     `json:"mandate"`
			Baseline    any     `json:"baseline"`
			ArenaID     string  `json:"arena_id"`
			ChallengeID string  `json:"challenge_id"`
		}
		token := sessionToken(r)
		if callWithToken("/arena/prepare", input, &prepared, token) != nil {
			respond(w, 409, map[string]string{"error": "Arena unavailable, queue item already used, or attempt budget exhausted"})
			return
		}
		receipt, e := decide(prepared.Payment, prepared, token)
		if e != nil {
			respond(w, 503, map[string]string{"error": e.Error()})
			return
		}
		var arena any
		if callWithToken("/arena/finish", map[string]any{"arena_id": prepared.ArenaID, "challenge_id": prepared.ChallengeID, "receipt": receipt}, &arena, token) != nil {
			respond(w, 503, map[string]string{"error": "Receipt committed but arena counter unavailable"})
			return
		}
		respond(w, 200, map[string]any{"receipt": receipt, "arena": arena, "scripted_proposal": true})
	}))
}
