import { applyDiscounts } from '../engine';
import { bulkDiscount, comboDiscount, loyaltyDiscount } from '../rules';
import { validateCart } from '../validation';
import { LineItem, LoyaltyTier, RuleContext, AppliedDiscount } from '../types';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeItem(overrides: Partial<LineItem> & { sku: string }): LineItem {
  return {
    name: overrides.sku,
    quantity: 1,
    unitPrice: 10,
    ...overrides,
  };
}

function makeContext(
  items: readonly LineItem[],
  loyaltyTier: LoyaltyTier = 'none',
): RuleContext {
  const subtotal = items.reduce((s, i) => s + i.quantity * i.unitPrice, 0);
  return { items, subtotal, loyaltyTier };
}

// ---------------------------------------------------------------------------
// validateCart
// ---------------------------------------------------------------------------

describe('validateCart', () => {
  it('throws on empty cart', () => {
    expect(() => validateCart({ items: [] })).toThrow('Cart cannot be empty');
  });

  it('throws on null/undefined items', () => {
    expect(() => validateCart({ items: null as any })).toThrow('Cart cannot be empty');
  });

  it('throws when quantity <= 0', () => {
    expect(() =>
      validateCart({ items: [makeItem({ sku: 'A', quantity: 0 })] }),
    ).toThrow(/Invalid quantity.*"A"/);
  });

  it('throws when quantity is negative', () => {
    expect(() =>
      validateCart({ items: [makeItem({ sku: 'B', quantity: -5 })] }),
    ).toThrow(/Invalid quantity.*"B"/);
  });

  it('throws when unitPrice is negative', () => {
    expect(() =>
      validateCart({ items: [makeItem({ sku: 'C', unitPrice: -1 })] }),
    ).toThrow(/Invalid unitPrice.*"C"/);
  });

  it('passes for valid items', () => {
    expect(() =>
      validateCart({ items: [makeItem({ sku: 'OK', quantity: 1, unitPrice: 0 })] }),
    ).not.toThrow();
  });

  it('allows unitPrice of 0 (free item)', () => {
    expect(() =>
      validateCart({ items: [makeItem({ sku: 'FREE', unitPrice: 0 })] }),
    ).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// Individual rules
// ---------------------------------------------------------------------------

describe('bulkDiscount', () => {
  it('returns empty for items below threshold', () => {
    const ctx = makeContext([makeItem({ sku: 'A', quantity: 9, unitPrice: 10 })]);
    expect(bulkDiscount(ctx)).toEqual([]);
  });

  it('returns 15% off for items at threshold (qty=10)', () => {
    const ctx = makeContext([makeItem({ sku: 'A', quantity: 10, unitPrice: 10 })]);
    const result = bulkDiscount(ctx);
    expect(result).toEqual([{ rule: 'bulk', sku: 'A', amount: 15 }]);
  });

  it('returns 15% off for items above threshold', () => {
    const ctx = makeContext([makeItem({ sku: 'A', quantity: 12, unitPrice: 10 })]);
    const result = bulkDiscount(ctx);
    expect(result).toEqual([{ rule: 'bulk', sku: 'A', amount: 18 }]);
  });

  it('returns multiple discounts for multiple qualifying items', () => {
    const items = [
      makeItem({ sku: 'A', quantity: 10, unitPrice: 10 }),
      makeItem({ sku: 'B', quantity: 20, unitPrice: 5 }),
    ];
    const ctx = makeContext(items);
    const result = bulkDiscount(ctx);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({ rule: 'bulk', sku: 'A', amount: 15 });
    expect(result[1]).toEqual({ rule: 'bulk', sku: 'B', amount: 15 });
  });
});

describe('comboDiscount', () => {
  it('returns $5 off when both WIDGET-A and WIDGET-B present', () => {
    const items = [
      makeItem({ sku: 'WIDGET-A' }),
      makeItem({ sku: 'WIDGET-B' }),
    ];
    expect(comboDiscount(makeContext(items))).toEqual([{ rule: 'combo', amount: 5 }]);
  });

  it('returns empty when only WIDGET-A present', () => {
    expect(comboDiscount(makeContext([makeItem({ sku: 'WIDGET-A' })]))).toEqual([]);
  });

  it('returns empty when only WIDGET-B present', () => {
    expect(comboDiscount(makeContext([makeItem({ sku: 'WIDGET-B' })]))).toEqual([]);
  });

  it('returns empty when neither present', () => {
    expect(comboDiscount(makeContext([makeItem({ sku: 'OTHER' })]))).toEqual([]);
  });
});

describe('loyaltyDiscount', () => {
  it('returns 10% for gold tier', () => {
    const ctx = makeContext([makeItem({ sku: 'A', quantity: 1, unitPrice: 100 })], 'gold');
    expect(loyaltyDiscount(ctx)).toEqual([{ rule: 'loyalty', amount: 10 }]);
  });

  it('returns 5% for silver tier', () => {
    const ctx = makeContext([makeItem({ sku: 'A', quantity: 1, unitPrice: 100 })], 'silver');
    expect(loyaltyDiscount(ctx)).toEqual([{ rule: 'loyalty', amount: 5 }]);
  });

  it('returns empty for none tier', () => {
    const ctx = makeContext([makeItem({ sku: 'A', quantity: 1, unitPrice: 100 })], 'none');
    expect(loyaltyDiscount(ctx)).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// applyDiscounts -- integration
// ---------------------------------------------------------------------------

describe('applyDiscounts', () => {
  // -- Basic happy paths ---------------------------------------------------

  it('calculates correct subtotal', () => {
    const items = [
      makeItem({ sku: 'A', quantity: 2, unitPrice: 25 }),
      makeItem({ sku: 'B', quantity: 3, unitPrice: 10 }),
    ];
    const result = applyDiscounts({ items, loyaltyTier: 'none' }, { rules: [] });
    expect(result.subtotal).toBe(80);
    expect(result.finalTotal).toBe(80);
    expect(result.discounts).toEqual([]);
  });

  it('applies bulk discount only when requested', () => {
    const items = [makeItem({ sku: 'X', quantity: 10, unitPrice: 20 })];
    const result = applyDiscounts(
      { items, loyaltyTier: 'none' },
      { rules: [bulkDiscount] },
    );
    expect(result.discounts).toEqual([{ rule: 'bulk', sku: 'X', amount: 30 }]);
    expect(result.totalDiscount).toBe(30);
    expect(result.finalTotal).toBe(170);
  });

  it('applies combo discount when WIDGET-A + WIDGET-B present', () => {
    const items = [
      makeItem({ sku: 'WIDGET-A', quantity: 1, unitPrice: 20 }),
      makeItem({ sku: 'WIDGET-B', quantity: 1, unitPrice: 30 }),
    ];
    const result = applyDiscounts(
      { items, loyaltyTier: 'none' },
      { rules: [comboDiscount] },
    );
    expect(result.discounts).toEqual([{ rule: 'combo', amount: 5 }]);
    expect(result.finalTotal).toBe(45);
  });

  it('applies loyalty discount for gold tier', () => {
    const items = [makeItem({ sku: 'A', quantity: 1, unitPrice: 100 })];
    const result = applyDiscounts(
      { items, loyaltyTier: 'gold' },
      { rules: [loyaltyDiscount] },
    );
    expect(result.discounts).toEqual([{ rule: 'loyalty', amount: 10 }]);
    expect(result.finalTotal).toBe(90);
  });

  it('applies loyalty discount for silver tier', () => {
    const items = [makeItem({ sku: 'A', quantity: 1, unitPrice: 100 })];
    const result = applyDiscounts(
      { items, loyaltyTier: 'silver' },
      { rules: [loyaltyDiscount] },
    );
    expect(result.discounts).toEqual([{ rule: 'loyalty', amount: 5 }]);
    expect(result.finalTotal).toBe(95);
  });

  // -- Rule stacking -------------------------------------------------------

  it('stacks all three rules', () => {
    const items = [
      makeItem({ sku: 'WIDGET-A', quantity: 12, unitPrice: 10 }), // bulk: 18
      makeItem({ sku: 'WIDGET-B', quantity: 3, unitPrice: 20 }),  // no bulk
    ];
    // subtotal = 120 + 60 = 180
    // bulk: 18, combo: 5, loyalty(gold): 18 => total = 41
    // 40% cap = 72, so all fit
    const result = applyDiscounts({ items, loyaltyTier: 'gold' });
    expect(result.subtotal).toBe(180);
    expect(result.discounts).toHaveLength(3);
    expect(result.totalDiscount).toBe(41);
    expect(result.finalTotal).toBe(139);
  });

  // -- Discount cap --------------------------------------------------------

  it('caps total discount at 40% of subtotal', () => {
    // Craft a scenario where discounts would exceed 40%
    // Item: qty 10, price 10 => subtotal 100, 40% cap = 40
    // bulk = 15, loyalty(gold) = 10 => 25, under cap
    // Let's use extreme: qty 10, price 5 => subtotal 50, cap 20
    // bulk = 7.5, combo won't trigger, loyalty(gold) = 5 => 12.5 -- still under
    // Need bigger discounts. Custom rule approach:
    const bigRule = () => [{ rule: 'big', amount: 999 }] as const;
    const items = [makeItem({ sku: 'A', quantity: 1, unitPrice: 100 })];
    const result = applyDiscounts(
      { items, loyaltyTier: 'none' },
      { rules: [bigRule] },
    );
    // 40% of 100 = 40
    expect(result.totalDiscount).toBe(40);
    expect(result.finalTotal).toBe(60);
    expect(result.warnings).toContain('Discount cap of 40% reached');
  });

  it('partially applies a discount when it would exceed the cap', () => {
    const rule25 = () => [{ rule: 'first', amount: 25 }] as const;
    const rule30 = () => [{ rule: 'second', amount: 30 }] as const;
    const items = [makeItem({ sku: 'A', quantity: 1, unitPrice: 100 })];
    // cap = 40, first takes 25, second clamped to 15
    const result = applyDiscounts(
      { items, loyaltyTier: 'none' },
      { rules: [rule25, rule30] },
    );
    expect(result.totalDiscount).toBe(40);
    expect(result.discounts).toEqual([
      { rule: 'first', amount: 25 },
      { rule: 'second', amount: 15 },
    ]);
    expect(result.warnings).toContain('Discount cap of 40% reached');
  });

  it('respects custom maxDiscountFraction', () => {
    const bigRule = () => [{ rule: 'big', amount: 999 }] as const;
    const items = [makeItem({ sku: 'A', quantity: 1, unitPrice: 100 })];
    const result = applyDiscounts(
      { items, loyaltyTier: 'none' },
      { rules: [bigRule], maxDiscountFraction: 0.2 },
    );
    expect(result.totalDiscount).toBe(20);
    expect(result.finalTotal).toBe(80);
    expect(result.warnings).toContain('Discount cap of 20% reached');
  });

  // -- Validation ----------------------------------------------------------

  it('throws on empty cart', () => {
    expect(() =>
      applyDiscounts({ items: [], loyaltyTier: 'none' }),
    ).toThrow('Cart cannot be empty');
  });

  it('throws on negative quantity', () => {
    expect(() =>
      applyDiscounts({
        items: [makeItem({ sku: 'BAD', quantity: -1 })],
        loyaltyTier: 'none',
      }),
    ).toThrow(/Invalid quantity/);
  });

  it('throws on negative unitPrice', () => {
    expect(() =>
      applyDiscounts({
        items: [makeItem({ sku: 'BAD', unitPrice: -5 })],
        loyaltyTier: 'none',
      }),
    ).toThrow(/Invalid unitPrice/);
  });

  it('throws on zero quantity', () => {
    expect(() =>
      applyDiscounts({
        items: [makeItem({ sku: 'ZERO', quantity: 0 })],
        loyaltyTier: 'none',
      }),
    ).toThrow(/Invalid quantity/);
  });

  // -- Edge cases -----------------------------------------------------------

  it('returns zero discounts for single item, no tier, no qualifying rules', () => {
    const items = [makeItem({ sku: 'SOLO', quantity: 1, unitPrice: 50 })];
    const result = applyDiscounts({ items, loyaltyTier: 'none' });
    expect(result.subtotal).toBe(50);
    expect(result.discounts).toEqual([]);
    expect(result.totalDiscount).toBe(0);
    expect(result.finalTotal).toBe(50);
    expect(result.warnings).toEqual([]);
  });

  it('handles free items (unitPrice=0) without errors', () => {
    const items = [makeItem({ sku: 'FREE', quantity: 5, unitPrice: 0 })];
    const result = applyDiscounts({ items, loyaltyTier: 'gold' });
    expect(result.subtotal).toBe(0);
    expect(result.finalTotal).toBe(0);
  });

  // -- Extensibility -------------------------------------------------------

  it('supports custom rules without modifying the core', () => {
    const bogo = (ctx: { items: readonly { sku: string; quantity: number; unitPrice: number }[] }) => {
      const results: AppliedDiscount[] = [];
      for (const item of ctx.items) {
        if (item.quantity >= 2) {
          results.push({ rule: 'bogo', sku: item.sku, amount: item.unitPrice });
        }
      }
      return results;
    };

    const items = [makeItem({ sku: 'SHOE', quantity: 2, unitPrice: 80 })];
    // subtotal = 160, cap = 64, bogo = 80 => clamped to 64
    const result = applyDiscounts(
      { items, loyaltyTier: 'none' },
      { rules: [bogo] },
    );
    expect(result.discounts).toEqual([{ rule: 'bogo', sku: 'SHOE', amount: 64 }]);
    expect(result.finalTotal).toBe(96);
  });

  it('applies default rules when no rules option is given', () => {
    const items = [
      makeItem({ sku: 'WIDGET-A', quantity: 10, unitPrice: 10 }),
      makeItem({ sku: 'WIDGET-B', quantity: 1, unitPrice: 20 }),
    ];
    const result = applyDiscounts({ items, loyaltyTier: 'gold' });
    // subtotal = 100 + 20 = 120
    // bulk on WIDGET-A: 10*10*0.15 = 15
    // combo: 5
    // loyalty(gold): 120*0.10 = 12
    // total discount = 32, cap = 48 => all fit
    expect(result.subtotal).toBe(120);
    expect(result.totalDiscount).toBe(32);
    expect(result.finalTotal).toBe(88);
  });

  // -- Adversarial: cross-item / aggregate edge cases ----------------------

  it('adversarial: many small discounts that individually fit but collectively exceed cap', () => {
    const manySmall = () =>
      Array.from({ length: 100 }, (_, i) => ({
        rule: `small-${i}`,
        amount: 1,
      }));
    const items = [makeItem({ sku: 'A', quantity: 1, unitPrice: 100 })];
    // cap = 40, should only apply 40 of the 100 $1 discounts
    const result = applyDiscounts(
      { items, loyaltyTier: 'none' },
      { rules: [manySmall] },
    );
    expect(result.totalDiscount).toBe(40);
    expect(result.discounts).toHaveLength(40);
    expect(result.warnings).toContain('Discount cap of 40% reached');
  });

  it('adversarial: discount amount equals exactly the cap', () => {
    const exactCap = () => [{ rule: 'exact', amount: 40 }] as const;
    const items = [makeItem({ sku: 'A', quantity: 1, unitPrice: 100 })];
    const result = applyDiscounts(
      { items, loyaltyTier: 'none' },
      { rules: [exactCap] },
    );
    expect(result.totalDiscount).toBe(40);
    expect(result.finalTotal).toBe(60);
    expect(result.warnings).toContain('Discount cap of 40% reached');
  });

  it('adversarial: very small fractional prices produce correct rounding', () => {
    const items = [makeItem({ sku: 'PENNY', quantity: 10, unitPrice: 0.01 })];
    // subtotal = 0.10, bulk = 0.10 * 0.15 = 0.015 => rounds to 0.02
    // cap = 0.10 * 0.40 = 0.04
    const result = applyDiscounts(
      { items, loyaltyTier: 'none' },
      { rules: [bulkDiscount] },
    );
    expect(result.subtotal).toBeCloseTo(0.10);
    expect(result.totalDiscount).toBe(0.02);
    expect(result.finalTotal).toBeCloseTo(0.08);
  });

  it('adversarial: zero-amount discount does not count toward cap', () => {
    const zeroDiscount = () => [{ rule: 'zero', amount: 0 }] as const;
    const items = [makeItem({ sku: 'A', quantity: 1, unitPrice: 100 })];
    const result = applyDiscounts(
      { items, loyaltyTier: 'none' },
      { rules: [zeroDiscount] },
    );
    expect(result.totalDiscount).toBe(0);
    expect(result.warnings).toEqual([]);
  });
});
