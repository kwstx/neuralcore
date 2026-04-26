import os
import httpx
from typing import Optional, Dict, Any

class OryIdentityManager:
    """
    Manages identity and sessions via Ory Kratos.
    """
    def __init__(self, kratos_public_url: str = "http://kratos-public.local", kratos_admin_url: str = "http://kratos-admin.local") -> None:
        self.public_url = kratos_public_url
        self.admin_url = kratos_admin_url

    async def get_session(self, cookie_header: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.public_url}/sessions/whoami",
                headers={"Cookie": cookie_header}
            )
            if response.status_code == 200:
                res = response.json()
                return res if isinstance(res, dict) else None
        return None

class OryRelationshipManager:
    """
    Manages relationship-based access control (ReBAC) via Ory Keto.
    """
    def __init__(self, keto_read_url: str = "http://keto-read.local", keto_write_url: str = "http://keto-write.local") -> None:
        self.read_url = keto_read_url
        self.write_url = keto_write_url

    async def check_permission(self, namespace: str, object: str, relation: str, subject_id: str) -> bool:
        """
        Checks if a subject has a specific relation to an object within a namespace.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.read_url}/relation-tuples/check",
                params={
                    "namespace": namespace,
                    "object": object,
                    "relation": relation,
                    "subject_id": subject_id
                }
            )
            if response.status_code == 200:
                return bool(response.json().get("allowed", False))
        return False
