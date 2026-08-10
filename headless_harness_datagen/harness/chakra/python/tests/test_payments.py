"""
Tests for the payments backend
"""

import unittest
from datetime import datetime
from payments import PaymentProcessor, PaymentStatus, PaymentMethod, PaymentBackend


class TestPaymentProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = PaymentProcessor()

    def test_create_payment(self):
        """Test creating a payment"""
        payment = self.processor.create_payment(
            amount=100.00,
            currency="USD",
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_id="cust_123",
            description="Test payment"
        )

        self.assertEqual(payment.amount, 100.00)
        self.assertEqual(payment.currency, "USD")
        self.assertEqual(payment.payment_method, PaymentMethod.CREDIT_CARD)
        self.assertEqual(payment.customer_id, "cust_123")
        self.assertEqual(payment.description, "Test payment")
        self.assertEqual(payment.status, PaymentStatus.PENDING)

    def test_process_payment_success(self):
        """Test processing a successful payment"""
        payment = self.processor.create_payment(
            amount=100.00,
            currency="USD",
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_id="cust_123",
            description="Test payment"
        )

        processed = self.processor.process_payment(payment.id)

        self.assertEqual(processed.status, PaymentStatus.COMPLETED)

    def test_process_payment_failure(self):
        """Test processing a failed payment"""
        payment = self.processor.create_payment(
            amount=0.00,
            currency="USD",
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_id="cust_123",
            description="Test payment"
        )

        processed = self.processor.process_payment(payment.id)

        self.assertEqual(processed.status, PaymentStatus.FAILED)

    def test_get_payment(self):
        """Test retrieving a payment"""
        payment = self.processor.create_payment(
            amount=100.00,
            currency="USD",
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_id="cust_123",
            description="Test payment"
        )

        retrieved = self.processor.get_payment(payment.id)
        self.assertEqual(retrieved, payment)

    def test_list_payments(self):
        """Test listing payments"""
        # Create two payments for same customer
        payment1 = self.processor.create_payment(
            amount=100.00,
            currency="USD",
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_id="cust_123",
            description="Test payment 1"
        )

        payment2 = self.processor.create_payment(
            amount=200.00,
            currency="USD",
            payment_method=PaymentMethod.PAYPAL,
            customer_id="cust_123",
            description="Test payment 2"
        )

        # Process both payments to make them completed
        self.processor.process_payment(payment1.id)
        self.processor.process_payment(payment2.id)

        # List all payments for this customer
        payments = self.processor.list_payments(customer_id="cust_123")
        self.assertEqual(len(payments), 2)

        # List by status
        completed_payments = self.processor.list_payments(status=PaymentStatus.COMPLETED)
        self.assertEqual(len(completed_payments), 2)  # Both are completed

    def test_cancel_payment(self):
        """Test cancelling a payment"""
        payment = self.processor.create_payment(
            amount=100.00,
            currency="USD",
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_id="cust_123",
            description="Test payment"
        )

        cancelled = self.processor.cancel_payment(payment.id)
        self.assertEqual(cancelled.status, PaymentStatus.CANCELLED)


class TestPaymentBackend(unittest.TestCase):
    def setUp(self):
        self.backend = PaymentBackend()

    def test_handle_payment_request_success(self):
        """Test handling a successful payment request"""
        request_data = {
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "credit_card",
            "customer_id": "cust_123",
            "description": "Test payment"
        }

        result = self.backend.handle_payment_request(request_data)
        # The method returns a dict, not JSON string
        result_dict = result

        self.assertTrue(result_dict["success"])
        self.assertEqual(result_dict["payment"]["status"], "completed")
        self.assertEqual(result_dict["payment"]["amount"], 100.00)

    def test_handle_payment_request_invalid_method(self):
        """Test handling a payment request with invalid method"""
        request_data = {
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "invalid_method",
            "customer_id": "cust_123",
            "description": "Test payment"
        }

        result = self.backend.handle_payment_request(request_data)
        # The method returns a dict, not JSON string
        result_dict = result

        self.assertFalse(result_dict["success"])
        self.assertIn("Invalid payment method", result_dict["error"])

    def test_handle_payment_request_missing_fields(self):
        """Test handling a payment request with missing fields"""
        request_data = {
            "amount": 100.00,
            "currency": "USD",
            # Missing payment_method, customer_id, description
        }

        result = self.backend.handle_payment_request(request_data)
        # The method returns a dict, not JSON string
        result_dict = result

        self.assertFalse(result_dict["success"])
        self.assertIn("Missing required field", result_dict["error"])


if __name__ == '__main__':
    unittest.main()