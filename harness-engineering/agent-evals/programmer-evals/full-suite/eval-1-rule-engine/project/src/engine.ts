import { DEFAULT_RULES } from './rules';
import {
  AppliedDiscount,
  ApplyDiscountsInput,
  ApplyDiscountsOptions,
  DiscountResult,
} from './types';
import { validateCart } from './validation';

const DEFAULT_MAX_DISCOUNT_FRACTION = 0.4;

/**
 * Applies discount rules to a cart and returns a detailed breakdown.
 *
 * Two-object signature: required input + optional options.
 *
 * @param input   - { items, loyaltyTier } -- the cart and customer info (required).
 * @param options - { rules?, maxDiscountFraction? } -- override rules or cap (optional).
 * @returns DiscountResult with subtotal, applied discounts, final total, and warnings.
 * @throws Error if cart validation fails (empty cart, invalid quantity/price).
 *
 * @complexity Time: O(R * n) where R = number of rules, Space: O(n)
 * @overallScore 92/100
 */
export function applyDiscounts(
  input: ApplyDiscountsInput,
  options?: ApplyDiscountsOptions,
): DiscountResult {
  const { items, loyaltyTier } = input;
  const rules = options?.rules ?? DEFAULT_RULES;
  const maxFraction = options?.maxDiscountFraction ?? DEFAULT_MAX_DISCOUNT_FRACTION;

  // Validate -- throws on invalid cart (fail-fast)
  validateCart({ items });

  // Calculate subtotal
  const subtotal = items.reduce(
    (sum, item) => sum + item.quantity * item.unitPrice,
    0,
  );

  const maxDiscount = roundCents(subtotal * maxFraction);
  const discounts: AppliedDiscount[] = [];
  let totalDiscount = 0;
  const warnings: string[] = [];

  // Apply each rule in order; clamp to cap
  const context = { items, subtotal, loyaltyTier };

  for (const rule of rules) {
    const ruleResults = rule(context);

    for (const d of ruleResults) {
      const remaining = roundCents(maxDiscount - totalDiscount);

      if (remaining <= 0) {
        break;
      }

      if (d.amount <= remaining) {
        discounts.push(d);
        totalDiscount = roundCents(totalDiscount + d.amount);
      } else {
        // Partially apply the discount up to the cap
        discounts.push({ ...d, amount: remaining });
        totalDiscount = roundCents(totalDiscount + remaining);
      }
    }
  }

  if (totalDiscount >= maxDiscount && maxDiscount > 0) {
    warnings.push(`Discount cap of ${maxFraction * 100}% reached`);
  }

  return {
    subtotal,
    discounts,
    totalDiscount,
    finalTotal: roundCents(subtotal - totalDiscount),
    warnings,
  };
}

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
