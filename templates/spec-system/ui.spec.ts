/**
 * UI Contract Spec: <feature-name>
 *
 * SPEC PACKAGE FILE: templates/spec-system/ui.spec.ts
 * Part of the spec-system package. See templates/spec-system/ for all required files.
 *
 * Spec ID:      SPEC-<NNN>
 * Feature:      FEAT-<NNN>-<short-feature-name>
 * Version:      <semver>
 * Content Hash: <sha256 — recompute on every edit>
 * Last Edited:  <ISO-8601 UTC>
 *
 * PURPOSE: This file defines the UI contract for all components in this feature
 * as TypeScript types. It is the authoritative source of truth for:
 *   - Component props interfaces (inputs from parent to component)
 *   - Event/callback interfaces (outputs from component to parent)
 *   - Display conditions (when a component renders vs is hidden/disabled)
 *   - Accessibility requirements (ARIA roles, labels, keyboard navigation)
 *   - Component composition rules (which components may be nested in which)
 *
 * This file does NOT define:
 *   - Visual design (colors, spacing, typography) — that belongs in a design spec
 *   - Animation details — document in behavior.spec.md if they affect behavior
 *   - Internal component state — that is an implementation detail
 *
 * This file is consumed by:
 *   - The TDD Agent (to write component contract tests and a11y tests)
 *   - The Programmer Agent (to implement the components)
 *   - The Code Review Agent (to verify implementation matches contract)
 */

// ---------------------------------------------------------------------------
// Component Registry
// ---------------------------------------------------------------------------

/**
 * All UI components defined by this feature.
 * Add one entry per public component. Internal components used only within
 * the feature are not listed here — they are implementation details.
 *
 * Each entry maps a component name to its props interface.
 */
export type FeatureComponentRegistry = {
  /** Top-level container component. Owns orchestrator and passes data down. */
  FeatureContainer: FeatureContainerProps;

  /** Displays the list of items. Pure — receives data and fires events only. */
  ItemList: ItemListProps;

  /** Displays a single item row/card within the list. */
  ItemCard: ItemCardProps;

  /** Form for creating a new item. */
  CreateItemForm: CreateItemFormProps;

  /** Confirmation dialog for destructive actions (delete, archive). */
  ConfirmActionDialog: ConfirmActionDialogProps;

  /** Empty state shown when items list is empty and isReady is true. */
  EmptyState: EmptyStateProps;

  /** Error banner shown when the most recent operation failed. */
  ErrorBanner: ErrorBannerProps;
};

// ---------------------------------------------------------------------------
// FeatureContainer Props
// ---------------------------------------------------------------------------

/**
 * Props for the top-level FeatureContainer component.
 * This component is responsible for wiring the orchestrator to child components.
 * Consumers render <FeatureContainer> — they do not interact with child components directly.
 */
export interface FeatureContainerProps {
  // --- Required ---

  /**
   * The ID of the parent resource this container operates within.
   * Passed through to the orchestrator's InputProps.parentId.
   */
  parentId: string;

  // --- Optional ---

  /**
   * Callback invoked after a successful item creation.
   * Receives the newly created item.
   */
  onItemCreated?: (item: ItemSummary) => void;

  /**
   * Callback invoked after a successful item deletion.
   * Receives the ID of the deleted item.
   */
  onItemDeleted?: (itemId: string) => void;

  /**
   * Optional CSS class name applied to the root element.
   * Use only for layout-level overrides (margin, position).
   * Do not use to override internal styles.
   */
  className?: string;

  /**
   * If provided, overrides the default page size for item loading.
   * Passed through to orchestrator.
   * Default: 20.
   */
  pageSize?: number;
}

// ---------------------------------------------------------------------------
// ItemList Props
// ---------------------------------------------------------------------------

/**
 * Props for the ItemList component.
 * Pure presentational: receives items and fires selection/action events.
 */
export interface ItemListProps {
  // --- Required ---

  /**
   * The items to display.
   * An empty array renders the EmptyState component.
   */
  items: ItemSummary[];

  /**
   * True while items are being fetched. Renders a loading skeleton.
   */
  isLoading: boolean;

  /**
   * True if more items can be loaded (pagination).
   * Renders a "Load more" control when true.
   */
  hasMoreItems: boolean;

  /**
   * Fired when the user activates a single item (click or Enter key).
   * Payload: the ID of the activated item.
   */
  onItemSelect: (itemId: string) => void;

  /**
   * Fired when the user requests to delete an item.
   * Payload: the ID of the item to delete.
   * The ItemList does not perform deletion — it fires the event.
   */
  onItemDeleteRequest: (itemId: string) => void;

  /**
   * Fired when the user activates the "Load more" control.
   * Only rendered when hasMoreItems is true and isLoading is false.
   */
  onLoadMore: () => void;

  // --- Optional ---

  /**
   * The ID of the currently selected item, or null.
   * The matching ItemCard renders in a "selected" visual state.
   */
  selectedItemId?: string | null;

  /**
   * True while the "Load more" operation is in-flight.
   * The "Load more" control renders a spinner when true.
   */
  isLoadingMore?: boolean;
}

// ---------------------------------------------------------------------------
// ItemCard Props
// ---------------------------------------------------------------------------

/**
 * Props for a single item card within the list.
 * Pure presentational.
 */
export interface ItemCardProps {
  // --- Required ---

  /** The item data to display. */
  item: ItemSummary;

  /** Fired when the user activates this card (click or Enter key). */
  onSelect: (itemId: string) => void;

  /** Fired when the user activates the delete action for this card. */
  onDeleteRequest: (itemId: string) => void;

  // --- Optional ---

  /** True if this card is currently selected. Applies selected visual state. */
  isSelected?: boolean;

  /**
   * True if this card represents an optimistically-created item not yet confirmed
   * by the server. Renders a pending indicator (e.g., spinner or muted opacity).
   */
  isPending?: boolean;
}

// ---------------------------------------------------------------------------
// CreateItemForm Props
// ---------------------------------------------------------------------------

/**
 * Props for the item creation form.
 */
export interface CreateItemFormProps {
  // --- Required ---

  /**
   * Fired when the user submits the form with valid input.
   * Payload: the validated form values.
   * The form does not perform the creation — it fires the event with the values.
   */
  onSubmit: (values: CreateItemFormValues) => void;

  // --- Optional ---

  /**
   * True while item creation is in-flight.
   * Disables the submit button and shows a loading indicator in it.
   */
  isSubmitting?: boolean;

  /**
   * If provided, the form renders this error inline below the submit button.
   * Null or undefined = no error displayed.
   */
  submitError?: FormFieldError | null;

  /**
   * Fired when the user explicitly cancels the form (e.g., presses Cancel button
   * or Escape key). If not provided, no cancel affordance is rendered.
   */
  onCancel?: () => void;

  /**
   * Initial values to pre-populate the form fields.
   * Use for "edit" mode (if this form is reused for editing).
   */
  initialValues?: Partial<CreateItemFormValues>;
}

/**
 * The values the CreateItemForm fires on submit.
 * These are validated, trimmed values — not raw form field strings.
 */
export interface CreateItemFormValues {
  /**
   * The item name. Trimmed. 1–255 characters.
   * The form validates this before firing onSubmit — onSubmit is never called
   * with a blank or overlong name.
   */
  name: string;

  /**
   * Whether to notify subscribers on completion.
   * Reflects the state of the corresponding checkbox.
   */
  notifyOnComplete: boolean;
}

// ---------------------------------------------------------------------------
// ConfirmActionDialog Props
// ---------------------------------------------------------------------------

/**
 * Props for the generic confirmation dialog.
 * Used for destructive actions that require explicit user confirmation.
 */
export interface ConfirmActionDialogProps {
  // --- Required ---

  /** True to show the dialog, false to hide it. Controlled externally. */
  isOpen: boolean;

  /**
   * The title displayed in the dialog header.
   * Example: "Delete item?"
   */
  title: string;

  /**
   * The body message displayed in the dialog.
   * Example: "This action cannot be undone. The item 'My Item' will be permanently deleted."
   */
  message: string;

  /**
   * Label for the confirm/destructive action button.
   * Example: "Delete", "Archive".
   */
  confirmLabel: string;

  /**
   * Fired when the user clicks the confirm button.
   * The dialog does not perform the action — it fires this event.
   */
  onConfirm: () => void;

  /**
   * Fired when the user dismisses the dialog (cancel button, Escape key, or
   * backdrop click).
   */
  onCancel: () => void;

  // --- Optional ---

  /**
   * True while the action triggered by onConfirm is in-flight.
   * Disables both buttons and shows a loading indicator on the confirm button.
   */
  isProcessing?: boolean;

  /**
   * Label for the cancel button.
   * Default: "Cancel".
   */
  cancelLabel?: string;
}

// ---------------------------------------------------------------------------
// EmptyState Props
// ---------------------------------------------------------------------------

/**
 * Props for the empty state component.
 * Rendered when the items list is empty and the list has been fetched (isReady = true).
 */
export interface EmptyStateProps {
  // --- Optional (all have defaults) ---

  /**
   * Heading text.
   * Default: "No items yet".
   */
  heading?: string;

  /**
   * Supporting description text.
   * Default: "Create your first item to get started."
   */
  description?: string;

  /**
   * If provided, renders a primary call-to-action button.
   * Fired when the user clicks the button.
   */
  onPrimaryAction?: () => void;

  /**
   * Label for the primary action button.
   * Required if onPrimaryAction is provided. Ignored otherwise.
   */
  primaryActionLabel?: string;
}

// ---------------------------------------------------------------------------
// ErrorBanner Props
// ---------------------------------------------------------------------------

/**
 * Props for the error banner component.
 * Rendered when the most recent operation has failed.
 */
export interface ErrorBannerProps {
  // --- Required ---

  /**
   * The error to display. If null, the banner is not rendered.
   * (Callers may choose to conditionally render the component or pass null.)
   */
  error: BannerError | null;

  // --- Optional ---

  /**
   * Fired when the user clicks the dismiss/close button.
   * If not provided, no dismiss affordance is rendered.
   */
  onDismiss?: () => void;

  /**
   * Fired when the user clicks the "Retry" button.
   * If not provided, no retry affordance is rendered.
   * Only show a retry button when the error's isRetryable flag is true.
   */
  onRetry?: () => void;
}

// ---------------------------------------------------------------------------
// Shared Sub-Types
// ---------------------------------------------------------------------------

/**
 * The item shape consumed by presentational components.
 * This is a view-level projection — may differ from API or state shapes.
 */
export interface ItemSummary {
  id: string;
  name: string;
  status: ItemDisplayStatus;
  createdAt: string;
  isPending: boolean;
}

export type ItemDisplayStatus =
  | 'pending'
  | 'active'
  | 'completed'
  | 'failed'
  | 'archived';

/**
 * A field-level form validation error.
 */
export interface FormFieldError {
  /** The form field that has the error. Must match the field name in the form. */
  field: keyof CreateItemFormValues;
  /** Human-readable error message. Displayed below the field. */
  message: string;
}

/**
 * The error shape consumed by the ErrorBanner component.
 */
export interface BannerError {
  /** Machine-readable code. Used to select the display message. */
  code: string;
  /** Human-readable message. */
  message: string;
  /** True if the operation is safe to retry. Controls whether "Retry" is shown. */
  isRetryable: boolean;
}

// ---------------------------------------------------------------------------
// Display Conditions
// ---------------------------------------------------------------------------

/**
 * When each component shows, hides, or changes visual state.
 * The TDD Agent must write tests asserting these conditions.
 * The Programmer Agent must implement these exactly as specified.
 *
 * Format: [ComponentName] <condition> => <result>
 */
export const DISPLAY_CONDITIONS = {
  FeatureContainer: {
    rendersItemList: 'always — even when items is empty or isLoading is true',
    rendersCreateItemForm: 'always — form is always present (not in a modal unless design specifies)',
    rendersErrorBanner: 'when orchestrator.error is non-null',
    rendersConfirmActionDialog: 'when user has activated a delete request (itemId is set in local dialog state)',
  },

  ItemList: {
    rendersLoadingSkeleton: 'when isLoading is true AND items.length === 0',
    rendersItems: 'when items.length > 0 (even while isLoading is true — shows stale items with overlay)',
    rendersEmptyState: 'when items.length === 0 AND isLoading is false',
    rendersLoadMore: 'when hasMoreItems is true AND isLoading is false',
    rendersLoadMoreSpinner: 'when isLoadingMore is true',
    loadMoreIsDisabled: 'when isLoadingMore is true',
  },

  ItemCard: {
    rendersSelectedState: 'when isSelected is true',
    rendersPendingIndicator: 'when isPending is true',
    deleteButtonIsDisabled: 'when isPending is true (cannot delete an unconfirmed item)',
    statusBadgeColor: 'maps status to color per design spec — not defined here',
  },

  CreateItemForm: {
    submitButtonIsDisabled: 'when isSubmitting is true OR name field is blank',
    rendersSubmitSpinner: 'when isSubmitting is true',
    rendersSubmitError: 'when submitError is non-null',
    rendersCancelButton: 'when onCancel prop is provided',
    cancelButtonIsDisabled: 'when isSubmitting is true',
  },

  ConfirmActionDialog: {
    rendersDialog: 'when isOpen is true',
    confirmButtonIsDisabled: 'when isProcessing is true',
    cancelButtonIsDisabled: 'when isProcessing is true',
    backdropDismiss: 'fires onCancel — same as cancel button',
    escapeDismiss: 'fires onCancel — same as cancel button',
  },

  ErrorBanner: {
    renders: 'when error prop is non-null',
    rendersRetryButton: 'when onRetry is provided AND error.isRetryable is true',
    rendersDismissButton: 'when onDismiss is provided',
  },
} as const;

// ---------------------------------------------------------------------------
// Accessibility Requirements
// ---------------------------------------------------------------------------

/**
 * Mandatory accessibility requirements for each component.
 * All requirements must be verified by the TDD Agent using accessibility testing tools.
 * Any deviation requires human sign-off and a note in checklists/spec-dod.md.
 */
export const ACCESSIBILITY_REQUIREMENTS = {
  FeatureContainer: {
    landmark: 'root element is <main> or wrapped in a <section> with aria-label describing the feature',
  },

  ItemList: {
    role: 'ul (unordered list) or role="list" if using non-semantic element',
    loadingAnnouncement: 'when loading starts, announce to screen readers via aria-live="polite" region: "Loading items..."',
    emptyAnnouncement: 'when empty state renders, aria-live region announces: "No items found."',
  },

  ItemCard: {
    role: 'li (list item)',
    interactiveElement: 'the card activate action is on a <button> — not a div with onClick',
    deleteButton: {
      label: 'aria-label="Delete [item name]" — not just "Delete" (must include item name for context)',
      confirmation: 'delete does not execute immediately — confirmation dialog is required (see ConfirmActionDialog)',
    },
    pendingState: 'aria-busy="true" on the card while isPending is true',
    selectedState: 'aria-selected="true" on the card when isSelected is true',
  },

  CreateItemForm: {
    role: 'form with aria-label="Create new item" (or equivalent)',
    nameField: {
      label: '<label> element associated via htmlFor/id — not placeholder-only',
      errorAssociation: 'error message element has id referenced in aria-describedby on the input',
      requiredMark: 'aria-required="true" on the name input',
    },
    submitButton: 'type="submit" — not type="button" with onClick',
    loadingAnnouncement: 'on submit, announce "Saving..." via aria-live region',
    successAnnouncement: 'on success, announce "Item created." via aria-live region',
    errorAnnouncement: 'on failure, focus is moved to the error message element',
  },

  ConfirmActionDialog: {
    role: 'role="dialog" with aria-modal="true"',
    titleAssociation: 'aria-labelledby pointing to the dialog title element',
    descriptionAssociation: 'aria-describedby pointing to the dialog message element',
    focusManagement: 'focus is moved to the dialog when it opens; returns to the trigger element when it closes',
    keyboardDismiss: 'Escape key fires onCancel',
    focusTrap: 'Tab key cycles only within the dialog while it is open',
  },

  ErrorBanner: {
    role: 'role="alert" with aria-live="assertive" for immediate announcement',
    dismissButton: 'aria-label="Dismiss error" — not just "X"',
    retryButton: 'aria-label="Retry" with optional description of what is being retried',
  },
} as const;

// ---------------------------------------------------------------------------
// Keyboard Navigation Contract
// ---------------------------------------------------------------------------

/**
 * Keyboard interaction requirements.
 * These supplement the accessibility requirements above.
 */
export const KEYBOARD_NAVIGATION = {
  ItemList: {
    'Tab': 'moves focus between ItemCard interactive elements',
    'Enter / Space on focused card': 'fires onItemSelect',
  },
  ItemCard: {
    'Enter / Space': 'fires onSelect',
    'Delete key': 'fires onDeleteRequest (same as clicking the delete button)',
  },
  CreateItemForm: {
    'Enter in name field': 'submits the form (if valid)',
    'Escape': 'fires onCancel (if provided)',
    'Tab': 'moves focus between form fields in document order',
  },
  ConfirmActionDialog: {
    'Escape': 'fires onCancel',
    'Enter on confirm button': 'fires onConfirm',
    'Tab / Shift+Tab': 'cycles focus within dialog only (focus trap active)',
  },
} as const;
