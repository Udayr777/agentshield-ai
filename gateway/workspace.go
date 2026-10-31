package main

import (
	"bytes"
	"encoding/json"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"
)

func sessionToken(r *http.Request) string {
	c, e := r.Cookie("agentshield_session")
	if e != nil {
		return ""
	}
	return c.Value
}
func serviceHeaders(req *http.Request, token string) {
	secret := os.Getenv("SERVICE_TOKEN")
	if secret == "" {
		path := os.Getenv("SERVICE_TOKEN_FILE")
		if path == "" {
			path = "../.service-token"
		}
		b, _ := os.ReadFile(path)
		secret = strings.TrimSpace(string(b))
	}
	req.Header.Set("X-Service-Token", secret)
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
}
func requireSession(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token := sessionToken(r)
		if token == "" {
			respond(w, 401, map[string]string{"error": "Sign in to access your workspace."})
			return
		}
		req, _ := http.NewRequest("GET", base()+"/session", nil)
		serviceHeaders(req, token)
		res, e := client.Do(req)
		if e != nil {
			respond(w, 503, map[string]string{"error": "Account service unavailable"})
			return
		}
		defer res.Body.Close()
		if res.StatusCode != 200 {
			status := res.StatusCode
			if status != 401 {
				status = 503
			}
			respond(w, status, map[string]string{"error": "Session unavailable. Sign in again if it expired."})
			return
		}
		next(w, r)
	}
}

type bucket struct {
	start time.Time
	count int
}

var limits = struct {
	sync.Mutex
	entries map[string]bucket
}{entries: map[string]bucket{}}

func boundary(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Cache-Control", "no-store")
		w.Header().Set("Referrer-Policy", "same-origin")
		if r.URL.Path == "/api/extension/import" {
			origin := r.Header.Get("Origin")
			u, e := url.Parse(origin)
			if origin != "" && e == nil && u.Scheme == "chrome-extension" && len(u.Host) == 32 {
				w.Header().Set("Access-Control-Allow-Origin", origin)
				w.Header().Set("Vary", "Origin")
				w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
				w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
				if r.Method == "OPTIONS" {
					w.WriteHeader(204)
					return
				}
			}
		}
		if r.Method != "GET" && r.Method != "POST" {
			respond(w, 405, map[string]string{"error": "Method not allowed"})
			return
		}
		if r.Method == "POST" {
			if !strings.HasPrefix(r.Header.Get("Content-Type"), "application/json") {
				respond(w, 415, map[string]string{"error": "JSON required"})
				return
			}
			if origin := r.Header.Get("Origin"); origin != "" {
				u, e := url.Parse(origin)
				extension := r.URL.Path == "/api/extension/import" && e == nil && u.Scheme == "chrome-extension" && len(u.Host) == 32
				if !extension && (e != nil || u.Host != r.Host || (u.Scheme != "http" && u.Scheme != "https")) {
					respond(w, 403, map[string]string{"error": "Cross-origin request blocked"})
					return
				}
			}
		}
		host, _, _ := net.SplitHostPort(r.RemoteAddr)
		key := host + "|" + r.URL.Path
		max := 600
		if r.Method == "POST" {
			max = 300
		}
		if r.URL.Path == "/api/chat" {
			max = 20
		}
		if strings.HasPrefix(r.URL.Path, "/api/gmail/") {
			max = 20
		}
		if r.URL.Path == "/api/arena/submit" {
			max = 10
		}
		if r.URL.Path == "/api/extension/import" {
			max = 10
		}
		if r.URL.Path == "/api/documents/upload" {
			max = 10
		}
		if r.URL.Path == "/api/auth/login" {
			max = 10
		}
		if r.URL.Path == "/api/auth/register" {
			max = 5
		}
		limits.Lock()
		now := time.Now()
		b := limits.entries[key]
		if now.Sub(b.start) > time.Minute {
			b = bucket{start: now}
		}
		b.count++
		limits.entries[key] = b
		if len(limits.entries) > 10000 {
			for k, v := range limits.entries {
				if now.Sub(v.start) > time.Minute {
					delete(limits.entries, k)
				}
			}
		}
		blocked := b.count > max || len(limits.entries) > 10000
		limits.Unlock()
		if blocked {
			w.Header().Set("Retry-After", "60")
			respond(w, 429, map[string]string{"error": "Request limit reached. Try again in a minute."})
			return
		}
		next.ServeHTTP(w, r)
	})
}
func proxyAgent(path string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		target := base() + path
		if r.URL.RawQuery != "" {
			target += "?" + r.URL.RawQuery
		}
		var body io.Reader
		if r.Method == "POST" {
			limit := int64(32768)
			if r.URL.Path == "/api/documents/upload" || r.URL.Path == "/api/extension/import" {
				limit = 6 * 1024 * 1024
			}
			b, e := io.ReadAll(http.MaxBytesReader(w, r.Body, limit))
			if e != nil {
				respond(w, 413, map[string]string{"error": "Request too large"})
				return
			}
			body = bytes.NewReader(b)
		}
		req, e := http.NewRequest(r.Method, target, body)
		if e != nil {
			w.WriteHeader(500)
			return
		}
		req.Header.Set("Content-Type", "application/json")
		serviceHeaders(req, sessionToken(r))
		res, e := client.Do(req)
		if e != nil {
			respond(w, 503, map[string]string{"error": "Workspace service unavailable"})
			return
		}
		defer res.Body.Close()
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(res.StatusCode)
		io.Copy(w, res.Body)
	}
}
func authHandler(path string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			w.WriteHeader(405)
			return
		}
		body, e := io.ReadAll(http.MaxBytesReader(w, r.Body, 4096))
		if e != nil {
			w.WriteHeader(413)
			return
		}
		req, _ := http.NewRequest("POST", base()+path, bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		serviceHeaders(req, "")
		res, e := client.Do(req)
		if e != nil {
			respond(w, 503, map[string]string{"error": "Account service unavailable"})
			return
		}
		defer res.Body.Close()
		var result struct {
			Token string `json:"token"`
			User  any    `json:"user"`
			Error string `json:"error"`
		}
		if json.NewDecoder(res.Body).Decode(&result) != nil {
			w.WriteHeader(503)
			return
		}
		if res.StatusCode != 200 {
			respond(w, res.StatusCode, map[string]string{"error": result.Error})
			return
		}
		http.SetCookie(w, &http.Cookie{Name: "agentshield_session", Value: result.Token, Path: "/api", HttpOnly: true, SameSite: http.SameSiteStrictMode, Secure: os.Getenv("COOKIE_SECURE") == "true", MaxAge: 28800})
		respond(w, 200, map[string]any{"user": result.User})
	}
}
func workspaceRoutes(mux *http.ServeMux) {
	gmailRoutes(mux)
	for _, path := range []string{"/judge-pack", "/help", "/help/chat", "/ledger", "/ledger/verify", "/council", "/council/review", "/council/standard"} {
		mux.HandleFunc("/api"+path, requireSession(proxyAgent(path)))
	}
	mux.HandleFunc("/api/auth/register", authHandler("/register"))
	mux.HandleFunc("/api/auth/login", authHandler("/login"))
	mux.HandleFunc("/api/auth/me", requireSession(proxyAgent("/session")))
	mux.HandleFunc("/api/auth/logout", requireSession(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			w.WriteHeader(405)
			return
		}
		var ack any
		if callWithToken("/logout", map[string]any{}, &ack, sessionToken(r)) != nil {
			w.WriteHeader(503)
			return
		}
		http.SetCookie(w, &http.Cookie{Name: "agentshield_session", Value: "", Path: "/api", HttpOnly: true, SameSite: http.SameSiteStrictMode, Secure: os.Getenv("COOKIE_SECURE") == "true", MaxAge: -1})
		respond(w, 200, map[string]bool{"ok": true})
	}))
	mux.HandleFunc("/api/invoices", requireSession(proxyAgent("/invoices")))
	mux.HandleFunc("/api/chat", requireSession(proxyAgent("/chat")))
	mux.HandleFunc("/api/invoices/review", requireSession(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			w.WriteHeader(405)
			return
		}
		var input struct {
			InvoiceID string `json:"invoice_id"`
		}
		d := json.NewDecoder(http.MaxBytesReader(w, r.Body, 4096))
		d.DisallowUnknownFields()
		if d.Decode(&input) != nil || len(input.InvoiceID) != 32 {
			respond(w, 400, map[string]string{"error": "Choose an invoice"})
			return
		}
		// Preserve 404/ownership errors; never accept recipient/amount overrides from chat or the client.
		b, _ := json.Marshal(input)
		req, _ := http.NewRequest("POST", base()+"/invoice-prepare", bytes.NewReader(b))
		req.Header.Set("Content-Type", "application/json")
		serviceHeaders(req, sessionToken(r))
		res, e := client.Do(req)
		if e != nil {
			w.WriteHeader(503)
			return
		}
		defer res.Body.Close()
		if res.StatusCode != 200 {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(res.StatusCode)
			io.Copy(w, res.Body)
			return
		}
		var prepared struct {
			Payment Payment `json:"payment"`
		}
		if json.NewDecoder(res.Body).Decode(&prepared) != nil {
			w.WriteHeader(503)
			return
		}
		v, e := decide(prepared.Payment, nil, sessionToken(r))
		if e != nil {
			respond(w, 503, map[string]string{"error": e.Error(), "decision": "deny"})
			return
		}
		respond(w, 200, v)
	}))
}
