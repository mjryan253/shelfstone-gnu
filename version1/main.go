package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"shelfstone/calibre"
	"shelfstone/database"
	"shelfstone/scanner"
	"github.com/gin-gonic/gin"
)

const (
	dbPath        = "./data/ebook_library.db"
	booksDir      = "./books"
	coversDir     = "./data/covers"
	processedDir  = "./data/processed_ebooks" // For converted ebooks, if needed
)

func ensureDir(dirPath string) {
	if _, err := os.Stat(dirPath); os.IsNotExist(err) {
		log.Printf("Creating directory: %s", dirPath)
		if err := os.MkdirAll(dirPath, 0755); err != nil {
			log.Fatalf("Failed to create directory %s: %v", dirPath, err)
		}
	} else if err != nil {
		log.Fatalf("Error checking directory %s: %v", dirPath, err)
	}
}

func processNewEbook(filePath string) {
	log.Printf("Processing new file: %s", filePath)
	baseName := strings.TrimSuffix(filepath.Base(filePath), filepath.Ext(filePath))

	// 1. Extract Metadata
	calibreMeta, err := calibre.ExtractMetadata(filePath)
	if err != nil {
		log.Printf("Error extracting metadata for %s: %v", filePath, err)
		// Optionally, move to a "failed_processing" directory
		return
	}
	log.Printf("Extracted metadata for %s: Title: %s, Authors: %v, Series: %s",
		filePath, calibreMeta.Title, calibreMeta.Author, calibreMeta.Series)

	// 2. Extract Cover Image
	coverImagePath, err := calibre.ExtractCoverImage(filePath, coversDir, baseName)
	if err != nil {
		log.Printf("Error extracting cover for %s: %v (this might be normal if no cover exists)", filePath, err)
		// No fatal error if cover extraction fails, coverImagePath will be empty or an error string
		coverImagePath = "" // Ensure it's an empty string if there was an error
	} else {
		log.Printf("Extracted cover for %s to %s", filePath, coverImagePath)
	}

	// 3. (Optional) Convert Book Format - e.g., to EPUB if it's not already
	// For now, we'll just store the original format. Conversion can be added later.
	originalFormat := strings.ToUpper(strings.TrimPrefix(filepath.Ext(filePath), "."))

	// 4. Add to Database
	dbBook := &database.Book{ // This is the database.Book struct, not calibre.BookMetadata
		Title: calibreMeta.Title,
		// Authors and Series are handled by their names in AddBook
	}

	var seriesNamePtr *string
	if calibreMeta.Series != "" {
		seriesNamePtr = &calibreMeta.Series
	}

	// The calibre.BookMetadata might have an ID field if Calibre itself assigned one.
	// We are not using that directly here, but it could be stored if ebook-meta provided it.
	// For now, we pass nil for externalCalibreID.
	var externalCalibreID *string // Assuming calibreMeta doesn't directly give this in a simple field.
                               // If it did, e.g. calibreMeta.CalibreID, we'd use &calibreMeta.CalibreID

	bookID, err := database.AddBook(dbBook, calibreMeta.Author, seriesNamePtr, filePath, coverImagePath, originalFormat, externalCalibreID)
	if err != nil {
		if strings.Contains(err.Error(), "already exists") {
			log.Printf("Book %s (path: %s) already in database. Skipping.", calibreMeta.Title, filePath)
		} else {
			log.Printf("Error adding book %s to database: %v", calibreMeta.Title, err)
		}
		return
	}

	log.Printf("Successfully processed and added book ID %d: %s", bookID, calibreMeta.Title)
}

func main() {
	// Ensure necessary directories exist
	ensureDir(filepath.Dir(dbPath)) // ./data
	ensureDir(booksDir)             // ./books
	ensureDir(coversDir)            // ./data/covers
	ensureDir(processedDir)         // ./data/processed_ebooks

	// Initialize Database
	if err := database.InitDB(dbPath); err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}

	// Start watching the books directory in a separate goroutine
	go scanner.WatchBooksDirectory(booksDir, processNewEbook)

	r := gin.Default()
	r.GET("/ping", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"message": "pong",
		})
	})
	r.Run() // listen and serve on 0.0.0.0:8080
}
