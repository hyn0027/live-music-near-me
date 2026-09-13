const filterButtons = [...document.querySelectorAll(".filter-chip")];
const mustSeeButtons = [...document.querySelectorAll(".must-see-filter")];
const cards = [...document.querySelectorAll(".event-card")];
const paginations = [...document.querySelectorAll(".pagination")];
const visibleCount = document.querySelector("#visible-count");
const filteredCount = document.querySelector("#filtered-count");
const emptyState = document.querySelector("#empty-state");
const saveButtons = [...document.querySelectorAll(".save-event")];
const savedOnlyButton = document.querySelector("#saved-only");
const savedCount = document.querySelector("#saved-count");
const exportSavedButton = document.querySelector("#export-saved");
const searchInput = document.querySelector("#event-search");
const eventGrid = document.querySelector("#event-grid");
const columnsSelect = document.querySelector("#events-per-row");

const SAVED_EVENTS_KEY = "live-music-near-me:saved-events:v1";
const COLUMNS_KEY = "live-music-near-me:columns:v1";

let currentPage = 1;
let selectedMustSee = "all";
let showSavedOnly = false;
let searchTerms = [];
let savedEventIds = loadSavedEventIds();

function loadColumnPreference() {
  try {
    const value = localStorage.getItem(COLUMNS_KEY) || "auto";
    return ["auto", "1", "2", "3", "4"].includes(value) ? value : "auto";
  } catch (error) {
    console.warn("Could not load the layout preference", error);
    return "auto";
  }
}

function setColumns(value) {
  eventGrid.dataset.columns = value;
  columnsSelect.value = value;
  try {
    localStorage.setItem(COLUMNS_KEY, value);
  } catch (error) {
    console.warn("Could not save the layout preference", error);
  }
}
const filters = {
  genre: { included: new Set(), excluded: new Set() },
  "detailed-genre": { included: new Set(), excluded: new Set() },
};

function cardGenres(card, type) {
  const value = type === "genre" ? card.dataset.genres : card.dataset.detailedGenres;
  return value ? value.split("|").filter(Boolean) : [];
}

function matchesType(card, type) {
  const genres = cardGenres(card, type);
  const state = filters[type];
  const included = state.included.size === 0 || genres.some((genre) => state.included.has(genre));
  const excluded = genres.some((genre) => state.excluded.has(genre));
  return included && !excluded;
}

function loadSavedEventIds() {
  try {
    const value = JSON.parse(localStorage.getItem(SAVED_EVENTS_KEY) || "[]");
    return new Set(Array.isArray(value) ? value.filter((item) => typeof item === "string") : []);
  } catch (error) {
    console.warn("Could not load saved events", error);
    return new Set();
  }
}

function persistSavedEventIds() {
  try {
    localStorage.setItem(SAVED_EVENTS_KEY, JSON.stringify([...savedEventIds]));
  } catch (error) {
    console.warn("Could not save events in this browser", error);
  }
}

function matches(card) {
  const matchesMustSee = selectedMustSee === "all" || card.dataset.mustSee === selectedMustSee;
  const matchesSaved = !showSavedOnly || savedEventIds.has(card.dataset.eventId);
  const searchableText = card.textContent.toLocaleLowerCase();
  const matchesSearch = searchTerms.every((term) => searchableText.includes(term));
  return matchesType(card, "genre") && matchesType(card, "detailed-genre") && matchesMustSee && matchesSaved && matchesSearch;
}

function updateSavedControls() {
  for (const card of cards) {
    const button = card.querySelector(".save-event");
    const isSaved = savedEventIds.has(card.dataset.eventId);
    button.classList.toggle("saved", isSaved);
    button.setAttribute("aria-pressed", String(isSaved));
    button.textContent = isSaved ? "♥ Saved" : "♡ Save";
  }
  savedCount.textContent = savedEventIds.size;
  exportSavedButton.disabled = savedEventIds.size === 0;
}

function updatePagination(totalPages, totalMatching) {
  for (const pagination of paginations) {
    pagination.classList.toggle("hidden", totalMatching <= PAGE_SIZE);
    pagination.querySelector('[data-page-action="prev"]').disabled = currentPage === 1;
    pagination.querySelector('[data-page-action="next"]').disabled = currentPage === totalPages;
    pagination.querySelector(".page-info").textContent = `Page ${currentPage} of ${totalPages}`;
  }
}

function updateEvents(resetPage = false) {
  if (resetPage) currentPage = 1;
  const matching = cards.filter(matches);
  const totalPages = Math.max(1, Math.ceil(matching.length / PAGE_SIZE));
  currentPage = Math.min(currentPage, totalPages);
  const pageCards = new Set(matching.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE));

  for (const card of cards) card.classList.toggle("hidden", !pageCards.has(card));
  visibleCount.textContent = pageCards.size;
  filteredCount.textContent = matching.length;
  emptyState.classList.toggle("visible", matching.length === 0);
  updatePagination(totalPages, matching.length);
}

filterButtons.forEach((button) => button.addEventListener("click", () => {
  const { filterMode: mode, filterType: type, genre } = button.dataset;
  const active = filters[type][`${mode}d`];
  const oppositeMode = mode === "include" ? "exclude" : "include";
  const opposite = filters[type][`${oppositeMode}d`];

  if (active.has(genre)) active.delete(genre);
  else {
    active.add(genre);
    opposite.delete(genre);
  }
  button.classList.toggle(`${mode}-active`, active.has(genre));
  const pair = filterButtons.find((candidate) =>
    candidate.dataset.filterType === type &&
    candidate.dataset.genre === genre &&
    candidate.dataset.filterMode === oppositeMode
  );
  pair?.classList.remove(`${oppositeMode}-active`);
  updateEvents(true);
}));

mustSeeButtons.forEach((button) => button.addEventListener("click", () => {
  selectedMustSee = button.dataset.mustSeeFilter;
  mustSeeButtons.forEach((candidate) => candidate.classList.toggle("active", candidate === button));
  updateEvents(true);
}));

saveButtons.forEach((button) => button.addEventListener("click", () => {
  const eventId = button.closest(".event-card").dataset.eventId;
  if (savedEventIds.has(eventId)) savedEventIds.delete(eventId);
  else savedEventIds.add(eventId);
  persistSavedEventIds();
  updateSavedControls();
  updateEvents(showSavedOnly);
}));

savedOnlyButton.addEventListener("click", () => {
  showSavedOnly = !showSavedOnly;
  savedOnlyButton.classList.toggle("active", showSavedOnly);
  savedOnlyButton.setAttribute("aria-pressed", String(showSavedOnly));
  updateEvents(true);
});

searchInput.addEventListener("input", () => {
  searchTerms = searchInput.value
    .toLocaleLowerCase()
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  updateEvents(true);
});

columnsSelect.addEventListener("change", () => setColumns(columnsSelect.value));

exportSavedButton.addEventListener("click", () => {
  const events = cards
    .filter((card) => savedEventIds.has(card.dataset.eventId))
    .map((card) => ({
      band: card.dataset.band,
      venue: card.dataset.venue,
      date: card.dataset.date,
      link: card.dataset.eventId,
    }));
  const blob = new Blob([JSON.stringify(events, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "saved-events.json";
  link.click();
  URL.revokeObjectURL(url);
});

document.querySelector("#clear-filters").addEventListener("click", () => {
  Object.values(filters).forEach((state) => {
    state.included.clear();
    state.excluded.clear();
  });
  selectedMustSee = "all";
  showSavedOnly = false;
  searchTerms = [];
  searchInput.value = "";
  filterButtons.forEach((button) => button.classList.remove("include-active", "exclude-active"));
  mustSeeButtons.forEach((button) => button.classList.toggle("active", button.dataset.mustSeeFilter === "all"));
  savedOnlyButton.classList.remove("active");
  savedOnlyButton.setAttribute("aria-pressed", "false");
  updateEvents(true);
});

paginations.forEach((pagination) => pagination.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button || button.disabled) return;
  currentPage += button.dataset.pageAction === "next" ? 1 : -1;
  updateEvents();
  window.scrollTo({ top: 0, behavior: "smooth" });
}));

updateSavedControls();
setColumns(loadColumnPreference());
updateEvents();
