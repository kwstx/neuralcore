import numpy as np
from sklearn.ensemble import IsolationForest
from typing import List, Dict, Any

class SecurityAnomalyDetector:
    """
    Mitigates confused deputy and supply-chain vulnerabilities.
    Employs Isolation Forest on behavioral feature vectors extracted from API call graphs.
    """
    def __init__(self):
        # contamination represents expected % of outliers
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.is_trained = False
        self.feature_history = []

    def extract_features(self, call_graph: Dict[str, Any]) -> np.ndarray:
        """
        Translates an API call graph (sequence, depth, frequency, target types) 
        into a numerical feature vector.
        """
        # Simplified feature extraction
        num_calls = len(call_graph.get("nodes", []))
        avg_depth = call_graph.get("max_depth", 1)
        unique_destinations = len(set(call_graph.get("targets", [])))
        call_frequency = call_graph.get("calls_per_second", 0)
        
        return np.array([num_calls, avg_depth, unique_destinations, call_frequency])

    def train(self, historical_call_graphs: List[Dict[str, Any]]):
        """
        Trains the isolation forest on 'normal' behavior data.
        """
        X = np.array([self.extract_features(cg) for cg in historical_call_graphs])
        self.model.fit(X)
        self.is_trained = True

    def check_anomaly(self, current_call_graph: Dict[str, Any]) -> bool:
        """
        Returns True if the current behavioral pattern is anomalous.
        """
        if not self.is_trained:
            # Collect data for initial training if not enough samples
            self.feature_history.append(self.extract_features(current_call_graph))
            if len(self.feature_history) > 20:
                self.train(self.feature_history)
            return False
            
        features = self.extract_features(current_call_graph).reshape(1, -1)
        prediction = self.model.predict(features)
        
        # IsolationForest returns -1 for anomalies
        return prediction[0] == -1

    def trigger_revocation(self, token_id: str):
        """
        Automatically revokes capability tokens if anomaly is detected.
        """
        print(f"ANOMALY DETECTED: Revoking capability token {token_id}")
        # In real system, this would call the Token Service/Topaz to invalidate
