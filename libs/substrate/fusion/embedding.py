import torch
import torch.nn as nn
import torch.nn.functional as F

class EpistemicEmbeddingFusion(nn.Module):
    """
    Innovative algorithm to project incoming vector embeddings into the graph space.
    Ensures semantic similarity queries resolve directly to precise multi-hop graph traversals.
    """
    def __init__(self, vector_dim: int = 768, graph_space_dim: int = 768):
        super(EpistemicEmbeddingFusion, self).__init__()
        # Learned projection matrix W
        self.W = nn.Linear(vector_dim, graph_space_dim, bias=False)
        
    def forward(self, v_i: torch.Tensor) -> torch.Tensor:
        """Project vector v_i into graph space."""
        return self.W(v_i)

def contrastive_loss(e_i: torch.Tensor, proj_v_i: torch.Tensor, all_e_j: torch.Tensor, temperature: float = 0.07):
    """
    Loss function: L = -log[exp(sim(e_i, proj(v_i))) / sum exp(sim(e_j, proj(v_j)))]
    Optimizes the projection matrix W against ground-truth triples.
    """
    # Calculate cosine similarity
    def sim(a, b):
        return F.cosine_similarity(a, b, dim=-1)

    # Numerator: sim(e_i, proj(v_i))
    pos_sim = sim(e_i, proj_v_i) / temperature
    
    # Denominator: sum exp(sim(e_j, proj(v_i))) - matching current proj with all ground truth nodes
    # We expand proj_v_i to match the shape of all_e_j for batch computation
    # proj_v_i: [batch_size, dim], all_e_j: [num_samples, dim]
    
    # Sim(v_i, e_j) for all j
    # Use matrix multiplication for efficiency: [batch, dim] * [dim, num_samples] -> [batch, num_samples]
    logits = torch.matmul(proj_v_i, all_e_j.transpose(0, 1)) / temperature
    
    # LogSoftmax over the logits to get the log-probability of the positive match
    # Usually we use cross_entropy where the target is the index of the positive sample
    batch_size = e_i.size(0)
    targets = torch.arange(batch_size).to(e_i.device)
    
    loss = F.cross_entropy(logits, targets)
    return loss

class FusionTrainer:
    def __init__(self, model: EpistemicEmbeddingFusion, lr: float = 1e-4):
        self.model = model
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

    def train_step(self, vector_batch: torch.Tensor, graph_node_batch: torch.Tensor, all_graph_nodes: torch.Tensor):
        self.optimizer.zero_grad()
        
        # v_i -> proj(v_i)
        projected = self.model(vector_batch)
        
        # Calculate contrastive loss
        loss = contrastive_loss(graph_node_batch, projected, all_graph_nodes)
        
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
