import logging
from typing import Dict, Any, List
from rdflib import Graph, Namespace, RDF, URIRef
from pyshacl import validate

logger = logging.getLogger("CapabilityRegistry")

class CapabilityRegistry:
    """
    Dynamically registers tool-use capabilities and validates them 
    against the ontology using SHACL constraints at runtime.
    """
    def __init__(self, ontology_path: str):
        self.ontology_path = ontology_path
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.shacl_graph = Graph()
        self.shacl_graph.parse(ontology_path, format="turtle")
        
        self.NC = Namespace("https://neuralcore.ai/ontology/")

    def register_capability(self, tool_id: str, schema_rdf: str):
        """
        Validates the tool schema against SHACL constraints before registration.
        """
        logger.info(f"Attempting to register capability: {tool_id}")
        
        # Load the tool's RDF schema
        tool_graph = Graph()
        tool_graph.parse(data=schema_rdf, format="turtle")
        
        # Validate against SHACL constraints in the ontology
        conforms, results_graph, results_text = validate(
            tool_graph,
            shacl_graph=self.shacl_graph,
            inference='rdfs',
            abort_on_first=False,
            allow_infos=True,
            allow_warnings=True
        )
        
        if not conforms:
            logger.error(f"Capability validation failed for {tool_id}: {results_text}")
            raise ValueError(f"Tool schema does not conform to ontology constraints: {results_text}")
        
        self.registry[tool_id] = {
            "id": tool_id,
            "graph": tool_graph,
            "status": "active"
        }
        logger.info(f"Capability {tool_id} registered successfully.")

    def get_capabilities(self) -> List[str]:
        return list(self.registry.keys())

    def validate_execution(self, tool_id: str, parameters: Dict[str, Any]) -> bool:
        """
        Optional: dynamically validate the parameters themselves against the ontology.
        """
        if tool_id not in self.registry:
            return False
        # Implementation for runtime parameter validation...
        return True
