/**
 * Typed contracts for the discount rule engine.
 *
 * Single source of truth for all domain types.
 */

/** A single line item in a shopping cart. */
export interface LineItem {
  readonly sku: string;
  readonly name: string;
  readonly quantity: number;
  readonly unitPrice: number;
}

/** A discount applied by a rule. */
export interface AppliedDiscount {
  readonly rule: string;
  readonly amount: number;
  readonly sku?: string;
}

/** The result of applying discounts to a cart. */
export interface DiscountResult {
  readonly subtotal: number;
  readonly discounts: readonly AppliedDiscount[];
  readonly totalDiscount: number;
  readonly finalTotal: number;
  readonly warnings: readonly string[];
}

/** Supported loyalty tiers. */
export type LoyaltyTier = 'gold' | 'silver' | 'none';

/** A discount rule function that inspects the cart and returns discounts. */
export type DiscountRule = (context: RuleContext) => readonly AppliedDiscount[];

/** Context passed to each discount rule. */
export interface RuleContext {
  readonly items: readonly LineItem[];
  readonly subtotal: number;
  readonly loyaltyTier: LoyaltyTier;
}

/** Required input for applyDiscounts. */
export interface ApplyDiscountsInput {
  readonly items: readonly LineItem[];
  readonly loyaltyTier: LoyaltyTier;
}

/** Optional configuration for applyDiscounts. */
export interface ApplyDiscountsOptions {
  readonly rules?: readonly DiscountRule[];
  readonly maxDiscountFraction?: number;
}
