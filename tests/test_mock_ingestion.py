import pytest
import json
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock

# --- Mock missing external modules before importing libs ---
def mock_package(name):
    m = MagicMock()
    m.__spec__ = MagicMock()
    sys.modules[name] = m
    return m

mock_torch = mock_package("torch")
mock_torch.nn = MagicMock()
mock_torch.nn.__spec__ = MagicMock()
class MockModule:
    def __init__(self, *args, **kwargs): pass
    def __call__(self, *args, **kwargs): return MagicMock()
mock_torch.nn.Module = MockModule
mock_torch.nn.functional = MagicMock()
mock_torch.nn.functional.__spec__ = MagicMock()
sys.modules["torch.nn"] = mock_torch.nn
sys.modules["torch.nn.functional"] = mock_torch.nn.functional

mock_nats = mock_package("nats")
mock_nats.aio = MagicMock()
mock_nats.aio.__spec__ = MagicMock()
mock_nats.aio.client = MagicMock()
mock_nats.aio.client.__spec__ = MagicMock()
sys.modules["nats.aio"] = mock_nats.aio
sys.modules["nats.aio.client"] = mock_nats.aio.client

mocks = [
    "pgvector", "pgvector.sqlalchemy", 
    "neo4j", "kafka", "sentence_transformers",
    "dgl", "rdflib", "pydantic", "langgraph", "pyshacl",
    "transformers", "pyro", "pyro.distributions", "pyro.infer", "pyro.optim",
    "wasmtime"
]
for m in mocks:
    mock_package(m)

from libs.fabric.backbone import NeuroSemanticFabric
from libs.substrate.manager import HybridSubstrateManager

# --- Mocks for Fabirc ---
@pytest.fixture
def mock_kafka():
    with patch('libs.fabric.backbone.KafkaProducer') as mock:
        instance = mock.return_value
        yield instance

@pytest.fixture
def mock_nats():
    with patch('libs.fabric.backbone.NATS') as mock:
        instance = mock.return_value
        instance.connect = AsyncMock()
        instance.jetstream = MagicMock()
        
        # Mock JetStream context
        js_mock = AsyncMock()
        instance.jetstream.return_value = js_mock
        js_mock.add_stream = AsyncMock()
        js_mock.publish = AsyncMock()
        
        yield instance

# --- Mocks for Substrate ---
@pytest.fixture
def mock_postgres():
    with patch('libs.substrate.manager.PostgresKnowledgeStore') as mock:
        instance = mock.return_value
        instance.upsert_node = MagicMock()
        yield instance

@pytest.fixture
def mock_neo4j():
    with patch('libs.substrate.manager.Neo4jTemporalGraph') as mock:
        instance = mock.return_value
        instance.create_unified_node = MagicMock()
        yield instance

# --- Golden File Fixture ---
@pytest.fixture
def golden_transcript():
    path = os.path.join(os.path.dirname(__file__), 'fixtures', 'transcript_sample.json')
    with open(path, 'r') as f:
        return json.load(f)

@pytest.mark.asyncio
async def test_fabric_publish_mock(mock_kafka, mock_nats):
    """Verify that fabric publishing triggers Kafka and NATS calls without real connections."""
    fabric = NeuroSemanticFabric()
    await fabric.connect()
    
    payload = {"task": "test_event", "value": 42}
    await fabric.publish_event("test.subject", payload)
    
    # Verify Kafka interaction
    assert mock_kafka.send.called
    args, kwargs = mock_kafka.send.call_args
    assert args[0] == 'neuralcore-event-log'
    assert kwargs['key'] == b'test.subject'
    
    # Verify NATS JetStream interaction
    js_mock = mock_nats.jetstream.return_value
    assert js_mock.publish.called
    js_args, _ = js_mock.publish.call_args
    assert js_args[0] == "neuralcore.test.subject"

def test_substrate_ingestion_mock(mock_postgres, mock_neo4j, golden_transcript):
    """Verify that substrate ingestion uses golden files and updates both stores."""
    manager = HybridSubstrateManager()
    
    # Use the golden file data
    metadata = golden_transcript['metadata']
    source = f"meeting_{golden_transcript['meeting_id']}"
    
    manager.ingest_artifact(
        artifact_type="code", # Using code since it's a simple branch in ingest_artifact
        source_path=source,
        metadata=metadata
    )
    
    # Verify Postgres update
    assert mock_postgres.upsert_node.called
    pg_args, _ = mock_postgres.upsert_node.call_args
    assert pg_args[0] == f"node_{source}"
    assert pg_args[2] == metadata
    
    # Verify Neo4j update
    assert mock_neo4j.create_unified_node.called
    neo_kwargs = mock_neo4j.create_unified_node.call_args.kwargs
    assert neo_kwargs['node_id'] == f"node_{source}"
    assert neo_kwargs['label'] == "KnowledgeElement"
    assert neo_kwargs['properties'] == metadata
    assert len(neo_kwargs['embedding']) == 768
