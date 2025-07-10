"use client"; // react-reader is a client-side component

import React, { useState, useRef } from 'react';
import { ReactReader, EpubView } from 'react-reader';

type EbookViewerProps = {
  bookUrl: string; // URL to the .epub file
  title?: string; // Optional title for the reader
};

export default function EbookViewer({ bookUrl, title }: EbookViewerProps) {
  const [location, setLocation] = useState<string | number | null>(null);
  const readerRef = useRef<EpubView>(null); // Ref for EpubView instance

  const onLocationChanged = (epubcifi: string | number) => {
    setLocation(epubcifi);
    // Optionally save location to localStorage or backend
  };

  // Basic styling for the viewer container to take up space
  // You'll likely want to customize this significantly
  const viewerContainerStyle: React.CSSProperties = {
    position: 'relative', // Or 'absolute' if you want it to fill a parent
    height: '80vh', // Example height
    width: '100%',
    border: '1px solid #ccc',
    overflow: 'hidden', // To contain the reader
  };

  const loadingView = (
    <div style={{ textAlign: 'center', padding: '20px' }}>
      <p>Loading book...</p>
      <p className="text-sm text-gray-500 mt-2">
        (Note: This viewer requires a direct URL to an EPUB file.
        The backend API may need a new endpoint to provide this.)
      </p>
    </div>
  );

  return (
    <div style={viewerContainerStyle}>
      <ReactReader
        url={bookUrl}
        title={title || "Ebook"}
        location={location}
        locationChanged={onLocationChanged}
        epubViewOptions={{
          // flow: 'scrolled-doc', // Example: enable scrolling mode
          // width: '100%', // Example: ensure it fills container
        }}
        loadingView={loadingView}
        ref={readerRef} // Assign ref here
      />
    </div>
  );
}
