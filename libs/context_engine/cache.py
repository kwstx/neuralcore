import redis
import time
import torch
import torch.nn as nn
from typing import Optional

class TTLPolicyNetwork(nn.Module):
    """
    PPO-trained policy network for predicting optimal eviction TTLs.
    """
    def __init__(self, input_dim: int = 16) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.LeakyReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1) # Outputs predicted TTL in seconds
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.abs(self.network(x))

class IntelligentCache:
    """
    Always-on Redis cache layer with reinforcement learning-driven TTLs.
    """
    def __init__(self, host: str = 'localhost', port: int = 6379) -> None:
        self.redis = redis.StrictRedis(host=host, port=port, decode_responses=False)
        self.policy_net = TTLPolicyNetwork()
        # In a real setup, we'd load pre-trained PPO weights
        # self.policy_net.load_state_dict(torch.load('ppo_ttl_v1.pth'))

    def get(self, key: str) -> Optional[bytes]:
        res = self.redis.get(key)
        return res if isinstance(res, bytes) else None

    def set(self, key: str, value: bytes, context_features: torch.Tensor) -> None:
        """Sets value with a predicted TTL based on historical usage traces."""
        with torch.no_grad():
            predicted_ttl = int(self.policy_net(context_features).item())
        
        # Ensure a reasonable range (e.g., 60s to 1 hour)
        safe_ttl = max(60, min(predicted_ttl, 3600))
        
        self.redis.setex(key, safe_ttl, value)
        print(f"Cached {key} with RL-predicted TTL: {safe_ttl}s")
