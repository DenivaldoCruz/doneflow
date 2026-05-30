/**
 * DoneFlow Eisenhower board UI module.
 *
 * This module owns DOM rendering for the 2x2 matrix without any framework
 * dependency. It uses semantic hooks already present in static/index.html and
 * CSS classes from static/css/board.css for card, skeleton, and bar animations.
 */

/**
 * Valid Eisenhower Matrix quadrant values.
 *
 * @typedef {"DO_NOW" | "SCHEDULE" | "DELEGATE" | "ELIMINATE"} Quadrant
 */

/**
 * Task payload rendered as a board card.
 *
 * @typedef {Object} BoardTask
 * @property {string | number} id - Stable task identifier used by data-task-id.
 * @property {string} description - Human-readable task description.
 * @property {Quadrant} quadrant - Eisenhower Matrix quadrant for the card.
 * @property {number} [ai_confidence] - Optional AI confidence from 0 to 1.
 * @property {number} [confidence] - Optional normalized confidence from 0 to 1.
 */

/**
 * Distribution payload returned by the DoneFlow API.
 *
 * @typedef {Object} Distribution
 * @property {number} DO_NOW - Number of urgent and important tasks.
 * @property {number} SCHEDULE - Number of important but not urgent tasks.
 * @property {number} DELEGATE - Number of urgent but less-important tasks.
 * @property {number} ELIMINATE - Number of low-priority tasks.
 * @property {number} total - Total number of tasks across all quadrants.
 */

/** @type {Quadrant[]} */
export const QUADRANTS = ["DO_NOW", "SCHEDULE", "DELEGATE", "ELIMINATE"];

const CARD_REGION_IDS = {
  DO_NOW: "cards-do-now",
  SCHEDULE: "cards-schedule",
  DELEGATE: "cards-delegate",
  ELIMINATE: "cards-eliminate",
};

const QUADRANT_LABELS = {
  DO_NOW: "Fazer agora",
  SCHEDULE: "Agendar",
  DELEGATE: "Delegar",
  ELIMINATE: "Eliminar",
};

const REMOVE_ANIMATION_MS = 220;

/**
 * Escape an arbitrary task id for safe use inside a CSS attribute selector.
 *
 * @param {string} value - Raw task id.
 * @returns {string} CSS-safe selector fragment.
 */
function escapeSelectorValue(value) {
  if (globalThis.CSS && typeof globalThis.CSS.escape === "function") {
    return globalThis.CSS.escape(value);
  }

  return value.replace(/[\\"\]]/g, "\\$&");
}

/**
 * Return the canonical quadrant value when the provided value is valid.
 *
 * @param {string} value - Candidate quadrant value.
 * @returns {Quadrant} Canonical quadrant value.
 * @throws {Error} When the quadrant is unknown.
 */
function normalizeQuadrant(value) {
  const normalized = String(value || "").trim().toUpperCase();

  if (QUADRANTS.includes(normalized)) {
    return normalized;
  }

  throw new Error(`Quadrante inválido no board DoneFlow: ${value}`);
}

/**
 * Get the card container for a quadrant.
 *
 * @param {Quadrant} quadrant - Quadrant whose card region should be selected.
 * @returns {HTMLElement} Card region element.
 * @throws {Error} When the region is missing from the static template.
 */
function getCardRegion(quadrant) {
  const region = document.getElementById(CARD_REGION_IDS[quadrant]);

  if (!(region instanceof HTMLElement)) {
    throw new Error(`Área de cards não encontrada para ${quadrant}.`);
  }

  return region;
}

/**
 * Get the section wrapper for a quadrant.
 *
 * @param {Quadrant} quadrant - Quadrant whose section should be selected.
 * @returns {HTMLElement | null} Matching quadrant section when present.
 */
function getQuadrantSection(quadrant) {
  return document.querySelector(`[data-quadrant="${quadrant}"]`);
}

/**
 * Format a confidence value as a Portuguese percentage label.
 *
 * @param {BoardTask} task - Task with optional confidence fields.
 * @returns {string} Confidence label displayed in card metadata.
 */
function formatConfidence(task) {
  const rawConfidence = task.ai_confidence ?? task.confidence;

  if (typeof rawConfidence !== "number" || Number.isNaN(rawConfidence)) {
    return "confiança não informada";
  }

  return `confiança ${Math.round(rawConfidence * 100)}%`;
}

/**
 * Build a task card DOM node using textContent to avoid HTML injection.
 *
 * @param {BoardTask} task - Task represented by the card.
 * @returns {HTMLElement} Renderable card element.
 */
function createTaskCard(task) {
  const quadrant = normalizeQuadrant(task.quadrant);
  const card = document.createElement("article");
  card.className = "task-card";
  card.dataset.taskId = String(task.id);
  card.dataset.quadrant = quadrant;
  card.setAttribute("aria-label", `Tarefa ${QUADRANT_LABELS[quadrant]}`);

  const text = document.createElement("p");
  text.className = "task-card__text";
  text.textContent = task.description;

  const removeButton = document.createElement("button");
  removeButton.className = "task-card__remove";
  removeButton.type = "button";
  removeButton.textContent = "×";
  removeButton.setAttribute("aria-label", "Remover tarefa");
  removeButton.addEventListener("click", () => {
    card.dispatchEvent(
      new CustomEvent("doneflow:remove-task", {
        bubbles: true,
        detail: { taskId: task.id },
      }),
    );
  });

  const meta = document.createElement("span");
  meta.className = "task-card__meta";
  meta.textContent = `${quadrant} · ${formatConfidence(task)}`;

  card.appendChild(text);
  card.appendChild(removeButton);
  card.appendChild(meta);

  return card;
}

/**
 * Count rendered task cards by quadrant, excluding skeleton loading cards.
 *
 * @returns {Record<Quadrant, number>} Current card counts by quadrant.
 */
function collectRenderedCounts() {
  return QUADRANTS.reduce((counts, quadrant) => {
    counts[quadrant] = getCardRegion(quadrant).querySelectorAll(
      ".task-card:not(.task-card--loading)",
    ).length;
    return counts;
  }, {});
}

/**
 * Render all tasks on the Eisenhower board, grouped into their quadrants.
 *
 * @param {BoardTask[]} tasks - Tasks returned by the DoneFlow API.
 * @returns {void}
 */
export function renderBoard(tasks) {
  QUADRANTS.forEach((quadrant) => {
    getCardRegion(quadrant).replaceChildren();
  });

  tasks.forEach((task) => {
    const quadrant = normalizeQuadrant(task.quadrant);
    getCardRegion(quadrant).appendChild(createTaskCard(task));
  });

  updateCounters();
}

/**
 * Add one task card to the correct quadrant with an entry animation.
 *
 * @param {BoardTask} task - Task created or updated by DoneFlow.
 * @returns {HTMLElement} The card appended to the board.
 */
export function addCard(task) {
  const quadrant = normalizeQuadrant(task.quadrant);
  const card = createTaskCard(task);
  card.classList.add("task-card--entering");
  card.style.opacity = "0";
  card.style.transform = "translateY(0.5rem) scale(0.98)";

  hideLoadingState(quadrant);
  getCardRegion(quadrant).appendChild(card);

  requestAnimationFrame(() => {
    card.classList.remove("task-card--entering");
    card.style.opacity = "";
    card.style.transform = "";
  });

  updateCounters();
  return card;
}

/**
 * Remove one task card from the board with an exit animation.
 *
 * @param {string | number} taskId - Identifier stored in the card data-task-id attribute.
 * @returns {boolean} True when a matching card was found.
 */
export function removeCard(taskId) {
  const selector = `.task-card[data-task-id="${escapeSelectorValue(String(taskId))}"]`;
  const card = document.querySelector(selector);

  if (!(card instanceof HTMLElement)) {
    return false;
  }

  card.classList.add("task-card--removing");
  card.style.overflow = "hidden";
  card.style.transition = [
    `opacity ${REMOVE_ANIMATION_MS}ms ease`,
    `transform ${REMOVE_ANIMATION_MS}ms ease`,
    `max-height ${REMOVE_ANIMATION_MS}ms ease`,
    `margin ${REMOVE_ANIMATION_MS}ms ease`,
    `padding ${REMOVE_ANIMATION_MS}ms ease`,
  ].join(", ");
  card.style.maxHeight = `${card.scrollHeight}px`;

  let removalFinished = false;
  const finishRemoval = () => {
    if (removalFinished) {
      return;
    }

    removalFinished = true;
    card.removeEventListener("transitionend", finishRemoval);
    card.remove();
    updateCounters();
  };

  card.addEventListener("transitionend", finishRemoval);
  setTimeout(finishRemoval, REMOVE_ANIMATION_MS + 80);

  requestAnimationFrame(() => {
    card.style.opacity = "0";
    card.style.transform = "translateY(-0.35rem) scale(0.98)";
    card.style.maxHeight = "0";
    card.style.margin = "0";
    card.style.paddingTop = "0";
    card.style.paddingBottom = "0";
  });

  return true;
}

/**
 * Update distribution panel counters and animate each progress bar.
 *
 * @param {Distribution} distribution - Counts grouped by quadrant plus total.
 * @returns {void}
 */
export function updateDistributionPanel(distribution) {
  const providedTotal = Number(distribution.total);
  const total = Number.isFinite(providedTotal)
    ? providedTotal
    : QUADRANTS.reduce((sum, quadrant) => sum + Number(distribution[quadrant] || 0), 0);

  QUADRANTS.forEach((quadrant, index) => {
    const item =
      document.querySelector(`.distribution__item[data-quadrant="${quadrant}"]`) ||
      document.querySelectorAll(".distribution__item")[index];

    if (!(item instanceof HTMLElement)) {
      return;
    }

    item.dataset.quadrant = quadrant;

    const count = Number(distribution[quadrant] || 0);
    const percentage = total > 0 ? Math.round((count / total) * 100) : 0;
    const meta = item.querySelector(".distribution__meta strong");
    const fill = item.querySelector(".distribution__fill");

    if (meta) {
      meta.textContent = `${count} · ${percentage}%`;
    }

    if (fill instanceof HTMLElement) {
      fill.style.setProperty("--value", "0%");
      fill.setAttribute("role", "progressbar");
      fill.setAttribute("aria-valuemin", "0");
      fill.setAttribute("aria-valuemax", "100");
      fill.setAttribute("aria-valuenow", String(percentage));
      fill.setAttribute("aria-label", `${QUADRANT_LABELS[quadrant]}: ${percentage}%`);

      requestAnimationFrame(() => {
        fill.style.setProperty("--value", `${percentage}%`);
      });
    }
  });
}

/**
 * Show a skeleton loading card in the quadrant currently being categorized.
 *
 * @param {Quadrant} quadrant - Quadrant that should display the loading placeholder.
 * @returns {HTMLElement} Loading card appended to the quadrant.
 */
export function showLoadingState(quadrant) {
  const normalizedQuadrant = normalizeQuadrant(quadrant);
  hideLoadingState(normalizedQuadrant);

  const loadingCard = document.createElement("article");
  loadingCard.className = "task-card task-card--loading";
  loadingCard.dataset.loadingQuadrant = normalizedQuadrant;
  loadingCard.setAttribute("aria-label", "Categorizando tarefa");
  loadingCard.setAttribute("aria-busy", "true");

  getCardRegion(normalizedQuadrant).appendChild(loadingCard);
  return loadingCard;
}

/**
 * Hide the skeleton loading card from the selected quadrant.
 *
 * @param {Quadrant} quadrant - Quadrant whose loading placeholder should be removed.
 * @returns {void}
 */
export function hideLoadingState(quadrant) {
  const normalizedQuadrant = normalizeQuadrant(quadrant);
  getCardRegion(normalizedQuadrant)
    .querySelectorAll(".task-card--loading")
    .forEach((loadingCard) => loadingCard.remove());
}

/**
 * Update each quadrant badge with the current rendered card count.
 *
 * @returns {Record<Quadrant, number>} Updated counts by quadrant.
 */
export function updateCounters() {
  const counts = collectRenderedCounts();

  QUADRANTS.forEach((quadrant) => {
    const count = counts[quadrant];
    const badge = getQuadrantSection(quadrant)?.querySelector(".quadrant__count");

    if (badge) {
      badge.textContent = String(count);
      badge.setAttribute("aria-label", `${count} ${count === 1 ? "tarefa" : "tarefas"}`);
    }
  });

  return counts;
}
