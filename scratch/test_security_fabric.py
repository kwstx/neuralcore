import asyncio
import os
import sys

# Ensure libs path is in sys.path
sys.path.append(os.getcwd())

from libs.swarm.orchestrator import SwarmOrchestrator

async def main():
    agent_configs = [
        {"id": "researcher", "role": "researcher"},
        {"id": "executor", "role": "executor"},
        {"id": "curator", "role": "curator"}
    ]
    
    # Initialize orchestrator with security fabric
    orchestrator = SwarmOrchestrator(agent_configs, tenant_id="acme-corp")
    
    print("--- Executing Secure Swarm Task ---")
    await orchestrator.execute_task("Analyze market trends for quantum computing")
    
    print("\n--- Verifying Audit Ledger ---")
    is_valid = orchestrator.ledger.verify_chain()
    print(f"Ledger Integrity: {'VALID' if is_valid else 'COMPROMISED'}")
    
    print("\n--- Testing Selective Disclosure Audit ---")
    last_block_idx = len(orchestrator.ledger.chain) - 1
    audit_data = orchestrator.ledger.selective_disclosure_audit(last_block_idx, ["actor", "decision"])
    print(f"Audit Result for Block {last_block_idx}: {audit_data}")

if __name__ == "__main__":
    asyncio.run(main())
