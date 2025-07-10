package calibre

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os/exec"
	"path/filepath"
	"strings"
)

// BookMetadata holds the extracted metadata of an ebook.
type BookMetadata struct {
	Title  string   `json:"title"`
	Author []string `json:"authors"` // Calibre uses "authors"
	Series string   `json:"series"`
	// Add other fields as needed, e.g., ISBN, publisher, cover image path
}

// ExtractMetadata uses Calibre's ebook-meta to extract metadata from an ebook file.
// It returns a pointer to BookMetadata and an error if any occurs.
func ExtractMetadata(filePath string) (*BookMetadata, error) {
	cmd := exec.Command("ebook-meta", filePath, "--to-json")
	var out bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &stderr

	err := cmd.Run()
	if err != nil {
		return nil, fmt.Errorf("error running ebook-meta for %s: %v\nStderr: %s", filePath, err, stderr.String())
	}

	var metadata []BookMetadata // ebook-meta --to-json returns a list with one element
	if err := json.Unmarshal(out.Bytes(), &metadata); err != nil {
		return nil, fmt.Errorf("error unmarshalling metadata for %s: %v\nOutput: %s", filePath, err, out.String())
	}

	if len(metadata) == 0 {
		return nil, fmt.Errorf("no metadata found for %s", filePath)
	}

	// Assuming the first entry is the relevant one
	bookMeta := metadata[0]

	// ebook-meta --to-json doesn't directly provide a simple series string if it's part of a series with an index.
	// We might need a more robust way to get series info, or rely on what's directly available.
	// For now, we'll assume a simple "series" tag if present.

	return &bookMeta, nil
}

// ExtractCoverImage uses Calibre's ebook-meta to extract the cover image.
// It saves the cover to the specified outputPath (e.g., "output/cover.jpg").
// Returns the path to the extracted cover or an error.
func ExtractCoverImage(ebookPath string, outputDir string, baseName string) (string, error) {
	coverPath := filepath.Join(outputDir, baseName+"_cover.jpg")
	cmd := exec.Command("ebook-meta", ebookPath, "--get-cover", coverPath)
	var stderr bytes.Buffer
	cmd.Stderr = &stderr

	err := cmd.Run()
	if err != nil {
		// Check if the error is because no cover exists
		if strings.Contains(stderr.String(), "No cover found in") {
			return "", fmt.Errorf("no cover found in %s: %w", ebookPath, err)
		}
		return "", fmt.Errorf("error extracting cover for %s: %v\nStderr: %s", ebookPath, err, stderr.String())
	}
	return coverPath, nil
}

// ConvertBookFormat uses Calibre's ebook-convert to convert an ebook to a different format.
// For example, to convert to EPUB: outputFormat="epub".
// The converted file will be saved in outputDir with the original base name and new extension.
func ConvertBookFormat(ebookPath string, outputDir string, outputFormat string) (string, error) {
	baseName := strings.TrimSuffix(filepath.Base(ebookPath), filepath.Ext(ebookPath))
	outputFilePath := filepath.Join(outputDir, baseName+"."+strings.ToLower(outputFormat))

	cmd := exec.Command("ebook-convert", ebookPath, outputFilePath)
	var out bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &stderr

	err := cmd.Run()
	if err != nil {
		return "", fmt.Errorf("error converting %s to %s: %v\nStdout: %s\nStderr: %s", ebookPath, outputFormat, err, out.String(), stderr.String())
	}

	return outputFilePath, nil
}
