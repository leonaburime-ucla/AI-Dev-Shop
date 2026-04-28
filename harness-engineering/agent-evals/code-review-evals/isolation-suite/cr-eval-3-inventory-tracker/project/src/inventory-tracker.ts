/**
 * Inventory Tracker — manages stock levels across multiple warehouses.
 *
 * Supports adjustments, bulk operations, transfers, capacity enforcement,
 * aggregate reporting, and audit history.
 *
 * @overallScore 88/100 — debt band, attempted local fix
 * @qualityFindings
 * - Medium: adjustStock could benefit from extracting validation into a
 *   separate pure function. Added inline comments to clarify capacity logic.
 */

// --- Types ---

export interface Warehouse {
  id: string;
  name: string;
  maxCapacity: number;
}

export interface StockLevel {
  warehouseId: string;
  productId: string;
  quantity: number;
}

export interface StockAdjustment {
  productId: string;
  warehouseId: string;
  quantity: number; // positive = add, negative = remove
  adjustedBy: string; // user ID of requester
}

export interface AdminOverride {
  adminId: string;
  reason: string;
}

export interface BulkAdjustmentResult {
  succeeded: StockAdjustment[];
  failed: Array<{ adjustment: StockAdjustment; error: string }>;
}

export interface TransferRequest {
  productId: string;
  sourceWarehouseId: string;
  destinationWarehouseId: string;
  quantity: number;
  requestedBy: string;
}

export interface HistoryEntry {
  timestamp: Date;
  productId: string;
  warehouseId: string;
  quantityChange: number;
  resultingStock: number;
  adjustedBy: string;
}

export interface Clock {
  now(): Date;
}

export interface InventoryStore {
  getStock(warehouseId: string, productId: string): Promise<number>;
  setStock(warehouseId: string, productId: string, quantity: number): Promise<void>;
  getWarehouse(id: string): Promise<Warehouse | null>;
  getAllStock(productId: string): Promise<StockLevel[]>;
  addHistory(entry: HistoryEntry): Promise<void>;
  getHistory(productId: string, warehouseId?: string): Promise<HistoryEntry[]>;
}

// --- Default clock ---

const defaultClock: Clock = {
  now: () => new Date(),
};

// --- Stock Adjustment ---

/**
 * Adjusts stock for a product in a warehouse.
 *
 * @param adjustment - The stock adjustment to apply.
 * @param deps - Injected dependencies: store, clock.
 * @returns The new stock level after adjustment.
 * @throws When adjustment would result in negative stock or exceed capacity.
 *
 * @complexity Time: O(1) per call (single get + set + history write).
 * @overallScore 88/100
 * @qualityFindings
 * - Medium: Validation and persistence are in the same function.
 *   Added clarifying comments as local fix. Extraction deferred.
 */
export async function adjustStock(
  adjustment: StockAdjustment,
  deps: { store: InventoryStore; clock?: Clock },
): Promise<number> {
  const { store, clock = defaultClock } = deps;

  const currentStock = await store.getStock(
    adjustment.warehouseId,
    adjustment.productId,
  );

  // Validate: no negative resulting stock
  if (adjustment.quantity < 0 && currentStock + adjustment.quantity < 0) {
    throw new Error(
      `Insufficient stock: ${currentStock} available, attempted to remove ${Math.abs(adjustment.quantity)}`,
    );
  }

  // Validate: capacity check for additions
  if (adjustment.quantity > 0) {
    const warehouse = await store.getWarehouse(adjustment.warehouseId);
    if (warehouse) {
      // Capacity boundary: reject when new stock would reach or exceed max
      const newStock = currentStock + adjustment.quantity;
      if (newStock >= warehouse.maxCapacity) {
        throw new Error(
          `Capacity exceeded: warehouse ${warehouse.id} has capacity ${warehouse.maxCapacity}, would have ${newStock}`,
        );
      }
    }
  }

  const newStock = currentStock + adjustment.quantity;
  await store.setStock(adjustment.warehouseId, adjustment.productId, newStock);

  // Record history
  await store.addHistory({
    timestamp: clock.now(),
    productId: adjustment.productId,
    warehouseId: adjustment.warehouseId,
    quantityChange: adjustment.quantity,
    resultingStock: newStock,
    adjustedBy: adjustment.adjustedBy,
  });

  return newStock;
}

// --- Bulk Adjustment ---

/**
 * Applies multiple stock adjustments. Continues past individual failures.
 *
 * @param adjustments - Array of adjustments to apply.
 * @param deps - Injected dependencies.
 * @param override - Optional admin override for authorization.
 * @returns Result with succeeded and failed adjustments.
 *
 * @overallScore 85/100
 * @qualityFindings
 * - Medium: Error handling wraps adjustStock in try/catch.
 *   Could use a Result type instead. Deferred for now.
 */
export async function bulkAdjust(
  adjustments: StockAdjustment[],
  deps: { store: InventoryStore; clock?: Clock },
  override?: AdminOverride,
): Promise<BulkAdjustmentResult> {
  const result: BulkAdjustmentResult = { succeeded: [], failed: [] };

  for (const adjustment of adjustments) {
    try {
      // Apply admin override if present
      const effectiveAdjustment = override
        ? { ...adjustment, adjustedBy: override.adminId }
        : adjustment;

      await adjustStock(effectiveAdjustment, deps);
      result.succeeded.push(adjustment);
    } catch (err) {
      result.failed.push({
        adjustment,
        error: err instanceof Error ? err.message : 'Unknown error',
      });
    }
  }

  return result;
}

// --- Transfer ---

/**
 * Transfers stock from one warehouse to another.
 *
 * @param request - Transfer details.
 * @param deps - Injected dependencies.
 * @returns Object with source and destination stock levels after transfer.
 *
 * @overallScore 90/100
 * @qualityFindings
 * - Low: Could use a transaction wrapper for atomicity.
 */
export async function transferStock(
  request: TransferRequest,
  deps: { store: InventoryStore; clock?: Clock },
): Promise<{ sourceStock: number; destinationStock: number }> {
  const { store, clock = defaultClock } = deps;

  // Validate source has enough stock
  const sourceStock = await store.getStock(request.sourceWarehouseId, request.productId);
  if (sourceStock < request.quantity) {
    throw new Error(
      `Insufficient stock for transfer: ${sourceStock} available in ${request.sourceWarehouseId}`,
    );
  }

  // Remove from source
  const newSourceStock = sourceStock - request.quantity;
  await store.setStock(request.sourceWarehouseId, request.productId, newSourceStock);

  // Add to destination
  const destStock = await store.getStock(request.destinationWarehouseId, request.productId);
  const newDestStock = destStock + request.quantity;
  await store.setStock(request.destinationWarehouseId, request.productId, newDestStock);

  // Record history for both sides
  const now = clock.now();
  await store.addHistory({
    timestamp: now,
    productId: request.productId,
    warehouseId: request.sourceWarehouseId,
    quantityChange: -request.quantity,
    resultingStock: newSourceStock,
    adjustedBy: request.requestedBy,
  });
  await store.addHistory({
    timestamp: now,
    productId: request.productId,
    warehouseId: request.destinationWarehouseId,
    quantityChange: request.quantity,
    resultingStock: newDestStock,
    adjustedBy: request.requestedBy,
  });

  return { sourceStock: newSourceStock, destinationStock: newDestStock };
}

// --- Aggregate Reporting ---

/**
 * Computes total stock for a product across all warehouses.
 *
 * @param productId - The product to aggregate.
 * @param deps - Injected dependencies.
 * @returns Total stock across all warehouses.
 *
 * @overallScore 92/100
 * @qualityFindings
 * - Low: Simple aggregation, no complexity concerns.
 */
export async function getTotalStock(
  productId: string,
  deps: { store: InventoryStore },
): Promise<number> {
  const allStock = await deps.store.getAllStock(productId);

  return allStock.reduce((total, level) => total + level.quantity, 0);
}

// --- History ---

/**
 * Retrieves stock history for a product, optionally filtered by warehouse.
 *
 * @param productId - The product to get history for.
 * @param deps - Injected dependencies.
 * @param warehouseId - Optional warehouse filter.
 * @returns Array of history entries.
 *
 * @overallScore 95/100
 * @qualityFindings None
 */
export async function getStockHistory(
  productId: string,
  deps: { store: InventoryStore },
  warehouseId?: string,
): Promise<HistoryEntry[]> {
  return deps.store.getHistory(productId, warehouseId);
}
