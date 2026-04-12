# oracle/services/gstn_client.py
"""
GSTN API Client
Verifies invoices and GST compliance for MSMEs
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import hashlib
import hmac
import base64

from app.config import settings

logger = logging.getLogger(__name__)


class GSTNAuthenticator:
    """Handles GSTN API authentication"""
    
    def __init__(self):
        self.client_id = settings.GSTN_CLIENT_ID
        self.client_secret = settings.GSTN_CLIENT_SECRET
        self.api_key = settings.GSTN_API_KEY
        self.base_url = settings.GSTN_API_URL
        
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
    
    async def get_access_token(self) -> str:
        """
        Get OAuth2 access token from GSTN
        
        Returns:
            Access token string
        """
        # Check if token is still valid
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry:
                return self.access_token
        
        logger.info("Requesting new GSTN access token")
        
        # OAuth2 token endpoint
        token_url = f"{self.base_url}/oauth/token"
        
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                self.access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)  # Default 1 hour
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
                
                logger.info("GSTN access token obtained successfully")
                return self.access_token
        
        except Exception as e:
            logger.error(f"Failed to get GSTN access token: {e}")
            raise


class GSTNClient:
    """
    Client for GSTN API operations
    
    NOTE: This is a simplified implementation.
    Real GSTN API requires:
    1. Proper registration on GST portal
    2. API subscription
    3. Digital signature certificate
    4. Whitelisted IP addresses
    """
    
    def __init__(self):
        self.authenticator = GSTNAuthenticator()
        self.base_url = settings.GSTN_API_URL
    
    async def verify_gstn(self, gstn: str) -> Dict:
        """
        Verify if GSTN is valid and active
        
        Args:
            gstn: 15-character GSTN number
        
        Returns:
            Dictionary with verification details
        """
        logger.info(f"Verifying GSTN: {gstn}")
        
        if not self._validate_gstn_format(gstn):
            return {
                "valid": False,
                "error": "Invalid GSTN format"
            }
        
        try:
            token = await self.authenticator.get_access_token()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.base_url}/taxpayers/{gstn}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                
                return {
                    "valid": True,
                    "gstn": gstn,
                    "legal_name": data.get("lgnm"),
                    "trade_name": data.get("tradeNam"),
                    "status": data.get("sts"),
                    "registration_date": data.get("rgdt"),
                    "state_code": gstn[:2],
                    "entity_type": data.get("ctb"),
                    "address": data.get("pradr", {}).get("addr"),
                    "api_response": data
                }
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {
                    "valid": False,
                    "error": "GSTN not found"
                }
            logger.error(f"GSTN verification failed: {e}")
            raise
        
        except Exception as e:
            logger.error(f"Error verifying GSTN: {e}")
            raise
    
    async def get_invoices(
        self,
        gstn: str,
        from_date: str,
        to_date: str,
        invoice_type: str = "B2B"
    ) -> List[Dict]:
        """
        Get invoices for a GSTN in date range
        
        Args:
            gstn: GSTN number
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            invoice_type: Type of invoice (B2B, B2C, etc.)
        
        Returns:
            List of invoice dictionaries
        """
        logger.info(f"Fetching invoices for GSTN {gstn} from {from_date} to {to_date}")
        
        try:
            token = await self.authenticator.get_access_token()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "from_date": from_date,
                "to_date": to_date,
                "type": invoice_type
            }
            
            url = f"{self.base_url}/returns/{gstn}/invoices"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                invoices = data.get("invoices", [])
                
                logger.info(f"Found {len(invoices)} invoices")
                return invoices
        
        except Exception as e:
            logger.error(f"Error fetching invoices: {e}")
            raise
    
    async def verify_invoice(
        self,
        gstn: str,
        invoice_number: str,
        invoice_date: str,
        invoice_amount: float
    ) -> Dict:
        """
        Verify if an invoice exists and matches the provided details
        
        Args:
            gstn: Seller's GSTN
            invoice_number: Invoice number to verify
            invoice_date: Expected invoice date
            invoice_amount: Expected invoice amount
        
        Returns:
            Verification result dictionary
        """
        logger.info(f"Verifying invoice {invoice_number} for GSTN {gstn}")
        
        try:
            # Get invoices for the date range
            date_obj = datetime.strptime(invoice_date, "%Y-%m-%d")
            from_date = (date_obj - timedelta(days=7)).strftime("%Y-%m-%d")
            to_date = (date_obj + timedelta(days=7)).strftime("%Y-%m-%d")
            
            invoices = await self.get_invoices(gstn, from_date, to_date)
            
            # Search for matching invoice
            for invoice in invoices:
                if invoice.get("invoice_number") == invoice_number:
                    # Verify amount matches (with 1% tolerance)
                    api_amount = float(invoice.get("total_amount", 0))
                    amount_diff = abs(api_amount - invoice_amount)
                    amount_tolerance = invoice_amount * 0.01
                    
                    if amount_diff <= amount_tolerance:
                        return {
                            "verified": True,
                            "invoice_number": invoice_number,
                            "invoice_date": invoice.get("invoice_date"),
                            "invoice_amount": api_amount,
                            "buyer_gstn": invoice.get("buyer_gstn"),
                            "buyer_name": invoice.get("buyer_name"),
                            "match_status": "EXACT" if amount_diff == 0 else "WITHIN_TOLERANCE",
                            "api_response": invoice
                        }
                    else:
                        return {
                            "verified": False,
                            "error": "Amount mismatch",
                            "expected_amount": invoice_amount,
                            "actual_amount": api_amount,
                            "difference": amount_diff
                        }
            
            return {
                "verified": False,
                "error": "Invoice not found in GSTN records"
            }
        
        except Exception as e:
            logger.error(f"Error verifying invoice: {e}")
            raise
    
    def _validate_gstn_format(self, gstn: str) -> bool:
        """
        Validate GSTN format
        Format: 22AAAAA0000A1Z5 (15 characters)
        - 2 digits: State code
        - 10 characters: PAN
        - 1 character: Entity number
        - 1 character: Z (default)
        - 1 character: Checksum
        """
        if not gstn or len(gstn) != 15:
            return False
        
        # State code should be numeric
        if not gstn[:2].isdigit():
            return False
        
        # Next 10 characters should match PAN format
        pan_part = gstn[2:12]
        if not (pan_part[:5].isalpha() and 
                pan_part[5:9].isdigit() and 
                pan_part[9].isalpha()):
            return False
        
        # 13th character should be a digit
        if not gstn[12].isdigit():
            return False
        
        # 14th character should be 'Z'
        if gstn[13] != 'Z':
            return False
        
        # 15th character is checksum (alphanumeric)
        if not gstn[14].isalnum():
            return False
        
        return True


# ============================================
# MOCK GSTN CLIENT (for testing)
# ============================================

class MockGSTNClient:
    """
    Mock GSTN client for testing without actual API access
    """
    
    def __init__(self):
        logger.info("Using MOCK GSTN client")
        self.mock_data = {
            "27AABCU9603R1ZM": {
                "legal_name": "ABC Manufacturing Pvt Ltd",
                "trade_name": "ABC Mfg",
                "status": "Active",
                "registration_date": "2017-07-01"
            },
            "24AABCU9603R1ZM": {
                "legal_name": "XYZ Enterprises",
                "trade_name": "XYZ Ent",
                "status": "Active",
                "registration_date": "2018-03-15"
            }
        }
    
    async def verify_gstn(self, gstn: str) -> Dict:
        """Mock GSTN verification"""
        logger.info(f"[MOCK] Verifying GSTN: {gstn}")
        
        if gstn in self.mock_data:
            return {
                "valid": True,
                "gstn": gstn,
                **self.mock_data[gstn]
            }
        else:
            # Generate fake data for any valid format GSTN
            if len(gstn) == 15:
                return {
                    "valid": True,
                    "gstn": gstn,
                    "legal_name": f"Company {gstn[:5]}",
                    "trade_name": f"Trade {gstn[:5]}",
                    "status": "Active",
                    "registration_date": "2020-01-01"
                }
            else:
                return {
                    "valid": False,
                    "error": "Invalid GSTN format"
                }
    
    async def get_invoices(
        self,
        gstn: str,
        from_date: str,
        to_date: str,
        invoice_type: str = "B2B"
    ) -> List[Dict]:
        """Mock invoice fetching"""
        logger.info(f"[MOCK] Fetching invoices for {gstn}")
        
        # Generate 2-3 fake invoices
        import random
        num_invoices = random.randint(2, 3)
        
        invoices = []
        for i in range(num_invoices):
            invoices.append({
                "invoice_number": f"INV-{random.randint(1000, 9999)}",
                "invoice_date": from_date,
                "total_amount": random.randint(100000, 1000000),
                "buyer_gstn": "29AABCT1332L1Z5",
                "buyer_name": "Government Department"
            })
        
        return invoices
    
    async def verify_invoice(
        self,
        gstn: str,
        invoice_number: str,
        invoice_date: str,
        invoice_amount: float
    ) -> Dict:
        """Mock invoice verification"""
        logger.info(f"[MOCK] Verifying invoice {invoice_number}")
        
        # Simulate 80% success rate
        import random
        if random.random() < 0.8:
            return {
                "verified": True,
                "invoice_number": invoice_number,
                "invoice_date": invoice_date,
                "invoice_amount": invoice_amount,
                "buyer_gstn": "29AABCT1332L1Z5",
                "buyer_name": "Government Department",
                "match_status": "EXACT"
            }
        else:
            return {
                "verified": False,
                "error": "Invoice not found in GSTN records"
            }


# ============================================
# FACTORY FUNCTION
# ============================================

def get_gstn_client(use_mock: bool = True) -> GSTNClient:
    """
    Get appropriate GSTN client instance
    
    Args:
        use_mock: If True, return mock client for testing
    
    Returns:
        GSTN client instance
    """
    if use_mock or not settings.GSTN_API_KEY:
        logger.info("Using MOCK GSTN client")
        return MockGSTNClient()
    else:
        logger.info("Using REAL GSTN client")
        return GSTNClient()


# ============================================
# CLI for testing
# ============================================

if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    async def test_gstn():
        print("Testing GSTN Client...")
        print("=" * 60)
        
        client = get_gstn_client(use_mock=True)
        
        # Test 1: Verify GSTN
        print("\n1. Testing GSTN verification:")
        result = await client.verify_gstn("27AABCU9603R1ZM")
        print(f"   Valid: {result.get('valid')}")
        print(f"   Name: {result.get('legal_name')}")
        print(f"   Status: {result.get('status')}")
        
        # Test 2: Get invoices
        print("\n2. Testing invoice retrieval:")
        invoices = await client.get_invoices(
            "27AABCU9603R1ZM",
            "2024-01-01",
            "2024-01-31"
        )
        print(f"   Found {len(invoices)} invoices")
        if invoices:
            print(f"   First invoice: {invoices[0].get('invoice_number')}")
        
        # Test 3: Verify specific invoice
        print("\n3. Testing invoice verification:")
        if invoices:
            inv = invoices[0]
            result = await client.verify_invoice(
                "27AABCU9603R1ZM",
                inv.get("invoice_number"),
                inv.get("invoice_date"),
                inv.get("total_amount")
            )
            print(f"   Verified: {result.get('verified')}")
            print(f"   Match status: {result.get('match_status')}")
        
        print("\n" + "=" * 60)
        print("✅ GSTN Client tests complete!")
    
    asyncio.run(test_gstn())