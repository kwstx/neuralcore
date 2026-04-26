import hashlib
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    OVERRIDDEN = "overridden"

class ProvenanceRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str
    action_type: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    parent_records: List[str] = [] # IDs of parent records in the DAG
    checksum: str = "" # Immutable hash of the record content
    metadata: Dict[str, Any] = {}

    def compute_hash(self) -> str:
        """
        Computes a deterministic hash of the execution path and data.
        Ensures provenance is immutable and traceable.
        """
        content = {
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "parent_records": sorted(self.parent_records),
            "timestamp": self.timestamp.isoformat()
        }
        serialized = json.dumps(content, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def finalize(self):
        self.checksum = self.compute_hash()

class GovernanceNode(BaseModel):
    node_id: str
    record: ProvenanceRecord
    status: ExecutionStatus = ExecutionStatus.PENDING
    approver_id: Optional[str] = None
    override_reason: Optional[str] = None

class GovernanceDAG:
    def __init__(self):
        self.nodes: Dict[str, GovernanceNode] = {}
        self.edges: List[tuple[str, str]] = [] # (parent_id, child_id)

    def add_execution(self, record: ProvenanceRecord):
        node = GovernanceNode(node_id=record.record_id, record=record)
        self.nodes[node.node_id] = node
        for parent_id in record.parent_records:
            if parent_id in self.nodes:
                self.edges.append((parent_id, node.node_id))

    def trigger_override(self, node_id: str, human_id: str, reason: str):
        """
        One-click human override that triggers immediate subgraph re-computation.
        """
        if node_id not in self.nodes:
            raise ValueError("Node not found")
        
        node = self.nodes[node_id]
        node.status = ExecutionStatus.OVERRIDDEN
        node.approver_id = human_id
        node.override_reason = reason
        
        # Identify children for re-computation
        affected_subgraph = self._get_descendants(node_id)
        for child_id in affected_subgraph:
            self.nodes[child_id].status = ExecutionStatus.PENDING
            # In a real system, this would trigger a re-execution message via NATS/Kafka
            print(f"Triggering re-computation for descendant: {child_id}")
            
        return affected_subgraph

    def _get_descendants(self, node_id: str) -> Set[str]:
        descendants = set()
        to_visit = [node_id]
        while to_visit:
            current = to_visit.pop()
            children = [child for parent, child in self.edges if parent == current]
            for child in children:
                if child not in descendants:
                    descendants.add(child)
                    to_visit.append(child)
        return descendants

    def to_visualization_json(self) -> Dict[str, Any]:
        """
        Returns a format suitable for D3.js or other causal visualization libraries.
        """
        return {
            "nodes": [
                {
                    "id": node.node_id,
                    "label": node.record.action_type,
                    "status": node.status,
                    "agent": node.record.agent_id,
                    "timestamp": node.record.timestamp.isoformat()
                } for node in self.nodes.values()
            ],
            "links": [
                {"source": parent, "target": child} for parent, child in self.edges
            ]
        }
