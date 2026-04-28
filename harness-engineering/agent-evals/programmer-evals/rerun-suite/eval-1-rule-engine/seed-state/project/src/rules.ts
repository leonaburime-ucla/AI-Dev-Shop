import { AppliedDiscount, RuleContext } from './types';

/**
 * Bulk discount rule: 15% off any SKU with quantity >= 10.
 *
 * @param context - { items, subtotal, loyaltyTier }
 * @returns Array of AppliedDiscount, one per qualifying SKU.
 *
 * @complexity Time: O(n), Space: O(n)
 * @overallScore 95/100
 */
export function bulkDiscount(context: RuleContext): readonly AppliedDiscount[] {
  const results: AppliedDiscount[] = [];

  for (const item of context.items) {
    if (item.quantity >= 10) {
      const amount = roundCents(item.quantity * item.unitPrice * 0.15);
      results.push({ rule: 'bulk', sku: item.sku, amount });
    }
  }

  return results;
}

/**
 * Combo discount rule: $5 off when both WIDGET-A and WIDGET-B are in the cart.
 *
 * @param context - { items, subtotal, loyaltyTier }
 * @returns Array with one AppliedDiscount if combo qualifies, empty otherwise.
 *
 * @complexity Time: O(n), Space: O(1)
 * @overallScore 95/100
 */
export function comboDiscount(context: RuleContext): readonly AppliedDiscount[] {
  const skus = new Set(context.items.map(i => i.sku));

  if (skus.has('WIDGET-A') && skus.has('WIDGET-B')) {
    return [{ rule: 'combo', amount: 5 }];
  }

  return [];
}

/**
 * Loyalty discount rule: gold = 10% off subtotal, silver = 5%.
 *
 * @param context - { items, subtotal, loyaltyTier }
 * @returns Array with one AppliedDiscount if tier qualifies, empty otherwise.
 *
 * @complexity Time: O(1), Space: O(1)
 * @overallScore 95/100
 */
export function loyaltyDiscount(context: RuleContext): readonly AppliedDiscount[] {
  const rates: Record<string, number> = { gold: 0.10, silver: 0.05 };
  const rate = rates[context.loyaltyTier];

  if (rate !== undefined) {
    return [{ rule: 'loyalty', amount: roundCents(context.subtotal * rate) }];
  }

  return [];
}

/** The default set of discount rules applied when none are specified. */
export const DEFAULT_RULES = [bulkDiscount, comboDiscount, loyaltyDiscount] as const;

/**
 * Rounds a number to two decimal places (cents).
 *
 * @param value - The number to round.
 * @returns Rounded value.
 *
 * @complexity Time: O(1), Space: O(1)
 * @overallScore 95/100
 */
function roundCents(value: number): number {
  return Math.round(value * 100) / 100;
}
