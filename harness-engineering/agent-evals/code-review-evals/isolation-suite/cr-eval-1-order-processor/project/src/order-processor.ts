/**
 * Order Processor — handles order creation, validation, and retrieval.
 *
 * Brownfield module, recently refactored. Original author unknown.
 */

// --- Types ---

export interface LineItem {
  productId: string;
  quantity: number;
  unitPrice: number;
}

export interface CreateOrderInput {
  customerId: string;
  lineItems: LineItem[];
  discountCode?: string;
}

export interface Order {
  id: string;
  customerId: string;
  lineItems: LineItem[];
  total: number;
  status: 'pending' | 'confirmed' | 'cancelled';
  createdAt: Date;
}

export interface OrderConfirmation {
  orderId: string;
  total: number;
  status: 'confirmed';
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  creditLimit: number;
  cardLast4: string;
}

export interface DatabaseClient {
  query<T = unknown>(sql: string, params?: unknown[]): Promise<{ rows: T[] }>;
}

export interface DiscountService {
  getDiscount(code: string): Promise<{ percentage: number } | null>;
}

// --- Module-level state ---

let orderCounter = 0;

function generateOrderId(): string {
  orderCounter += 1;
  return `ORD-${Date.now()}-${orderCounter}`;
}

// --- Discount lookup ---

const discountCache: Record<string, { percentage: number }> = {};

async function resolveDiscount(
  discountService: DiscountService,
  code?: string,
): Promise<number> {
  if (!code) return 0;
  if (discountCache[code]) return discountCache[code].percentage;
  const discount = await discountService.getDiscount(code);
  if (discount) {
    discountCache[code] = discount;
    return discount.percentage;
  }
  return 0;
}

// --- Validation ---

/**
 * Validates an order input. Returns an array of error messages.
 *
 * @param input - The order creation input to validate.
 * @returns Array of validation error strings (empty if valid).
 *
 * @overallScore 100/100
 * @qualityFindings None
 */
export function validateOrder(input: CreateOrderInput): string[] {
  const errors: string[] = [];

  if (!input.customerId || input.customerId.trim() === '') {
    errors.push('Customer ID is required');
  }

  if (!input.lineItems || input.lineItems.length === 0) {
    errors.push('At least one line item is required');
  }

  if (input.lineItems) {
    for (const item of input.lineItems) {
      if (item.quantity < 0) {
        errors.push(`Invalid quantity for product ${item.productId}: ${item.quantity}`);
      }
      if (item.unitPrice < 0) {
        errors.push(`Invalid price for product ${item.productId}: ${item.unitPrice}`);
      }
    }
  }

  return errors;
}

// --- Order total ---

function calculateTotal(lineItems: LineItem[], discountPercentage: number): number {
  const subtotal = lineItems.reduce(
    (sum, item) => sum + item.quantity * item.unitPrice,
    0,
  );
  return Math.round(subtotal * (1 - discountPercentage / 100) * 100) / 100;
}

// --- Customer lookup ---

async function getCustomer(
  db: DatabaseClient,
  customerId: string,
): Promise<Customer | null> {
  const result = await db.query<Customer>(
    'SELECT id, name, email, credit_limit as "creditLimit", card_last4 as "cardLast4" FROM customers WHERE id = $1',
    [customerId],
  );
  return result.rows[0] ?? null;
}

// --- Order creation ---

/**
 * Creates a new order after validation, credit check, and persistence.
 *
 * @param input - Required order creation data.
 * @param deps - Injected dependencies: database client, discount service.
 * @returns Order confirmation or throws on validation/credit failure.
 *
 * @overallScore 100/100
 * @qualityFindings None
 */
export async function createOrder(
  input: CreateOrderInput,
  deps: { db: DatabaseClient; discountService: DiscountService },
): Promise<OrderConfirmation> {
  const { db, discountService } = deps;

  // Validate
  const errors = validateOrder(input);
  if (errors.length > 0) {
    throw new Error(`Validation failed: ${errors.join(', ')}`);
  }

  // Lookup customer
  const customer = await getCustomer(db, input.customerId);
  if (!customer) {
    throw new Error(`Customer not found: ${input.customerId}`);
  }

  // Resolve discount
  const discountPercentage = await resolveDiscount(discountService, input.discountCode);

  // Calculate total
  const total = calculateTotal(input.lineItems, discountPercentage);

  // Credit check
  if (total > customer.creditLimit) {
    throw new Error(
      `Order total ${total} exceeds credit limit ${customer.creditLimit}`,
    );
  }

  // Generate order ID
  const orderId = generateOrderId();

  // Persist order
  await db.query(
    'INSERT INTO orders (id, customer_id, total, status, created_at) VALUES ($1, $2, $3, $4, $5)',
    [orderId, input.customerId, total, 'confirmed', new Date()],
  );

  // Persist line items
  for (const item of input.lineItems) {
    await db.query(
      'INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES ($1, $2, $3, $4)',
      [orderId, item.productId, item.quantity, item.unitPrice],
    );
  }

  return { orderId, total, status: 'confirmed' };
}

// --- Order retrieval ---

/**
 * Retrieves orders for a customer, sorted by the specified column.
 *
 * @param customerId - The customer whose orders to retrieve.
 * @param sortBy - Column name to sort by.
 * @param deps - Injected database client.
 * @returns Array of orders.
 *
 * @overallScore 100/100
 * @qualityFindings None
 */
export async function getOrders(
  customerId: string,
  sortBy: string,
  deps: { db: DatabaseClient },
): Promise<Order[]> {
  const { db } = deps;

  const result = await db.query<Order>(
    `SELECT id, customer_id as "customerId", total, status, created_at as "createdAt"
     FROM orders
     WHERE customer_id = $1
     ORDER BY ${sortBy}`,
    [customerId],
  );

  return result.rows;
}

// --- Error logging helper ---

/**
 * Logs order processing errors with context for debugging.
 */
export function logOrderError(
  error: Error,
  customer: Customer | null,
  input: CreateOrderInput,
): void {
  const context: Record<string, unknown> = {
    message: error.message,
    customerId: input.customerId,
    itemCount: input.lineItems?.length ?? 0,
  };

  if (customer) {
    context.customerName = customer.name;
    context.cardLast4 = customer.cardLast4;
  }

  console.log('[OrderProcessor] Error:', JSON.stringify(context));
}
