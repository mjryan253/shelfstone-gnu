<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import ePub, { type Book, type Rendition } from 'epubjs';

  export let epubData: ArrayBuffer | null = null; // Expecting ePub data as ArrayBuffer

  let rendition: Rendition | null = null;
  let book: Book | null = null;
  let viewerElement: HTMLElement; // This will bind to the div where the ePub will be rendered

  onMount(async () => {
    if (!epubData || !viewerElement) {
      console.error('EpubRenderer: No ePub data or viewer element.');
      return;
    }

    try {
      book = ePub(epubData);
      rendition = book.renderTo(viewerElement, {
        width: '100%', // Responsive width
        height: '600px', // Default height, can be customized
        spread: 'auto', // Or 'none' for single page view
        // flow: 'paginated' // or 'scrolled-doc' or 'scrolled-continuous'
      });
      await rendition.display();

      // Example: Add navigation (can be expanded)
      // You might want to expose methods or use events to control navigation from parent
      // For simplicity, adding basic key listeners here
      const keyListener = (e: KeyboardEvent) => {
        if (e.key === 'ArrowLeft') {
          rendition?.prev();
        }
        if (e.key === 'ArrowRight') {
          rendition?.next();
        }
      };
      window.addEventListener('keydown', keyListener);

      // Cleanup on destroy
      onDestroy(() => {
        window.removeEventListener('keydown', keyListener);
        rendition?.destroy();
        book?.destroy();
      });

    } catch (error) {
      console.error('Error rendering ePub:', error);
      // Handle rendering errors, e.g., display a message
      viewerElement.innerHTML = `<p style="color: red;">Could not render ePub: ${error instanceof Error ? error.message : String(error)}</p>`;
    }
  });

  onDestroy(() => {
    // Ensure cleanup even if onMount failed partially
    if (rendition) rendition.destroy();
    if (book) book.destroy();
  });
</script>

<div bind:this={viewerElement} class="epub-viewer-container">
  <!-- ePub content will be rendered here -->
</div>

<style>
  .epub-viewer-container {
    width: 100%;
    height: 600px; /* Or make this configurable via props */
    border: 1px solid #ccc;
    overflow: hidden; /* Important for some epubjs rendering flows */
  }
</style>
