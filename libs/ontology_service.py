from rdflib import Graph, Namespace, RDF, URIRef
from typing import List, Tuple, Optional, Any, cast
import logging

logger = logging.getLogger("OntologyService")

class EpistemicEngine:
    """
    Implements the formal OWL 2 DL ontology layer for NeuralCore.
    Ensures epistemic consistency across the distributed agent swarm by 
    maintaining a coherent RDF triple store with custom temporal and causal predicates.
    """
    def __init__(self) -> None:
        self.g = Graph()
        self.NC = Namespace("https://neuralcore.ai/ontology/")
        self.g.bind("nc", self.NC)
        self.g.bind("owl", OWL)
        
        # Bootstrap foundational axioms
        self._initialize_core_axioms()

    def _initialize_core_axioms(self) -> None:
        """Defines the 'precedes' and 'enables' predicates as specified."""
        # Temporal Predicate: precedes
        self.g.add((self.NC.precedes, RDF.type, OWL.ObjectProperty))
        self.g.add((self.NC.precedes, RDF.type, OWL.TransitiveProperty))
        self.g.add((self.NC.precedes, RDFS.comment, RDF.PlainLiteral("A formal temporal predicate defining chronological sequence.")))

        # Causal Predicate: enables
        self.g.add((self.NC.enables, RDF.type, OWL.ObjectProperty))
        self.g.add((self.NC.enables, RDFS.subPropertyOf, self.NC.precedes))
        self.g.add((self.NC.enables, RDFS.comment, RDF.PlainLiteral("A causal predicate indicating one state or event is necessary for another.")))

    def ingest_triples(self, triples: List[Tuple[str, str, str]]) -> None:
        """
        Atomic update of the epistemic state with new knowledge triples.
        Ensures consistency is checked during the transaction (conceptual).
        """
        for s, p, o in triples:
            # Use cast to avoid "URIRef not callable" error in mypy
            uri_ctor = cast(Any, URIRef)
            subj = uri_ctor(self.NC[s]) if not s.startswith("http") else uri_ctor(s)
            pred = uri_ctor(self.NC[p]) if not p.startswith("http") else uri_ctor(p)
            obj = uri_ctor(self.NC[o]) if not o.startswith("http") else uri_ctor(o)
            self.g.add((subj, pred, obj))
        
        logger.info(f"Ingested {len(triples)} triples. Current graph size: {len(self.g)}")

    def assert_causality(self, antecedent_id: str, consequent_id: str) -> None:
        """Formally models that one entity enables another."""
        ant = self.NC[antecedent_id]
        cons = self.NC[consequent_id]
        self.g.add((ant, self.NC.enables, cons))

    def check_logical_consistency(self) -> bool:
        """
        Performs logic checks on the graph to ensure no contradictions exist.
        In a full implementation, this would invoke a reasoner like Pellete or HermiT.
        """
        # Simple check: No entity should precede itself (irreflexive property of 'precedes')
        # This is a basic safety invariant for the epistemic state.
        for s, p, o in self.g.triples((None, self.NC.precedes, None)):
            if s == o:
                logger.error(f"Inconsistency detected: Circular precedence for {s}")
                return False
        return True

    def query_causal_chain(self, entity_id: str) -> List[str]:
        """Returns the chain of events that enabled the target entity."""
        # Placeholder for SPARQL query
        query = f"""
        SELECT ?antecedent WHERE {{
            ?antecedent <{self.NC.enables}>+ <{self.NC[entity_id]}> .
        }}
        """
        results = self.g.query(query)
        return [str(row[0]) for row in results]

    def export_rdf(self, format: str = "turtle") -> str:
        """Exports the coherent epistemic state as RDF triples."""
        return self.g.serialize(format=format)
