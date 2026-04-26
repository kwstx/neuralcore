import torch
import torch.nn as nn
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Dict, Any, Optional, Tuple, List, cast

class GCNLayer(nn.Module):
    """
    A lightweight Graph Convolutional Network layer for fusing knowledge graph context.
    Uses a simple neighborhood aggregation: X' = sigma(A * X * W)
    """
    def __init__(self, in_features: int, out_features: int) -> None:
        super(GCNLayer, self).__init__()
        self.linear = nn.Linear(in_features, out_features)
        self.relu = nn.ReLU()

    def forward(self, node_features: torch.Tensor, adj_matrix: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for GCN.
        node_features: [N, in_features]
        adj_matrix: [N, N]
        """
        # Neighborhood aggregation
        support = torch.matmul(adj_matrix, node_features)
        # Linear transformation
        output = self.linear(support)
        return self.relu(output)

class NeuroSemanticEncoder:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2') -> None:
        """
        Initializes the Neuro-Semantic Encoder.
        Fuses LLM-based semantic embeddings with GCN-based structural embeddings.
        """
        # MiniLM-L6-v2 produces 384-dim embeddings
        self.transformer: SentenceTransformer = SentenceTransformer(model_name)
        
        # Projection layer to reach 768 dimensions as requested
        self.projection: nn.Linear = nn.Linear(384, 768)
        
        # GCN layer for knowledge graph fusion
        self.gcn: GCNLayer = GCNLayer(768, 768)
        
        # Fusion layer to integrate text and graph context
        self.fusion_gate: nn.Linear = nn.Linear(768 * 2, 768)
        self.layernorm: nn.LayerNorm = nn.LayerNorm(768)

    def encode(self, text: str, graph_context: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """
        Generates a 768-dimensional neuro-semantic embedding.
        
        Args:
            text (str): The textual description or event payload.
            graph_context (dict, optional): A dictionary containing 'adj' (Adjacency Matrix) 
                and 'features' (Node Features) for GCN processing.
        
        Returns:
            np.ndarray: A 768-dimensional float32 vector.
        """
        # 1. Compute Base Semantic Embedding via MiniLM
        with torch.no_grad():
            base_emb = self.transformer.encode(text, convert_to_tensor=True)
            projected_text = self.projection(base_emb) # [768]
        
        if graph_context is not None:
            # 2. Compute Structural Embedding via GCN
            adj = graph_context['adj']
            node_features = graph_context['features']
            
            graph_output = self.gcn(node_features, adj) # [N, 768]
            
            # Global Average Pooling for graph representation
            pooled_graph = torch.mean(graph_output, dim=0) # [768]
            
            # 3. Non-linear Fusion
            combined = torch.cat([projected_text, pooled_graph], dim=-1)
            fused = torch.tanh(self.fusion_gate(combined))
            final_emb = self.layernorm(fused)
            return cast(np.ndarray, final_emb.detach().cpu().numpy())
        
        return cast(np.ndarray, projected_text.detach().cpu().numpy())

    def prefix_payload(self, payload: bytes, embedding: np.ndarray) -> bytes:
        """
        Prefixes the binary payload with the 768-dimensional embedding vector.
        Total prefix length: 768 * 4 = 3072 bytes.
        """
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding, dtype=np.float32)
        
        emb_bytes = embedding.astype(np.float32).tobytes()
        return emb_bytes + payload

    @staticmethod
    def extract_embedding(raw_data: bytes) -> Tuple[np.ndarray, bytes]:
        """
        Separates the embedding prefix from the actual payload.
        """
        emb_size = 768 * 4
        embedding = np.frombuffer(raw_data[:emb_size], dtype=np.float32)
        payload = raw_data[emb_size:]
        return embedding, payload
