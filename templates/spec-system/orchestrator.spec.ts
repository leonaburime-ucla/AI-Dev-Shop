/**
 * Orchestrator Output Model Spec: <feature-name>
 *
 * SPEC PACKAGE FILE: templates/spec-system/orchestrator.spec.ts
 * Part of the spec-system package. See templates/spec-system/ for all required files.
 *
 * Spec ID:      SPEC-<NNN>
 * Feature:      FEAT-<NNN>-<short-feature-name>
 * Version:      <semver>
 * Content Hash: <sha256 — recompute on every edit>
 * Last Edited:  <ISO-8601 UTC>
 *
 * PURPOSE: This file defines the input/output contract of the orchestrator layer
 * for this feature as TypeScript types. It is the authoritative source of truth for:
 *   - What the orchestrator receives as input (props / call arguments)
 *   - What the orchestrator exposes as output (return value / injected interface)
 *   - Which output fields are required vs optional
 *   - The lifecycle hooks the orchestrator calls and when
 *   - The error surface the orchestrator surfaces to consumers
 *
 * "Orchestrator" means any coordinator layer: a React hook, a service class,
 * a use-case object, a saga/thunk coordinator, or a controller. The shape
 * defined here is what downstream consumers depend on — not the internal impl.
 *
 * This file is consumed by:
 *   - The TDD Agent (to write orchestrator contract tests)
 *   - The Programmer Agent (to implement the orchestrator)
 *   - The UI Agent (to build components that consume the orchestrator)
 *   - The Code Review Agent (to verify implementation matches contract)
 */

// ---------------------------------------------------------------------------
// Orchestrator Identity
// ---------------------------------------------------------------------------

/**
 * Human-readable name for this orchestrator.
 * Used in test output, error messages, and logging.
 * Format: "<FeatureName>Orchestrator"
 */
export const ORCHESTRATOR_NAME = '<FeatureName>Orchestrator' as const;

// ---------------------------------------------------------------------------
// Input Props
// ---------------------------------------------------------------------------

/**
 * All inputs the orchestrator receives at initialization / call time.
 *
 * Rules:
 *   - If consumed as a React hook: these are the hook's parameters.
 *   - If consumed as a class: these are constructor arguments.
 *   - If consumed as a function: these are the function's parameters.
 *   - Required fields have no `?`. Optional fields have `?` and a documented default.
 *   - No input field should be a callback that mutates external state directly —
 *     use the output's callback props for that.
 */
export interface OrchestratorInputProps {
  // --- Required Inputs ---

  /**
   * The ID of the parent resource this orchestrator operates within.
   * Must be a valid UUID v4. The orchestrator does not validate format —
   * invalid IDs will result in an API error surfaced through the error output.
   */
  parentId: string;

  // --- Optional Inputs (with documented defaults) ---

  /**
   * Maximum number of items to load per page.
   * Default: 20. Min: 1. Max: 100.
   * Values outside [1, 100] are clamped silently — no error is thrown.
   */
  pageSize?: number;

  /**
   * If true, the orchestrator will automatically fetch the first page of items
   * on mount/initialization without requiring an explicit call to `loadItems`.
   * Default: true.
   */
  autoFetch?: boolean;

  /**
   * Callback invoked after a successful item creation.
   * Receives the newly created item.
   * Optional — omitting it does not affect orchestrator behavior.
   */
  onItemCreated?: (item: OrchestratorItem) => void;

  /**
   * Callback invoked after a successful item deletion.
   * Receives the ID of the deleted item.
   * Optional — omitting it does not affect orchestrator behavior.
   */
  onItemDeleted?: (itemId: string) => void;

  /**
   * Callback invoked whenever an error occurs.
   * Receives the error. The orchestrator does not suppress errors when this
   * callback is provided — errors are still surfaced through the output's
   * `errors` field.
   * Optional — omitting it does not affect orchestrator behavior.
   */
  onError?: (error: OrchestratorError) => void;
}

// ---------------------------------------------------------------------------
// Orchestrator Output (Return Interface)
// ---------------------------------------------------------------------------

/**
 * The complete interface exposed by the orchestrator to its consumers.
 *
 * All fields are part of the public contract. Any field not listed here
 * is an implementation detail — consumers must not depend on it.
 *
 * Rules:
 *   - Required output fields have no `?`. They are always present in the returned object.
 *   - Optional output fields have `?`. They may be absent when not applicable.
 *   - Functions are included as typed method signatures.
 *   - Async functions return Promise<T> — never return void from an async operation
 *     that can fail (return Promise<OrchestratorResult<T>> instead).
 */
export interface OrchestratorOutput {
  // -------------------------------------------------------------------------
  // State (derived from underlying state — read-only to consumers)
  // -------------------------------------------------------------------------

  /**
   * The current list of loaded items, sorted by createdAt descending.
   * Empty array if none have been loaded. Never null.
   * This is a derived view — mutate via the action functions below.
   */
  items: OrchestratorItem[];

  /**
   * The currently selected item, or null if no item is selected.
   */
  selectedItem: OrchestratorItem | null;

  /**
   * True if any async operation is currently in-flight.
   * Use to disable UI controls globally.
   */
  isLoading: boolean;

  /**
   * Granular loading flags per operation.
   * Use when different UI elements need to reflect individual operation states.
   */
  loadingStates: OrchestratorLoadingStates;

  /**
   * The most recent error across all operations, or null if no error is present.
   * Cleared automatically when the corresponding operation is retried.
   */
  error: OrchestratorError | null;

  /**
   * Granular error slots per operation.
   * Use when different UI elements need to display individual operation errors.
   */
  errors: OrchestratorErrorStates;

  /**
   * True if there are more items to load (pagination).
   * False if all items have been fetched or no items exist.
   */
  hasMoreItems: boolean;

  /**
   * True if the item list has been successfully fetched at least once
   * and is not currently loading. Use to distinguish "empty" from "not yet loaded."
   */
  isReady: boolean;

  // -------------------------------------------------------------------------
  // Actions (async operations — always return OrchestratorResult<T>)
  // -------------------------------------------------------------------------

  /**
   * Loads the first page of items. Replaces any previously loaded items.
   * Sets loading.fetchingItems = true while in-flight.
   * On success: items is replaced, error.fetchItems is cleared.
   * On failure: items is unchanged, error.fetchItems is set.
   */
  loadItems: () => Promise<OrchestratorResult<OrchestratorItem[]>>;

  /**
   * Loads the next page of items and appends to the current list.
   * No-op if hasMoreItems is false.
   * Sets loading.fetchingItems = true while in-flight.
   */
  loadMoreItems: () => Promise<OrchestratorResult<OrchestratorItem[]>>;

  /**
   * Creates a new item under the parentId provided in InputProps.
   * Applies an optimistic update immediately.
   * On success: items contains the server-confirmed item.
   * On failure: optimistic item is removed, error.createItem is set.
   * Calls InputProps.onItemCreated on success.
   */
  createItem: (params: CreateItemParams) => Promise<OrchestratorResult<OrchestratorItem>>;

  /**
   * Updates an existing item by ID.
   * Applies an optimistic update immediately.
   * On success: item is replaced with server-confirmed version.
   * On failure: item is rolled back, error.updateItem is set.
   */
  updateItem: (
    itemId: string,
    changes: UpdateItemChanges
  ) => Promise<OrchestratorResult<OrchestratorItem>>;

  /**
   * Deletes an item by ID.
   * Removes the item optimistically.
   * On success: item remains removed.
   * On failure: item is restored, error.deleteItem is set.
   * Calls InputProps.onItemDeleted on success.
   */
  deleteItem: (itemId: string) => Promise<OrchestratorResult<void>>;

  /**
   * Selects an item by ID. Sets selectedItem to the matching item.
   * No-op if the ID does not match any item in the current list.
   * This is a synchronous operation — no loading state changes.
   */
  selectItem: (itemId: string) => void;

  /**
   * Clears the current selection. Sets selectedItem to null.
   */
  clearSelection: () => void;

  /**
   * Resets the orchestrator to its initial state.
   * Cancels any in-flight requests (best-effort).
   * Clears all items, errors, and selection.
   */
  reset: () => void;
}

// ---------------------------------------------------------------------------
// Supporting Types for Orchestrator Output
// ---------------------------------------------------------------------------

/**
 * The item shape exposed to consumers through the orchestrator output.
 * This may be a projected/derived view of the underlying state shape.
 * Consumers depend on this type — not on the internal FeatureItem type.
 */
export interface OrchestratorItem {
  /** UUID v4. */
  id: string;

  /** Human-readable name. */
  name: string;

  /** Current lifecycle status. */
  status: OrchestratorItemStatus;

  /** ISO-8601 UTC creation timestamp. */
  createdAt: string;

  /** ISO-8601 UTC last-modified timestamp. */
  updatedAt: string;

  /**
   * True if this item is the result of an optimistic update that has not yet
   * been confirmed by the server. Consumers may render a pending indicator.
   */
  isPending: boolean;
}

export type OrchestratorItemStatus =
  | 'pending'
  | 'active'
  | 'completed'
  | 'failed'
  | 'archived';

/**
 * Parameters for the createItem action.
 */
export interface CreateItemParams {
  /** Human-readable name. 1–255 characters, non-blank. */
  name: string;

  /**
   * Optional configuration overrides.
   * Defaults are applied per behavior.spec.md if omitted.
   */
  options?: {
    notifyOnComplete?: boolean;
    maxRetries?: number;
  };
}

/**
 * Fields that can be changed via the updateItem action.
 * At least one field must be present — an empty object is rejected.
 */
export interface UpdateItemChanges {
  /** New name. 1–255 characters, non-blank. Optional. */
  name?: string;

  /** New status. Only valid transitions per behavior.spec.md are accepted. */
  status?: OrchestratorItemStatus;
}

/**
 * Granular loading state per operation, exposed by the orchestrator output.
 */
export interface OrchestratorLoadingStates {
  fetchingItems: boolean;
  creatingItem: boolean;
  updatingItem: boolean;
  deletingItem: boolean;
}

/**
 * Granular error state per operation, exposed by the orchestrator output.
 * null = no error for that operation.
 */
export interface OrchestratorErrorStates {
  fetchItems: OrchestratorError | null;
  createItem: OrchestratorError | null;
  updateItem: OrchestratorError | null;
  deleteItem: OrchestratorError | null;
}

/**
 * The error shape exposed by the orchestrator to consumers.
 * Decoupled from HTTP transport — consumers should not need to know about
 * status codes. Switch on `code`.
 */
export interface OrchestratorError {
  /**
   * Machine-readable error code. Consumers switch on this field.
   * Maps to ApiErrorCode in api.spec.ts for network errors.
   * Additional codes for client-side errors are defined below.
   */
  code: string;

  /**
   * Human-readable description. For display/logging only — do not parse.
   */
  message: string;

  /**
   * ISO-8601 UTC timestamp of when the error occurred.
   */
  occurredAt: string;

  /**
   * True if the operation that produced this error is safe to retry
   * without additional user input.
   */
  isRetryable: boolean;

  /**
   * Correlation ID from the server, if the error originated from an API call.
   * null for client-side errors.
   */
  correlationId: string | null;
}

/**
 * The result type returned by all async orchestrator action functions.
 * Consumers must check `success` before accessing `data`.
 * Consumers must check `!success` before accessing `error`.
 *
 * This is a tagged union — never mix success and error fields.
 */
export type OrchestratorResult<T> =
  | { success: true; data: T }
  | { success: false; error: OrchestratorError };

// ---------------------------------------------------------------------------
// Lifecycle Hooks (for testing)
// ---------------------------------------------------------------------------

/**
 * Documents the orchestrator's lifecycle call sequence.
 * The TDD Agent uses this to write lifecycle integration tests.
 *
 * On initialization (mount or construction):
 *   1. InputProps are validated. If invalid, onError is called and initialization aborts.
 *   2. If autoFetch is true (default), loadItems() is called automatically.
 *
 * On loadItems() call:
 *   1. loadingStates.fetchingItems → true
 *   2. errors.fetchItems → null (cleared)
 *   3. API request is issued
 *   4a. On success: items replaced, lastFetchedAt updated, loadingStates.fetchingItems → false
 *   4b. On failure: items unchanged, errors.fetchItems set, loadingStates.fetchingItems → false
 *   5. onError callback called if 4b
 *
 * On createItem() call:
 *   1. loadingStates.creatingItem → true
 *   2. errors.createItem → null (cleared)
 *   3. Optimistic item added to items with isPending = true
 *   4. API request is issued
 *   5a. On success: optimistic item replaced with server item (isPending = false),
 *       loadingStates.creatingItem → false, onItemCreated callback called
 *   5b. On failure: optimistic item removed, errors.createItem set,
 *       loadingStates.creatingItem → false, onError callback called
 *
 * On reset() call:
 *   1. All in-flight requests are cancelled (best-effort — network responses may still arrive)
 *   2. State is reset to initial values
 *   3. No callbacks are invoked
 */
export const ORCHESTRATOR_LIFECYCLE = {
  onInit: ['validate InputProps', 'if autoFetch: call loadItems'],
  onLoadItems: ['set loading', 'clear error', 'fetch', 'update state', 'call onError if failed'],
  onCreateItem: ['set loading', 'clear error', 'optimistic add', 'fetch', 'reconcile or rollback', 'call onItemCreated or onError'],
  onUpdateItem: ['set loading', 'clear error', 'optimistic update', 'fetch', 'reconcile or rollback', 'call onError if failed'],
  onDeleteItem: ['set loading', 'clear error', 'optimistic remove', 'fetch', 'confirm or restore', 'call onItemDeleted or onError'],
  onReset: ['cancel in-flight requests', 'reset to initial state'],
} as const;

// ---------------------------------------------------------------------------
// Contract Invariants
// ---------------------------------------------------------------------------

/**
 * Invariants that must hold on the orchestrator output at any point in time.
 * The TDD Agent must assert these after every action in integration tests.
 */
export const ORCHESTRATOR_INVARIANTS = [
  'items is always an array — never null or undefined',
  'selectedItem, if non-null, always has an id that exists in items',
  'isLoading is true if and only if at least one loadingStates field is true',
  'error equals the most recently occurred non-null error in errors, or null if all errors are null',
  'hasMoreItems is false when isReady is false (cannot know if there are more before first fetch)',
  'isPending on any item is false after a successful server confirmation',
  'all async action functions return OrchestratorResult — never throw (errors are always returned, not thrown)',
  'reset() called during an in-flight operation does not cause a state update after reset completes',
] as const;
