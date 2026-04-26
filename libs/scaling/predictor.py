import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, cast

class EpistemicLoadForecaster:
    """
    Forecasts swarm load from epistemic activity patterns (context updates, knowledge graph entropy).
    """
    def __init__(self) -> None:
        self.history = []
    
    def record_activity(self, entropy: float, node_count: int, edge_count: int) -> None:
        self.history.append({
            "timestamp": datetime.now(),
            "entropy": entropy,
            "node_count": node_count,
            "edge_count": edge_count
        })
        if len(self.history) > 1000:
            self.history.pop(0)

    def forecast_load(self) -> float:
        if len(self.history) < 5:
            return 1.0
        
        # Simple linear trend of entropy and density changes
        entropies = [h["entropy"] for h in self.history[-10:]]
        trend = np.polyfit(range(len(entropies)), entropies, 1)[0]
        
        # Predicted load = current density * (1 + trend)
        current_load = self.history[-1]["node_count"] / 1000.0 # Normalized
        predicted_load = max(1.0, current_load * (1 + cast(float, trend)))
        return float(predicted_load)

class BanditResourceAllocator:
    """
    Predictive auto-scaling rules driven by a bandit-algorithm.
    """
    def __init__(self, min_replicas: int = 2, max_replicas: int = 50):
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.best_config_reward = 0
        self.options = [2, 4, 8, 16, 32, 50]
        self.counts = np.zeros(len(self.options))
        self.values = np.zeros(len(self.options))

    def select_scaling_target(self, predicted_load: float) -> int:
        # Epsilon-greedy or UCB to find optimal replica count for a given load
        # For simplicity, we sample from options close to predicted_load
        idx = np.random.randint(len(self.options)) # Exploration
        if np.random.random() > 0.1:
            # Exploitation: based on past rewards for similar loads
            # Real implementation would use Contextual Bandits (Vowpal Wabbit style)
            idx = np.argmax(self.values)
        
        return int(self.options[idx])

    def record_reward(self, replicas: int, p50_latency: float, cost: float) -> None:
        # Reward = 1 / (latency * cost)
        reward = 1.0 / (p50_latency * cost + 1e-6)
        idx = self.options.index(replicas)
        self.counts[idx] += 1
        n = self.counts[idx]
        value = self.values[idx]
        self.values[idx] = ((n - 1) / n) * value + (1 / n) * reward
