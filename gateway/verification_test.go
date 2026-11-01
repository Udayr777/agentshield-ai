package main

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestVerificationRoutesKeepResendPrivateAndConfirmationPublic(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/email-verification/confirm" || r.Method != "POST" {
			t.Errorf("unexpected upstream request %s %s", r.Method, r.URL.Path)
		}
		if r.Header.Get("X-Service-Token") != "test-service-secret" {
			t.Error("internal authentication missing")
		}
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"message":"Email verified"}`))
	}))
	defer upstream.Close()
	t.Setenv("AGENT_URL", upstream.URL)
	t.Setenv("SERVICE_TOKEN", "test-service-secret")
	mux := http.NewServeMux()
	workspaceRoutes(mux)
	for _, path := range []string{"/api/email-verification", "/api/email-verification/request"} {
		recorder := httptest.NewRecorder()
		mux.ServeHTTP(recorder, httptest.NewRequest("POST", path, strings.NewReader(`{}`)))
		if recorder.Code != 401 {
			t.Errorf("anonymous access to %s: %d", path, recorder.Code)
		}
	}
	recorder := httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest("POST", "/api/auth/email-verification/confirm", strings.NewReader(`{"token":"synthetic-token"}`)))
	if recorder.Code != 200 {
		t.Fatalf("confirmation unavailable without session: %d", recorder.Code)
	}
}
