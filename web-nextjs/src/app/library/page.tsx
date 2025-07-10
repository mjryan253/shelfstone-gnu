"use client";

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';

// Define a basic Book type - this should be refined based on actual API response
// The API for GET /books/ returns a list of objects, each object is a book.
// Example fields from calibredb list: id, title, authors, formats, isbn, path, publisher, series, tags, timestamp
type Book = {
  id: number; // Mandatory
  title: string; // Mandatory
  authors?: string; // Comes as a string from `calibredb list`, e.g., "Author One & Author Two"
  tags?: string; // Comes as a string, e.g., "tag1,tag2"
  formats?: string; // Comes as a string, e.g., "EPUB,MOBI"
  publisher?: string;
  series?: string;
  series_index?: number;
  // Add other relevant fields based on the API response as needed
};

// Helper to parse authors and tags if they are strings
const parseAuthors = (authorsStr?: string): string[] => {
  if (!authorsStr) return [];
  return authorsStr.split(' & ');
};

const parseTags = (tagsStr?: string): string[] => {
  if (!tagsStr) return [];
  return tagsStr.split(',');
};


export default function LibraryPage() {
  const [allBooks, setAllBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [sortBy, setSortBy] = useState<keyof Book | 'id'>('title'); // Default sort by title

  useEffect(() => {
    async function fetchBooks() {
      setLoading(true);
      try {
        // Construct URL for fetching books.
        // The API supports a `search` query parameter.
        // For now, we fetch all and filter/sort client-side.
        // Later, we can implement server-side search by passing `searchTerm` to this URL.
        const apiUrl = `http://localhost:8001/books/`;
        const response = await fetch(apiUrl);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: Book[] = await response.json();
        setAllBooks(data);
      } catch (e) {
        if (e instanceof Error) {
          setError(e.message);
        } else {
          setError("An unknown error occurred");
        }
      } finally {
        setLoading(false);
      }
    }

    fetchBooks();
  }, []); // Fetch books once on component mount

  const filteredAndSortedBooks = useMemo(() => {
    let booksToShow = [...allBooks];

    // Filter by search term (case-insensitive)
    if (searchTerm) {
      booksToShow = booksToShow.filter(book =>
        book.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (book.authors && book.authors.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (book.tags && book.tags.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Sort books
    booksToShow.sort((a, b) => {
      const valA = a[sortBy];
      const valB = b[sortBy];

      if (typeof valA === 'string' && typeof valB === 'string') {
        return valA.localeCompare(valB);
      }
      if (typeof valA === 'number' && typeof valB === 'number') {
        return valA - valB;
      }
      // Handle cases where one might be undefined or types differ, or for complex sorting
      if (valA === undefined && valB !== undefined) return 1; // undefined comes last
      if (valA !== undefined && valB === undefined) return -1;
      if (valA === undefined && valB === undefined) return 0;

      // Fallback for mixed types or other complex cases - convert to string and compare
      return String(valA).localeCompare(String(valB));
    });

    return booksToShow;
  }, [allBooks, searchTerm, sortBy]);

  if (loading) return <p className="text-center mt-8">Loading books...</p>;
  if (error) return <p className="text-center mt-8 text-red-500">Error loading books: {error}</p>;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-center">Book Library</h1>

      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <input
          type="text"
          placeholder="Search by title, author, or tag..."
          className="flex-grow p-2 border rounded shadow-sm focus:ring-2 focus:ring-blue-500 outline-none"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <select
          className="p-2 border rounded shadow-sm focus:ring-2 focus:ring-blue-500 outline-none"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as keyof Book)}
        >
          <option value="title">Sort by Title</option>
          <option value="authors">Sort by Author</option>
          {/* Add more sort options based on available Book fields if needed */}
          <option value="id">Sort by ID</option>
        </select>
      </div>

      {filteredAndSortedBooks.length === 0 ? (
        <p className="text-center text-gray-500">No books found matching your criteria.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAndSortedBooks.map((book) => (
            <div key={book.id} className="p-4 border rounded-lg shadow-lg hover:shadow-xl transition-shadow bg-white">
              <Link href={`/books/${book.id}`} legacyBehavior>
                <a className="block">
                  <h2 className="text-xl font-semibold text-blue-600 hover:text-blue-800 mb-2 truncate" title={book.title}>{book.title}</h2>
                </a>
              </Link>
              {book.authors && (
                <p className="text-sm text-gray-700 mb-1">
                  <strong>Authors:</strong> {parseAuthors(book.authors).join(', ')}
                </p>
              )}
              {book.tags && (
                <p className="text-xs text-gray-500 mb-2">
                  <strong>Tags:</strong> {parseTags(book.tags).join(', ')}
                </p>
              )}
              {book.formats && (
                <p className="text-xs text-gray-500">
                  <strong>Formats:</strong> {book.formats}
                </p>
              )}
              {/* Link to book details page */}
              <Link href={`/books/${book.id}`} legacyBehavior>
                <a className="text-sm text-blue-500 hover:underline mt-2 inline-block">View Details</a>
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
