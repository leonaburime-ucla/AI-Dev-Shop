# Order Processor — Project Brief

## Overview

A brownfield order processing module for an e-commerce platform. The module
receives orders from an API gateway, validates them, persists them to a
PostgreSQL database, and returns order confirmations.

This is an existing codebase that was "refactored and cleaned up" by the
Programmer agent. Code Review should assess the current state of the code.

## Requirements

### Functional Requirements

1. **Order creation**: Accept an order containing a customer ID, a list of line
   items (product ID, quantity, unit price), and an optional discount code.
2. **Validation**: Reject orders where:
   - Customer ID is missing or empty
   - Line items array is empty
   - Any line item has a quantity of 0 or negative quantity
   - Any line item has a negative unit price
   - Total exceeds the customer's credit limit
3. **Persistence**: Save valid orders to the `orders` table and each line item
   to the `order_items` table.
4. **Order total**: Computed as `SUM(quantity * unitPrice)` minus any applicable
   discount.
5. **Sorting**: Orders can be retrieved sorted by any column the caller
   specifies.
6. **Customer lookup**: When creating an order, look up the customer record to
   verify credit limit.

### Non-Functional Requirements

1. Database queries should be efficient — avoid per-item queries when batch
   operations are available.
2. All user inputs must be validated and sanitized before use in queries.
3. No sensitive customer data (credit card numbers, SSNs) should appear in
   application logs.

### Acceptance Criteria

- AC-1: Orders with valid data are persisted and a confirmation with order ID is
  returned.
- AC-2: Orders with 0 quantity line items are rejected with a clear error
  message.
- AC-3: Orders exceeding credit limit are rejected before persistence.
- AC-4: Order listing supports caller-specified sort columns.
- AC-5: No N+1 query patterns in the order creation path.
- AC-6: No sensitive data in logs.

## Spec Hash

`spec-order-proc-v2-abc123`
