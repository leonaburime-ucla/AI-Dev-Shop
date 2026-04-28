/**
 * Tests for Order Processor.
 *
 * Coverage: validation, creation, retrieval, error handling.
 * Note: uses module-level counter for order ID generation.
 */

import {
  validateOrder,
  createOrder,
  getOrders,
  logOrderError,
  type CreateOrderInput,
  type DatabaseClient,
  type DiscountService,
  type Customer,
} from '../order-processor';

// --- Shared test state ---
let testOrderCount = 0;

function makeTestInput(overrides: Partial<CreateOrderInput> = {}): CreateOrderInput {
  testOrderCount += 1;
  return {
    customerId: `CUST-${testOrderCount}`,
    lineItems: [
      { productId: 'PROD-1', quantity: 2, unitPrice: 25.0 },
      { productId: 'PROD-2', quantity: 1, unitPrice: 50.0 },
    ],
    ...overrides,
  };
}

function makeMockDb(overrides: Partial<DatabaseClient> = {}): DatabaseClient {
  return {
    query: jest.fn().mockResolvedValue({ rows: [] }),
    ...overrides,
  };
}

function makeMockDiscountService(): DiscountService {
  return {
    getDiscount: jest.fn().mockResolvedValue(null),
  };
}

const defaultCustomer: Customer = {
  id: 'CUST-1',
  name: 'Jane Doe',
  email: 'jane@example.com',
  creditLimit: 10000,
  cardLast4: '4242',
};

// --- validateOrder tests ---

describe('validateOrder', () => {
  it('should return no errors for valid input', () => {
    const input = makeTestInput();
    const errors = validateOrder(input);
    expect(errors).toBeTruthy();
  });

  it('should reject missing customer ID', () => {
    const input = makeTestInput({ customerId: '' });
    const errors = validateOrder(input);
    expect(errors.length).toBeGreaterThan(0);
  });

  it('should reject empty line items', () => {
    const input = makeTestInput({ lineItems: [] });
    const errors = validateOrder(input);
    expect(errors).toContain('At least one line item is required');
  });

  it('should reject negative quantity', () => {
    const input = makeTestInput({
      lineItems: [{ productId: 'PROD-1', quantity: -1, unitPrice: 10 }],
    });
    const errors = validateOrder(input);
    expect(errors.length).toBeGreaterThan(0);
  });

  it('should reject negative price', () => {
    const input = makeTestInput({
      lineItems: [{ productId: 'PROD-1', quantity: 1, unitPrice: -10 }],
    });
    const errors = validateOrder(input);
    expect(errors.length).toBeGreaterThan(0);
  });

});

// --- createOrder tests ---

describe('createOrder', () => {
  it('should create an order and return confirmation', async () => {
    const db = makeMockDb();
    (db.query as jest.Mock)
      .mockResolvedValueOnce({ rows: [defaultCustomer] }) // customer lookup
      .mockResolvedValueOnce({ rows: [] }) // order insert
      .mockResolvedValueOnce({ rows: [] }) // item insert 1
      .mockResolvedValueOnce({ rows: [] }); // item insert 2

    const discountService = makeMockDiscountService();
    const input = makeTestInput();

    const result = await createOrder(input, { db, discountService });

    expect(result).toBeTruthy();
    expect(result.status).toBe('confirmed');
    expect(result.total).toBe(100);
  });

  it('should throw on validation failure', async () => {
    const db = makeMockDb();
    const discountService = makeMockDiscountService();
    const input = makeTestInput({ customerId: '' });

    await expect(
      createOrder(input, { db, discountService }),
    ).rejects.toThrow('Validation failed');
  });

  it('should throw when customer not found', async () => {
    const db = makeMockDb();
    (db.query as jest.Mock).mockResolvedValueOnce({ rows: [] });

    const discountService = makeMockDiscountService();
    const input = makeTestInput();

    await expect(
      createOrder(input, { db, discountService }),
    ).rejects.toThrow('Customer not found');
  });

  it('should throw when total exceeds credit limit', async () => {
    const lowCreditCustomer = { ...defaultCustomer, creditLimit: 10 };
    const db = makeMockDb();
    (db.query as jest.Mock).mockResolvedValueOnce({
      rows: [lowCreditCustomer],
    });

    const discountService = makeMockDiscountService();
    const input = makeTestInput();

    await expect(
      createOrder(input, { db, discountService }),
    ).rejects.toThrow('exceeds credit limit');
  });

  it('should apply discount when code is provided', async () => {
    const db = makeMockDb();
    (db.query as jest.Mock)
      .mockResolvedValueOnce({ rows: [defaultCustomer] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] });

    const discountService: DiscountService = {
      getDiscount: jest.fn().mockResolvedValue({ percentage: 10 }),
    };

    const input = makeTestInput({ discountCode: 'SAVE10' });
    const result = await createOrder(input, { db, discountService });

    expect(result.total).toBe(90);
  });
});

// --- getOrders tests ---

describe('getOrders', () => {
  it('should retrieve orders for a customer', async () => {
    const mockOrders = [
      {
        id: 'ORD-1',
        customerId: 'CUST-1',
        total: 100,
        status: 'confirmed',
        createdAt: new Date(),
      },
    ];
    const db = makeMockDb();
    (db.query as jest.Mock).mockResolvedValueOnce({ rows: mockOrders });

    const orders = await getOrders('CUST-1', 'created_at', { db });

    expect(orders).toHaveLength(1);
    expect(orders[0].id).toBe('ORD-1');
  });

  it('should return empty array when no orders found', async () => {
    const db = makeMockDb();
    const orders = await getOrders('CUST-UNKNOWN', 'created_at', { db });
    expect(orders).toHaveLength(0);
  });

});

// --- logOrderError tests ---

describe('logOrderError', () => {
  it('should log error context', () => {
    const spy = jest.spyOn(console, 'log').mockImplementation();
    const error = new Error('Something went wrong');
    const input = makeTestInput();

    logOrderError(error, defaultCustomer, input);

    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });

});
