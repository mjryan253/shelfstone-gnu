"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation'; // Changed from next/router for App Router

// Re-using the Book type from library page for consistency.
// It might need more fields for a "details" view.
type Book = {
  id: number;
  title: string;
  authors?: string;
  tags?: string;
  formats?: string;
  publisher?: string;
  series?: string;
  series_index?: number;
  isbn?: string;
  comments?: string; // Often a longer text
  // path?: string; // Path on the server, might not be directly useful to display
};

// Helper to parse authors and tags if they are strings (same as library page)
const parseAuthors = (authorsStr?: string): string[] => {
  if (!authorsStr) return [];
  return authorsStr.split(' & ');
};

const parseTags = (tagsStr?: string): string[] => {
  if (!tagsStr) return [];
  return tagsStr.split(',');
};

type BookDetailsPageProps = {
  params: {
    id: string; // Book ID from the route
  };
};

export default function BookDetailsPage({ params }: BookDetailsPageProps) {
  const { id } = params;
  const [book, setBook] = useState<Book | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!id) return;

    async function fetchBookDetails() {
      setLoading(true);
      try {
        // As there's no dedicated GET /books/{id} endpoint,
        // we fetch all books and find the one with the matching ID.
        // This is not optimal for large libraries.
        // Alternatively, if the API supports `search=id:BOOK_ID`, that would be better.
        // For now, using `calibredb list --for-machine --item-id {id}` on backend would be best.
        // Assuming current API: fetch all and filter.
        // Or, if the /books/ endpoint can take an ID search:
        // const response = await fetch(`http://localhost:8001/books/?search=id:${id}`);
        // For now, I'll stick to fetching the specific book by constructing a search query
        // if the API allows it. The docs for GET /books/ mention a `search` parameter.
        // Example: `search=id:123`. This needs to be tested if `calibredb list` supports `id:` prefix.
        // Calibre's search syntax is powerful, `ids:123` or `id:123` might work.
        // Let's try with `search=ids:${id}` as `ids` is a common Calibre search field.
        const response = await fetch(`http://localhost:8001/books/?search=ids:${id}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: Book[] = await response.json();
        if (data.length > 0) {
          setBook(data[0]); // Assuming the search returns an array, take the first item
        } else {
          setError("Book not found.");
        }
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

    fetchBookDetails();
  }, [id]);

  const handleDeleteBook = async () => {
    if (!book) return;
    if (window.confirm(`Are you sure you want to delete "${book.title}"?`)) {
      try {
        const response = await fetch(`http://localhost:8001/books/${book.id}/`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `Failed to delete book: ${response.statusText}`);
        }
        alert("Book deleted successfully.");
        router.push('/library'); // Redirect to library after deletion
      } catch (e) {
        if (e instanceof Error) {
          setError(`Failed to delete book: ${e.message}`);
        } else {
          setError("An unknown error occurred during deletion.");
        }
        alert(`Error: ${error}`);
      }
    }
  };


  if (loading) return <p className="text-center mt-8">Loading book details...</p>;
  if (error) return <p className="text-center mt-8 text-red-500">Error: {error}</p>;
  if (!book) return <p className="text-center mt-8">Book not found.</p>;

  const authorsList = parseAuthors(book.authors);
  const tagsList = parseTags(book.tags);

  return (
    <div className="container mx-auto p-4">
      <nav className="mb-4 text-sm">
        <Link href="/library" legacyBehavior><a className="text-blue-500 hover:underline">Back to Library</a></Link>
      </nav>
      <div className="bg-white shadow-lg rounded-lg p-6">
        <h1 className="text-3xl font-bold mb-4">{book.title}</h1>

        {authorsList.length > 0 && (
          <p className="text-lg text-gray-700 mb-2"><strong>Authors:</strong> {authorsList.join(', ')}</p>
        )}

        {book.series && (
          <p className="text-md text-gray-600 mb-1">
            <strong>Series:</strong> {book.series} (Book {book.series_index || 'N/A'})
          </p>
        )}

        {book.publisher && (
          <p className="text-md text-gray-600 mb-1"><strong>Publisher:</strong> {book.publisher}</p>
        )}

        {book.isbn && (
          <p className="text-md text-gray-600 mb-1"><strong>ISBN:</strong> {book.isbn}</p>
        )}

        {tagsList.length > 0 && (
          <div className="mt-4 mb-2">
            <h3 className="font-semibold">Tags:</h3>
            <div className="flex flex-wrap gap-2 mt-1">
              {tagsList.map(tag => (
                <span key={tag} className="bg-gray-200 text-gray-700 px-2 py-1 rounded-full text-xs">{tag}</span>
              ))}
            </div>
          </div>
        )}

        {book.formats && (
          <p className="text-sm text-gray-500 mt-2 mb-4"><strong>Formats:</strong> {book.formats}</p>
        )}

        {book.comments && (
          <div className="mt-4">
            <h3 className="font-semibold">Comments:</h3>
            <div className="prose max-w-none mt-1" dangerouslySetInnerHTML={{ __html: book.comments }} />
          </div>
        )}

        <div className="mt-6 flex flex-wrap gap-4">
          <Link href={`/read/${book.id}`} legacyBehavior>
            <a className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">
              Read Book (EPUB)
            </a>
          </Link>
          <Link href={`/books/${book.id}/edit`} legacyBehavior>
            <a className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
              Edit Metadata
            </a>
          </Link>
          <button
            onClick={handleDeleteBook}
            className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
          >
            Delete Book
          </button>
        </div>
      </div>
    </div>
  );
}
