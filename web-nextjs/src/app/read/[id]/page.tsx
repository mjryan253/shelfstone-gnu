"use client";

import { useState, useEffect } from 'react';
import EbookViewer from '@/components/EbookViewer'; // Using alias @
import Link from 'next/link';

// Assuming Book type is similar to other pages
type Book = {
  id: number;
  title: string;
  formats?: string; // e.g., "EPUB,MOBI"
  // other fields...
};

type ReadPageProps = {
  params: {
    id: string; // Book ID from the route
  };
};

export default function ReadPage({ params }: ReadPageProps) {
  const { id } = params;
  const [book, setBook] = useState<Book | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [bookFileUrl, setBookFileUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    async function fetchBookInfo() {
      setLoading(true);
      try {
        // Fetch book metadata to get title and available formats
        const response = await fetch(`http://localhost:6336/books/?search=ids:${id}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data: Book[] = await response.json();

        if (data.length > 0) {
          const fetchedBook = data[0];
          setBook(fetchedBook);

          // Construct the URL to the EPUB file using the backend endpoint.
          const formats = fetchedBook.formats?.toLowerCase().split(',') || [];
          if (formats.includes('epub')) {
            setBookFileUrl(`http://localhost:6336/books/${fetchedBook.id}/file/epub`);
            setError(null); // Clear any previous error message
          } else {
            setError("EPUB format not found for this book. Other formats are not yet supported by this viewer.");
          }
        } else {
          setError("Book not found.");
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "An unknown error occurred");
      } finally {
        setLoading(false);
      }
    }
    fetchBookInfo();
  }, [id]);

  if (loading) return <p className="text-center mt-8">Loading book information...</p>;
  // We show the error/note but still attempt to load viewer if URL is set
  // if (error && !bookFileUrl) return <p className="text-center mt-8 text-red-500">Error: {error}</p>;
  if (!book) return <p className="text-center mt-8">Book details not found.</p>;

  return (
    <div className="container mx-auto p-4">
      <nav className="mb-4 text-sm">
        <Link href={`/books/${id}`} legacyBehavior><a className="text-blue-500 hover:underline">Back to Book Details</a></Link>
        <span className="mx-2">|</span>
        <Link href="/library" legacyBehavior><a className="text-blue-500 hover:underline">Back to Library</a></Link>
      </nav>
      <h1 className="text-2xl font-bold mb-4">Reading: {book.title}</h1>

      {error && <p className="mb-4 text-orange-500 bg-orange-100 p-3 rounded">{error}</p>}

      {bookFileUrl ? (
        <EbookViewer bookUrl={bookFileUrl} title={book.title} />
      ) : (
        !loading && <p className="text-center text-gray-500">No EPUB file URL available for this book.</p>
      )}
    </div>
  );
}
