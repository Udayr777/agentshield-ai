package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestInterception(t *testing.T) {
	for _, auditOK := range []bool{true, false} {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == "/analyze" {
				w.Write([]byte(`{"risk":"low","mode":"mock","reason":"test"}`))
				return
			}
			if !auditOK {
				w.WriteHeader(503)
				return
			}
			w.Write([]byte(`{"saved":true,"decision":"allow","reason":"test committed","comparison":{"available":true}}`))
		}))
		t.Setenv("AGENT_URL", server.URL)
		req := httptest.NewRequest("POST", "/api/payments", strings.NewReader(`{"recipient":"vendor_acme","amount_cents":10000,"approval_id":"test-capability","invoice":"Invoice 42"}`))
		w := httptest.NewRecorder()
		payment(w, req)
		want := 200
		if !auditOK {
			want = 503
		}
		if w.Code != want {
			t.Fatalf("auditOK=%v status=%d", auditOK, w.Code)
		}
		if auditOK {
			var result struct {
				Comparison struct {
					Available bool `json:"available"`
				} `json:"comparison"`
			}
			if json.Unmarshal(w.Body.Bytes(), &result) != nil || !result.Comparison.Available {
				t.Fatal("Committed source comparison was dropped by the gateway")
			}
		}
		server.Close()
	}
	for _, body := range []string{`{`, `{"amount_cents":1.2}`, `{"unexpected":true}`, `{} {}`} {
		w := httptest.NewRecorder()
		payment(w, httptest.NewRequest("POST", "/api/payments", strings.NewReader(body)))
		if w.Code != 400 {
			t.Fatalf("bad input accepted: %s", body)
		}
	}
}
func TestPolicy(t *testing.T) {
	good := Payment{Recipient: "vendor_acme", Amount: 10000, ApprovalID: "test-capability", Invoice: "Invoice 42"}
	tests := []struct {
		name string
		p    Payment
		r    Risk
		want string
	}{{"authorized", good, Risk{Risk: "low", Mode: "mock"}, "allow"}, {"high risk", good, Risk{Risk: "high", Reason: "injection", Mode: "meta"}, "deny"}, {"failure", good, Risk{Risk: "unknown", Mode: "unavailable"}, "deny"}, {"forged mode", good, Risk{Risk: "low", Mode: "invented"}, "deny"}}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, _ := policy(tt.p, tt.r)
			if got != tt.want {
				t.Fatal(got)
			}
		})
	}
	for _, p := range []Payment{{Recipient: "attacker", Amount: 10000, ApprovalID: good.ApprovalID}, {Recipient: "vendor_acme", Amount: 999999, ApprovalID: good.ApprovalID}, {Recipient: "vendor_acme", Amount: 10000, Approval: "looks fine"}, {Recipient: "vendor_acme", Amount: -1, ApprovalID: good.ApprovalID}} {
		if d, _ := policy(p, Risk{Risk: "low", Mode: "mock"}); d != "deny" {
			t.Fatal("unsafe allow")
		}
	}
}
