/**
 * DoneFlow browser entry point.
 *
 * This ES module coordinates the REST API client and board renderer to deliver
 * the PRD 7.2 task creation flow with validation, loading feedback, real-time
 * distribution updates, and Portuguese toast notifications.
 */

import {
  createTask,
  deleteTask,
  getAllTasks,
  getDistribution,
} from "./api.js";
import {
  QUADRANTS,
  addCard,
  hideLoadingState,
  removeCard,
  renderBoard,
  showLoadingState,
  updateDistributionPanel,
} from "./board.js";

const MIN_TASK_DESCRIPTION_LENGTH = 5;
const LOADING_QUADRANT = "DO_NOW";
const TOAST_DURATION_MS = 4200;

const QUADRANT_LABELS = {
  DO_NOW: "Fazer agora",
  SCHEDULE: "Agendar",
  DELEGATE: "Delegar",
  ELIMINATE: "Eliminar",
};

/**
 * @typedef {Object} ValidationResult
 * @property {boolean} valid - Whether the task description can be submitted.
 * @property {string} description - Trimmed task description.
 * @property {string} [message] - Friendly validation message when invalid.
 */

/**
 * Validate the task description before any API call is attempted.
 *
 * @param {string} value - Raw textarea value typed by the user.
 * @returns {ValidationResult} Validation state and sanitized description.
 */
export function validateTaskDescription(value) {
  const description = String(value || "").trim();

  if (description.length < MIN_TASK_DESCRIPTION_LENGTH) {
    return {
      valid: false,
      description,
      message: "A descrição precisa ter pelo menos 5 caracteres.",
    };
  }

  return { valid: true, description };
}

/**
 * Create or reuse the toast region used by DoneFlow notifications.
 *
 * @returns {HTMLElement} Toast container element.
 */
function getToastRegion() {
  let region = document.querySelector(".toast-region");

  if (region instanceof HTMLElement) {
    return region;
  }

  region = document.createElement("div");
  region.className = "toast-region";
  region.setAttribute("aria-live", "polite");
  region.setAttribute("aria-atomic", "true");
  document.body.appendChild(region);

  return region;
}

/**
 * Show a short toast notification in Portuguese.
 *
 * @param {string} message - Message displayed to the user.
 * @param {"success" | "error"} [variant="error"] - Visual notification variant.
 * @returns {HTMLElement} Toast element added to the DOM.
 */
export function showToast(message, variant = "error") {
  const toast = document.createElement("p");
  toast.className = `toast toast--${variant}`;
  toast.textContent = message;
  toast.setAttribute("role", variant === "error" ? "alert" : "status");

  getToastRegion().appendChild(toast);

  setTimeout(() => {
    toast.classList.add("toast--leaving");
    toast.addEventListener("transitionend", () => toast.remove(), { once: true });
    setTimeout(() => toast.remove(), 250);
  }, TOAST_DURATION_MS);

  return toast;
}

/**
 * Toggle form controls while a task is being categorized.
 *
 * @param {HTMLFormElement} form - New task form.
 * @param {boolean} isLoading - Whether the create flow is waiting for the API.
 * @returns {void}
 */
function setFormLoading(form, isLoading) {
  const button = form.querySelector('button[type="submit"]');
  const field = form.querySelector("#task-description");

  form.classList.toggle("new-task--loading", isLoading);
  form.setAttribute("aria-busy", String(isLoading));

  if (field instanceof HTMLTextAreaElement) {
    field.disabled = isLoading;
  }

  if (button instanceof HTMLButtonElement) {
    if (!button.dataset.defaultLabel) {
      button.dataset.defaultLabel = button.textContent || "Adicionar";
    }

    button.disabled = isLoading;
    button.textContent = isLoading ? "Categorizando..." : button.dataset.defaultLabel;
  }
}

/**
 * Hide any skeleton card shown during task creation.
 *
 * @returns {void}
 */
function hideAllLoadingStates() {
  QUADRANTS.forEach((quadrant) => hideLoadingState(quadrant));
}

/**
 * Refresh the side-panel distribution counters and progress bars.
 *
 * @returns {Promise<void>} Resolves after the panel is updated.
 */
export async function refreshDistribution() {
  const distribution = await getDistribution();
  updateDistributionPanel(distribution);
}

/**
 * Load existing tasks as soon as the page opens.
 *
 * @returns {Promise<void>} Resolves once initial board state is rendered.
 */
async function loadInitialTasks() {
  try {
    const tasks = await getAllTasks();
    renderBoard(tasks);
    await refreshDistribution();
  } catch (error) {
    showToast(
      `Não foi possível carregar suas tarefas. ${error instanceof Error ? error.message : ""}`.trim(),
    );
  }
}

/**
 * Submit the current task description to DoneFlow for AI categorization.
 *
 * @param {SubmitEvent} event - Browser submit event from the new task form.
 * @returns {Promise<void>} Resolves after create/render/distribution updates finish.
 */
export async function handleTaskSubmit(event) {
  event.preventDefault();

  const form = event.currentTarget;
  if (!(form instanceof HTMLFormElement)) {
    return;
  }

  const field = form.querySelector("#task-description");
  if (!(field instanceof HTMLTextAreaElement)) {
    showToast("Não foi possível encontrar o campo de descrição da tarefa.");
    return;
  }

  const validation = validateTaskDescription(field.value);
  if (!validation.valid) {
    showToast(validation.message || "Revise a descrição da tarefa.");
    field.focus();
    return;
  }

  setFormLoading(form, true);
  showLoadingState(LOADING_QUADRANT);

  try {
    const description = validation.description;
    const task = await createTask(description);
    hideAllLoadingStates();
    addCard(task);
    field.value = "";
    await refreshDistribution();
    showToast(`Tarefa adicionada ao quadrante ${QUADRANT_LABELS[task.quadrant]}.`, "success");
  } catch (error) {
    hideAllLoadingStates();
    showToast(
      `Não foi possível adicionar a tarefa. ${error instanceof Error ? error.message : ""}`.trim(),
    );
  } finally {
    setFormLoading(form, false);
    field.focus();
  }
}

/**
 * Remove a task when a card dispatches the board removal event.
 *
 * @param {Event} event - Custom board event with the task id in detail.
 * @returns {Promise<void>} Resolves after removal and distribution refresh.
 */
async function handleRemoveTask(event) {
  const taskId = event instanceof CustomEvent ? event.detail?.taskId : null;

  if (!taskId) {
    return;
  }

  try {
    await deleteTask(String(taskId));
    removeCard(taskId);
    await refreshDistribution();
    showToast("Tarefa removida com sucesso.", "success");
  } catch (error) {
    showToast(
      `Não foi possível remover a tarefa. ${error instanceof Error ? error.message : ""}`.trim(),
    );
  }
}

/**
 * Wire event listeners for the DoneFlow static UI.
 *
 * @returns {void}
 */
export function initDoneFlowApp() {
  const form = document.querySelector(".new-task");
  const field = document.getElementById("task-description");

  if (form instanceof HTMLFormElement) {
    form.addEventListener("submit", (event) => {
      void handleTaskSubmit(event);
    });
  }

  if (field instanceof HTMLTextAreaElement && form instanceof HTMLFormElement) {
    field.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });
  }

  document.addEventListener("doneflow:remove-task", (event) => {
    void handleRemoveTask(event);
  });

  void loadInitialTasks();
}

document.addEventListener("DOMContentLoaded", initDoneFlowApp);
