package main

import (
	"net/http"
)

func gmailRoutes(mux *http.ServeMux) {
	for _, path := range []string{"/gmail/status", "/gmail/connect", "/gmail/search", "/gmail/attachments", "/gmail/import", "/gmail/disconnect", "/gmail/delete-draft"} {
		mux.HandleFunc("/api"+path, requireSession(proxyAgent(path)))
	}
	mux.HandleFunc("/api/gmail/callback", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Referrer-Policy", "no-referrer")
		if r.Method != "GET" || len(r.URL.RawQuery) > 8192 {
			http.Error(w, "Invalid callback", 400)
			return
		}
		// The backend validates a single-use state bound to an active app session.
		req, _ := http.NewRequest("GET", base()+"/gmail/callback?"+r.URL.RawQuery, nil)
		serviceHeaders(req, "")
		res, err := client.Do(req)
		success := false
		if err == nil {
			success = res.StatusCode == 200
			res.Body.Close()
		}
		target := "/#gmail=error"
		if success {
			target = "/#gmail=connected"
		}
		http.Redirect(w, r, target, http.StatusSeeOther)
	})
}
