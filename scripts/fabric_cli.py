import asyncio
import argparse
import json
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from libs.fabric.backbone import NeuroSemanticFabric
from libs.fabric.local import LocalFabric

async def inject_event(subject, payload_file, use_local=False):
    """
    Injects an event into the Neuro-Semantic Fabric.
    """
    if os.path.exists(payload_file):
        with open(payload_file, 'r') as f:
            payload = json.load(f)
    else:
        # Try to parse payload_file as JSON string if it's not a file
        try:
            payload = json.loads(payload_file)
        except json.JSONDecodeError:
            print(f"Error: Payload must be a JSON file or JSON string.")
            return

    if use_local:
        print(f"Using LocalFabric (In-Memory)...")
        fabric = LocalFabric()
    else:
        print(f"Using NeuroSemanticFabric (NATS/Kafka)...")
        fabric = NeuroSemanticFabric()
    
    await fabric.connect()
    await fabric.publish_event(subject, payload)
    print(f"Event published to {subject}")
    
    if hasattr(fabric, 'shutdown'):
        fabric.shutdown()

def main():
    parser = argparse.ArgumentParser(description="NeuralCore Fabric CLI - Inject mock events")
    parser.add_argument("subject", help="The subject to publish to (e.g., 'task.assigned')")
    parser.add_argument("payload", help="JSON string or path to JSON file containing the payload")
    parser.add_argument("--local", action="store_true", help="Use the local in-memory fabric (for smoke tests)")

    args = parser.parse_args()

    asyncio.run(inject_event(args.subject, args.payload, args.local))

if __name__ == "__main__":
    main()
