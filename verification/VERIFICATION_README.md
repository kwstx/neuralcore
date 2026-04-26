# NeuralCore Formal Verification Suite

This document outlines the implementation of the formal verification substrate for the Neuro-Semantic Fabric, ensuring research-grade reliability through TLA+ specifications and automated CI validation.

## 1. TLA+ Specification (`verification/tla/`)
We have implemented an exhaustive specification modeled with PlusCal that defines the state machines for the substrate and agents.

- **`NeuroSemanticFabric.tla`**: Key logic for context propagation, safety invariants, and liveness properties.
- **`NeuroSemanticFabric.cfg`**: Model checker configuration with symmetry reduction.

### Key Managed Properties:
| Property | Type | Description |
| :--- | :--- | :--- |
| `NoStaleContext` | Safety | Proves no agent ever accepts a version newer than the source (no ghost context). |
| `EventualConsistency` | Liveness | Proves every update eventually reaches all non-faulty agents. |

## 2. Byzantine Fault Modeling
The specification includes a `ByzantineAgents` constant. Faulty agents can:
- Corrupt local context views.
- Drop update messages.
- Inject inconsistent states (modeled via the state space exploration).

## 3. CI Pipeline Integration
Automated verification is integrated into the development lifecycle.

- **`verification/verify.py`**: A Python-based runner that executes the verification suite and triggers the audit export.
- **`.github/workflows/formal-verification.yml`**: Triggers on push/PR to ensure invariants hold before merging.

## 4. Audit Compliance Export
Proofs are automatically exported to LaTeX for human-readable verification records.
- **Path**: `verification/reports/Formal_Verification_Report.tex`
- **Content**: Summary of model checking results, state space stats, and formal proof confirmation.
