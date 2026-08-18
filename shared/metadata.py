from pydantic import BaseModel, ConfigDict
from numpy.typing import NDArray

class CollectionData(BaseModel):
    """Metadata for a document chunk."""


    model_config = ConfigDict(arbitrary_types_allowed = True)
    
    name: str
    text: str
    sourcefile: str
    is_chunked: bool
    dense_vector: list|NDArray = None
    ichunk: int = 1 
    chunks: list = [1]
    
