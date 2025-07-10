<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';

  interface Book {
    id: number;
    title: string;
    authors: string[] | null;
    formats: string[] | null;
    // Add other relevant fields from your Book model if needed for display
    // e.g., cover: string | null;
  }

  let books: Book[] = [];
  let error: string | null = null;
  let isLoading = true;

  const dispatch = createEventDispatcher();

  onMount(async () => {
    try {
      // Assuming the API is running on localhost:6336 as per previous context
      const response = await fetch('http://localhost:6336/books/');
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      const data: Book[] = await response.json();
      books = data;
    } catch (e: any) {
      console.error('Failed to fetch books:', e);
      error = e.message || 'Failed to load library. Please ensure the backend is running and accessible.';
    } finally {
      isLoading = false;
    }
  });

  function selectBook(bookId: number, formats: string[] | null) {
    // Find the EPUB format, or default to the first available format if EPUB is not found.
    // For now, we'll primarily look for EPUB as the reader is set up for it.
    let formatToLoad = 'epub'; // Default to EPUB

    if (formats && formats.length > 0) {
      const epubFormat = formats.find(f => f.toLowerCase() === 'epub');
      if (!epubFormat) {
        // If EPUB not found, maybe pick the first one or handle error
        // For now, we still request EPUB and let the backend/reader handle if it's not available.
        // A more robust solution would be to check available formats.
        console.warn(`Book ID ${bookId} does not explicitly list EPUB format. Attempting to load EPUB anyway.`);
      }
    } else {
        console.warn(`Book ID ${bookId} has no listed formats. Attempting to load EPUB.`);
    }

    dispatch('bookselected', {
      bookId: bookId,
      format: formatToLoad
    });
  }
</script>

<div class="library-view">
  <h2>My Library</h2>
  {#if isLoading}
    <p>Loading library...</p>
  {:else if error}
    <p class="error-message">{error}</p>
  {:else if books.length === 0}
    <p>Your library is empty.</p>
  {:else}
    <ul class="book-list">
      {#each books as book (book.id)}
        <li class="book-item" on:click={() => selectBook(book.id, book.formats)} on:keypress={() => selectBook(book.id, book.formats)} role="button" tabindex="0">
          <span class="book-title">{book.title}</span>
          {#if book.authors && book.authors.length > 0}
            <span class="book-authors">by {book.authors.join(', ')}</span>
          {/if}
          <!-- TODO: Display cover image if available -->
          <!-- TODO: Display available formats if needed -->
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .library-view {
    padding: 1rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    background-color: #f9f9f9;
    max-height: 80vh; /* Example max height */
    overflow-y: auto;
  }

  .book-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .book-item {
    padding: 0.75rem;
    border-bottom: 1px solid #eee;
    cursor: pointer;
    transition: background-color 0.2s ease;
  }

  .book-item:last-child {
    border-bottom: none;
  }

  .book-item:hover {
    background-color: #e9e9e9;
  }

  .book-title {
    font-weight: bold;
    display: block;
    margin-bottom: 0.25rem;
  }

  .book-authors {
    font-size: 0.9em;
    color: #555;
  }

  .error-message {
    color: red;
    padding: 1rem;
    border: 1px solid red;
    background-color: #ffebeb;
    border-radius: 4px;
  }
</style>
