/**
 * State Contract Spec: <feature-name>
 *
 * SPEC PACKAGE FILE: templates/spec-system/state.spec.ts
 * Part of the spec-system package. See templates/spec-system/ for all required files.
 *
 * Spec ID:      SPEC-<NNN>
 * Feature:      FEAT-<NNN>-<short-feature-name>
 * Version:      <semver>
 * Content Hash: <sha256 — recompute on every edit>
 * Last Edited:  <ISO-8601 UTC>
 *
 * PURPOSE: This file defines the state shape and all valid state transitions for
 * this feature as TypeScript types. It is the authoritative source of truth for:
 *   - The shape of state at rest (initial and derived)
 *   - Every action that can mutate state (discriminated union)
 *   - The before/after state shape for each action
 *   - Derived state selectors and their return types
 *   - State invariants (conditions that must always hold)
 *
 * This file is consumed by:
 *   - The TDD Agent (to write state transition tests)
 *   - The Programmer Agent (to implement the state manager/store)
 *   - The Architect Agent (to validate state boundaries)
 *   - The Code Review Agent (to verify implementation matches contract)
 *
 * NOTE: This file does not dictate the state management library (Redux, Zustand,
 * MobX, plain objects, etc.). It defines the shape — not the mechanism.
 */

// ---------------------------------------------------------------------------
// State Shape
// ---------------------------------------------------------------------------

/**
 * The complete state shape managed by this feature.
 * This is the shape at rest — what a snapshot of state looks like at any point in time.
 *
 * Rules:
 *   - All fields that can be absent are typed as `T | null`, never `T | undefined`,
 *     to make nullability explicit and searchable.
 *   - Loading and error states are explicit fields, not derived from data being null.
 *   - Timestamps are ISO-8601 strings, not Date objects.
 */
export interface FeatureState {
  // --- Core data ---

  /**
   * The list of resources managed by this feature.
   * Empty array if none have been loaded. Never null.
   */
  items: FeatureItem[];

  /**
   * The currently selected item's ID, or null if no item is selected.
   */
  selectedItemId: string | null;

  // --- Async operation state ---

  /**
   * Loading state per async operation.
   * Each field is true while the corresponding operation is in-flight.
   */
  loading: FeatureLoadingState;

  /**
   * Error state per async operation.
   * Each field holds the last error for that operation, or null if the last
   * attempt succeeded (or the operation has never been attempted).
   */
  errors: FeatureErrorState;

  // --- Pagination ---

  /**
   * Pagination cursor for the items list.
   * null means either the list has not been fetched, or there are no more pages.
   */
  nextPageCursor: string | null;

  /**
   * Whether all pages have been loaded.
   * true only when the API has confirmed there is no next page.
   */
  allItemsLoaded: boolean;

  // --- Timestamps ---

  /**
   * ISO-8601 UTC timestamp of the last successful fetch, or null if never fetched.
   */
  lastFetchedAt: string | null;
}

/**
 * Loading flags for async operations.
 * Each field corresponds to one async action type.
 * true = operation is in-flight; false = idle.
 */
export interface FeatureLoadingState {
  /** True while the item list is being fetched. */
  fetchingItems: boolean;

  /** True while a single item is being fetched. */
  fetchingItem: boolean;

  /** True while a new item is being created. */
  creatingItem: boolean;

  /** True while an item is being updated. */
  updatingItem: boolean;

  /** True while an item is being deleted. */
  deletingItem: boolean;
}

/**
 * Error slots for async operations.
 * null = no error (last attempt succeeded, or operation never attempted).
 * Non-null = the error from the most recent failed attempt.
 */
export interface FeatureErrorState {
  /** Error from the last fetchItems attempt, or null. */
  fetchItems: FeatureStateError | null;

  /** Error from the last fetchItem attempt, or null. */
  fetchItem: FeatureStateError | null;

  /** Error from the last createItem attempt, or null. */
  createItem: FeatureStateError | null;

  /** Error from the last updateItem attempt, or null. */
  updateItem: FeatureStateError | null;

  /** Error from the last deleteItem attempt, or null. */
  deleteItem: FeatureStateError | null;
}

/**
 * The shape of an error stored in state.
 * Mirrors the API error contract but is decoupled from HTTP transport concerns.
 */
export interface FeatureStateError {
  /** Machine-readable error code. Consumers switch on this field. */
  code: string;

  /** Human-readable message. For display only — do not parse. */
  message: string;

  /** ISO-8601 UTC timestamp of when the error occurred. */
  occurredAt: string;

  /** Correlation ID from the API response, if available. */
  correlationId: string | null;
}

/**
 * A single item in the feature's items list.
 * This is the in-memory representation — it may differ from the API response shape.
 */
export interface FeatureItem {
  /** UUID v4. Immutable after creation. */
  id: string;

  /** Human-readable name. */
  name: string;

  /** Current lifecycle status. */
  status: FeatureItemStatus;

  /** ISO-8601 UTC creation timestamp. */
  createdAt: string;

  /** ISO-8601 UTC last-modified timestamp. */
  updatedAt: string;

  /**
   * Optimistic update version counter.
   * Incremented locally on every optimistic write, reconciled with server on success.
   * Used to detect and resolve conflicts on re-fetch.
   */
  localVersion: number;
}

/** Lifecycle status values for FeatureItem. Mirrors ExampleResourceStatus in api.spec.ts. */
export type FeatureItemStatus =
  | 'pending'
  | 'active'
  | 'completed'
  | 'failed'
  | 'archived';

// ---------------------------------------------------------------------------
// Initial State
// ---------------------------------------------------------------------------

/**
 * The initial state of the feature before any actions are dispatched.
 * Use this as the reset target and as the starting state in tests.
 *
 * IMPORTANT: This object is frozen — do not mutate it. Clone it for tests.
 */
export const INITIAL_FEATURE_STATE: FeatureState = {
  items: [],
  selectedItemId: null,
  loading: {
    fetchingItems: false,
    fetchingItem: false,
    creatingItem: false,
    updatingItem: false,
    deletingItem: false,
  },
  errors: {
    fetchItems: null,
    fetchItem: null,
    createItem: null,
    updateItem: null,
    deleteItem: null,
  },
  nextPageCursor: null,
  allItemsLoaded: false,
  lastFetchedAt: null,
};

// ---------------------------------------------------------------------------
// Action Types (Discriminated Union)
// ---------------------------------------------------------------------------

/**
 * Every action that can mutate FeatureState.
 * All actions are discriminated by their `type` field.
 *
 * Naming convention: "<DOMAIN>/<VERB>_<OBJECT>[_<QUALIFIER>]"
 * Past tense = something that happened (event-sourced style).
 * Imperative = command (command-sourced style). Choose one and be consistent.
 *
 * This spec uses past-tense event naming.
 */

// --- Fetch items ---

/** Dispatched when a fetch of the full items list is initiated. */
export interface FetchItemsStartedAction {
  type: 'FEATURE/FETCH_ITEMS_STARTED';
}

/** Dispatched when a fetch of the items list succeeds. */
export interface FetchItemsSucceededAction {
  type: 'FEATURE/FETCH_ITEMS_SUCCEEDED';
  payload: {
    /** The fetched items. Replaces the current items list. */
    items: FeatureItem[];
    /** Pagination cursor for the next page, or null if no more pages. */
    nextPageCursor: string | null;
    /** ISO-8601 UTC timestamp of when the fetch completed. */
    fetchedAt: string;
  };
}

/** Dispatched when a fetch of the items list fails. */
export interface FetchItemsFailedAction {
  type: 'FEATURE/FETCH_ITEMS_FAILED';
  payload: {
    error: FeatureStateError;
  };
}

// --- Create item ---

/** Dispatched when item creation is initiated (before server response). */
export interface CreateItemStartedAction {
  type: 'FEATURE/CREATE_ITEM_STARTED';
  payload: {
    /**
     * Optimistic temporary ID for the item. Replaced by the server-assigned ID
     * on success. Used to identify the optimistic item for removal on failure.
     */
    optimisticId: string;
    name: string;
  };
}

/** Dispatched when item creation succeeds. */
export interface CreateItemSucceededAction {
  type: 'FEATURE/CREATE_ITEM_SUCCEEDED';
  payload: {
    /** The temporary optimistic ID that was used during the in-flight period. */
    optimisticId: string;
    /** The server-confirmed item, including the real server-assigned ID. */
    item: FeatureItem;
  };
}

/** Dispatched when item creation fails. */
export interface CreateItemFailedAction {
  type: 'FEATURE/CREATE_ITEM_FAILED';
  payload: {
    /** The optimistic ID used during the in-flight period — must be removed from state. */
    optimisticId: string;
    error: FeatureStateError;
  };
}

// --- Update item ---

/** Dispatched when an item update is initiated. */
export interface UpdateItemStartedAction {
  type: 'FEATURE/UPDATE_ITEM_STARTED';
  payload: {
    /** ID of the item being updated. */
    itemId: string;
    /** The fields being changed (partial). Applied optimistically to state. */
    changes: Partial<Pick<FeatureItem, 'name' | 'status'>>;
  };
}

/** Dispatched when an item update succeeds. */
export interface UpdateItemSucceededAction {
  type: 'FEATURE/UPDATE_ITEM_SUCCEEDED';
  payload: {
    /** The server-confirmed item after the update. */
    item: FeatureItem;
  };
}

/** Dispatched when an item update fails. */
export interface UpdateItemFailedAction {
  type: 'FEATURE/UPDATE_ITEM_FAILED';
  payload: {
    /** ID of the item that failed to update — optimistic change must be rolled back. */
    itemId: string;
    /** The pre-update item state, for rollback. */
    previousItem: FeatureItem;
    error: FeatureStateError;
  };
}

// --- Delete item ---

/** Dispatched when an item deletion is initiated. */
export interface DeleteItemStartedAction {
  type: 'FEATURE/DELETE_ITEM_STARTED';
  payload: {
    /** ID of the item being deleted. Removed optimistically from state. */
    itemId: string;
  };
}

/** Dispatched when an item deletion succeeds. */
export interface DeleteItemSucceededAction {
  type: 'FEATURE/DELETE_ITEM_SUCCEEDED';
  payload: {
    /** ID of the deleted item. Must be confirmed removed from state. */
    itemId: string;
  };
}

/** Dispatched when an item deletion fails. */
export interface DeleteItemFailedAction {
  type: 'FEATURE/DELETE_ITEM_FAILED';
  payload: {
    /** ID of the item that failed to delete — must be restored to state. */
    itemId: string;
    /** The pre-delete item state, for rollback. */
    previousItem: FeatureItem;
    error: FeatureStateError;
  };
}

// --- Selection ---

/** Dispatched when the user selects an item. */
export interface ItemSelectedAction {
  type: 'FEATURE/ITEM_SELECTED';
  payload: {
    /** ID of the selected item. Must exist in state.items. */
    itemId: string;
  };
}

/** Dispatched when the user clears the selection. */
export interface ItemDeselectedAction {
  type: 'FEATURE/ITEM_DESELECTED';
}

// --- Reset ---

/** Dispatched to reset the feature state to INITIAL_FEATURE_STATE. */
export interface FeatureResetAction {
  type: 'FEATURE/RESET';
}

/** Union of all valid actions for this feature. */
export type FeatureAction =
  | FetchItemsStartedAction
  | FetchItemsSucceededAction
  | FetchItemsFailedAction
  | CreateItemStartedAction
  | CreateItemSucceededAction
  | CreateItemFailedAction
  | UpdateItemStartedAction
  | UpdateItemSucceededAction
  | UpdateItemFailedAction
  | DeleteItemStartedAction
  | DeleteItemSucceededAction
  | DeleteItemFailedAction
  | ItemSelectedAction
  | ItemDeselectedAction
  | FeatureResetAction;

// ---------------------------------------------------------------------------
// State Transitions (Before/After per Action)
// ---------------------------------------------------------------------------

/**
 * Documents the expected state change for each action.
 * The Programmer Agent must implement a reducer that satisfies every transition below.
 * The TDD Agent must write a test for each transition.
 *
 * Format: each entry describes:
 *   - The action type
 *   - Which fields change and how
 *   - Which fields must NOT change
 *   - Any invariants that must hold after the transition
 */
export const STATE_TRANSITIONS = {
  'FEATURE/FETCH_ITEMS_STARTED': {
    changes: {
      'loading.fetchingItems': 'false → true',
      'errors.fetchItems': 'any → null (clear error on retry)',
    },
    unchanged: ['items', 'selectedItemId', 'nextPageCursor', 'allItemsLoaded'],
    postConditionInvariants: [
      'loading.fetchingItems === true',
      'errors.fetchItems === null',
    ],
  },

  'FEATURE/FETCH_ITEMS_SUCCEEDED': {
    changes: {
      'loading.fetchingItems': 'true → false',
      items: '[] or existing → payload.items (full replacement)',
      'nextPageCursor': 'any → payload.nextPageCursor',
      'allItemsLoaded': 'any → (payload.nextPageCursor === null)',
      'lastFetchedAt': 'any → payload.fetchedAt',
    },
    unchanged: ['selectedItemId', 'errors'],
    postConditionInvariants: [
      'loading.fetchingItems === false',
      'allItemsLoaded === (nextPageCursor === null)',
      'lastFetchedAt === payload.fetchedAt',
    ],
  },

  'FEATURE/FETCH_ITEMS_FAILED': {
    changes: {
      'loading.fetchingItems': 'true → false',
      'errors.fetchItems': 'null → payload.error',
    },
    unchanged: ['items', 'selectedItemId', 'nextPageCursor', 'allItemsLoaded', 'lastFetchedAt'],
    postConditionInvariants: [
      'loading.fetchingItems === false',
      'errors.fetchItems !== null',
      'items list is unchanged from before the failed fetch',
    ],
  },

  'FEATURE/CREATE_ITEM_STARTED': {
    changes: {
      'loading.creatingItem': 'false → true',
      'errors.createItem': 'any → null',
      items: 'existing → existing + optimistic item with payload.optimisticId',
    },
    unchanged: ['selectedItemId', 'nextPageCursor', 'allItemsLoaded'],
    postConditionInvariants: [
      'loading.creatingItem === true',
      'items.find(i => i.id === payload.optimisticId) !== undefined',
      'optimistic item has status === "pending"',
    ],
  },

  'FEATURE/CREATE_ITEM_SUCCEEDED': {
    changes: {
      'loading.creatingItem': 'true → false',
      items: 'replace item with optimisticId → payload.item (server-confirmed)',
    },
    unchanged: ['selectedItemId', 'errors.createItem', 'nextPageCursor'],
    postConditionInvariants: [
      'loading.creatingItem === false',
      'items.find(i => i.id === payload.optimisticId) === undefined (optimistic removed)',
      'items.find(i => i.id === payload.item.id) !== undefined (server item present)',
    ],
  },

  'FEATURE/CREATE_ITEM_FAILED': {
    changes: {
      'loading.creatingItem': 'true → false',
      'errors.createItem': 'any → payload.error',
      items: 'remove item with payload.optimisticId',
    },
    unchanged: ['selectedItemId', 'nextPageCursor', 'allItemsLoaded'],
    postConditionInvariants: [
      'loading.creatingItem === false',
      'errors.createItem !== null',
      'items.find(i => i.id === payload.optimisticId) === undefined (optimistic rolled back)',
    ],
  },

  'FEATURE/UPDATE_ITEM_STARTED': {
    changes: {
      'loading.updatingItem': 'false → true',
      'errors.updateItem': 'any → null',
      items: 'apply payload.changes optimistically to item with payload.itemId',
    },
    unchanged: ['selectedItemId', 'nextPageCursor', 'allItemsLoaded'],
    postConditionInvariants: [
      'loading.updatingItem === true',
      'items.find(i => i.id === payload.itemId) has changes applied',
      'optimistically updated item has localVersion incremented by 1',
    ],
  },

  'FEATURE/UPDATE_ITEM_FAILED': {
    changes: {
      'loading.updatingItem': 'true → false',
      'errors.updateItem': 'any → payload.error',
      items: 'replace item with payload.itemId with payload.previousItem (rollback)',
    },
    unchanged: ['selectedItemId', 'nextPageCursor', 'allItemsLoaded'],
    postConditionInvariants: [
      'loading.updatingItem === false',
      'errors.updateItem !== null',
      'items.find(i => i.id === payload.itemId) === payload.previousItem (rolled back)',
    ],
  },

  'FEATURE/DELETE_ITEM_STARTED': {
    changes: {
      'loading.deletingItem': 'false → true',
      'errors.deleteItem': 'any → null',
      items: 'remove item with payload.itemId optimistically',
      selectedItemId: 'if === payload.itemId → null',
    },
    unchanged: ['nextPageCursor', 'allItemsLoaded'],
    postConditionInvariants: [
      'loading.deletingItem === true',
      'items.find(i => i.id === payload.itemId) === undefined (optimistic remove)',
      'if selectedItemId was the deleted id, selectedItemId === null',
    ],
  },

  'FEATURE/DELETE_ITEM_FAILED': {
    changes: {
      'loading.deletingItem': 'true → false',
      'errors.deleteItem': 'any → payload.error',
      items: 'restore payload.previousItem',
    },
    unchanged: ['nextPageCursor', 'allItemsLoaded'],
    postConditionInvariants: [
      'loading.deletingItem === false',
      'errors.deleteItem !== null',
      'items.find(i => i.id === payload.itemId) !== undefined (restored)',
    ],
  },

  'FEATURE/RESET': {
    changes: {
      ALL: 'any → INITIAL_FEATURE_STATE',
    },
    unchanged: [],
    postConditionInvariants: [
      'state deep-equals INITIAL_FEATURE_STATE',
    ],
  },
} as const;

// ---------------------------------------------------------------------------
// Derived State Selectors
// ---------------------------------------------------------------------------

/**
 * Selector return-type contracts.
 * The Programmer Agent must implement functions that return exactly these types.
 * The TDD Agent must write tests that assert on these return values.
 */

/**
 * Returns the currently selected item, or null if none is selected
 * or the selectedItemId does not match any item in state.items.
 */
export type SelectSelectedItem = (state: FeatureState) => FeatureItem | null;

/**
 * Returns items filtered by status.
 * Returns an empty array if no items match.
 * Never returns null.
 */
export type SelectItemsByStatus = (
  state: FeatureState,
  status: FeatureItemStatus
) => FeatureItem[];

/**
 * Returns true if any async operation is currently in-flight.
 * Used to disable UI controls globally while a mutation is pending.
 */
export type SelectIsAnyOperationLoading = (state: FeatureState) => boolean;

/**
 * Returns the most recently occurred error across all error slots,
 * or null if no errors are present.
 * "Most recent" is determined by the error's `occurredAt` timestamp.
 */
export type SelectLatestError = (state: FeatureState) => FeatureStateError | null;

/**
 * Returns true if the item list has been successfully fetched at least once
 * (i.e., lastFetchedAt is non-null) and is not currently loading.
 */
export type SelectIsItemListReady = (state: FeatureState) => boolean;

// ---------------------------------------------------------------------------
// State Invariants
// ---------------------------------------------------------------------------

/**
 * Conditions that must hold for any valid FeatureState.
 * The TDD Agent must write invariant tests that assert these hold after every action.
 *
 * These mirror the invariants in feature.spec.md but expressed as type-level constraints.
 */
export const STATE_INVARIANTS = [
  'items is always an array — never null or undefined',
  'selectedItemId, if non-null, must always refer to an id that exists in items',
  'allItemsLoaded is true only when nextPageCursor is null',
  'no two items in the items array have the same id',
  'loading flags are boolean — never null or undefined',
  'error slots are FeatureStateError | null — never undefined',
  'localVersion on any item is always a non-negative integer',
  'all timestamp fields (createdAt, updatedAt, lastFetchedAt, occurredAt) are ISO-8601 strings when non-null',
] as const;
