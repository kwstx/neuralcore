import httpx
from typing import Dict, Any

class PolicyDecisionPoint:
    """
    Evaluates Rego policies at the edge using OPA.
    Queries the knowledge graph for dynamic attribute resolution.
    """
    def __init__(self, opa_url: str = "http://opa.local/v1/data"):
        self.opa_url = opa_url

    async def evaluate(self, policy_path: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a policy evaluation request against OPA.
        The input_data typically contains actor identity, resource attributes,
        and environmental context.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.opa_url}/{policy_path}",
                json={"input": input_data}
            )
            response.raise_for_status()
            return response.json().get("result", {})

    async def authorize(self, identity: Dict[str, Any], resource: str, action: str) -> bool:
        """
        Convenience method to check authorization for a specific action on a resource.
        """
        # In a real scenario, this would fetch dynamic attributes from the knowledge graph
        # and include them in the input to OPA.
        input_data = {
            "identity": identity,
            "resource": resource,
            "action": action,
        }
        result = await self.evaluate("neuralcore/authz", input_data)
        return result.get("allow", False)
