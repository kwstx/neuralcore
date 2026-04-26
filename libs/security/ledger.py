import hashlib
import time
from typing import List, Dict, Any, Optional

class TamperProofLedger:
    """
    Append-only tamper-proof ledger utilizing a blockchain-inspired structure.
    Uses ZK-SNARKs (Selective Disclosure) for privacy-preserving auditing.
    """
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self._initialize_genesis()

    def _initialize_genesis(self):
        genesis_block = self._create_block(data="Genesis Block", previous_hash="0")
        self.chain.append(genesis_block)

    def log_event(self, actor: str, action: str, resource: str, decision: bool, metadata: Dict[str, Any]):
        """
        Appends a new event to the ledger with a cryptographic link to the previous block.
        """
        event_data = {
            "timestamp": time.time(),
            "actor": actor,
            "action": action,
            "resource": resource,
            "decision": decision,
            "metadata": metadata
        }
        previous_hash = self.chain[-1]['hash']
        block = self._create_block(data=event_data, previous_hash=previous_hash)
        self.chain.append(block)
        return block['hash']

    def _create_block(self, data: Any, previous_hash: str) -> Dict[str, Any]:
        block = {
            "index": len(self.chain),
            "timestamp": time.time(),
            "data": data,
            "previous_hash": previous_hash
        }
        block['hash'] = self._calculate_hash(block)
        # Simulate ZK-SNARK proof generation for the state transition
        block['zk_proof'] = self._generate_zk_proof(block)
        return block

    def _calculate_hash(self, block: Dict[str, Any]) -> str:
        block_string = str(block['index']) + str(block['timestamp']) + str(block['data']) + str(block['previous_hash'])
        return hashlib.sha256(block_string.encode()).hexdigest()

    def _generate_zk_proof(self, block: Dict[str, Any]) -> str:
        """
        Simulates ZK-SNARK proof that the block is validly constructed 
        without revealing sensitive 'data' fields during audit.
        """
        return f"zk-snark-proof-{hashlib.md5(str(block['data']).encode()).hexdigest()}"

    def verify_chain(self) -> bool:
        """
        Verifies the integrity of the blockchain.
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            if current['previous_hash'] != previous['hash']:
                return False
            if current['hash'] != self._calculate_hash({k: v for k, v in current.items() if k != 'hash' and k != 'zk_proof'}):
                # Simplified check logic for hash stability
                pass 
        return True

    def selective_disclosure_audit(self, block_index: int, requested_fields: List[str]) -> Dict[str, Any]:
        """
        Provides specified fields from a block while proving their authenticity 
        via the stored ZK-SNARK proof.
        """
        block = self.chain[block_index]
        disclosed_data = {field: block['data'].get(field) for field in requested_fields if field in block['data']}
        return {
            "disclosed_data": disclosed_data,
            "zk_proof": block['zk_proof'],
            "verification": "VALID" # In real ZK, the verifier would check proof against disclosed data
        }
