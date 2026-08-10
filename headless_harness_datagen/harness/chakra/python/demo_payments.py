"""
Demo script for the payments backend functionality
"""

import json
from payments import PaymentBackend, PaymentMethod

def main():
    print("=== Chakra Payments Backend Demo ===\n")

    # Initialize the payment backend
    backend = PaymentBackend()

    # Example 1: Create and process a payment
    print("1. Creating a new payment...")
    request_data = {
        "amount": 99.99,
        "currency": "USD",
        "payment_method": "credit_card",
        "customer_id": "cust_001",
        "description": "Premium subscription for 1 month",
        "metadata": {
            "product": "premium_plan",
            "billing_cycle": "monthly"
        }
    }

    result = backend.handle_payment_request(request_data)
    payment_response = json.loads(result)

    if payment_response["success"]:
        payment = payment_response["payment"]
        print(f"✅ Payment created successfully!")
        print(f"   ID: {payment['id']}")
        print(f"   Status: {payment['status']}")
        print(f"   Amount: {payment['amount']} {payment['currency']}")
        print(f"   Description: {payment['description']}")
        print(f"   Created: {payment['created_at']}")
        print()
    else:
        print(f"❌ Failed to create payment: {payment_response['error']}")
        print()

    # Example 2: Check payment status
    print("2. Checking payment status...")
    if payment_response["success"]:
        payment_id = payment["id"]
        status_result = backend.get_payment_status(payment_id)
        status_response = json.loads(status_result)

        if status_response["success"]:
            payment_status = status_response["payment"]
            print(f"✅ Payment status: {payment_status['status']}")
            print(f"   Updated: {payment_status['updated_at']}")
            print()
        else:
            print(f"❌ Failed to get payment status: {status_response['error']}")
            print()

    # Example 3: List customer payments
    print("3. Listing customer payments...")
    list_result = backend.list_customer_payments("cust_001")
    list_response = json.loads(list_result)

    if list_response["success"]:
        payments = list_response["payments"]
        print(f"Found {len(payments)} payments for customer cust_001:")
        for payment in payments:
            print(f"   - {payment['id']}: {payment['amount']} {payment['currency']} ({payment['status']})")
        print()
    else:
        print(f"❌ Failed to list payments: {list_response['error']}")
        print()

if __name__ == "__main__":
    main()