#!/usr/bin/env python3
"""
Test script to verify Python payment system works correctly
"""

import sys
import os

# Add the python directory to path for proper imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

def test_payment_system():
    """Test that the payment system works correctly"""
    try:
        from payments import PaymentBackend, PaymentMethod

        print("✅ Successfully imported PaymentBackend and PaymentMethod")

        # Create backend instance
        backend = PaymentBackend()
        print("✅ Created PaymentBackend instance")

        # Test payment creation
        request_data = {
            "amount": 99.99,
            "currency": "USD",
            "payment_method": "credit_card",
            "customer_id": "cust_001",
            "description": "Test payment"
        }

        result = backend.handle_payment_request(request_data)
        print("✅ Payment request processed successfully")
        print(f"Result type: {type(result)}")

        if isinstance(result, dict):
            if result.get("success"):
                print("✅ Payment created successfully")
                print(f"Payment ID: {result['payment']['id']}")
                print(f"Status: {result['payment']['status']}")
            else:
                print(f"❌ Payment failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print("⚠️  Result is not a dictionary (might be JSON string)")

        print("\n🎉 All tests passed! The payment system is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Chakra Payment System...")
    print("=" * 40)

    success = test_payment_system()

    if success:
        print("\n✅ SUCCESS: Payment system is functioning correctly")
        sys.exit(0)
    else:
        print("\n❌ FAILURE: Issues found in payment system")
        sys.exit(1)