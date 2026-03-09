from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
import uuid

class EvidenceObject(BaseModel):
    document_id: str
    extracted_text: str
    character_offsets: List[int]
    bounding_box: List[List[int]]

class NormalizedFeatures(BaseModel):
    standardized_name: Optional[str] = None
    phonetic_key: Optional[str] = None
    date_start: Optional[str] = None
    normalized_place: Optional[str] = None
    owner: Optional[str] = None
    plantation: Optional[str] = None
    embedding: Optional[List[float]] = None

class GraphNode(BaseModel):
    node_id: str = Field(default_factory=lambda: f"node_{uuid.uuid4().hex[:8]}")
    label: str
    normalized_data: NormalizedFeatures
    evidence: List[EvidenceObject] = Field(default_factory=list)

class EdgeStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    AUTO_MERGED = "AUTO_MERGED"

class HypothesisEdge(BaseModel):
    edge_id: str = Field(default_factory=lambda: f"edge_{uuid.uuid4().hex[:8]}")
    source_node_id: str
    target_node_id: str
    confidence_score: float
    explanation: str
    status: EdgeStatus = Field(default=EdgeStatus.PENDING_REVIEW)
    reviewed_by: Optional[str] = None