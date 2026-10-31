package main

import (
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
)

func TestStaticBoundary(t *testing.T) {
	dir := t.TempDir()
	os.WriteFile(filepath.Join(dir, "index.html"), []byte("demo"), 0600)
	handler := staticHandler(dir)
	for _, c := range []struct {
		path   string
		status int
	}{{"/", 200}, {"/.env", 404}, {"/api/missing", 404}, {"/../secret", 404}} {
		w := httptest.NewRecorder()
		handler(w, httptest.NewRequest("GET", c.path, nil))
		if w.Code != c.status {
			t.Fatalf("%s got %d", c.path, w.Code)
		}
	}
}
