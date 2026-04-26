import asyncio
import json
import numpy as np
from kafka import KafkaProducer
from nats.aio.client import Client as NATS
from .embedding_engine import NeuroSemanticEncoder

class NeuroSemanticFabric:
    """
    The foundational distributed cognitive substrate of NeuralCore.
    A hybrid event-driven actor-model backbone integrating Kafka and NATS JetStream.
    
    Attributes:
        encoder (NeuroSemanticEncoder): Computes 768-dim knowledge graph embeddings.
        kafka_producer (KafkaProducer): Handles high-throughput event ordering.
        js (JetStreamContext): Handles low-latency, at-least-once delivery guarantees.
    """
    def __init__(self, kafka_bootstrap='localhost:9092', nats_url='nats://localhost:4222'):
        # Kafka for global event ordering and log persistence
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap,
            compression_type='gzip',
            value_serializer=None # We handle prefixing ourselves
        )
        self.nats_client = NATS()
        self.nats_url = nats_url
        self.encoder = NeuroSemanticEncoder()
        self.js = None

    async def connect(self):
        """Initializes NATS connection and JetStream context."""
        await self.nats_client.connect(
            self.nats_url,
            reconnect_time_wait=2,
            max_reconnect_attempts=60
        )
        self.js = self.nats_client.jetstream()
        
        # Ensure the cognitive substrate stream is initialized
        try:
            await self.js.add_stream(name="NEURALCORE", subjects=["neuralcore.>"])
        except Exception as e:
            # Stream might already exist
            pass

    async def publish_event(self, subject: str, payload: dict, graph_context: dict = None):
        """
        Publishes an event into the Fabric with semantic metadata.
        
        Args:
            subject (str): The routing subject (e.g., 'agent.creation').
            payload (dict): The event data.
            graph_context (dict, optional): Knowledge graph context for GCN fusion.
        """
        # 1. Compute Semantic Vector (LLM + GCN)
        # We use a string representation of the payload for semantic analysis
        semantic_data = payload.get('description', json.dumps(payload))
        embedding = self.encoder.encode(semantic_data, graph_context=graph_context)
        
        # 2. Fabric Prefixing
        # Construct the wire-format: [3072 bytes embedding] + [JSON payload]
        raw_payload = json.dumps(payload).encode('utf-8')
        wire_data = self.encoder.prefix_payload(raw_payload, embedding)
        
        # 3. Distributed Log Sequencing (Kafka)
        # Ensures a single coherent temporal ordering of all system events
        self.kafka_producer.send(
            'neuralcore-event-log', 
            wire_data, 
            key=subject.encode('utf-8')
        )
        
        # 4. Low-Latency Pub-Sub (NATS JetStream)
        # Provides at-least-once delivery and dynamic semantic routing
        await self.js.publish(f"neuralcore.{subject}", wire_data)
        
        # Note: Kafka flush is handled asynchronously by the producer's background thread
        # for maximum throughput, but we could flush here if strict durability is required.

    async def subscribe(self, subject: str, callback, queue_group: str = None):
        """
        Subscribes to a subject with automatic embedding extraction.
        
        Args:
            subject (str): Subject pattern to subscribe to (e.g., 'agent.*').
            callback (coroutine): Function to handle (payload, embedding).
            queue_group (str, optional): For load-balanced consumer groups.
        """
        async def internal_cb(msg):
            try:
                # Extract the 768-dim semantic header
                embedding, raw_payload = NeuroSemanticEncoder.extract_embedding(msg.data)
                payload = json.loads(raw_payload.decode('utf-8'))
                
                # Execute the bound actor logic or agent handler
                await callback(payload, embedding)
                
                # Acknowledge completion for at-least-once reliability
                await msg.ack()
            except Exception as e:
                # Basic error handling for malformed events
                print(f"Error processing fabric event on {subject}: {e}")
                # We do not ack, allowing for retry according to JetStream policy

        return await self.js.subscribe(
            f"neuralcore.{subject}",
            queue=queue_group,
            cb=internal_cb,
            manual_ack=True
        )

    def shutdown(self):
        """Graceful termination of fabric components."""
        self.kafka_producer.flush()
        self.kafka_producer.close()
        # NATS client closing should be handled by the event loop
