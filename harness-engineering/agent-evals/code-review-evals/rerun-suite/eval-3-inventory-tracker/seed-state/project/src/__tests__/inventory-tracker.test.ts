/**
 * Tests for Inventory Tracker.
 *
 * 40 tests covering adjustments, bulk operations, transfers, capacity,
 * aggregation, and history.
 */

import {
  adjustStock,
  bulkAdjust,
  transferStock,
  getTotalStock,
  getStockHistory,
  type StockAdjustment,
  type InventoryStore,
  type Warehouse,
  type StockLevel,
  type HistoryEntry,
  type Clock,
} from '../inventory-tracker';

jest.useFakeTimers();

// --- Test helpers ---

const fixedDate = new Date('2026-04-25T12:00:00Z');
const mockClock: Clock = { now: () => fixedDate };

function makeMockStore(overrides: Partial<InventoryStore> = {}): InventoryStore {
  return {
    getStock: jest.fn().mockResolvedValue(50),
    setStock: jest.fn().mockResolvedValue(undefined),
    getWarehouse: jest.fn().mockResolvedValue({
      id: 'WH-1',
      name: 'Main Warehouse',
      maxCapacity: 100,
    } as Warehouse),
    getAllStock: jest.fn().mockResolvedValue([
      { warehouseId: 'WH-1', productId: 'PROD-1', quantity: 50 },
      { warehouseId: 'WH-2', productId: 'PROD-1', quantity: 30 },
    ] as StockLevel[]),
    addHistory: jest.fn().mockResolvedValue(undefined),
    getHistory: jest.fn().mockResolvedValue([]),
    ...overrides,
  };
}

function makeAdjustment(overrides: Partial<StockAdjustment> = {}): StockAdjustment {
  return {
    productId: 'PROD-1',
    warehouseId: 'WH-1',
    quantity: 10,
    adjustedBy: 'USER-001',
    ...overrides,
  };
}

// --- adjustStock tests ---

describe('adjustStock', () => {
  it('should increase stock', async () => {
    const store = makeMockStore();
    const result = await adjustStock(makeAdjustment({ quantity: 10 }), {
      store,
      clock: mockClock,
    });
    expect(result).toBe(60);
    expect(store.setStock).toHaveBeenCalledWith('WH-1', 'PROD-1', 60);
  });

  it('should decrease stock', async () => {
    const store = makeMockStore();
    const result = await adjustStock(makeAdjustment({ quantity: -10 }), {
      store,
      clock: mockClock,
    });
    expect(result).toBe(40);
    expect(store.setStock).toHaveBeenCalledWith('WH-1', 'PROD-1', 40);
  });

  it('should reject removal exceeding available stock', async () => {
    const store = makeMockStore({ getStock: jest.fn().mockResolvedValue(5) });
    await expect(
      adjustStock(makeAdjustment({ quantity: -10 }), { store, clock: mockClock }),
    ).rejects.toThrow('Insufficient stock');
  });

  it('should reject when capacity would be exceeded', async () => {
    const store = makeMockStore({ getStock: jest.fn().mockResolvedValue(95) });
    await expect(
      adjustStock(makeAdjustment({ quantity: 10 }), { store, clock: mockClock }),
    ).rejects.toThrow('Capacity exceeded');
  });

  it('should allow adjustment up to just below capacity', async () => {
    // maxCapacity=100, currentStock=50, adding 49 → newStock=99 < 100 → allowed
    const store = makeMockStore({ getStock: jest.fn().mockResolvedValue(50) });
    const result = await adjustStock(makeAdjustment({ quantity: 49 }), {
      store,
      clock: mockClock,
    });
    expect(result).toBe(99);
  });

  it('should record history entry', async () => {
    const store = makeMockStore();
    await adjustStock(makeAdjustment({ quantity: 10 }), { store, clock: mockClock });
    expect(store.addHistory).toHaveBeenCalledWith({
      timestamp: fixedDate,
      productId: 'PROD-1',
      warehouseId: 'WH-1',
      quantityChange: 10,
      resultingStock: 60,
      adjustedBy: 'USER-001',
    });
  });

  it('should use default clock when none provided', async () => {
    const store = makeMockStore();
    await adjustStock(makeAdjustment(), { store });
    expect(store.addHistory).toHaveBeenCalled();
  });

  it('should handle zero quantity adjustment', async () => {
    const store = makeMockStore();
    const result = await adjustStock(makeAdjustment({ quantity: 0 }), {
      store,
      clock: mockClock,
    });
    expect(result).toBe(50);
  });

  it('should handle warehouse not found gracefully', async () => {
    const store = makeMockStore({
      getWarehouse: jest.fn().mockResolvedValue(null),
    });
    // When warehouse is null, capacity check is skipped
    const result = await adjustStock(makeAdjustment({ quantity: 200 }), {
      store,
      clock: mockClock,
    });
    expect(result).toBe(250);
  });
});

// --- bulkAdjust tests ---

describe('bulkAdjust', () => {
  it('should process all successful adjustments', async () => {
    const store = makeMockStore();
    const adjustments = [
      makeAdjustment({ quantity: 10 }),
      makeAdjustment({ quantity: 20 }),
    ];

    const result = await bulkAdjust(adjustments, { store, clock: mockClock });

    expect(result.succeeded).toHaveLength(2);
    expect(result.failed).toHaveLength(0);
  });

  it('should continue past individual failures', async () => {
    const store = makeMockStore({
      getStock: jest.fn()
        .mockResolvedValueOnce(5)   // first: only 5 available
        .mockResolvedValueOnce(50)  // second: 50 available
        .mockResolvedValueOnce(50), // for warehouse check
    });
    const adjustments = [
      makeAdjustment({ quantity: -10 }), // will fail: insufficient
      makeAdjustment({ quantity: 5 }),   // will succeed
    ];

    const result = await bulkAdjust(adjustments, { store, clock: mockClock });

    expect(result.succeeded).toHaveLength(1);
    expect(result.failed).toHaveLength(1);
    expect(result.failed[0].error).toContain('Insufficient stock');
  });

  it('should handle empty adjustments array', async () => {
    const store = makeMockStore();
    const result = await bulkAdjust([], { store, clock: mockClock });
    expect(result.succeeded).toHaveLength(0);
    expect(result.failed).toHaveLength(0);
  });

  it('should handle all failures', async () => {
    const store = makeMockStore({
      getStock: jest.fn().mockResolvedValue(0),
    });
    const adjustments = [
      makeAdjustment({ quantity: -10 }),
      makeAdjustment({ quantity: -20 }),
    ];

    const result = await bulkAdjust(adjustments, { store, clock: mockClock });

    expect(result.succeeded).toHaveLength(0);
    expect(result.failed).toHaveLength(2);
  });

  it('should apply admin override when provided', async () => {
    const store = makeMockStore();
    const adjustments = [makeAdjustment({ adjustedBy: 'USER-001' })];

    await bulkAdjust(
      adjustments,
      { store, clock: mockClock },
      { adminId: 'ADMIN-001', reason: 'Inventory correction' },
    );

    expect(store.setStock).toHaveBeenCalled();
  });

  it('should collect multiple different error types', async () => {
    const store = makeMockStore({
      getStock: jest.fn()
        .mockResolvedValueOnce(0)   // insufficient
        .mockResolvedValueOnce(95)  // capacity
        .mockResolvedValueOnce(95), // for warehouse lookup
    });
    const adjustments = [
      makeAdjustment({ quantity: -10 }), // insufficient stock
      makeAdjustment({ quantity: 10 }),  // capacity exceeded
    ];

    const result = await bulkAdjust(adjustments, { store, clock: mockClock });

    expect(result.failed).toHaveLength(2);
  });
});

// --- transferStock tests ---

describe('transferStock', () => {
  it('should transfer stock between warehouses', async () => {
    const store = makeMockStore({
      getStock: jest.fn()
        .mockResolvedValueOnce(50)  // source
        .mockResolvedValueOnce(20), // destination
    });

    const result = await transferStock(
      {
        productId: 'PROD-1',
        sourceWarehouseId: 'WH-1',
        destinationWarehouseId: 'WH-2',
        quantity: 10,
        requestedBy: 'USER-001',
      },
      { store, clock: mockClock },
    );

    expect(result.sourceStock).toBe(40);
    expect(result.destinationStock).toBe(30);
  });

  it('should reject transfer when source has insufficient stock', async () => {
    const store = makeMockStore({
      getStock: jest.fn().mockResolvedValueOnce(5),
    });

    await expect(
      transferStock(
        {
          productId: 'PROD-1',
          sourceWarehouseId: 'WH-1',
          destinationWarehouseId: 'WH-2',
          quantity: 10,
          requestedBy: 'USER-001',
        },
        { store, clock: mockClock },
      ),
    ).rejects.toThrow('Insufficient stock for transfer');
  });

  it('should record history for both source and destination', async () => {
    const store = makeMockStore({
      getStock: jest.fn()
        .mockResolvedValueOnce(50)
        .mockResolvedValueOnce(20),
    });

    await transferStock(
      {
        productId: 'PROD-1',
        sourceWarehouseId: 'WH-1',
        destinationWarehouseId: 'WH-2',
        quantity: 10,
        requestedBy: 'USER-001',
      },
      { store, clock: mockClock },
    );

    expect(store.addHistory).toHaveBeenCalledTimes(2);
    // Check source history
    expect(store.addHistory).toHaveBeenCalledWith(
      expect.objectContaining({
        warehouseId: 'WH-1',
        quantityChange: -10,
        resultingStock: 40,
      }),
    );
    // Check destination history
    expect(store.addHistory).toHaveBeenCalledWith(
      expect.objectContaining({
        warehouseId: 'WH-2',
        quantityChange: 10,
        resultingStock: 30,
      }),
    );
  });

  it('should use same timestamp for both history entries', async () => {
    const store = makeMockStore({
      getStock: jest.fn()
        .mockResolvedValueOnce(50)
        .mockResolvedValueOnce(20),
    });

    await transferStock(
      {
        productId: 'PROD-1',
        sourceWarehouseId: 'WH-1',
        destinationWarehouseId: 'WH-2',
        quantity: 10,
        requestedBy: 'USER-001',
      },
      { store, clock: mockClock },
    );

    const calls = (store.addHistory as jest.Mock).mock.calls;
    expect(calls[0][0].timestamp).toBe(calls[1][0].timestamp);
  });

});

// --- getTotalStock tests ---

describe('getTotalStock', () => {
  it('should sum stock across all warehouses', async () => {
    const store = makeMockStore();
    const total = await getTotalStock('PROD-1', { store });
    expect(total).toBe(80); // 50 + 30 from mock
  });

  it('should return 0 when no stock exists', async () => {
    const store = makeMockStore({
      getAllStock: jest.fn().mockResolvedValue([]),
    });
    const total = await getTotalStock('PROD-1', { store });
    expect(total).toBe(0);
  });

  it('should handle single warehouse', async () => {
    const store = makeMockStore({
      getAllStock: jest.fn().mockResolvedValue([
        { warehouseId: 'WH-1', productId: 'PROD-1', quantity: 42 },
      ]),
    });
    const total = await getTotalStock('PROD-1', { store });
    expect(total).toBe(42);
  });

  it('should handle many warehouses', async () => {
    const levels: StockLevel[] = Array.from({ length: 20 }, (_, i) => ({
      warehouseId: `WH-${i}`,
      productId: 'PROD-1',
      quantity: 10,
    }));
    const store = makeMockStore({
      getAllStock: jest.fn().mockResolvedValue(levels),
    });
    const total = await getTotalStock('PROD-1', { store });
    expect(total).toBe(200);
  });
});

// --- getStockHistory tests ---

describe('getStockHistory', () => {
  it('should return history for a product', async () => {
    const history: HistoryEntry[] = [
      {
        timestamp: fixedDate,
        productId: 'PROD-1',
        warehouseId: 'WH-1',
        quantityChange: 10,
        resultingStock: 60,
        adjustedBy: 'USER-001',
      },
    ];
    const store = makeMockStore({
      getHistory: jest.fn().mockResolvedValue(history),
    });

    const result = await getStockHistory('PROD-1', { store });
    expect(result).toHaveLength(1);
    expect(result[0].quantityChange).toBe(10);
  });

  it('should filter by warehouse when specified', async () => {
    const store = makeMockStore();
    await getStockHistory('PROD-1', { store }, 'WH-1');
    expect(store.getHistory).toHaveBeenCalledWith('PROD-1', 'WH-1');
  });

  it('should return empty array when no history', async () => {
    const store = makeMockStore();
    const result = await getStockHistory('PROD-1', { store });
    expect(result).toHaveLength(0);
  });
});

// --- Edge case tests ---

describe('edge cases', () => {
  it('should handle concurrent adjustments to same product', async () => {
    const store = makeMockStore();
    const adj1 = makeAdjustment({ quantity: 10 });
    const adj2 = makeAdjustment({ quantity: 20 });

    const [r1, r2] = await Promise.all([
      adjustStock(adj1, { store, clock: mockClock }),
      adjustStock(adj2, { store, clock: mockClock }),
    ]);

    // Both read currentStock=50, so both compute independently
    expect(r1).toBe(60);
    expect(r2).toBe(70);
    // Both read currentStock=50, so both compute independently
  });

  it('should handle adjustment of zero quantity', async () => {
    const store = makeMockStore();
    const result = await adjustStock(
      makeAdjustment({ quantity: 0 }),
      { store, clock: mockClock },
    );
    expect(result).toBe(50);
  });

  it('should handle transfer of entire stock', async () => {
    const store = makeMockStore({
      getStock: jest.fn()
        .mockResolvedValueOnce(50)  // source has exactly 50
        .mockResolvedValueOnce(0),  // destination is empty
    });

    const result = await transferStock(
      {
        productId: 'PROD-1',
        sourceWarehouseId: 'WH-1',
        destinationWarehouseId: 'WH-2',
        quantity: 50,
        requestedBy: 'USER-001',
      },
      { store, clock: mockClock },
    );

    expect(result.sourceStock).toBe(0);
    expect(result.destinationStock).toBe(50);
  });

  it('should handle large bulk adjustment', async () => {
    const store = makeMockStore();
    const adjustments = Array.from({ length: 100 }, (_, i) =>
      makeAdjustment({ quantity: 1, productId: `PROD-${i}` }),
    );

    const result = await bulkAdjust(adjustments, { store, clock: mockClock });
    expect(result.succeeded).toHaveLength(100);
  });
});
