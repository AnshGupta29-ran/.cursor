"""
Simple demo script for the payments backend functionality
"""

import json
from payments import PaymentBackend

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
    # The method already returns a dict, no need to parse JSON
    payment_response = result

    if payment_response["success"]:
        payment = payment_response["payment"]
        print(f"✅ Payment created successfully!")
        print(f"   ID: {payment['id']}")
        print(f"   Status: {payment['status']}")
        print(f"   Amount: {payment['amount']} {payment['currency']}")
        print(f"   Description: {payment['description']}")
        print(f"   Created: {payment['created_at']}")
        print()

        # Check payment status
        print("2. Checking payment status...")
        status_result = backend.get_payment_status(payment['id'])
        # The method already returns a dict, no need to parse JSON
        status_response = status_result

        if status_response["success"]:
            payment_status = status_response["payment"]
            print(f"✅ Payment status: {payment_status['status']}")
            print(f"   Updated: {payment_status['updated_at']}")
            print()
        else:
            print(f"❌ Failed to get payment status: {status_response['error']}")
            print()

        # List customer payments
        print("3. Listing customer payments...")
        list_result = backend.list_customer_payments("cust_001")
        # The method already returns a dict, no need to parse JSON
        list_response = list_result

        if list_response["success"]:
            payments = list_response["payments"]
            print(f"Found {len(payments)} payments for customer cust_001:")
            for payment in payments:
                print(f"   - {payment['id']}: {payment['amount']} {payment['currency']} ({payment['status']})")
            print()
        else:
            print(f"❌ Failed to list payments: {list_response['error']}")
            print()
    else:
        print(f"❌ Failed to create payment: {payment_response['error']}")
        print()

if __name__ == "__main__":
    main()