import sys
from rdflib import Graph
from pyshacl import validate
import os

def verify_ontology(data_path: str, shacl_path: str = None):
    """
    Validates an RDF graph against SHACL constraints.
    If shacl_path is not provided, it assumes the constraints are in the same file.
    """
    print(f"[*] Loading data graph from {data_path}...")
    data_graph = Graph()
    data_graph.parse(data_path, format="turtle")

    shacl_graph = None
    if shacl_path:
        print(f"[*] Loading SHACL constraints from {shacl_path}...")
        shacl_graph = Graph()
        shacl_graph.parse(shacl_path, format="turtle")
    else:
        print("[*] Assuming SHACL constraints are embedded in data graph.")
        shacl_graph = data_graph

    print("[*] Performing SHACL validation...")
    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shacl_graph,
        inference='owlrl', # Enable OWL 2 RL inference for consistency
        abort_on_first_error=False,
        meta_shacl=False,
        debug=False
    )

    if conforms:
        print("[+] Validation Success: Ontology is sound and conforms to SHACL constraints.")
        return True
    else:
        print("[-] Validation Failed!")
        print(results_text)
        return False

if __name__ == "__main__":
    ontology_dir = "ontology"
    core_ttl = os.path.join(ontology_dir, "core.ttl")
    
    if not os.path.exists(core_ttl):
        print(f"[!] Core ontology file not found at {core_ttl}")
        sys.exit(1)
        
    # Check if there's a specific SHACL schema directory
    shacl_dir = os.path.join(ontology_dir, "schema")
    shacl_files = [os.path.join(shacl_dir, f) for f in os.listdir(shacl_dir) if f.endswith(".ttl")] if os.path.exists(shacl_dir) else []
    
    success = True
    if shacl_files:
        for sf in shacl_files:
            if not verify_ontology(core_ttl, sf):
                success = False
    else:
        success = verify_ontology(core_ttl)
        
    if not success:
        sys.exit(1)
