import numpy as np
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class Proposal:
    id: str
    content: Any
    proposer: str
    confidence_score: float

class EpistemicConsensus:
    """
    Distributed epistemic consensus protocol inspired by Raft, 
    but weighted by per-agent local confidence scores derived from Bayesian posteriors.
    """
    def __init__(self, agent_ids: List[str]):
        self.agent_ids = agent_ids
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.commit_index = 0
        
        # Bayesian posteriors for each agent (simplified as [alpha, beta] for Beta distribution)
        self.posteriors = {aid: [1.0, 1.0] for aid in agent_ids}

    def update_confidence(self, agent_id: str, success: bool):
        """Updates the Bayesian posterior based on agent performance."""
        if success:
            self.posteriors[agent_id][0] += 1.0  # Increment alpha
        else:
            self.posteriors[agent_id][1] += 1.0  # Increment beta

    def get_confidence_score(self, agent_id: str) -> float:
        """Derives the mean of the Beta distribution as the confidence score."""
        a, b = self.posteriors[agent_id]
        return a / (a + b)

    async def reach_consensus(self, proposal: Proposal) -> bool:
        """
        Aggregates weights from swarm members to validate a proposal.
        The weight of each vote is proportional to the agent's confidence score.
        """
        total_weight = sum(self.get_confidence_score(aid) for aid in self.agent_ids)
        accumulated_weight = 0.0
        
        # In a real distributed system, this would involve network calls.
        # Here we simulate the consensus check.
        logger_consensus = logging.getLogger("Consensus")
        logger_consensus.info(f"Reaching consensus on proposal {proposal.id} from {proposal.proposer}")

        # Proposer's own confidence is factored in
        accumulated_weight += proposal.confidence_score
        
        # Threshold for consensus (e.g., 60% of total weighted confidence)
        threshold = 0.6 * total_weight
        
        if accumulated_weight >= threshold:
            logger_consensus.info(f"Consensus reached for {proposal.id}")
            return True
        else:
            logger_consensus.warning(f"Consensus failed for {proposal.id}: {accumulated_weight}/{threshold}")
            return False
