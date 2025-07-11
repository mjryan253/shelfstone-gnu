"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState<string>('');
  const [authors, setAuthors] = useState<string>(''); // Comma-separated
  const [tags, setTags] = useState<string>(''); // Comma-separated
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const router = useRouter();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0]);
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) {
      setError("Please select a file to upload.");
      return;
    }

    setIsUploading(true);
    setError(null);
    setSuccessMessage(null);

    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    if (authors) formData.append('authors', authors); // API expects comma-separated string
    if (tags) formData.append('tags', tags); // API expects comma-separated string
    // Add other optional parameters from API docs as needed, e.g., library_path, duplicates, automerge

    try {
      const response = await fetch('http://localhost:6336/books/add/', {
        method: 'POST',
        body: formData,
        // Headers are not typically needed for FormData; browser sets Content-Type to multipart/form-data
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || `Failed to upload book: ${response.statusText}`);
      }

      setSuccessMessage(result.message || "Book uploaded successfully!");
      // Optionally reset form or redirect
      setFile(null);
      setTitle('');
      setAuthors('');
      setTags('');
      // router.push('/library'); // Or redirect to the new book's page if ID is returned and usable

    } catch (e) {
      if (e instanceof Error) {
        setError(e.message);
      } else {
        setError("An unknown error occurred during upload.");
      }
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">Upload New Book</h1>

      <form onSubmit={handleSubmit} className="max-w-lg mx-auto bg-white p-6 rounded-lg shadow-md">
        {error && <p className="mb-4 text-red-500 bg-red-100 p-3 rounded">{error}</p>}
        {successMessage && <p className="mb-4 text-green-500 bg-green-100 p-3 rounded">{successMessage}</p>}

        <div className="mb-4">
          <label htmlFor="file" className="block text-sm font-medium text-gray-700 mb-1">Book File (EPUB, MOBI, etc.)</label>
          <input
            type="file"
            id="file"
            onChange={handleFileChange}
            required
            className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none p-2"
          />
        </div>

        <div className="mb-4">
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">Title (Optional)</label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>

        <div className="mb-4">
          <label htmlFor="authors" className="block text-sm font-medium text-gray-700 mb-1">Authors (Optional, comma-separated)</label>
          <input
            type="text"
            id="authors"
            value={authors}
            onChange={(e) => setAuthors(e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="e.g., Author One, Author Two"
          />
        </div>

        <div className="mb-6">
          <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-1">Tags (Optional, comma-separated)</label>
          <input
            type="text"
            id="tags"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="e.g., fiction, sci-fi, classic"
          />
        </div>

        <button
          type="submit"
          disabled={isUploading || !file}
          className="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:bg-gray-400"
        >
          {isUploading ? 'Uploading...' : 'Upload Book'}
        </button>
      </form>
    </div>
  );
}
