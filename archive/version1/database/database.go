package database

import (
	"database/sql"
	"fmt"
	"log"
	"strings"
	"time"

	_ "github.com/mattn/go-sqlite3" // SQLite driver
)

// Book represents the structure for books in the database.
type Book struct {
	ID              int64
	Title           string
	AuthorIDs       []int64  // Foreign keys to Authors table
	Authors         []string // For display; populated by joining with Authors
	SeriesID        *int64   // Foreign key to Series table, nullable
	SeriesName      *string  // For display; populated by joining with Series
	FilePath        string   // Path to the original ebook file
	CoverImagePath  *string  // Path to the extracted cover image, nullable
	Format          string   // e.g., EPUB, MOBI
	ProcessedAt     time.Time
	AddedAt         time.Time
	ExternalCalibreID *string // Calibre's own ID if available
}

// Author represents an author.
type Author struct {
	ID   int64
	Name string
}

// Series represents a book series.
type Series struct {
	ID   int64
	Name string
}

var db *sql.DB

// InitDB initializes the SQLite database connection and creates tables if they don't exist.
func InitDB(dataSourceName string) error {
	var err error
	db, err = sql.Open("sqlite3", dataSourceName)
	if err != nil {
		return fmt.Errorf("failed to open database: %w", err)
	}

	if err = db.Ping(); err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}

	// Create tables
	if err = createTables(); err != nil {
		return fmt.Errorf("failed to create tables: %w", err)
	}

	log.Println("Database initialized successfully.")
	return nil
}

func createTables() error {
	// Authors table
	_, err := db.Exec(`
		CREATE TABLE IF NOT EXISTS authors (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL UNIQUE
		);
	`)
	if err != nil {
		return fmt.Errorf("failed to create authors table: %w", err)
	}

	// Series table
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS series (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL UNIQUE
		);
	`)
	if err != nil {
		return fmt.Errorf("failed to create series table: %w", err)
	}

	// Books table
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS books (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			title TEXT NOT NULL,
			series_id INTEGER, -- Nullable
			file_path TEXT NOT NULL UNIQUE,
			cover_image_path TEXT, -- Nullable
			format TEXT,
			processed_at DATETIME,
			added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
			external_calibre_id TEXT, -- Nullable
			FOREIGN KEY (series_id) REFERENCES series(id)
		);
	`)
	if err != nil {
		return fmt.Errorf("failed to create books table: %w", err)
	}

	// Book_Authors junction table (many-to-many relationship)
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS book_authors (
			book_id INTEGER,
			author_id INTEGER,
			PRIMARY KEY (book_id, author_id),
			FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
			FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
		);
	`)
	if err != nil {
		return fmt.Errorf("failed to create book_authors table: %w", err)
	}

	log.Println("Tables created or already exist.")
	return nil
}

// AddBook adds a new book to the database, along with its authors and series if they don't exist.
// It handles the relationships in the junction table.
func AddBook(bookMeta *Book, authorNames []string, seriesName *string, filePath, coverPath, format string, externalCalibreID *string) (int64, error) {
	tx, err := db.Begin()
	if err != nil {
		return 0, fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback() // Rollback if not committed

	// Handle Authors
	var authorIDs []int64
	for _, name := range authorNames {
		var authorID int64
		// Check if author exists
		err := tx.QueryRow("SELECT id FROM authors WHERE name = ?", name).Scan(&authorID)
		if err == sql.ErrNoRows {
			// Author does not exist, insert it
			res, err := tx.Exec("INSERT INTO authors (name) VALUES (?)", name)
			if err != nil {
				return 0, fmt.Errorf("failed to insert author %s: %w", name, err)
			}
			authorID, err = res.LastInsertId()
			if err != nil {
				return 0, fmt.Errorf("failed to get last insert ID for author %s: %w", name, err)
			}
		} else if err != nil {
			return 0, fmt.Errorf("failed to query author %s: %w", name, err)
		}
		authorIDs = append(authorIDs, authorID)
	}

	// Handle Series
	var seriesID_sql sql.NullInt64
	if seriesName != nil && *seriesName != "" {
		var sID int64
		err := tx.QueryRow("SELECT id FROM series WHERE name = ?", *seriesName).Scan(&sID)
		if err == sql.ErrNoRows {
			res, err := tx.Exec("INSERT INTO series (name) VALUES (?)", *seriesName)
			if err != nil {
				return 0, fmt.Errorf("failed to insert series %s: %w", *seriesName, err)
			}
			sID, err = res.LastInsertId()
			if err != nil {
				return 0, fmt.Errorf("failed to get last insert ID for series %s: %w", *seriesName, err)
			}
		} else if err != nil {
			return 0, fmt.Errorf("failed to query series %s: %w", *seriesName, err)
		}
		seriesID_sql = sql.NullInt64{Int64: sID, Valid: true}
	}

	// Insert Book
	var coverPathSQL sql.NullString
	if coverPath != "" {
		coverPathSQL = sql.NullString{String: coverPath, Valid: true}
	}
    var externalCalibreIDSQL sql.NullString
    if externalCalibreID != nil && *externalCalibreID != "" {
        externalCalibreIDSQL = sql.NullString{String: *externalCalibreID, Valid: true}
    }

	res, err := tx.Exec(
		"INSERT INTO books (title, series_id, file_path, cover_image_path, format, processed_at, external_calibre_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
		bookMeta.Title, seriesID_sql, filePath, coverPathSQL, format, time.Now(), externalCalibreIDSQL,
	)
	if err != nil {
		// Check for UNIQUE constraint violation for file_path
		if strings.Contains(err.Error(), "UNIQUE constraint failed: books.file_path") {
			// Try to get the existing book ID
			var existingBookID int64
			errQuery := tx.QueryRow("SELECT id FROM books WHERE file_path = ?", filePath).Scan(&existingBookID)
			if errQuery == nil {
				log.Printf("Book with file_path %s already exists with ID %d. Skipping insert.", filePath, existingBookID)
				// We can choose to return the existing ID or an error indicating duplication
				return existingBookID, fmt.Errorf("book already exists with file_path %s (ID: %d)", filePath, existingBookID)
			}
			return 0, fmt.Errorf("book with file_path %s already exists, but failed to retrieve its ID: %w (original error: %v)", filePath, errQuery, err)
		}
		return 0, fmt.Errorf("failed to insert book %s: %w", bookMeta.Title, err)
	}
	bookID, err := res.LastInsertId()
	if err != nil {
		return 0, fmt.Errorf("failed to get last insert ID for book %s: %w", bookMeta.Title, err)
	}

	// Link Book and Authors in book_authors table
	for _, authorID := range authorIDs {
		_, err := tx.Exec("INSERT INTO book_authors (book_id, author_id) VALUES (?, ?)", bookID, authorID)
		if err != nil {
			return 0, fmt.Errorf("failed to link book %d with author %d: %w", bookID, authorID, err)
		}
	}

	if err = tx.Commit(); err != nil {
		return 0, fmt.Errorf("failed to commit transaction: %w", err)
	}

	log.Printf("Successfully added book: %s (ID: %d)", bookMeta.Title, bookID)
	return bookID, nil
}

// GetBookByID retrieves a single book by its ID.
func GetBookByID(id int64) (*Book, error) {
	row := db.QueryRow(`
		SELECT
			b.id, b.title, b.series_id, s.name as series_name, b.file_path,
			b.cover_image_path, b.format, b.processed_at, b.added_at, b.external_calibre_id
		FROM books b
		LEFT JOIN series s ON b.series_id = s.id
		WHERE b.id = ?;
	`, id)

	book := &Book{}
	var seriesID sql.NullInt64
	var seriesName sql.NullString
	var coverPath sql.NullString
    var externalCalibreID sql.NullString


	err := row.Scan(
		&book.ID, &book.Title, &seriesID, &seriesName, &book.FilePath,
		&coverPath, &book.Format, &book.ProcessedAt, &book.AddedAt, &externalCalibreID,
	)
	if err == sql.ErrNoRows {
		return nil, nil // Not found
	}
	if err != nil {
		return nil, fmt.Errorf("error scanning book ID %d: %w", id, err)
	}

	if seriesID.Valid {
		book.SeriesID = &seriesID.Int64
	}
	if seriesName.Valid {
		book.SeriesName = &seriesName.String
	}
	if coverPath.Valid {
		book.CoverImagePath = &coverPath.String
	}
    if externalCalibreID.Valid {
        book.ExternalCalibreID = &externalCalibreID.String
    }


	// Get authors
	rows, err := db.Query(`
		SELECT a.id, a.name
		FROM authors a
		JOIN book_authors ba ON a.id = ba.author_id
		WHERE ba.book_id = ?;
	`, id)
	if err != nil {
		return nil, fmt.Errorf("error querying authors for book ID %d: %w", id, err)
	}
	defer rows.Close()

	for rows.Next() {
		var authorID int64
		var authorName string
		if err := rows.Scan(&authorID, &authorName); err != nil {
			return nil, fmt.Errorf("error scanning author for book ID %d: %w", id, err)
		}
		book.AuthorIDs = append(book.AuthorIDs, authorID)
		book.Authors = append(book.Authors, authorName)
	}
	if err = rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating authors for book ID %d: %w", id, err)
	}

	return book, nil
}

// GetAllBooks retrieves all books from the database.
func GetAllBooks() ([]*Book, error) {
	rows, err := db.Query(`
		SELECT
			b.id, b.title, b.series_id, s.name as series_name, b.file_path,
			b.cover_image_path, b.format, b.processed_at, b.added_at, b.external_calibre_id
		FROM books b
		LEFT JOIN series s ON b.series_id = s.id
		ORDER BY b.title;
	`)
	if err != nil {
		return nil, fmt.Errorf("error querying all books: %w", err)
	}
	defer rows.Close()

	var books []*Book
	for rows.Next() {
		book := &Book{}
		var seriesID sql.NullInt64
		var seriesName sql.NullString
		var coverPath sql.NullString
        var externalCalibreID sql.NullString

		err := rows.Scan(
			&book.ID, &book.Title, &seriesID, &seriesName, &book.FilePath,
			&coverPath, &book.Format, &book.ProcessedAt, &book.AddedAt, &externalCalibreID,
		)
		if err != nil {
			return nil, fmt.Errorf("error scanning book row: %w", err)
		}

		if seriesID.Valid {
			book.SeriesID = &seriesID.Int64
		}
		if seriesName.Valid {
			book.SeriesName = &seriesName.String
		}
		if coverPath.Valid {
			book.CoverImagePath = &coverPath.String
		}
        if externalCalibreID.Valid {
            book.ExternalCalibreID = &externalCalibreID.String
        }


		// Get authors for this book
		authorRows, err := db.Query(`
			SELECT a.id, a.name
			FROM authors a
			JOIN book_authors ba ON a.id = ba.author_id
			WHERE ba.book_id = ?;
		`, book.ID)
		if err != nil {
			// Log error but continue, so one book's author issue doesn't stop all
			log.Printf("Error querying authors for book ID %d: %v", book.ID, err)
			// Potentially return partial data or handle more gracefully
		} else {
			for authorRows.Next() {
				var authorID int64
				var authorName string
				if err := authorRows.Scan(&authorID, &authorName); err != nil {
					log.Printf("Error scanning author for book ID %d: %v", book.ID, err)
				} else {
					book.AuthorIDs = append(book.AuthorIDs, authorID)
					book.Authors = append(book.Authors, authorName)
				}
			}
			authorRows.Close()
			if err = authorRows.Err(); err != nil {
				log.Printf("Error iterating authors for book ID %d: %v", book.ID, err)
			}
		}
		books = append(books, book)
	}

	if err = rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating book rows: %w", err)
	}

	return books, nil
}

// GetDB returns the current database connection.
// Useful for more complex queries or operations not covered by existing functions.
func GetDB() *sql.DB {
	return db
}
