import httpx
from typing import Dict, Any, List

class TopazPDP:
    """
    Topaz Policy Decision Point (PDP).
    Evaluates Attribute-Based (ABAC) and Relationship-Based (ReBAC) policies.
    Consults the knowledge graph in real-time for context-aware decisions.
    """
    def __init__(self, topaz_url: str = "http://topaz.local:8282") -> None:
        self.topaz_url = topaz_url

    async def is_authorized(self, 
                             subject: str, 
                             action: str, 
                             resource: str, 
                             context: Dict[str, Any]) -> bool:
        """
        Decision call to Topaz checking if subject can perform action on resource.
        """
        # Enrichment: Consult Knowledge Graph for subject/resource attributes
        enriched_context = await self._enrich_from_knowledge_graph(subject, resource, context)
        
        async with httpx.AsyncClient() as client:
            try:
                # Topaz /is authorized API call
                response = await client.post(
                    f"{self.topaz_url}/api/v1/authz/is",
                    json={
                        "identity": {"type": "IDENTITY_TYPE_SUB", "subject": subject},
                        "resource": resource,
                        "action": action,
                        "context": enriched_context
                    }
                )
                if response.status_code == 200:
                    return bool(response.json().get("decision", False))
            except Exception as e:
                print(f"Topaz PDP error: {e}")
        
        return False

    async def _enrich_from_knowledge_graph(self, subject: str, resource: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates consulting the Neo4j/RDF knowledge graph to resolve 
        Subject-Object-Relation (ReBAC) and Attribute (ABAC) traits.
        """
        # Mocking KG lookup
        kg_attributes = {
            "subject_clearance": "L3",
            "resource_classification": "Confidential",
            "relationship": "owner" if "tenant" in resource else "viewer"
        }
        return {**context, **kg_attributes}
