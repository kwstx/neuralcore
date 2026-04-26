import asyncio
from kafka import KafkaProducer, KafkaConsumer
from nats.aio.client import Client as NATS
from .embedding_engine import NeuroSemanticEncoder
import json

class NeuroSemanticFabric:
    def __init__(self, kafka_bootstrap='localhost:9092', nats_url='nats://localhost:4222'):
        self.kafka_producer = KafkaProducer(bootstrap_servers=kafka_bootstrap)
        self.nats_client = NATS()
        self.nats_url = nats_url
        self.encoder = NeuroSemanticEncoder()

    async def connect(self):
        await self.nats_client.connect(self.nats_url)
        self.js = self.nats_client.jetstream()

    async def publish_event(self, topic, payload_dict, semantic_context=""):
        """
        Publishes an event with embedding-based routing.
        Uses Kafka for ordering and NATS JetStream for delivery.
        """
        # 1. Generate Semantic Embedding
        embedding = self.encoder.encode(semantic_context)
        
        # 2. Prepare Payload
        content = json.dumps(payload_dict).encode('utf-8')
        prefixed_payload = self.encoder.prefix_payload(content, embedding)
        
        # 3. Publish to Kafka (Ordering)
        self.kafka_producer.send(topic, prefixed_payload)
        
        # 4. Publish to NATS JetStream (At-least-once delivery)
        await self.js.publish(topic, prefixed_payload)

    async def subscribe(self, topic, callback):
        """
        Subscribes to a topic via NATS JetStream.
        """
        sub = await self.js.subscribe(topic, cb=callback)
        return sub

    def extract_embedding(self, raw_payload: bytes):
        """
        Helper to separate the 768-float embedding from the payload.
        """
        emb_size = 768 * 4 # 768 floats * 4 bytes each
        embedding = np.frombuffer(raw_payload[:emb_size], dtype=np.float32)
        payload = raw_payload[emb_size:]
        return embedding, payload
