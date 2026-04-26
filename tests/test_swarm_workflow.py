import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Mocking heavy/missing dependencies before they are imported by orchestrator
mock_mods = ["hvac", "topaz", "age_encryption", "ledger", "anomaly", "tokens", "vault"]
for mod in mock_mods:
    sys.modules[f"libs.security.{mod}"] = MagicMock()
sys.modules["libs.fabric.backbone"] = MagicMock()
sys.modules["libs.fabric"] = MagicMock()

from libs.swarm.orchestrator import SwarmOrchestrator, SwarmState


@pytest.mark.asyncio
async def test_swarm_handoff_sequence():
    """Verifies that the swarm follows the researcher -> executor -> curator sequence."""
    agent_configs = [{"id": "researcher"}, {"id": "executor"}, {"id": "curator"}]
    orchestrator = SwarmOrchestrator(agent_configs)
    
    # Mocking external dependencies
    orchestrator.pdp.is_authorized = AsyncMock(return_value=True)
    orchestrator.anomaly_detector.check_anomaly = MagicMock(return_value=False)
    orchestrator.consensus.reach_consensus = AsyncMock(return_value=True)
    orchestrator.supervisor.decide_handoff = MagicMock(side_effect=["executor", "curator", None])
    orchestrator.age.encrypt = MagicMock(return_value=b"encrypted-data")


    task = "Analyze market trends and execute strategy."
    
    # We use a spy or history to track the flow
    # Since execute_task prints and streams, we might want to capture history
    
    initial_state = {
        "current_agent": "researcher",
        "task_description": task,
        "context": {},
        "history": [],
        "confidence_scores": {"researcher": 0.8, "executor": 0.7, "curator": 0.9}
    }
    
    # Compile graph and run
    app = orchestrator.graph
    final_state = await app.ainvoke(initial_state)
    
    assert "researcher completed step" in final_state["history"]
    assert "executor completed step" in final_state["history"]
    assert "curator completed step" in final_state["history"]
    assert len(final_state["history"]) == 3

@pytest.mark.asyncio
async def test_security_failure_handling():
    """Verifies that unauthorized access is logged and does not execute agent logic."""
    agent_configs = [{"id": "researcher"}]
    orchestrator = SwarmOrchestrator(agent_configs)
    
    # Mocking unauthorized access
    orchestrator.pdp.is_authorized = AsyncMock(return_value=False)
    
    initial_state = {
        "current_agent": "researcher",
        "task_description": "Sensitive task",
        "context": {},
        "history": [],
        "confidence_scores": {"researcher": 0.8}
    }
    
    app = orchestrator.graph
    final_state = await app.ainvoke(initial_state)
    
    # Check that security failure was recorded in history
    assert any("SECURITY FAILURE" in h for h in final_state["history"])
    # Ensure standard completion message is NOT there (since step returned early)
    assert "researcher completed step" not in final_state["history"]

@pytest.mark.asyncio
async def test_consensus_failure_logging(caplog):
    """Verifies that consensus failure is logged but doesn't crash the executor."""
    agent_configs = [{"id": "executor"}]
    orchestrator = SwarmOrchestrator(agent_configs)
    
    orchestrator.pdp.is_authorized = AsyncMock(return_value=True)
    orchestrator.consensus.reach_consensus = AsyncMock(return_value=False)
    orchestrator.supervisor.decide_handoff = MagicMock(return_value="executor")
    orchestrator.age.encrypt = MagicMock(return_value=b"encrypted-data")
    
    initial_state = {
        "current_agent": "executor", # Force start at executor for test
        "task_description": "Execute decision",
        "context": {},
        "history": [],
        "confidence_scores": {"executor": 0.7}
    }
    
    # We need to add the node manually if we want to start there easily, 
    # or just use the compiled graph starting from entry point.
    # Entry point is researcher, so let's mock researcher out.
    orchestrator.supervisor.decide_handoff = MagicMock(return_value="executor")
    
    app = orchestrator.graph
    # We'll invoke it. It will go Researcher -> Executor
    final_state = await app.ainvoke(initial_state)
    
    # Verify warning was logged
    assert "Consensus not reached, backing off." in caplog.text
    assert "executor completed step" in final_state["history"]
