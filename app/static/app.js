const form = document.querySelector("#add-form");
const message = document.querySelector("#message");
const tableBody = document.querySelector("#watchlist tbody");
const emptyState = document.querySelector("#empty");
const checkButton = document.querySelector("#check-button");

function euro(value) {
  return value == null ? "–" : `€${value}`;
}

function formatDate(value) {
  if (!value) return "–";
  // SQLite drops the timezone; the API stores UTC, so treat a bare timestamp as UTC.
  const hasZone = /(Z|[+-]\d\d:?\d\d)$/.test(value);
  return new Date(hasZone ? value : `${value}Z`).toLocaleString(undefined, {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function showMessage(text, kind) {
  message.textContent = text;
  message.className = `message ${kind}`;
  message.hidden = false;
}

async function errorText(response) {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((error) => `${error.loc.at(-1)}: ${error.msg}`).join("; ");
    }
  } catch {
    // Response was not JSON; fall through to the generic message.
  }
  return `Request failed with status ${response.status}`;
}

async function request(url, options) {
  try {
    return await fetch(url, options);
  } catch {
    showMessage("Could not reach the server. Is uvicorn running?", "error");
    return null;
  }
}

function cell(content, className) {
  const td = document.createElement("td");
  if (content instanceof Node) td.append(content);
  else td.textContent = content;
  if (className) td.className = className;
  return td;
}

function renderRow(card) {
  const price = card.latest_price;

  const link = document.createElement("a");
  link.href = card.cardmarket_url;
  link.target = "_blank";
  link.rel = "noopener";
  link.textContent = card.name;

  const lowest = cell(euro(price?.low), "number");
  if (price?.low != null && Number(price.low) <= Number(card.target_price)) {
    lowest.classList.add("below-target");
    lowest.title = "At or below your target price";
  }

  const removeButton = document.createElement("button");
  removeButton.type = "button";
  removeButton.className = "secondary";
  removeButton.textContent = "Remove";
  removeButton.addEventListener("click", () => removeCard(card));

  const row = document.createElement("tr");
  row.append(
    cell(link),
    cell(`${card.set_name} (${card.set_code.toUpperCase()})`, "wrap"),
    cell(card.foil ? "Yes" : "No"),
    cell(euro(card.target_price), "number"),
    lowest,
    cell(euro(price?.trend), "number"),
    cell(euro(price?.avg30), "number"),
    cell(formatDate(price?.checked_at)),
    cell(removeButton),
  );
  return row;
}

async function loadWatchlist() {
  const response = await request("/watchlist");
  if (!response) return;
  if (!response.ok) {
    showMessage(await errorText(response), "error");
    return;
  }
  const cards = await response.json();
  tableBody.replaceChildren(...cards.map(renderRow));
  emptyState.hidden = cards.length > 0;
}

async function removeCard(card) {
  if (!confirm(`Remove ${card.name} (${card.set_name}) and its price history?`)) return;
  const response = await request(`/watchlist/${card.id}`, { method: "DELETE" });
  if (!response) return;
  if (response.ok) {
    showMessage(`Removed ${card.name}.`, "success");
    await loadWatchlist();
  } else {
    showMessage(await errorText(response), "error");
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const payload = {
    name: data.get("name").trim(),
    set_code: data.get("set_code").trim().toLowerCase(),
    target_price: data.get("target_price"),
    foil: data.get("foil") === "on",
  };

  const submitButton = form.querySelector("button[type=submit]");
  submitButton.disabled = true;
  const response = await request("/watchlist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  submitButton.disabled = false;
  if (!response) return;

  if (response.ok) {
    const card = await response.json();
    showMessage(`Added ${card.name} (${card.set_name}). Click "Check prices now" to fetch its price.`, "success");
    form.reset();
    await loadWatchlist();
  } else {
    showMessage(await errorText(response), "error");
  }
});

checkButton.addEventListener("click", async () => {
  checkButton.disabled = true;
  checkButton.textContent = "Checking…";
  const response = await request("/watchlist/check", { method: "POST" });
  checkButton.disabled = false;
  checkButton.textContent = "Check prices now";
  if (!response) return;

  if (!response.ok) {
    showMessage(await errorText(response), "error");
    return;
  }
  const result = await response.json();
  showMessage(
    `Checked ${result.checked}, skipped ${result.skipped} (price guide unchanged), alerts sent ${result.alerts_sent}.`,
    "success",
  );
  await loadWatchlist();
});

loadWatchlist();
