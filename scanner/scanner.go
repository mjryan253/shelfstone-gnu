package scanner

import (
	"log"
	"os"
	"path/filepath"
	"time"
)

// WatchBooksDirectory monitors the specified directory for new ebook files.
// It checks the directory periodically and calls the provided callback function
// when a new file is detected.
func WatchBooksDirectory(dir string, callback func(string)) {
	processedFiles := make(map[string]bool)

	// Initial scan
	files, err := os.ReadDir(dir)
	if err != nil {
		log.Printf("Error reading directory %s: %v", dir, err)
		return
	}
	for _, file := range files {
		if !file.IsDir() {
			filePath := filepath.Join(dir, file.Name())
			processedFiles[filePath] = true
			// For initial scan, we assume files are already processed or will be handled by a separate initial import.
			// So, we don't call the callback here, only mark them as processed.
		}
	}

	ticker := time.NewTicker(10 * time.Second) // Check every 10 seconds
	defer ticker.Stop()

	for range ticker.C {
		files, err := os.ReadDir(dir)
		if err != nil {
			log.Printf("Error reading directory %s: %v", dir, err)
			continue
		}

		for _, file := range files {
			if !file.IsDir() {
				filePath := filepath.Join(dir, file.Name())
				if _, ok := processedFiles[filePath]; !ok {
					log.Printf("New file detected: %s", filePath)
					processedFiles[filePath] = true
					callback(filePath)
				}
			}
		}
	}
}
