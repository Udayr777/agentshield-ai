package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestGmailCallbackStripsCodeAndUsesFixedLocalRedirect(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/gmail/callback" {
			t.Errorf("unexpected path %s", r.URL.Path)
		}
		w.WriteHeader(200)
	}))
	defer upstream.Close()
	t.Setenv("AGENT_URL", upstream.URL)
	mux := http.NewServeMux()
	gmailRoutes(mux)
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, httptest.NewRequest("GET", "/api/gmail/callback?state=opaque&code=private-code", nil))
	if w.Code != 303 || w.Header().Get("Location") != "/#gmail=connected" || w.Header().Get("Referrer-Policy") != "no-referrer" {
		t.Fatalf("unsafe callback: %d %s", w.Code, w.Header().Get("Location"))
	}
	w = httptest.NewRecorder()
	mux.ServeHTTP(w, httptest.NewRequest("GET", "/api/gmail/status", nil))
	if w.Code != 401 {
		t.Fatalf("Gmail status must require auth, got %d", w.Code)
	}
}
