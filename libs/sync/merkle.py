import hashlib
from typing import List, Optional

class MerkleTree:
    """
    Merkle tree implementation for cryptographic verification of sync states.
    """
    def __init__(self, data_batches: List[bytes]):
        self.leaves = [hashlib.sha256(batch).digest() for batch in data_batches]
        self.tree = self._build_tree(self.leaves)

    def _build_tree(self, leaves: List[bytes]) -> List[List[bytes]]:
        tree = [leaves]
        current_level = leaves
        while len(current_level) > 1:
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])
            
            next_level = []
            for i in range(0, len(current_level), 2):
                combined = current_level[i] + current_level[i+1]
                next_level.append(hashlib.sha256(combined).digest())
            tree.append(next_level)
            current_level = next_level
        return tree

    @property
    def root_hash(self) -> bytes:
        return self.tree[-1][0] if self.tree else b""

    def get_proof(self, index: int) -> List[tuple[bytes, bool]]:
        """
        Returns a Merkle proof for the leaf at the given index.
        Proof is a list of (hash, is_left_sibling).
        """
        proof = []
        for level in self.tree[:-1]:
            if index % 2 == 0:
                proof.append((level[index + 1], False))
            else:
                proof.append((level[index - 1], True))
            index //= 2
        return proof

def verify_proof(leaf_hash: bytes, root_hash: bytes, proof: List[tuple[bytes, bool]]) -> bool:
    """
    Verifies a Merkle proof.
    """
    current_hash = leaf_hash
    for sibling_hash, is_left in proof:
        if is_left:
            current_hash = hashlib.sha256(sibling_hash + current_hash).digest()
        else:
            current_hash = hashlib.sha256(current_hash + sibling_hash).digest()
    return current_hash == root_hash
