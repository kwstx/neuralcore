import hvac
import os
from typing import Optional, Any

class VaultKeyManager:
    """
    Manages per-tenant encryption keys using HashiCorp Vault.
    Supports HSM integration for on-prem installations.
    """
    def __init__(self, url: Optional[str] = None, token: Optional[str] = None) -> None:
        self.url = url or os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
        self.token = token or os.getenv("VAULT_TOKEN")
        self.client = hvac.Client(url=self.url, token=self.token)

    def get_tenant_key(self, tenant_id: str) -> str:
        """
        Retrieves or generates a transit key for a specific tenant.
        """
        try:
            # Check if key exists
            self.client.secrets.transit.read_key(name=f"tenant-{tenant_id}")
        except:
            # Create key if it doesn't exist
            self.client.secrets.transit.create_key(name=f"tenant-{tenant_id}")
        
        # In a real scenario, we might use the transit engine to encrypt/decrypt
        # or export the key if it's exportable and HSM allows.
        # For this implementation, we'll return a key identifier.
        return f"transit/tenant-{tenant_id}"

    def encrypt_snapshot(self, tenant_id: str, plaintext: bytes) -> str:
        """
        Encrypts data using Vault's transit engine.
        """
        response = self.client.secrets.transit.encrypt_data(
            name=f"tenant-{tenant_id}",
            plaintext=plaintext.decode('utf-8')
        )
        return str(response['data']['ciphertext'])

    def decrypt_snapshot(self, tenant_id: str, ciphertext: str) -> bytes:
        """
        Decrypts data using Vault's transit engine.
        """
        response = self.client.secrets.transit.decrypt_data(
            name=f"tenant-{tenant_id}",
            ciphertext=ciphertext
        )
        return bytes(response['data']['plaintext'].encode('utf-8'))
