# oracle/services/blockchain_client.py
"""
Blockchain Client
Interacts with Polygon blockchain and smart contracts
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware  # Updated import
from eth_account import Account
from eth_account.signers.local import LocalAccount
from typing import Optional, Dict, Any, List
import json
import logging
from decimal import Decimal

from app.config import settings

logger = logging.getLogger(__name__)


class BlockchainClient:
    """
    Client for interacting with Polygon blockchain
    """
    
    def __init__(self):
        # Connect to Polygon RPC
        self.w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
        
        # Add PoA middleware for Polygon (updated)
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        # Load oracle account
        self.oracle_account: LocalAccount = Account.from_key(
            settings.ORACLE_PRIVATE_KEY
        )
        
        # Contract addresses (will be set after deployment)
        self.order_factory_address = settings.ORDER_FACTORY_ADDRESS
        self.oracle_registry_address = settings.ORACLE_REGISTRY_ADDRESS
        
        # Contract ABIs (simplified - will be loaded from files)
        self.order_factory_abi: Optional[List] = None
        self.order_contract_abi: Optional[List] = None
        
        logger.info(f"Blockchain client initialized")
        logger.info(f"Oracle address: {self.oracle_account.address}")
        try:
            chain_id = self.w3.eth.chain_id
            logger.info(f"Network chain ID: {chain_id}")
        except Exception as e:
            logger.warning(f"Could not get chain ID: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to blockchain"""
        try:
            return self.w3.is_connected()
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False
    
    def get_balance(self, address: Optional[str] = None) -> Decimal:
        """
        Get MATIC balance of address
        
        Args:
            address: Address to check (defaults to oracle address)
        
        Returns:
            Balance in MATIC
        """
        addr = address or self.oracle_account.address
        balance_wei = self.w3.eth.get_balance(addr)
        balance_matic = Decimal(balance_wei) / Decimal(10**18)
        return balance_matic
    
    def load_contract_abi(self, contract_name: str) -> List:
        """
        Load contract ABI from artifacts
        
        Args:
            contract_name: Name of the contract
        
        Returns:
            ABI list
        """
        # Path to compiled contract artifacts
        artifacts_path = Path(__file__).parent.parent.parent / "blockchain" / "artifacts" / "contracts"
        
        # Find the JSON file
        abi_file = artifacts_path / f"{contract_name}.sol" / f"{contract_name}.json"
        
        if abi_file.exists():
            with open(abi_file, 'r') as f:
                artifact = json.load(f)
                return artifact.get("abi", [])
        else:
            logger.warning(f"ABI file not found: {abi_file}")
            return []
    
    def create_order_contract(
        self,
        gem_order_id: str,
        order_amount: int,  # in wei
        delivery_deadline: int,  # unix timestamp
        oracle_signature: bytes
    ) -> Dict[str, Any]:
        """
        Create a new order contract on blockchain
        
        Args:
            gem_order_id: GeM order ID
            order_amount: Order amount in wei
            delivery_deadline: Delivery deadline timestamp
            oracle_signature: Oracle's signature
        
        Returns:
            Transaction receipt
        """
        if not self.order_factory_address:
            raise ValueError("OrderFactory address not set")
        
        logger.info(f"Creating order contract for GeM order: {gem_order_id}")
        
        # Load contract
        factory_contract = self.w3.eth.contract(
            address=self.order_factory_address,
            abi=self.order_factory_abi
        )
        
        # Encode order data
        gem_data = self.w3.codec.encode(
            ['string', 'uint256', 'uint256'],
            [gem_order_id, order_amount, delivery_deadline]
        )
        
        # Build transaction
        transaction = factory_contract.functions.createOrderFromGeM(
            gem_data,
            oracle_signature
        ).build_transaction({
            'from': self.oracle_account.address,
            'nonce': self.w3.eth.get_transaction_count(self.oracle_account.address),
            'gas': 500000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        # Sign transaction
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction,
            self.oracle_account.key
        )
        
        # Send transaction
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        logger.info(f"Transaction sent: {tx_hash.hex()}")
        
        # Wait for receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        logger.info(f"Order contract created at block: {receipt['blockNumber']}")
        
        # Extract contract address from logs
        contract_address = None
        for log in receipt['logs']:
            if len(log['topics']) > 0:
                contract_address = self.w3.to_checksum_address(log['address'])
                break
        
        return {
            'transaction_hash': tx_hash.hex(),
            'block_number': receipt['blockNumber'],
            'gas_used': receipt['gasUsed'],
            'status': receipt['status'],
            'contract_address': contract_address
        }
    
    def confirm_delivery(
        self,
        order_contract_address: str,
        invoice_hash: bytes,
        oracle_signature: bytes
    ) -> Dict[str, Any]:
        """
        Confirm delivery for an order
        
        Args:
            order_contract_address: Address of order contract
            invoice_hash: Hash of delivery invoice
            oracle_signature: Oracle's signature
        
        Returns:
            Transaction receipt
        """
        logger.info(f"Confirming delivery for order: {order_contract_address}")
        
        # Load order contract
        order_contract = self.w3.eth.contract(
            address=order_contract_address,
            abi=self.order_contract_abi
        )
        
        # Build transaction
        transaction = order_contract.functions.confirmDelivery(
            invoice_hash
        ).build_transaction({
            'from': self.oracle_account.address,
            'nonce': self.w3.eth.get_transaction_count(self.oracle_account.address),
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        # Sign and send
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction,
            self.oracle_account.key
        )
        
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        logger.info(f"Delivery confirmed in block: {receipt['blockNumber']}")
        
        return {
            'transaction_hash': tx_hash.hex(),
            'block_number': receipt['blockNumber'],
            'gas_used': receipt['gasUsed'],
            'status': receipt['status']
        }
    
    def get_order_state(self, order_contract_address: str) -> Dict[str, Any]:
        """
        Get current state of an order contract
        
        Args:
            order_contract_address: Address of order contract
        
        Returns:
            Order state dictionary
        """
        order_contract = self.w3.eth.contract(
            address=order_contract_address,
            abi=self.order_contract_abi
        )
        
        # Call view functions
        current_state = order_contract.functions.currentState().call()
        gem_order_id = order_contract.functions.gemOrderId().call()
        order_amount = order_contract.functions.orderAmount().call()
        msme_address = order_contract.functions.msmeAddress().call()
        total_funded = order_contract.functions.totalFunded().call()
        
        return {
            'contract_address': order_contract_address,
            'current_state': current_state,
            'gem_order_id': gem_order_id,
            'order_amount': order_amount,
            'msme_address': msme_address,
            'total_funded': total_funded
        }
    
    def sign_message(self, message: bytes) -> bytes:
        """
        Sign a message with oracle private key
        
        Args:
            message: Message to sign
        
        Returns:
            Signature bytes
        """
        message_hash = Web3.keccak(message)
        signed = self.oracle_account.signHash(message_hash)
        return signed.signature


# ============================================
# MOCK BLOCKCHAIN CLIENT (for testing)
# ============================================

class MockBlockchainClient:
    """Mock blockchain client for testing without actual connection"""
    
    def __init__(self):
        logger.info("Using MOCK Blockchain client")
        self.oracle_account = type('Account', (), {
            'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb'
        })()
        self.mock_contracts = {}
    
    def is_connected(self) -> bool:
        return True
    
    def get_balance(self, address: Optional[str] = None) -> Decimal:
        return Decimal("10.0")  # Mock 10 MATIC
    
    def load_contract_abi(self, contract_name: str) -> List:
        return []  # Mock empty ABI
    
    def create_order_contract(
        self,
        gem_order_id: str,
        order_amount: int,
        delivery_deadline: int,
        oracle_signature: bytes
    ) -> Dict[str, Any]:
        logger.info(f"[MOCK] Creating order contract for {gem_order_id}")
        
        # Generate fake contract address
        import random
        contract_address = f"0x{random.randbytes(20).hex()}"
        
        self.mock_contracts[contract_address] = {
            'gem_order_id': gem_order_id,
            'order_amount': order_amount,
            'state': 0  # PENDING_VERIFICATION
        }
        
        return {
            'transaction_hash': f"0x{random.randbytes(32).hex()}",
            'block_number': random.randint(10000, 99999),
            'gas_used': 450000,
            'status': 1,
            'contract_address': contract_address
        }
    
    def confirm_delivery(
        self,
        order_contract_address: str,
        invoice_hash: bytes,
        oracle_signature: bytes
    ) -> Dict[str, Any]:
        logger.info(f"[MOCK] Confirming delivery for {order_contract_address}")
        
        import random
        return {
            'transaction_hash': f"0x{random.randbytes(32).hex()}",
            'block_number': random.randint(10000, 99999),
            'gas_used': 150000,
            'status': 1
        }
    
    def get_order_state(self, order_contract_address: str) -> Dict[str, Any]:
        contract_data = self.mock_contracts.get(order_contract_address, {})
        
        return {
            'contract_address': order_contract_address,
            'current_state': contract_data.get('state', 0),
            'gem_order_id': contract_data.get('gem_order_id', ''),
            'order_amount': contract_data.get('order_amount', 0),
            'msme_address': '0x0000000000000000000000000000000000000000',
            'total_funded': 0
        }
    
    def sign_message(self, message: bytes) -> bytes:
        import random
        return random.randbytes(65)


# ============================================
# FACTORY FUNCTION
# ============================================

def get_blockchain_client(use_mock: bool = True) -> BlockchainClient:
    """Get blockchain client instance"""
    if use_mock or not settings.POLYGON_RPC_URL or settings.POLYGON_RPC_URL == "https://polygon-mumbai.g.alchemy.com/v2/demo":
        return MockBlockchainClient()
    else:
        return BlockchainClient()


# ============================================
# CLI for testing
# ============================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Blockchain Client...")
    print("=" * 60)
    
    client = get_blockchain_client(use_mock=True)
    
    # Test connection
    print(f"\n1. Connected: {client.is_connected()}")
    print(f"   Oracle address: {client.oracle_account.address}")
    print(f"   Balance: {client.get_balance()} MATIC")
    
    # Test contract creation
    print("\n2. Creating order contract...")
    result = client.create_order_contract(
        gem_order_id="GEM12345",
        order_amount=1000000,
        delivery_deadline=1234567890,
        oracle_signature=b'\x00' * 65
    )
    print(f"   Contract address: {result['contract_address']}")
    print(f"   Transaction hash: {result['transaction_hash']}")
    print(f"   Gas used: {result['gas_used']}")
    
    # Test getting order state
    print("\n3. Getting order state...")
    state = client.get_order_state(result['contract_address'])
    print(f"   GeM Order ID: {state['gem_order_id']}")
    print(f"   State: {state['current_state']}")
    print(f"   Amount: {state['order_amount']}")
    
    print("\n" + "=" * 60)
    print("✅ Blockchain client tests complete!")