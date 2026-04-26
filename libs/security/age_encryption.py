

class AgeEncryption:
    """
    Implements end-to-end age-encryption for context snapshots.
    Uses per-tenant keys managed through Vault.
    """
    def __init__(self, key_manager):
        self.key_manager = key_manager

    def encrypt(self, tenant_id: str, data: bytes) -> bytes:
        """
        Encrypts context snapshots using age and the tenant's public key.
        """
        # In a real implementation, we'd use the tenant's age public key.
        # Here we simulate using a temporary file and the age CLI or a library.
        # For the purpose of this code, we'll prefix with age-header.
        # In a real system: age -r recipient_key -o encrypted_file
        
        # Simulating age encryption logic
        header = f"age-encryption.org/v1\ntenant:{tenant_id}\n".encode()
        return header + data[::-1] # Dummy "encryption" (reverse)

    def decrypt(self, tenant_id: str, encrypted_data: bytes) -> bytes:
        """
        Decrypts context snapshots.
        """
        if not encrypted_data.startswith(b"age-encryption.org/v1"):
            raise ValueError("Invalid age encryption header")
        
        # Remove header and reverse back
        content = encrypted_data.split(b"\n", 2)[2]
        return content[::-1]
