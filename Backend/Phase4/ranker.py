import numpy as np
import uuid
from typing import Tuple

from Phase4.models import GraphNode, HypothesisEdge, EdgeStatus


class HybridCandidateRanker:
    def __init__(self, review_threshold=0.70):
        self.review_threshold = review_threshold

    def _cosine_similarity(self, vec1: list, vec2: list) -> float:
        if not vec1 or not vec2: return 0.0
        v1, v2 = np.array(vec1), np.array(vec2)
        norm_v1, norm_v2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if norm_v1 == 0 or norm_v2 == 0: return 0.0
        return float(np.dot(v1, v2) / (norm_v1 * norm_v2))

    def evaluate_pair(self, node_a_dict: dict, node_b_dict: dict) -> HypothesisEdge:
        """Evaluates two node dictionaries retrieved from Postgres."""
        
        # 1. Hard Constraints (Chronology)
        year_a = int(node_a_dict.get('date_start', '0')[:4]) if node_a_dict.get('date_start') else 0
        year_b = int(node_b_dict.get('date_start', '0')[:4]) if node_b_dict.get('date_start') else 0
        
        constraint_msg = "Passed chronological constraints."
        if year_a > 0 and year_b > 0 and abs(year_a - year_b) > 90:
            return self._build_edge(node_a_dict, node_b_dict, 0.0, f"VETO: Improbable age gap ({abs(year_a - year_b)} years).", EdgeStatus.REJECTED)

        # 2. Base ML Score (Cosine Similarity)
        base_score = self._cosine_similarity(node_a_dict.get('embedding'), node_b_dict.get('embedding'))
        
        # 3. Contextual Overlap Boosts
        boost = 0.0
        explanations = []

        if node_a_dict.get('owner') and node_a_dict.get('owner') == node_b_dict.get('owner'):
            boost += 0.20
            explanations.append(f"Identical owner ({node_a_dict['owner']}).")

        if node_a_dict.get('plantation') and node_a_dict.get('plantation') == node_b_dict.get('plantation'):
            boost += 0.25
            explanations.append(f"Same plantation ({node_a_dict['plantation']}).")

        # 4. Final Math
        final_score = round(min(0.99, base_score + boost), 4)
        boost_msg = " Boosts: " + " ".join(explanations) if explanations else " No contextual overlap."
        full_explanation = f"Base ML Match: {round(base_score, 2)}.{boost_msg} {constraint_msg}"

        status = EdgeStatus.PENDING_REVIEW if final_score >= self.review_threshold else EdgeStatus.REJECTED
        
        return self._build_edge(node_a_dict, node_b_dict, final_score, full_explanation, status)

    def _build_edge(self, node_a, node_b, score, explanation, status) -> HypothesisEdge:
        return HypothesisEdge(
            edge_id=f"edge_{uuid.uuid4().hex[:8]}",
            source_node_id=node_a["node_id"],
            target_node_id=node_b["node_id"],
            confidence_score=score,
            explanation=explanation,
            status=status
        )