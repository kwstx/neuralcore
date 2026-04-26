from typing import Annotated, TypeVar
import numpy as np

# Define a type for 768-dimensional embedding vectors
# We use Annotated to hold metadata about the expected shape, 
# which can be used by runtime validators or static analysis plugins.
EmbeddingVector = Annotated[np.ndarray, (768,)]

# Type variable for generics
T = TypeVar("T")

def validate_embedding(vec: np.ndarray) -> EmbeddingVector:
    """
    Runtime validation for embedding dimensions.
    """
    if vec.shape != (768,):
        raise ValueError(f"Expected embedding shape (768,), got {vec.shape}")
    return vec
