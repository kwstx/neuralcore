import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Any

class TemporalComplEx(nn.Module):
    """
    Differentiable Knowledge Graph Completion via Temporal ComplEx embeddings.
    Incorporates exponential decay for edge freshness.
    """
    def __init__(self, num_entities: int, num_relations: int, embedding_dim: int, decay_rate: float = 0.01) -> None:
        super(TemporalComplEx, self).__init__()
        self.embedding_dim = embedding_dim
        self.decay_rate = nn.Parameter(torch.tensor([decay_rate]))
        
        # Complex embeddings: (real, imag)
        self.entity_real = nn.Embedding(num_entities, embedding_dim)
        self.entity_imag = nn.Embedding(num_entities, embedding_dim)
        self.relation_real = nn.Embedding(num_relations, embedding_dim)
        self.relation_imag = nn.Embedding(num_relations, embedding_dim)
        
        # Initialization
        nn.init.xavier_uniform_(self.entity_real.weight)
        nn.init.xavier_uniform_(self.entity_imag.weight)
        nn.init.xavier_uniform_(self.relation_real.weight)
        nn.init.xavier_uniform_(self.relation_imag.weight)

    def forward(self, h_idx: torch.Tensor, r_idx: torch.Tensor, t_idx: torch.Tensor, tau: torch.Tensor, tau_now: torch.Tensor) -> torch.Tensor:
        """
        Computes the scoring function for potential triples.
        Score = Re((e_h ⊙ e_r) · conj(e_t)) * exp(-λ(τ_now - τ))
        """
        h_re, h_im = self.entity_real(h_idx), self.entity_imag(h_idx)
        r_re, r_im = self.relation_real(r_idx), self.relation_imag(r_idx)
        t_re, t_im = self.entity_real(t_idx), self.entity_imag(t_idx)
        
        # ComplEx scoring function: Re( (h_re + i*h_im) * (r_re + i*r_im) * (t_re - i*t_im) )
        # = h_re*r_re*t_re + h_im*r_im*t_re + h_re*r_im*t_im - h_im*r_re*t_im
        
        score = (h_re * r_re * t_re + 
                 h_im * r_im * t_re + 
                 h_re * r_im * t_im - 
                 h_im * r_re * t_im)
        
        # Sum over embedding dimensions
        score = torch.sum(score, dim=-1)
        
        # Temporal decay factor: exp(-λ(τ_now - τ))
        time_diff = tau_now - tau
        decay = torch.exp(-self.decay_rate * time_diff)
        
        return score * decay

def train_completion(model: TemporalComplEx, loader: torch.utils.data.DataLoader[Any], epochs: int = 10, lr: float = 1e-3, grad_clip: float = 1.0) -> TemporalComplEx:
    """
    Optimized via AdamW with gradient clipping to proactively surface knowledge gaps.
    """
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    
    for epoch in range(epochs):
        for h, r, t, tau, tau_now, labels in loader:
            optimizer.zero_grad()
            
            scores = model(h, r, t, tau, tau_now)
            # Binary Cross Entropy with Logits for triple validity
            loss = F.binary_cross_entropy_with_logits(scores, labels)
            
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            
            optimizer.step()
            
    return model
