# Frontend Testing Guidelines

Please pull the latest changes, run `docker compose up -d --build`, and test the application. The frontend should be accessible at `http://localhost:6464`.

## 1. Library View (`/library` or homepage)
*   Are books listed correctly?
*   Does searching by title, author, or tag work as expected?
*   Does sorting by title, author, or ID work correctly?
*   Does clicking on a book title or "View Details" link navigate to the correct book detail page?

## 2. Book Details View (`/books/[id]`)
*   Is all book information displayed accurately (title, authors, tags, series, publisher, ISBN, comments)?
*   **Delete Functionality:**
    *   Does a confirmation dialog appear when you try to delete a book?
    *   Is the book successfully deleted from the library upon confirmation? (Verify in the library view or via API).
*   **Edit Navigation:**
    *   Does clicking the "Edit Metadata" button navigate to the correct metadata editing page for that book?

## 3. Edit Metadata Page (`/books/[id]/edit`)
*   Is the form correctly pre-filled with the book's current metadata?
*   **Saving Changes:**
    *   Try modifying various fields (e.g., title, authors, tags, rating, comments).
    *   Are the changes saved successfully?
    *   Are the updated details reflected correctly on the Book Details page and in the Library view?

## 4. Upload Page (`/upload`)
*   *(You might need to navigate directly to `/upload` if no explicit link is present yet).*
*   Try uploading a new ebook file (e.g., an EPUB or MOBI).
*   Optionally, fill in metadata fields like title, authors, and tags during upload.
*   Does the upload process complete successfully?
*   Is the newly uploaded book visible in the library with the correct metadata (if provided)?

## 5. Ebook Viewer (`/read/[id]`)
*   Navigate to the reader page using the "Read Book (EPUB)" button from a book's detail page.
*   **Expected Behavior (Important Note):**
    *   The page should attempt to load the `EbookViewer` component.
    *   It is **expected** that the book itself will **not** load correctly.
    *   You should see a message within the viewer area or an error message indicating that the book URL is a placeholder or that a backend endpoint is required.
    *   The purpose of this test is to confirm the viewer *page* loads and the component is present, not that the book content renders (as this depends on a backend change not yet made).
*   Please confirm if you see the viewer frame and any messages related to the placeholder URL or missing backend functionality.

## 6. General Responsiveness
*   Resize your browser window to various widths (e.g., simulate desktop, tablet, mobile).
*   Does the layout adapt reasonably to different screen sizes? Are elements usable?

## 7. Navigation
*   *(This is an area for potential improvement as a full navigation bar was not explicitly part of the initial implementation).*
*   Are there basic navigation links present (e.g., "Back to Library" from detail/edit pages, links to upload page if any were added)?
*   Is navigation generally intuitive for the implemented features?

## Reporting Issues
For any issues encountered, please provide:
*   The page URL where the issue occurred.
*   Steps to reproduce the issue.
*   Expected behavior vs. actual behavior.
*   Any error messages displayed on the page or in the browser's developer console (Press F12, check the "Console" tab).

Thank you for testing!
