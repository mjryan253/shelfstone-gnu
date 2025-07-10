<script lang="ts">
  import EpubFetcher from '$lib/components/EpubFetcher.svelte';
  import EpubRenderer from '$lib/components/EpubRenderer.svelte';

  // !!! IMPORTANT: Replace this with your actual API endpoint !!!
  // User provided base URL: http://localhost:6336/
  // Using a placeholder path, please update this to your actual API endpoint.
  const epubApiUrl = 'http://localhost:6336/api/get-epub/example-book-id'; // Placeholder

  let currentEpubData: ArrayBuffer | null = null;
  let fetcherKey = 0; // Used to re-trigger fetcher if needed, e.g., URL changes

  function handleEpubLoaded(event: CustomEvent<ArrayBuffer>) {
    currentEpubData = event.detail;
  }

  function handleEpubLoadFailed(event: CustomEvent<string>) {
    console.error("Failed to load EPUB:", event.detail);
    // Optionally, display a more user-friendly error message on the page
  }

  // If you want to allow changing the URL and re-fetching:
  // function fetchNewEpub(newUrl: string) {
  //   epubApiUrl = newUrl; // This won't reactive by itself with const
  //   currentEpubData = null; // Clear old data
  //   fetcherKey++; // Re-creates the EpubFetcher component to trigger a new fetch
  // }
</script>

<svelte:head>
  <title>ePub Reader</title>
</svelte:head>

<main>
  <h1>ePub Viewer</h1>

  <!--
    You might want to add an input field here to set/change epubApiUrl
    and then call a function like fetchNewEpub.
    For now, it uses the hardcoded placeholder.
  -->

  {#key fetcherKey}
    <EpubFetcher
      apiUrl={epubApiUrl}
      on:epubloaded={handleEpubLoaded}
      on:epubloadfailed={handleEpubLoadFailed}
    />
  {/key}

  {#if currentEpubData}
    <div class="epub-renderer-wrapper">
      <EpubRenderer epubData={currentEpubData} />
    </div>
  {:else}
    <p class="status-message">
      Waiting for ePub data to be loaded...
      Make sure the API URL is correct and the server is running.
      Current API URL: <code>{epubApiUrl}</code>
    </p>
  {/if}
</main>

<style>
  main {
    font-family: sans-serif;
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
    text-align: center;
  }

  .epub-renderer-wrapper {
    margin-top: 20px;
    border: 1px solid #eee;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }

  .status-message {
    margin-top: 30px;
    font-style: italic;
    color: #555;
  }

  code {
    background-color: #f0f0f0;
    padding: 2px 5px;
    border-radius: 3px;
  }
</style>
