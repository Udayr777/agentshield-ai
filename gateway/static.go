package main

import (
	"io/fs"
	"net/http"
	"os"
	"strings"
)

// Serve only built public assets. Missing API routes never receive the SPA.
func staticHandler(directory string) http.HandlerFunc {
	files := os.DirFS(directory)
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "GET" || strings.HasPrefix(r.URL.Path, "/api/") {
			http.NotFound(w, r)
			return
		}
		name := strings.TrimPrefix(r.URL.Path, "/")
		if name == "" {
			name = "index.html"
		}
		if !fs.ValidPath(name) || strings.HasPrefix(name, ".") {
			http.NotFound(w, r)
			return
		}
		info, err := fs.Stat(files, name)
		if err != nil || info.IsDir() {
			http.NotFound(w, r)
			return
		}
		http.FileServer(http.FS(files)).ServeHTTP(w, r)
	}
}
