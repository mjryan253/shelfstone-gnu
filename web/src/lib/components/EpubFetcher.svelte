<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';

  export let apiUrl: string = ''; // API URL will be passed as a prop

  let isLoading: boolean = true;
  let error: string | null = null;
  let epubData: ArrayBuffer | null = null;

  const dispatch = createEventDispatcher<{ epubloaded: ArrayBuffer; epubloadfailed: string }>();

  onMount(async () => {
    if (!apiUrl) {
      error = 'API URL is not provided.';
      isLoading = false;
      dispatch('epubloadfailed', error);
      return;
    }

    try {
      isLoading = true;
      error = null;
      const response = await fetch(apiUrl);

      if (!response.ok) {
        throw new Error(`Failed to fetch ePub: ${response.status} ${response.statusText}`);
      }

      epubData = await response.arrayBuffer();
      dispatch('epubloaded', epubData);
    } catch (e: any) {
      error = e.message || 'An unknown error occurred while fetching the ePub.';
      dispatch('epubloadfailed', error);
    } finally {
      isLoading = false;
    }
  });
</script>

{#if isLoading}
  <p>Loading ePub...</p>
{:else if error}
  <p style="color: red;">Error: {error}</p>
{:else if epubData}
  <p>ePub data loaded successfully. Ready to render.</p>
  <!-- Slot for parent to pass content or for the renderer component -->
  <slot arrayBuffer={epubData}></slot>
{:else}
  <p>No ePub data.</p>
{/if}
