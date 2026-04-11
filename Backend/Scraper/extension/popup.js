const scanButton = document.getElementById("scanButton");
const statusBox = document.getElementById("statusBox");
const resultsBox = document.getElementById("results");

function setStatus(message) {
  statusBox.textContent = message;
}

function renderResults(result) {
  const items = result?.extracted_requirements || [];
  resultsBox.innerHTML = "";

  if (!items.length) {
    resultsBox.innerHTML = '<div class="popup__card"><strong>No fields found</strong><span>The page did not expose visible form fields.</span></div>';
    return;
  }

  for (const item of items.slice(0, 8)) {
    const card = document.createElement("div");
    card.className = "popup__card";

    const title = document.createElement("strong");
    title.textContent = item.requirement || item.field_key || "Field";

    const meta = document.createElement("span");
    meta.textContent = `${item.input_kind || "text"}${item.required ? " • required" : ""}`;

    card.appendChild(title);
    card.appendChild(meta);
    resultsBox.appendChild(card);
  }
}

async function scanCurrentPage() {
  scanButton.disabled = true;
  setStatus("Scanning current page...");
  resultsBox.innerHTML = "";

  try {
    const response = await chrome.runtime.sendMessage({ type: "SCRAPE_CURRENT_TAB" });
    if (!response?.ok) {
      throw new Error(response?.error || "Scan failed");
    }

    const result = response.result;
    setStatus(`Found ${result.total_fields} fields on ${result.title || "this page"}.`);
    renderResults(result);
  } catch (error) {
    setStatus(`Error: ${String(error)}`);
  } finally {
    scanButton.disabled = false;
  }
}

scanButton.addEventListener("click", scanCurrentPage);
scanCurrentPage();
