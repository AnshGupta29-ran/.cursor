"""
Payment Tool for Chakra Assistant

This tool allows the Chakra assistant to process payments through the payments backend.
"""

import json
from typing import Dict, Any
import sys
import os

# Add current directory to Python path to enable imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from payments import payment_backend


class PaymentTool:
    """Chakra-compatible payment processing tool"""

    def __init__(self):
        self.name = "payment_processor"
        self.description = (
            "Process payments for customers. Use this tool when a user wants to make a payment. "
            "You must collect all required information before using this tool."
        )
        self.parameters = {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The action to perform: 'create', 'status', or 'list'",
                    "enum": ["create", "status", "list"]
                },
                "amount": {
                    "type": "number",
                    "description": "Payment amount (required for 'create' action)"
                },
                "currency": {
                    "type": "string",
                    "description": "Currency code (e.g., 'USD', 'EUR') (required for 'create' action)"
                },
                "payment_method": {
                    "type": "string",
                    "description": "Payment method (credit_card, debit_card, paypal, bank_transfer, crypto) (required for 'create' action)"
                },
                "customer_id": {
                    "type": "string",
                    "description": "Customer identifier (required for 'create' and 'list' actions)"
                },
                "description": {
                    "type": "string",
                    "description": "Description of the payment (required for 'create' action)"
                },
                "payment_id": {
                    "type": "string",
                    "description": "Payment ID (required for 'status' action)"
                },
                "status_filter": {
                    "type": "string",
                    "description": "Filter payments by status (optional for 'list' action)"
                }
            },
            "required": ["action", "customer_id"],
            "additionalProperties": False
        }

    def execute(self, arguments: Dict[str, Any]) -> str:
        """
        Execute the payment operation based on arguments

        Args:
            arguments: Dictionary containing tool arguments

        Returns:
            JSON string response with result
        """
        try:
            action = arguments.get("action")

            if action == "create":
                # Validate required fields for creation
                required_fields = ["amount", "currency", "payment_method", "description"]
                for field in required_fields:
                    if field not in arguments:
                        return json.dumps({
                            "success": False,
                            "error": f"Missing required field '{field}' for payment creation"
                        })

                request_data = {
                    "amount": arguments["amount"],
                    "currency": arguments["currency"],
                    "payment_method": arguments["payment_method"],
                    "customer_id": arguments["customer_id"],
                    "description": arguments["description"],
                    "metadata": arguments.get("metadata", {})
                }

                result = payment_backend.handle_payment_request(request_data)

            elif action == "status":
                # Validate required fields for status check
                if "payment_id" not in arguments:
                    return json.dumps({
                        "success": False,
                        "error": "Missing required field 'payment_id' for status check"
                    })

                result = payment_backend.get_payment_status(arguments["payment_id"])

            elif action == "list":
                # For listing payments
                status_filter = arguments.get("status_filter")
                result = payment_backend.list_customer_payments(
                    customer_id=arguments["customer_id"],
                    status=status_filter
                )
            else:
                return json.dumps({
                    "success": False,
                    "error": f"Unknown action: {action}"
                })

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            })


# Create a singleton instance
payment_tool = PaymentTool()