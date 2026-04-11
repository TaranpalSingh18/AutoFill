# Scraper Module

This module receives form-field metadata scraped by a browser extension and extracts field requirements for downstream RAG retrieval.

## Backend endpoint

- Method: POST
- Path: /scraper/extract-requirements
- Input: URL + title + fields array
- Output: normalized field requirements

## Example request body

{
  "url": "https://example.com/form",
  "title": "Application Form",
  "fields": [
    {
      "tag": "input",
      "input_type": "text",
      "name": "firstName",
      "label": "First name",
      "placeholder": "Enter first name",
      "required": true
    }
  ]
}

## Extension starter

The extension scaffold is in:

- extension/manifest.json
- extension/content.js
- extension/background.js
- extension/popup.html
- extension/popup.css
- extension/popup.js

## Popup behavior

Clicking the extension icon opens a compact white popup titled AutoFill.
It automatically scans the current page and shows the extracted field summary.

## Quick run

1. Start backend on localhost:8000.
2. Open Chrome Extensions page and enable Developer mode.
3. Load unpacked extension from Backend/Scraper/extension.
4. Open any form page and click the extension action icon.
5. Check service worker console logs for extracted results.
