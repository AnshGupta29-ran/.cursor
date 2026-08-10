# Chakra Payments Backend

An end-to-end payment processing system designed to integrate with the Chakra assistant framework.

## Overview

This module provides a complete payment processing solution that can be used by the Chakra assistant to handle financial transactions. It includes:

- Payment creation and processing
- Payment status tracking
- Customer payment history
- Tool integration for assistant use

## Features

- **Payment Processing**: Create, process, and track payments
- **Multiple Payment Methods**: Support for credit cards, debit cards, PayPal, bank transfers, and crypto
- **Status Management**: Track payments through PENDING → PROCESSING → COMPLETED/FAILED/CANCELLED states
- **Customer Management**: Organize payments by customer ID
- **Tool Integration**: Ready-to-use tool for Chakra assistant

## Installation

The payments backend is included in the Python package. No additional installation is required beyond the existing setup.

## Usage

### Basic Usage

```python
from payments import PaymentBackend

# Initialize the backend
backend = PaymentBackend()

# Create a payment
request_data = {
    "amount": 99.99,
    "currency": "USD",
    "payment_method": "credit_card",
    "customer_id": "cust_001",
    "description": "Premium subscription"
}

result = backend.handle_payment_request(request_data)
```

### Using with Chakra Assistant

The payment tool can be integrated directly into the Chakra assistant:

```python
from payment_tool import payment_tool

# The tool will be automatically available to the assistant
# when configured properly
```

## API Reference

### PaymentBackend Methods

- `handle_payment_request(request_data)`: Process a new payment request
- `get_payment_status(payment_id)`: Get the status of a specific payment
- `list_customer_payments(customer_id, status_filter)`: List all payments for a customer

### Payment Statuses

- `PENDING`: Payment has been created but not yet processed
- `PROCESSING`: Payment is being processed
- `COMPLETED`: Payment was successful
- `FAILED`: Payment failed during processing
- `CANCELLED`: Payment was cancelled before processing

### Payment Methods

- `CREDIT_CARD`
- `DEBIT_CARD`
- `PAYPAL`
- `BANK_TRANSFER`
- `CRYPTO`

## Security Considerations

- All payment data is stored in memory (in production, use persistent storage)
- Sensitive information should be handled securely
- Real implementations would integrate with secure payment gateways
- Always validate input data before processing payments

## Testing

Run tests with:

```bash
python -m pytest python/tests/test_payments.py -v
```

## Demo

Run the demo script to see the system in action:

```bash
python python/demo_payments.py
```