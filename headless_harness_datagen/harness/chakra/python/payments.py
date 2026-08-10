"""
Payments backend for Chakra - End-to-End Payment Processing System

This module provides a complete payment processing solution that can be integrated
with the Chakra assistant framework.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    CRYPTO = "crypto"


@dataclass
class Payment:
    """Payment record data structure"""
    id: str
    amount: float
    currency: str
    status: PaymentStatus
    payment_method: PaymentMethod
    customer_id: str
    description: str
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class PaymentProcessor:
    """Core payment processing logic"""

    def __init__(self):
        self.payments: Dict[str, Payment] = {}

    def create_payment(self, amount: float, currency: str, payment_method: PaymentMethod,
                      customer_id: str, description: str, metadata: Optional[Dict[str, Any]] = None) -> Payment:
        """Create a new payment"""
        payment_id = str(uuid.uuid4())
        now = datetime.now()

        payment = Payment(
            id=payment_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
            payment_method=payment_method,
            customer_id=customer_id,
            description=description,
            created_at=now,
            updated_at=now,
            metadata=metadata
        )

        self.payments[payment_id] = payment
        return payment

    def process_payment(self, payment_id: str) -> Payment:
        """Process a payment (simulated)"""
        if payment_id not in self.payments:
            raise ValueError(f"Payment {payment_id} not found")

        payment = self.payments[payment_id]

        # Simulate payment processing
        payment.status = PaymentStatus.PROCESSING
        payment.updated_at = datetime.now()

        # In a real implementation, this would call external payment gateway APIs
        # For now, we'll simulate success/failure based on amount
        if payment.amount > 0:
            payment.status = PaymentStatus.COMPLETED
        else:
            payment.status = PaymentStatus.FAILED

        payment.updated_at = datetime.now()
        return payment

    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Retrieve a payment by ID"""
        return self.payments.get(payment_id)

    def list_payments(self, customer_id: str = None, status: PaymentStatus = None) -> List[Payment]:
        """List payments, optionally filtered by customer or status"""
        payments = list(self.payments.values())

        if customer_id:
            payments = [p for p in payments if p.customer_id == customer_id]

        if status:
            payments = [p for p in payments if p.status == status]

        return payments

    def cancel_payment(self, payment_id: str) -> Payment:
        """Cancel a pending payment"""
        if payment_id not in self.payments:
            raise ValueError(f"Payment {payment_id} not found")

        payment = self.payments[payment_id]

        if payment.status != PaymentStatus.PENDING:
            raise ValueError(f"Cannot cancel payment {payment_id} - status is {payment.status.value}")

        payment.status = PaymentStatus.CANCELLED
        payment.updated_at = datetime.now()
        return payment


class PaymentBackend:
    """Main entry point for payment operations"""

    def __init__(self):
        self.processor = PaymentProcessor()

    def handle_payment_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a payment request from the assistant

        Expected request_data format:
        {
            "amount": float,
            "currency": str,
            "payment_method": str (enum value),
            "customer_id": str,
            "description": str,
            "metadata": dict (optional)
        }
        """
        try:
            # Validate required fields
            required_fields = ["amount", "currency", "payment_method", "customer_id", "description"]
            for field in required_fields:
                if field not in request_data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }

            # Parse payment method
            try:
                payment_method = PaymentMethod(request_data["payment_method"])
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid payment method: {request_data['payment_method']}"
                }

            # Create payment
            payment = self.processor.create_payment(
                amount=request_data["amount"],
                currency=request_data["currency"],
                payment_method=payment_method,
                customer_id=request_data["customer_id"],
                description=request_data["description"],
                metadata=request_data.get("metadata")
            )

            # Process payment
            processed_payment = self.processor.process_payment(payment.id)

            return {
                "success": True,
                "payment": {
                    "id": processed_payment.id,
                    "status": processed_payment.status.value,
                    "amount": processed_payment.amount,
                    "currency": processed_payment.currency,
                    "description": processed_payment.description,
                    "created_at": processed_payment.created_at.isoformat(),
                    "updated_at": processed_payment.updated_at.isoformat()
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get the status of a specific payment"""
        try:
            payment = self.processor.get_payment(payment_id)
            if not payment:
                return {
                    "success": False,
                    "error": f"Payment {payment_id} not found"
                }

            return {
                "success": True,
                "payment": {
                    "id": payment.id,
                    "status": payment.status.value,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "description": payment.description,
                    "created_at": payment.created_at.isoformat(),
                    "updated_at": payment.updated_at.isoformat()
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def list_customer_payments(self, customer_id: str, status: str = None) -> Dict[str, Any]:
        """List all payments for a customer"""
        try:
            status_enum = None
            if status:
                status_enum = PaymentStatus(status)

            payments = self.processor.list_payments(customer_id=customer_id, status=status_enum)

            return {
                "success": True,
                "payments": [
                    {
                        "id": p.id,
                        "status": p.status.value,
                        "amount": p.amount,
                        "currency": p.currency,
                        "description": p.description,
                        "created_at": p.created_at.isoformat(),
                        "updated_at": p.updated_at.isoformat()
                    } for p in payments
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global instance for easy access
payment_backend = PaymentBackend()


def handle_payment_request(request_data: Dict[str, Any]) -> str:
    """
    Convenience function to handle payment requests and return JSON response
    """
    result = payment_backend.handle_payment_request(request_data)
    return json.dumps(result, indent=2)


def get_payment_status(payment_id: str) -> str:
    """
    Convenience function to get payment status and return JSON response
    """
    result = payment_backend.get_payment_status(payment_id)
    return json.dumps(result, indent=2)


def list_customer_payments(customer_id: str, status: str = None) -> str:
    """
    Convenience function to list customer payments and return JSON response
    """
    result = payment_backend.list_customer_payments(customer_id, status)
    return json.dumps(result, indent=2)