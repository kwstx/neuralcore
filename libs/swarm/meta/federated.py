import numpy as np
from typing import List, Any
import logging

logger = logging.getLogger(__name__)

class PrivacyPreservingAggregator:
    """
    Differentially private federated learning aggregator.
    Calibrated to epsilon=1.0 for cross-company intelligence compounding.
    """
    def __init__(self, epsilon: float = 1.0):
        self.epsilon = epsilon

    def add_laplacian_noise(self, weights: np.ndarray, sensitivity: float = 1.0) -> np.ndarray:
        """
        Injects Laplacian noise for Differential Privacy.
        Scale β = Sensitivity / Epsilon.
        """
        beta = sensitivity / self.epsilon
        noise = np.random.laplace(0, beta, weights.shape)
        return weights + noise

    def federated_average(self, tenant_updates: List[np.ndarray]) -> np.ndarray:
        """
        Aggregates updates from isolated tenant instances with DP noise.
        """
        if not tenant_updates:
            raise ValueError("No updates to aggregate")

        # Compute simple average first
        aggregated_weights = np.mean(tenant_updates, axis=0)
        
        # Apply DP noise before sharing back to tenants
        logger.info(f"Applying DP noise with epsilon={self.epsilon}")
        private_weights = self.add_laplacian_noise(aggregated_weights)
        
        return private_weights

    def update_agent_policies(self, local_weights: np.ndarray, global_updates: np.ndarray):
        """
        Updates local agent policies/embeddings using aggregated intelligence.
        """
        # In practice, this would update LoRA layers or embedding matrices
        return local_weights + 0.1 * global_updates
