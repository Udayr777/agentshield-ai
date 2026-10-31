package main

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestBoundaryAndAnonymousAccess(t *testing.T) {
	handler := boundary(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(204) }))
	tests := []struct {
		method, origin, content string
		status                  int
	}{{"POST", "https://evil.example", "application/json", 403}, {"POST", "http://example.test", "text/plain", 415}, {"DELETE", "", "", 405}, {"POST", "http://example.test", "application/json", 204}}
	for _, tt := range tests {
		r := httptest.NewRequest(tt.method, "http://example.test/api/invoices", strings.NewReader(`{}`))
		r.Header.Set("Origin", tt.origin)
		r.Header.Set("Content-Type", tt.content)
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, r)
		if w.Code != tt.status {
			t.Fatalf("%+v got %d", tt, w.Code)
		}
	}
	w := httptest.NewRecorder()
	requireSession(func(w http.ResponseWriter, r *http.Request) { t.Fatal("Anonymous request reached protected handler") })(w, httptest.NewRequest("GET", "/api/invoices", nil))
	if w.Code != 401 {
		t.Fatal(w.Code)
	}
}
