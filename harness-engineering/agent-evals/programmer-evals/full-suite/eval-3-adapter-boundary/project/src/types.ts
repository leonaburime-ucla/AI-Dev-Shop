export interface PaymentSDK {
  charge(amount: number, currency: string, cardToken: string): Promise<{ transactionId: string; status: string }>;
  refund(transactionId: string, amount: number): Promise<{ refundId: string; status: string }>;
  getTransaction(transactionId: string): Promise<{ transactionId: string; amount: number; status: string; createdAt: string }>;
}
