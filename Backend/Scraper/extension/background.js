const BACKEND_ENDPOINT = "http://localhost:8000/scraper/extract-requirements";

async function runScrape(tabId) {
  const response = await chrome.tabs.sendMessage(tabId, { type: "SCRAPE_FORM_FIELDS" });
  if (!response?.ok) {
    throw new Error(response?.error || "Failed to scrape form fields from page");
  }

  const req = await fetch(BACKEND_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(response.payload)
  });

  if (!req.ok) {
    const detail = await req.text();
    throw new Error(`Backend request failed: ${req.status} ${detail}`);
  }

  return req.json();
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "SCRAPE_CURRENT_TAB") {
    return;
  }

  chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
    try {
      const tab = tabs?.[0];
      if (!tab?.id) {
        throw new Error("No active tab found");
      }

      const result = await runScrape(tab.id);
      sendResponse({ ok: true, result });
    } catch (error) {
      sendResponse({ ok: false, error: String(error) });
    }
  });

  return true;
});
