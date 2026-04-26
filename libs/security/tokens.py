import jwt
import datetime
from typing import List, Optional, Set

class CapabilityTokenService:
    """
    Issues and validates capability-based security tokens scoped to subgraphs.
    Supports atomic revocation.
    """
    def __init__(self, secret_key: str) -> None:
        self.secret_key = secret_key
        self.revoked_tokens: Set[str] = set()

    def issue_token(self, principal: str, allowed_subgraphs: List[str], expiration_minutes: int = 60) -> str:
        """
        Issues a token with capability scopes.
        """
        payload = {
            "sub": principal,
            "capabilities": allowed_subgraphs,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=expiration_minutes),
            "iat": datetime.datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def validate_token(self, token: str, required_subgraph: Optional[str] = None) -> bool:
        """
        Validates the token and checks if it grants access to the required subgraph.
        """
        if token in self.revoked_tokens:
            return False
            
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            if required_subgraph and required_subgraph not in payload.get("capabilities", []):
                return False
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False

    def revoke_token(self, token: str) -> None:
        """
        Revokes a capability token.
        """
        self.revoked_tokens.add(token)
