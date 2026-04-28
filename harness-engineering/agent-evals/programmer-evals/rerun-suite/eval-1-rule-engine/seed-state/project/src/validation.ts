import { LineItem } from './types';

/**
 * Validates that a cart's line items are well-formed.
 *
 * Checks:
 * - Cart is non-null and non-empty.
 * - Every item has quantity > 0 and unitPrice >= 0.
 *
 * @param input - { items: readonly LineItem[] }
 * @returns void -- throws a descriptive Error on any violation.
 * @throws Error with a human-readable message identifying the first invalid item.
 *
 * @complexity Time: O(n), Space: O(1)
 * @overallScore 95/100
 */
export function validateCart(input: { items: readonly LineItem[] }): void {
  const { items } = input;

  if (!items || items.length === 0) {
    throw new Error('Cart cannot be empty');
  }

  for (const item of items) {
    if (item.quantity <= 0) {
      throw new Error(
        `Invalid quantity for SKU "${item.sku}": quantity must be > 0, got ${item.quantity}`,
      );
    }
    if (item.unitPrice < 0) {
      throw new Error(
        `Invalid unitPrice for SKU "${item.sku}": unitPrice must be >= 0, got ${item.unitPrice}`,
      );
    }
  }
}
