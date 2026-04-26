import asyncio
import json
import logging
from typing import Annotated, Dict, List, Union
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END
# Note: swarm_supervisor is the Rust module we created
# We'll assume it's compiled and available as a python module.
try:
    from .supervisor.swarm_supervisor import MetaSupervisor
except ImportError:
    # Fallback for development if Rust lib isn't compiled
    class MetaSupervisor:
        def update_agent(self, state): pass
        def decide_handoff(self, current_agent_id): return None

from .registry.service import CapabilityRegistry
from .consensus.protocol import EpistemicConsensus, Proposal
from .memory.persistence import PersistentAgent

# Define the Swarm State
class SwarmState(TypedDict):
    """Represents the global state of the agent swarm."""
    current_agent: str
    task_description: str
    context: Dict[str, Any]
    history: List[str]
    confidence_scores: Dict[str, float]

class SwarmOrchestrator:
    """
    The proactive agent swarm orchestration engine.
    Extends LangGraph with a custom meta-reasoning supervisor.
    """
    def __init__(self, agent_configs: List[Dict]):
        self.supervisor = MetaSupervisor()
        self.registry = CapabilityRegistry("ontology/core.ttl")
        self.consensus = EpistemicConsensus([cfg["id"] for cfg in agent_configs])
        
        self.agents = agent_configs
        self.graph = self._build_graph()

    def _build_graph(self):
        """Constructs the hierarchical LangGraph."""
        builder = StateGraph(SwarmState)
        
        # Add nodes for different agent roles
        builder.add_node("researcher", self._agent_step("researcher"))
        builder.add_node("executor", self._agent_step("executor"))
        builder.add_node("curator", self._agent_step("curator"))
        
        # Define the entry point (Meta-Reasoning Supervisor)
        builder.set_entry_point("researcher")
        
        # Hierarchical routing based on MetaSupervisor decisions
        builder.add_conditional_edges(
            "researcher",
            self._supervisor_routing,
            {
                "executor": "executor",
                "curator": "curator",
                "done": END
            }
        )
        
        builder.add_edge("executor", "curator")
        builder.add_edge("curator", END)
        
        return builder.compile()

    def _agent_step(self, role: str):
        """Wrapper for agent execution logic."""
        async def step(state: SwarmState):
            logging.info(f"Agent {role} executing task: {state['task_description'][:50]}")
            
            # 1. Update supervisor with current agent state
            agent_state = {
                "id": role,
                "confidence": state["confidence_scores"].get(role, 0.5),
                "latency": 0.2, # Simulated
                "activity": f"Performing {role} task"
            }
            self.supervisor.update_agent(json.dumps(agent_state))
            
            # 2. Check for consensus if a major decision is made
            if role == "executor":
                prop = Proposal(id="exec-1", content="Action Proposed", proposer=role, confidence_score=0.9)
                if not await self.consensus.reach_consensus(prop):
                    logging.warning("Consensus not reached, backing off.")
            
            return {**state, "history": state["history"] + [f"{role} completed step"]}
        
        return step

    def _supervisor_routing(self, state: SwarmState) -> str:
        """Consults the Rust meta-supervisor for the next move."""
        next_agent = self.supervisor.decide_handoff(state["current_agent"])
        if next_agent:
            return next_agent
        
        # Heuristic fallback
        if "research" in state["history"][-1]:
            return "executor"
        return "done"

    async def execute_task(self, task: str):
        initial_state = {
            "current_agent": "researcher",
            "task_description": task,
            "context": {},
            "history": [],
            "confidence_scores": {"researcher": 0.8, "executor": 0.7, "curator": 0.9}
        }
        
        async for output in self.graph.astream(initial_state):
            print(f"--- Swarm Step ---\n{output}")
        
        print("Swarm mission accomplished.")
