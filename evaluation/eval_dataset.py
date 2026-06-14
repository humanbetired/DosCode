EVAL_DATASET = [
    {
        "id": "eval_001",
        "name": "Hardcoded credentials",
        "description": "File dengan hardcoded API key dan password",
        "code": '''
import requests

API_KEY = "sk-prod-abc123xyz789"
PASSWORD = "admin123"

def get_data():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    return requests.get("https://api.example.com/data", headers=headers)
''',
        "expected_issues": {
            "security": ["hardcoded_secret", "hardcoded_password"],
            "lint": [],
            "complexity": [],
        },
        "expected_severity": "critical",
        "expected_verdict": "REJECT",
    },
    {
        "id": "eval_002",
        "name": "High complexity function",
        "description": "Function dengan cyclomatic complexity sangat tinggi",
        "code": '''
def process_order(order, user, inventory, payment, shipping):
    if order:
        if user:
            if user.get("verified"):
                if inventory:
                    if inventory.get("available"):
                        if payment:
                            if payment.get("valid"):
                                if shipping:
                                    if shipping.get("address"):
                                        if order.get("items"):
                                            return "processed"
                                        else:
                                            return "no items"
                                    else:
                                        return "no address"
                                else:
                                    return "no shipping"
                            else:
                                return "invalid payment"
                        else:
                            return "no payment"
                    else:
                        return "out of stock"
                else:
                    return "no inventory"
            else:
                return "unverified"
        else:
            return "no user"
    else:
        return "no order"
''',
        "expected_issues": {
            "security": [],
            "lint": ["too_many_parameters"],
            "complexity": ["high_cyclomatic_complexity"],
        },
        "expected_severity": "high",
        "expected_verdict": "REQUEST CHANGES",
    },
    {
        "id": "eval_003",
        "name": "Dangerous eval usage",
        "description": "Penggunaan eval() dengan input eksternal",
        "code": '''
from flask import request

def calculate():
    user_input = request.args.get("formula")
    result = eval(user_input)  # dangerous!
    return str(result)

def execute_command(cmd):
    import subprocess
    output = subprocess.run(cmd, shell=True, capture_output=True)
    return output.stdout
''',
        "expected_issues": {
            "security": ["eval_usage", "shell_injection"],
            "lint": [],
            "complexity": [],
        },
        "expected_severity": "critical",
        "expected_verdict": "REJECT",
    },
    {
        "id": "eval_004",
        "name": "Clean code",
        "description": "File yang bersih — harusnya APPROVE",
        "code": '''
import os
from typing import Optional


MAX_RETRIES = 3


def fetch_user(user_id: str) -> Optional[dict]:
    """Fetch user data by ID from environment-configured endpoint.
    
    Args:
        user_id: The unique identifier for the user.
        
    Returns:
        User data dict or None if not found.
    """
    api_url = os.environ.get("API_URL", "http://localhost:8000")
    
    if not user_id:
        return None
    
    return {"id": user_id, "url": api_url}


def calculate_total(items: list[dict]) -> float:
    """Calculate total price from list of items."""
    return sum(item.get("price", 0.0) for item in items)
''',
        "expected_issues": {
            "security": [],
            "lint": [],
            "complexity": [],
        },
        "expected_severity": "low",
        "expected_verdict": "APPROVE",
    },
    {
        "id": "eval_005",
        "name": "Style violations",
        "description": "Naming convention dan style issues",
        "code": '''
import os, sys, json

def ProcessData(inputData, secondParam, thirdParam, fourthParam, fifthParam):
    X = inputData
    Y = secondParam
    unusedVar = "this is never used"
    
    myList = []
    for i in range(len(X)):
        myList.append(X[i])
    
    return myList

class myProcessor:
    def __init__(self):
        self.Val=1
        self.Data=[]
    
    def doProcess(self):
        return self.Val
''',
        "expected_issues": {
            "security": [],
            "lint": ["naming_convention", "unused_import", "unused_variable"],
            "complexity": [],
        },
        "expected_severity": "medium",
        "expected_verdict": "REQUEST CHANGES",
    },
]