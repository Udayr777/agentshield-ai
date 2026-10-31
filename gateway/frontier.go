package main

import (
	"encoding/json"
	"net/http"
)

func frontierRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/api/network/feed", proxyAgent("/network/feed"))
	for _, path := range []string{"/network", "/network/preferences", "/policies", "/policies/propose", "/policies/promote", "/policies/rollback", "/escrow", "/escrow/create", "/escrow/cancel", "/passkeys/register/options", "/passkeys/register/verify", "/escrow/release/options"} {
		mux.HandleFunc("/api"+path, requireSession(proxyAgent(path)))
	}
	mux.HandleFunc("/api/escrow/release", requireSession(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			w.WriteHeader(405)
			return
		}
		var input map[string]any
		if json.NewDecoder(http.MaxBytesReader(w, r.Body, 32768)).Decode(&input) != nil {
			respond(w, 400, map[string]string{"error": "Invalid passkey assertion"})
			return
		}
		var prepared struct {
			Payment Payment `json:"payment"`
			HoldID  string  `json:"hold_id"`
		}
		if callWithToken("/escrow/release/authorize", input, &prepared, sessionToken(r)) != nil {
			respond(w, 409, map[string]string{"error": "Passkey release was not authorized. Check the challenge, hold expiry and registered device."})
			return
		}
		receipt, err := decide(prepared.Payment, map[string]string{"kind": "passkey-gated-synthetic-release", "hold_id": prepared.HoldID}, sessionToken(r))
		if err != nil {
			respond(w, 503, map[string]string{"error": "Simulation did not complete; inspect the hold before retrying."})
			return
		}
		respond(w, 200, receipt)
	}))
}
