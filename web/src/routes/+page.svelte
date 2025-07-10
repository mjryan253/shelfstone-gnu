<script lang="ts">
  import EpubFetcher from '$lib/components/EpubFetcher.svelte';
  import EpubRenderer from '$lib/components/EpubRenderer.svelte';
  import LibraryView from '$lib/components/LibraryView.svelte';

  // Base URL for the API
  const API_BASE_URL = 'http://localhost:6336';

  let currentEpubData: ArrayBuffer | null = null;
  let currentBookId: number | null = null;
  let currentBookFormat: string | null = null;
  let fetcherKey = 0; // Used to re-trigger fetcher if needed
  let epubApiUrl = ''; // Will be set dynamically

  let showReader = false; // Controls visibility of the reader section

  function handleEpubLoaded(event: CustomEvent<ArrayBuffer>) {
    currentEpubData = event.detail;
    showReader = true; // Show reader once data is loaded
  }

  function handleEpubLoadFailed(event: CustomEvent<string>) {
    console.error("Failed to load EPUB:", event.detail);
    alert(`Failed to load EPUB: ${event.detail}. Ensure the book has this format and the backend is running.`);
    currentEpubData = null;
    showReader = false; // Hide reader on fail
  }

  function handleBookSelected(event: CustomEvent<{ bookId: number; format: string }>) {
    const { bookId, format } = event.detail;
    currentBookId = bookId;
    currentBookFormat = format; // e.g., 'epub'

    // Update the API URL for the EpubFetcher
    // Ensure format is part of the path, defaulting to 'epub' if not specified by selection logic.
    epubApiUrl = `${API_BASE_URL}/books/${currentBookId}/file/${currentBookFormat || 'epub'}`;

    currentEpubData = null; // Clear previous book data
    fetcherKey++; // Re-render EpubFetcher to trigger a new fetch
    // showReader = true; // Optionally, show reader immediately or wait for load
  }
</script>

<svelte:head>
  <title>ShelfStone - ePub Reader & Library</title>
</svelte:head>

<div class="app-container">
  <header class="app-header">
    <h1>ShelfStone</h1>
  </header>

  <main class="main-content">
    <div class="library-pane">
      <LibraryView on:bookselected={handleBookSelected} />
    </div>

    <div class="reader-pane">
      {#if epubApiUrl && fetcherKey > 0} <!-- Only show fetcher if a book has been selected -->
        {#key fetcherKey}
          <EpubFetcher
            apiUrl={epubApiUrl}
            on:epubloaded={handleEpubLoaded}
            on:epubloadfailed={handleEpubLoadFailed}
          />
        {/key}
      {/if}

      {#if showReader && currentEpubData}
        <div class="epub-renderer-wrapper">
          <EpubRenderer epubData={currentEpubData} />
        </div>
      {:else if epubApiUrl && !currentEpubData && fetcherKey > 0}
        <p class="status-message">Loading selected book...</p>
      {:else if !epubApiUrl}
         <p class="status-message">Select a book from the library to start reading.</p>
      {/if}
    </div>
  </main>
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
      Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    background-color: #f0f2f5;
    color: #333;
  }

  .app-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
  }

  .app-header {
    background-color: #333;
    color: white;
    padding: 1rem 1.5rem;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }

  .app-header h1 {
    margin: 0;
    font-size: 1.8rem;
  }

  .main-content {
    display: flex;
    flex-grow: 1;
    overflow: hidden; /* Prevent overall page scroll, panes will scroll */
    padding: 1rem;
    gap: 1rem;
  }

  .library-pane {
    flex: 0 0 350px; /* Fixed width for library, adjust as needed */
    overflow-y: auto; /* Scroll for library list if it overflows */
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
  }

  .reader-pane {
    flex-grow: 1;
    display: flex; /* Use flex to center status messages */
    flex-direction: column; /* Stack fetcher/renderer vertically */
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    padding: 1rem;
    overflow-y: auto; /* Allow reader content to scroll */
  }

  .epub-renderer-wrapper {
    /* Wrapper for the renderer, takes available space */
    flex-grow: 1;
    border: 1px solid #eee; /* Optional border around renderer area */
    min-height: 0; /* Important for flex children that scroll */
  }

  .status-message {
    margin: auto; /* Center message in reader-pane when no book is loaded/loading */
    font-style: italic;
    color: #555;
    text-align: center;
  }

  /* Ensure EpubRenderer component itself handles its internal scrolling and layout */
</style>
