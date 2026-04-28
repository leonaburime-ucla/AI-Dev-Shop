/**
 * Sales Report Generator — Test Suite
 *
 * Covers: all three formats, deduplication, PII stripping, rounding,
 * refund handling, edge cases, and adversarial inputs.
 */

import {
  generateReport,
  Transaction,
  SummaryReport,
  DetailedReport,
  ExecutiveReport,
  formatCurrency,
  isWithinRange,
  normalizeRegion,
  roundTwo,
} from '../reporter';

// -- Fixtures ---------------------------------------------------------------

function tx(overrides: Partial<Transaction> = {}): Transaction {
  return {
    id: 'tx-001',
    customerId: 'cust-a',
    customerEmail: 'alice@example.com',
    amount: 100,
    currency: 'USD',
    date: '2026-01-15',
    region: 'North America',
    salesRepId: 'rep-1',
    ...overrides,
  };
}

const sampleTransactions: Transaction[] = [
  tx({ id: 'tx-001', customerId: 'cust-a', customerEmail: 'alice@example.com', amount: 100, date: '2026-01-15', region: 'North America' }),
  tx({ id: 'tx-002', customerId: 'cust-b', customerEmail: 'bob@example.com', amount: 150, date: '2026-02-20', region: 'Europe' }),
  tx({ id: 'tx-003', customerId: 'cust-a', customerEmail: 'alice@example.com', amount: 50, date: '2026-03-10', region: 'North America' }),
];

// -- Summary Report ---------------------------------------------------------

describe('generateReport — summary format', () => {
  test('computes correct totals', () => {
    const report = generateReport(
      { transactions: sampleTransactions },
      { format: 'summary' },
    ) as SummaryReport;

    expect(report.totalRevenue).toBe(300);
    expect(report.transactionCount).toBe(3);
    expect(report.averageOrderValue).toBe(100);
  });

  test('groups revenue by region', () => {
    const report = generateReport(
      { transactions: sampleTransactions },
      { format: 'summary' },
    ) as SummaryReport;

    expect(report.revenueByRegion['North America']).toBe(150);
    expect(report.revenueByRegion['Europe']).toBe(150);
  });

  test('returns top customers aggregated by total spend, not max single tx', () => {
    const report = generateReport(
      { transactions: sampleTransactions },
      { format: 'summary' },
    ) as SummaryReport;

    const custA = report.topCustomers.find((c) => c.customerId === 'cust-a');
    expect(custA).toBeDefined();
    // cust-a has tx-001 ($100) + tx-003 ($50) = $150 total spend
    expect(custA!.totalSpend).toBe(150);
  });

  test('limits topCustomers to 5', () => {
    const manyCustomers = Array.from({ length: 10 }, (_, i) =>
      tx({ id: `tx-${i}`, customerId: `cust-${i}`, amount: (i + 1) * 10 }),
    );
    const report = generateReport(
      { transactions: manyCustomers },
      { format: 'summary' },
    ) as SummaryReport;

    expect(report.topCustomers).toHaveLength(5);
    // Highest spender should be first
    expect(report.topCustomers[0].customerId).toBe('cust-9');
  });

  test('computes correct date range', () => {
    const report = generateReport(
      { transactions: sampleTransactions },
      { format: 'summary' },
    ) as SummaryReport;

    expect(report.dateRange.start).toBe('2026-01-15');
    expect(report.dateRange.end).toBe('2026-03-10');
  });

  test('all monetary fields are numbers, not strings', () => {
    const report = generateReport(
      { transactions: sampleTransactions },
      { format: 'summary' },
    ) as SummaryReport;

    expect(typeof report.totalRevenue).toBe('number');
    expect(typeof report.averageOrderValue).toBe('number');
    expect(typeof report.revenueByRegion['North America']).toBe('number');
    for (const c of report.topCustomers) {
      expect(typeof c.totalSpend).toBe('number');
    }
  });
});

// -- Detailed Report --------------------------------------------------------

describe('generateReport — detailed format', () => {
  test('includes per-transaction breakdown', () => {
    const report = generateReport(
      { transactions: sampleTransactions },
      { format: 'detailed' },
    ) as DetailedReport;

    expect(report.transactions).toHaveLength(3);
    expect(report.totalRevenue).toBe(300);
  });

  test('does NOT expose customer email in transactions', () => {
    const report = generateReport(
      { transactions: sampleTransactions },
      { format: 'detailed' },
    ) as DetailedReport;

    for (const t of report.transactions) {
      const json = JSON.stringify(t);
      expect(json).not.toContain('customerEmail');
      expect(json).not.toContain('alice@example.com');
      expect(json).not.toContain('bob@example.com');
    }
  });

  test('does NOT expose phone, notes, or raw record in transactions', () => {
    const txsWithPII = [
      tx({
        id: 'tx-pii',
        customerPhone: '555-1234',
        customerNotes: 'VIP client',
      }),
    ];
    const report = generateReport(
      { transactions: txsWithPII },
      { format: 'detailed' },
    ) as DetailedReport;

    const json = JSON.stringify(report.transactions);
    expect(json).not.toContain('customerPhone');
    expect(json).not.toContain('555-1234');
    expect(json).not.toContain('customerNotes');
    expect(json).not.toContain('VIP client');
    expect(json).not.toContain('debug');
    expect(json).not.toContain('rawRecord');
  });

  test('transaction amounts are rounded to 2dp', () => {
    const txs = [tx({ id: 'tx-round', amount: 33.335 })];
    const report = generateReport(
      { transactions: txs },
      { format: 'detailed' },
    ) as DetailedReport;

    expect(report.transactions[0].amount).toBe(33.34);
  });
});

// -- Executive Report -------------------------------------------------------

describe('generateReport — executive format', () => {
  test('returns only top-line metrics', () => {
    const report = generateReport(
      { transactions: sampleTransactions },
      { format: 'executive' },
    ) as ExecutiveReport;

    expect(report.totalRevenue).toBe(300);
    expect(report.transactionCount).toBe(3);
    expect(report.averageOrderValue).toBe(100);
    expect(report.dateRange.start).toBe('2026-01-15');

    // Should NOT have region or customer breakdowns
    expect((report as any).revenueByRegion).toBeUndefined();
    expect((report as any).topCustomers).toBeUndefined();
    expect((report as any).transactions).toBeUndefined();
  });
});

// -- Edge Cases: Empty / Invalid -------------------------------------------

describe('generateReport — edge cases', () => {
  test('empty transactions array returns zeroed report', () => {
    const report = generateReport(
      { transactions: [] },
      { format: 'summary' },
    ) as SummaryReport;

    expect(report.totalRevenue).toBe(0);
    expect(report.transactionCount).toBe(0);
    expect(report.averageOrderValue).toBe(0);
    expect(report.topCustomers).toEqual([]);
    expect(report.revenueByRegion).toEqual({});
    expect(report.dateRange).toEqual({ start: '', end: '' });
  });

  test('empty array with detailed format includes empty transactions', () => {
    const report = generateReport(
      { transactions: [] },
      { format: 'detailed' },
    ) as DetailedReport;

    expect(report.transactions).toEqual([]);
  });

  test('empty array with executive format returns zeroed exec report', () => {
    const report = generateReport(
      { transactions: [] },
      { format: 'executive' },
    ) as ExecutiveReport;

    expect(report.totalRevenue).toBe(0);
    expect(report.transactionCount).toBe(0);
  });

  test('throws on invalid format', () => {
    expect(() =>
      generateReport({ transactions: [] }, { format: 'csv' as any }),
    ).toThrow('Invalid report format');
  });

  test('defaults to summary when no format specified', () => {
    const report = generateReport({ transactions: sampleTransactions });

    expect((report as SummaryReport).revenueByRegion).toBeDefined();
    expect((report as SummaryReport).topCustomers).toBeDefined();
  });

  test('filters out invalid transactions (missing required fields)', () => {
    const txs = [
      tx({ id: 'tx-good', amount: 100 }),
      { id: '', customerId: 'x', customerEmail: 'x', amount: 50, currency: 'USD', date: '2026-01-01', region: 'EU', salesRepId: 'r' } as Transaction,
      { id: 'tx-no-amount', customerId: 'x', customerEmail: 'x', amount: undefined as any, currency: 'USD', date: '2026-01-01', region: 'EU', salesRepId: 'r' } as Transaction,
    ];
    const report = generateReport(
      { transactions: txs },
      { format: 'summary' },
    ) as SummaryReport;

    expect(report.transactionCount).toBe(1);
    expect(report.totalRevenue).toBe(100);
  });
});

// -- Deduplication ----------------------------------------------------------

describe('generateReport — deduplication', () => {
  test('deduplicates transactions by ID, keeping first occurrence', () => {
    const txs = [
      tx({ id: 'tx-dup', amount: 100 }),
      tx({ id: 'tx-dup', amount: 999 }), // duplicate — should be dropped
      tx({ id: 'tx-other', amount: 50 }),
    ];
    const report = generateReport(
      { transactions: txs },
      { format: 'summary' },
    ) as SummaryReport;

    expect(report.transactionCount).toBe(2);
    expect(report.totalRevenue).toBe(150); // 100 + 50, NOT 100 + 999 + 50
  });

  test('dedup applies before customer aggregation', () => {
    const txs = [
      tx({ id: 'tx-a1', customerId: 'cust-x', amount: 100 }),
      tx({ id: 'tx-a1', customerId: 'cust-x', amount: 100 }), // dup
      tx({ id: 'tx-a2', customerId: 'cust-x', amount: 50 }),
    ];
    const report = generateReport(
      { transactions: txs },
      { format: 'summary' },
    ) as SummaryReport;

    const custX = report.topCustomers.find((c) => c.customerId === 'cust-x');
    expect(custX!.totalSpend).toBe(150); // 100 + 50, not 200 + 50
  });
});

// -- Refunds (negative amounts) --------------------------------------------

describe('generateReport — refunds', () => {
  test('negative amounts reduce total revenue', () => {
    const txs = [
      tx({ id: 'tx-sale', amount: 200 }),
      tx({ id: 'tx-refund', amount: -50 }),
    ];
    const report = generateReport(
      { transactions: txs },
      { format: 'summary' },
    ) as SummaryReport;

    expect(report.totalRevenue).toBe(150);
    expect(report.transactionCount).toBe(2);
  });
});

// -- Rounding ---------------------------------------------------------------

describe('generateReport — rounding', () => {
  test('all monetary values rounded to 2 decimal places', () => {
    const txs = [
      tx({ id: 'tx-r1', customerId: 'c1', amount: 10.005, region: 'R1' }),
      tx({ id: 'tx-r2', customerId: 'c1', amount: 20.005, region: 'R1' }),
      tx({ id: 'tx-r3', customerId: 'c2', amount: 33.333, region: 'R2' }),
    ];
    const report = generateReport(
      { transactions: txs },
      { format: 'summary' },
    ) as SummaryReport;

    // totalRevenue: 10.005 + 20.005 + 33.333 = 63.343 -> 63.34
    expect(report.totalRevenue).toBe(63.34);
    // Per-region should be rounded
    expect(report.revenueByRegion['R1']).toBe(30.01);
    expect(report.revenueByRegion['R2']).toBe(33.33);
    // Top customer spend should be rounded
    const c1 = report.topCustomers.find((c) => c.customerId === 'c1');
    expect(c1!.totalSpend).toBe(30.01);
  });

  test('floating point drift does not produce extra decimals', () => {
    // 0.1 + 0.2 === 0.30000000000000004 in JS
    const txs = [
      tx({ id: 'tx-fp1', amount: 0.1 }),
      tx({ id: 'tx-fp2', amount: 0.2 }),
    ];
    const report = generateReport(
      { transactions: txs },
      { format: 'summary' },
    ) as SummaryReport;

    expect(report.totalRevenue).toBe(0.3);
  });
});

// -- PII: cross-format checks ----------------------------------------------

describe('generateReport — PII stripping across all formats', () => {
  const piiTx = tx({
    id: 'tx-pii-check',
    customerEmail: 'secret@corp.com',
    customerPhone: '555-SECRET',
    customerNotes: 'top-secret-note',
  });

  for (const format of ['summary', 'detailed', 'executive'] as const) {
    test(`${format} format does not contain email`, () => {
      const report = generateReport(
        { transactions: [piiTx] },
        { format },
      );
      const json = JSON.stringify(report);
      expect(json).not.toContain('secret@corp.com');
      expect(json).not.toContain('555-SECRET');
      expect(json).not.toContain('top-secret-note');
      expect(json).not.toContain('customerEmail');
      expect(json).not.toContain('customerPhone');
      expect(json).not.toContain('customerNotes');
    });
  }
});

// -- Utility functions ------------------------------------------------------

describe('formatCurrency', () => {
  test('formats positive amount', () => {
    expect(formatCurrency(1234.5)).toBe('$1234.50');
  });

  test('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });

  test('formats negative amount', () => {
    expect(formatCurrency(-50)).toBe('$-50.00');
  });
});

describe('isWithinRange', () => {
  test('returns true for date within range', () => {
    expect(isWithinRange('2026-06-15', '2026-01-01', '2026-12-31')).toBe(true);
  });

  test('returns true for date equal to start', () => {
    expect(isWithinRange('2026-01-01', '2026-01-01', '2026-12-31')).toBe(true);
  });

  test('returns false for date outside range', () => {
    expect(isWithinRange('2025-12-31', '2026-01-01', '2026-12-31')).toBe(false);
  });
});

describe('normalizeRegion', () => {
  test('trims and uppercases', () => {
    expect(normalizeRegion('  north america  ')).toBe('NORTH AMERICA');
  });
});

describe('roundTwo', () => {
  test('rounds 0.005 up', () => {
    expect(roundTwo(1.005)).toBe(1.01);
  });

  test('leaves clean values unchanged', () => {
    expect(roundTwo(100)).toBe(100);
    expect(roundTwo(99.99)).toBe(99.99);
  });

  test('handles negative values', () => {
    expect(roundTwo(-1.005)).toBe(-1);
  });
});
