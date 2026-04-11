function textOrEmpty(value) {
  return (value || "").trim();
}

function getLabelText(el) {
  if (el.id) {
    const label = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
    if (label) return textOrEmpty(label.innerText || label.textContent);
  }

  const wrappedLabel = el.closest("label");
  if (wrappedLabel) {
    return textOrEmpty(wrappedLabel.innerText || wrappedLabel.textContent);
  }

  return "";
}

function getSectionHint(el) {
  const section = el.closest("section, fieldset, form, [role='group'], [data-section]");
  if (!section) return "";

  const heading = section.querySelector("h1, h2, h3, legend, [data-title]");
  if (heading) return textOrEmpty(heading.innerText || heading.textContent);

  return textOrEmpty(section.getAttribute("aria-label") || section.getAttribute("data-section"));
}

function extractFields() {
  const selector = "input, textarea, select";
  const nodes = Array.from(document.querySelectorAll(selector));

  const fields = nodes
    .filter((el) => !el.disabled && el.type !== "hidden")
    .map((el) => {
      const tag = el.tagName.toLowerCase();
      const options =
        tag === "select"
          ? Array.from(el.options || []).map((o) => textOrEmpty(o.textContent)).filter(Boolean)
          : [];

      return {
        tag,
        input_type: textOrEmpty(el.type),
        name: textOrEmpty(el.getAttribute("name")),
        id: textOrEmpty(el.id),
        label: getLabelText(el),
        placeholder: textOrEmpty(el.getAttribute("placeholder")),
        aria_label: textOrEmpty(el.getAttribute("aria-label")),
        section: getSectionHint(el),
        required: el.required || el.getAttribute("aria-required") === "true",
        options
      };
    });

  return {
    url: window.location.href,
    title: document.title,
    fields
  };
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "SCRAPE_FORM_FIELDS") {
    return;
  }

  try {
    const payload = extractFields();
    sendResponse({ ok: true, payload });
  } catch (error) {
    sendResponse({ ok: false, error: String(error) });
  }
});
