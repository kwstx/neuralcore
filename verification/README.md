# NeuralCore Formal Verification Suite

This directory contains the exhaustive TLA+ specifications and verification tools for the NeuralCore Neuro-Semantic Fabric.

## Overview

The substrate is verified using TLA+ and PlusCal to ensure epistemic consistency across the distributed agent swarm. The suite focuses on:

1.  **Safety**: Proving that no stale context is ever injected into any bounded context.
2.  **Liveness**: Ensuring every update eventually reaches all relevant actors within bounded latency.
3.  **Fault Tolerance**: Simulating up to 1,000 concurrent read-write operations under Byzantine fault assumptions.

## Directory Structure

- `/tla`: Contains the `.tla` and `.cfg` files for model checking.
    - `NeuroSemanticFabric.tla`: Main specification for context propagation.
- `/scripts`: Automation for the TLC model checker and LaTeX export.
- `/reports`: Automatically generated audit compliance documents (LaTeX/PDF).

## CI/CD Integration

The verification suite is executed in the CI pipeline using the **TLC Model Checker** with symmetry reduction to prune the state space. 

### Running Verification Locally

```bash
# Example command to run TLC (requires TLA+ tools)
java -cp tla2tools.jar tlc2.TLC -modelcheck verification/tla/NeuroSemanticFabric.tla
```

### Audit Compliance

Proofs are automatically exported as human-readable LaTeX documents. This serves as the bedrock for the system's reliability before any production code is deployed.
