"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation'; // For App Router
import Link from 'next/link';

// Re-using the Book type, ensure it covers all editable fields from the API
type Book = {
  id: number;
  title: string;
  authors?: string; // Calibre API might expect "Author One & Author Two" or list for set_metadata
  publisher?: string;
  pubdate?: string; // YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
  tags?: string; // Calibre API might expect "tag1,tag2" or list for set_metadata
  series?: string;
  series_index?: number;
  isbn?: string;
  comments?: string;
  rating?: number; // 0-10 for Calibre
};

// Type for the form data, aligning with API's PUT /books/{book_id}/metadata/ request body
// API expects authors and tags as lists of strings.
type BookMetadataFormData = {
  title?: string;
  authors?: string[];
  publisher?: string;
  pubdate?: string;
  tags?: string[];
  series?: string;
  series_index?: number;
  isbn?: string;
  comments?: string;
  rating?: number;
};

type EditBookPageProps = {
  params: {
    id: string; // Book ID from the route
  };
};

// Helper to convert comma/space separated string to array of strings for authors/tags
const stringToList = (str: string | undefined): string[] => {
  if (!str) return [];
  return str.split(/[,&]+/).map(item => item.trim()).filter(item => item.length > 0);
};

// Helper to convert Calibre's "Author1 & Author2" string to a comma-separated string for form input
const authorsToStringForForm = (authorsStr?: string): string => {
  if (!authorsStr) return '';
  return authorsStr.split(' & ').join(', ');
};


export default function EditBookPage({ params }: EditBookPageProps) {
  const { id } = params;
  const router = useRouter();
  const [book, setBook] = useState<Book | null>(null);
  const [formData, setFormData] = useState<Partial<BookMetadataFormData>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    async function fetchBookData() {
      setLoading(true);
      try {
        // Fetch existing book data to prefill the form
        const response = await fetch(`http://localhost:8001/books/?search=ids:${id}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data: Book[] = await response.json();
        if (data.length > 0) {
          const fetchedBook = data[0];
          setBook(fetchedBook);
          // Pre-fill form data
          setFormData({
            title: fetchedBook.title,
            // The API PUT /books/{book_id}/metadata/ expects authors and tags as arrays of strings.
            // The GET /books/ endpoint returns authors as "Author One & Author Two" and tags as "tag1,tag2".
            // So, we need to convert them for the form and then back for submission.
            // For the form, it's easier to edit comma-separated strings.
            // Let's keep them as strings in the form state, and convert on submit.
            // OR, use the API's expected format (list of strings) directly in form state if input fields are managed accordingly.
            // For simplicity, let's use strings in form fields and parse on submit.
            authors: stringToList(fetchedBook.authors), // Keep as list for API
            publisher: fetchedBook.publisher,
            pubdate: fetchedBook.pubdate?.split('T')[0], // Format as YYYY-MM-DD for date input
            tags: stringToList(fetchedBook.tags), // Keep as list for API
            series: fetchedBook.series,
            series_index: fetchedBook.series_index,
            isbn: fetchedBook.isbn,
            comments: fetchedBook.comments,
            rating: fetchedBook.rating ? fetchedBook.rating / 2 : undefined, // Calibre rating 0-10 -> 0-5 stars
          });
        } else {
          setError("Book not found.");
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "An unknown error occurred");
      } finally {
        setLoading(false);
      }
    }
    fetchBookData();
  }, [id]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;

    let processedValue: string | number | string[] | undefined = value;
    if (type === 'number') {
      processedValue = value === '' ? undefined : parseFloat(value);
    }
    if (name === 'rating' && value !== '') {
        processedValue = parseFloat(value); // Keep as 0-5 for form, will convert to 0-10 on submit
    }
    // For authors and tags, we expect comma-separated strings from input, convert to array for API
    if (name === 'authors' || name === 'tags') {
        processedValue = stringToList(value);
    }

    setFormData(prev => ({ ...prev, [name]: processedValue }));
  };

  // Specific handler for authors/tags if they are kept as strings in form and converted here
  const handleListStringChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value })); // Store as string
  };


  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!book) return;

    setSaving(true);
    setError(null);
    setSuccessMessage(null);

    // Prepare payload for the API
    const payload: BookMetadataFormData = { ...formData };

    // Convert form string for authors/tags (if stored as string) to list for API
    if (typeof formData.authors === 'string') {
        payload.authors = stringToList(formData.authors);
    }
    if (typeof formData.tags === 'string') {
        payload.tags = stringToList(formData.tags);
    }


    // Convert rating from 0-5 stars (form) to 0-10 (Calibre)
    if (payload.rating !== undefined) {
      payload.rating = payload.rating * 2;
    }
     // Ensure empty strings are not sent if the API expects them to be omitted or null
    Object.keys(payload).forEach(key => {
        const k = key as keyof BookMetadataFormData;
        if (payload[k] === '') {
            delete payload[k]; // Or set to null if API prefers
        }
    });


    try {
      const response = await fetch(`http://localhost:8001/books/${book.id}/metadata/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || `Failed to update metadata: ${response.statusText}`);
      }
      setSuccessMessage(result.message || "Metadata updated successfully!");
      // Optionally, refresh book data or redirect
      // router.push(`/books/${book.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "An unknown error occurred during save");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="text-center mt-8">Loading book data for editing...</p>;
  if (error && !book) return <p className="text-center mt-8 text-red-500">Error: {error}</p>;
  if (!book) return <p className="text-center mt-8">Book not found.</p>;

  // For authors/tags, join array back to comma-separated string for input field
  const authorsForForm = Array.isArray(formData.authors) ? formData.authors.join(', ') : '';
  const tagsForForm = Array.isArray(formData.tags) ? formData.tags.join(', ') : '';


  return (
    <div className="container mx-auto p-4">
      <nav className="mb-4 text-sm">
        <Link href={`/books/${id}`} legacyBehavior><a className="text-blue-500 hover:underline">Back to Book Details</a></Link>
      </nav>
      <h1 className="text-2xl font-bold mb-6">Edit Metadata: {book.title}</h1>

      <form onSubmit={handleSubmit} className="max-w-2xl mx-auto bg-white p-6 rounded-lg shadow-md">
        {error && <p className="mb-4 text-red-500 bg-red-100 p-3 rounded">{error}</p>}
        {successMessage && <p className="mb-4 text-green-500 bg-green-100 p-3 rounded">{successMessage}</p>}

        {/* Title */}
        <div className="mb-4">
          <label htmlFor="title" className="block text-sm font-medium text-gray-700">Title</label>
          <input type="text" name="title" id="title" value={formData.title || ''} onChange={handleInputChange} className="mt-1 block w-full input-style" />
        </div>

        {/* Authors (comma-separated string for input) */}
        <div className="mb-4">
          <label htmlFor="authors" className="block text-sm font-medium text-gray-700">Authors (comma-separated)</label>
          <input type="text" name="authors" id="authors" value={authorsForForm} onChange={handleListStringChange} className="mt-1 block w-full input-style" placeholder="Author One, Author Two"/>
        </div>

        {/* Publisher */}
        <div className="mb-4">
          <label htmlFor="publisher" className="block text-sm font-medium text-gray-700">Publisher</label>
          <input type="text" name="publisher" id="publisher" value={formData.publisher || ''} onChange={handleInputChange} className="mt-1 block w-full input-style" />
        </div>

        {/* Publication Date */}
        <div className="mb-4">
          <label htmlFor="pubdate" className="block text-sm font-medium text-gray-700">Publication Date</label>
          <input type="date" name="pubdate" id="pubdate" value={formData.pubdate || ''} onChange={handleInputChange} className="mt-1 block w-full input-style" />
        </div>

        {/* Tags (comma-separated string for input) */}
        <div className="mb-4">
          <label htmlFor="tags" className="block text-sm font-medium text-gray-700">Tags (comma-separated)</label>
          <input type="text" name="tags" id="tags" value={tagsForForm} onChange={handleListStringChange} className="mt-1 block w-full input-style" placeholder="fiction, sci-fi"/>
        </div>

        {/* Series */}
        <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
                <label htmlFor="series" className="block text-sm font-medium text-gray-700">Series</label>
                <input type="text" name="series" id="series" value={formData.series || ''} onChange={handleInputChange} className="mt-1 block w-full input-style" />
            </div>
            <div>
                <label htmlFor="series_index" className="block text-sm font-medium text-gray-700">Series Index</label>
                <input type="number" name="series_index" id="series_index" value={formData.series_index || ''} onChange={handleInputChange} step="0.1" className="mt-1 block w-full input-style" />
            </div>
        </div>

        {/* ISBN */}
        <div className="mb-4">
          <label htmlFor="isbn" className="block text-sm font-medium text-gray-700">ISBN</label>
          <input type="text" name="isbn" id="isbn" value={formData.isbn || ''} onChange={handleInputChange} className="mt-1 block w-full input-style" />
        </div>

        {/* Rating (0-5 stars for form) */}
        <div className="mb-4">
          <label htmlFor="rating" className="block text-sm font-medium text-gray-700">Rating (0-5 stars)</label>
          <input type="number" name="rating" id="rating" value={formData.rating === undefined ? '' : formData.rating} onChange={handleInputChange} min="0" max="5" step="0.5" className="mt-1 block w-full input-style" />
        </div>

        {/* Comments */}
        <div className="mb-6">
          <label htmlFor="comments" className="block text-sm font-medium text-gray-700">Comments</label>
          <textarea name="comments" id="comments" value={formData.comments || ''} onChange={handleInputChange} rows={4} className="mt-1 block w-full input-style"></textarea>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="w-full bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:bg-gray-400"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </form>
      <style jsx>{`
        .input-style {
          display: block;
          width: 100%;
          padding: 0.5rem;
          border: 1px solid #D1D5DB; // gray-300
          border-radius: 0.375rem; // rounded-md
          box-shadow: sm;
        }
        .input-style:focus {
          outline: none;
          border-color: #3B82F6; // blue-500
          box-shadow: 0 0 0 2px #BFDBFE; // ring-blue-500 with opacity
        }
      `}</style>
    </div>
  );
}
