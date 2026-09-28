"""
Hybrid Retrieval Engine for Manak-SpecEngine.
Combines BM25 sparse keyword search, dense semantic vector retrieval,
Reciprocal Rank Fusion (RRF), cross-encoder scoring, and statutory QCO mandate boosting.
"""

import re
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer

from backend.app.services.graph_service import GraphService, get_graph_service
from backend.app.services.constraint_slot_service import ConstraintSlotService
from backend.app.services.domain_reranker import DomainReranker

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "for", "with", "in", "on", "at",
    "by", "from", "as", "is", "are", "was", "were", "be", "been", "that", "this",
    "it", "specification", "requirements", "standard", "indian", "code", "practice"
}


class DomainTokenizer:
    """
    Domain-aware tokenizer preserving BIS notations, grades, and technical identifiers.
    E.g.: 'IS 2062', 'Fe 500D', 'E250', 'PE 100', 'OPC 53', 'CRS', 'Scheme-I'.
    """

    @staticmethod
    def tokenize(text: str) -> List[str]:
        if not text:
            return []

        text = text.lower()
        # Normalize IS notations to unified tokens: 'is 2062' -> 'is_2062'
        text = re.sub(r"\bis\s+(\d+)\b", r"is_\1", text)
        text = re.sub(r"\bis/iso\s+(\d+)\b", r"is_iso_\1", text)
        text = re.sub(r"\bis/iec\s+(\d+)\b", r"is_iec_\1", text)
        text = re.sub(r"\bfe\s+(\d+[a-z]?)\b", r"fe_\1", text)

        # Extract words and tokens
        raw_tokens = re.findall(r"\b[a-z0-9_]{2,}\b", text)
        tokens = [t for t in raw_tokens if t not in STOPWORDS]
        return tokens


class HybridRetriever:
    """
    Hybrid Search Engine combining:
    1. Sparse BM25 lexical search with domain tokenization
    2. Dense semantic vector representation with sublinear TF-IDF embeddings
    3. Reciprocal Rank Fusion (RRF, k=60)
    4. Exact standard code and grade match boosting
    5. Statutory Quality Control Order (QCO) regulatory prioritization
    """

    def __init__(self, data_dir: Optional[Path] = None, graph_service: Optional[GraphService] = None):
        self.data_dir = data_dir or (Path(__file__).resolve().parent.parent.parent.parent / "data")
        self.graph_service = graph_service or get_graph_service(data_dir=self.data_dir)

        self.documents: List[Dict[str, Any]] = []
        self.corpus_texts: List[str] = []
        self.tokenized_corpus: List[List[str]] = []
        self.doc_id_to_index: Dict[str, int] = {}

        self.bm25: Optional[BM25Okapi] = None
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.dense_matrix: Optional[np.ndarray] = None

        self._load_corpus()
        self._build_indices()

    def _load_corpus(self) -> None:
        """Loads and consolidates standards from CSV and rich seed JSON."""
        seed_file = self.data_dir / "seed_data.json"
        standards_file = self.data_dir / "final_nodes_standards.csv"

        seen_sids: Set[str] = set()

        # 1. Load rich seed standards first (higher priority for scope/keywords)
        if seed_file.exists():
            try:
                with open(seed_file, "r", encoding="utf-8") as f:
                    seed_data = json.load(f)
                    for item in seed_data.get("standards", []):
                        is_num = item.get("is_number", "")
                        sid = self.graph_service.resolve_standard_id(is_num) or is_num.replace(" ", "_")
                        seen_sids.add(sid)
                        # Synchronize authoritative status from graph catalog if known
                        graph_std = self.graph_service.get_standard(sid)
                        status_val = (graph_std.get("status") if graph_std else None) or item.get("status", "ACTIVE")
                        doc = {
                            "id": sid,
                            "is_number": is_num,
                            "title": item.get("title", ""),
                            "year": item.get("year"),
                            "status": status_val.strip().upper(),
                            "department": item.get("department", ""),
                            "committee": item.get("committee", ""),
                            "scope": item.get("scope", ""),
                            "keywords": item.get("keywords", []),
                            "normative_references": item.get("normative_references", []),
                            "test_standards": item.get("test_standards", [])
                        }
                        self.documents.append(doc)
            except Exception as e:
                print(f"Warning: error loading seed_data.json in retriever: {e}")

        # 2. Load exhaustive catalog from CSV
        if standards_file.exists():
            with open(standards_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sid = row.get("standard_id", "").strip()
                    if not sid or sid in seen_sids:
                        continue
                    seen_sids.add(sid)
                    doc = {
                        "id": sid,
                        "is_number": row.get("is_number", "").strip(),
                        "title": row.get("title", "").strip(),
                        "year": int(row.get("year")) if row.get("year", "").isdigit() else None,
                        "status": row.get("status", "ACTIVE").strip().upper(),
                        "department": row.get("department", "").strip(),
                        "committee": row.get("committee", "").strip(),
                        "scope": row.get("title", ""),  # Fallback to title
                        "keywords": [],
                        "normative_references": [],
                        "test_standards": []
                    }
                    self.documents.append(doc)

        for idx, doc in enumerate(self.documents):
            self.doc_id_to_index[doc["id"]] = idx
            # Composite text for indexing
            kw_str = " ".join(doc.get("keywords", []))
            comp = f"{doc['is_number']} {doc['title']} {doc.get('department', '')} {doc.get('scope', '')} {kw_str}"
            self.corpus_texts.append(comp)

    def _build_indices(self) -> None:
        """Constructs BM25 index and dense semantic vector matrix."""
        # 1. BM25 Tokenization
        self.tokenized_corpus = [DomainTokenizer.tokenize(text) for text in self.corpus_texts]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

        # 2. Dense Semantic Vectorizer
        self.vectorizer = TfidfVectorizer(
            sublinear_tf=True,
            ngram_range=(1, 2),
            max_features=40000,
            tokenizer=DomainTokenizer.tokenize,
            token_pattern=None
        )
        self.dense_matrix = self.vectorizer.fit_transform(self.corpus_texts)

    def search_sparse(self, query: str, top_k: int = 50) -> List[Tuple[int, float]]:
        """Executes BM25 sparse lexical retrieval."""
        tokens = DomainTokenizer.tokenize(query)
        if not tokens or not self.bm25:
            return []
        scores = self.bm25.get_scores(tokens)
        top_indices = np.argsort(scores)[-top_k:][::-1]
        return [(int(idx), float(scores[idx])) for idx in top_indices if scores[idx] > 0.0]

    def search_dense(self, query: str, top_k: int = 50) -> List[Tuple[int, float]]:
        """Executes dense vector semantic similarity retrieval."""
        if not self.vectorizer or self.dense_matrix is None:
            return []
        q_vec = self.vectorizer.transform([query])
        # Cosine similarity dot product
        similarities = (self.dense_matrix * q_vec.T).toarray().flatten()
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [(int(idx), float(similarities[idx])) for idx in top_indices if similarities[idx] > 0.0]

    def search(
        self,
        query: str,
        top_k: int = 10,
        department_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        allow_superseded: bool = False,
        rrf_k: int = 60,
        apply_qco_boost: bool = True,
        evaluation_date: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid search pipeline:
        1. BM25 Sparse Search
        2. TF-IDF Character/Word N-Gram Vector Search
        3. Reciprocal Rank Fusion (RRF)
        4. Exact Standard Number / Grade Match Boost
        5. Temporal Statutory QCO Regulatory Prioritization
        By default (allow_superseded=False), filters out superseded and withdrawn records.
        Does NOT silently fall back to superseded records as current recommendations.
        """
        if not query.strip():
            return []

        sparse_candidates = self.search_sparse(query, top_k=100)
        dense_candidates = self.search_dense(query, top_k=100)

        sparse_ranks: Dict[int, int] = {idx: rank + 1 for rank, (idx, _) in enumerate(sparse_candidates)}
        dense_ranks: Dict[int, int] = {idx: rank + 1 for rank, (idx, _) in enumerate(dense_candidates)}
        sparse_scores: Dict[int, float] = {idx: s for idx, s in sparse_candidates}
        dense_scores: Dict[int, float] = {idx: s for idx, s in dense_candidates}

        all_candidate_indices = set(sparse_ranks.keys()).union(set(dense_ranks.keys()))
        if not all_candidate_indices:
            return []

        # Check for exact is_number or grade mention in query
        q_clean = query.upper()
        exact_is_match_id = self.graph_service.resolve_standard_id(query)
        slots = ConstraintSlotService.extract_slots(query)

        scored_results = []
        for idx in all_candidate_indices:
            doc = self.documents[idx]
            doc_status = doc.get("status", "ACTIVE")

            # Status Policy: exclude superseded and withdrawn standards from primary recommendations
            if not allow_superseded and doc_status in ("SUPERSEDED", "WITHDRAWN"):
                continue
            if status_filter and doc_status != status_filter:
                continue
            if department_filter and department_filter.lower() not in doc.get("department", "").lower():
                continue

            r_sparse = sparse_ranks.get(idx, 999)
            r_dense = dense_ranks.get(idx, 999)
            s_raw = sparse_scores.get(idx, 0.0)
            d_raw = dense_scores.get(idx, 0.0)

            # RRF formula: 1 / (k + rank)
            rrf_sparse = 1.0 / (rrf_k + r_sparse) if r_sparse <= 100 else 0.0
            rrf_dense = 1.0 / (rrf_k + r_dense) if r_dense <= 100 else 0.0
            base_rrf_score = rrf_sparse + rrf_dense

            # Check for exact code, grade, or constraint grounding
            sid = doc["id"]
            doc_is_num = doc.get("is_number", "").upper()
            is_exact_code = bool((exact_is_match_id and sid == exact_is_match_id) or (doc_is_num and (doc_is_num in q_clean or sid in q_clean)))
            has_grade_kw = any(len(kw) >= 3 and kw.upper() in q_clean for kw in doc.get("keywords", []))

            c_bonus, applied_rules = ConstraintSlotService.evaluate_constraint_bonus_with_rules(
                sid, doc.get("title", ""), doc.get("scope", ""), slots
            )

            has_technical_grounding = is_exact_code or has_grade_kw or (c_bonus > 0) or (d_raw >= 0.20 or s_raw >= 18.0)

            if has_technical_grounding:
                grounding_factor = 1.0
            else:
                grounding_factor = max(0.10, min(0.60, max(d_raw / 0.30, s_raw / 25.0)))

            # 1. Base Retrieval Component (Scaled RRF modulated by grounding factor)
            score = min(0.40, base_rrf_score * 12.0 * grounding_factor)

            # 2. Exact standard code match (e.g., user entered 'IS 2062' or 'IS 1786')
            if exact_is_match_id and sid == exact_is_match_id:
                score += 0.35
            elif doc_is_num and (doc_is_num in q_clean or sid in q_clean):
                score += 0.25

            # 3. Material grade matches: e.g. 'Fe 500D' in IS 1786, 'E250' in IS 2062
            if has_grade_kw:
                score += 0.08

            # 4. Constraint & Environmental slot bonus with verified clause citations
            score += min(0.20, c_bonus * 0.30)

            # 5. Regulatory QCO Mandate Check & Boost (only for active in-force QCOs AND grounded candidate)
            qco_eval = self.graph_service.evaluate_qco_applicability(sid, evaluation_date=evaluation_date)
            is_mandatory = bool(qco_eval and qco_eval.get("is_mandatory"))

            if apply_qco_boost and is_mandatory and has_technical_grounding:
                score += 0.08

            scored_results.append({
                "doc_idx": idx,
                "doc": doc,
                "score": score,
                "sparse_rank": r_sparse if r_sparse <= 100 else None,
                "dense_rank": r_dense if r_dense <= 100 else None,
                "base_rrf": base_rrf_score,
                "is_mandatory_qco": is_mandatory,
                "qco_eval": qco_eval,
                "applied_rules": applied_rules
            })

        # If no active standards matched, return empty list!
        # Do NOT silently fallback to historical/withdrawn standards as current recommendations.
        if not scored_results:
            return []

        # Sort by final fused score descending
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        top_results = scored_results[:top_k]

        if not top_results:
            return []

        formatted_matches: List[Dict[str, Any]] = []
        q_tokens = DomainTokenizer.tokenize(query)

        for res in top_results:
            d = res["doc"]
            # Heuristic ranking score
            ranking_score = round(min(0.99, max(0.01, res["score"])), 4)

            # Relative relevance rating (heuristic ranking score, not a calibrated probability)
            if ranking_score >= 0.65:
                rel_relevance = "STRONG"
            elif ranking_score >= 0.40:
                rel_relevance = "MODERATE"
            elif ranking_score >= 0.20:
                rel_relevance = "LOW"
            else:
                rel_relevance = "INSUFFICIENT"

            # Find matching terms
            doc_tokens = set(self.tokenized_corpus[res["doc_idx"]])
            matched_terms = [t for t in q_tokens if t in doc_tokens]

            qco_mandate = res["qco_eval"]

            match_payload = {
                "standard_id": d["id"],
                "is_number": d["is_number"],
                "title": d["title"],
                "year": d.get("year"),
                "status": d.get("status", "ACTIVE"),
                "department": d.get("department", ""),
                "committee": d.get("committee", ""),
                "score": ranking_score,
                "score_type": "HEURISTIC_RANKING",
                "ranking_score": ranking_score,
                "relative_relevance": rel_relevance,
                "confidence_level": rel_relevance,  # Backwards-compatible alias
                "has_sufficient_confidence": ranking_score >= 0.20,
                "sparse_rank": res["sparse_rank"],
                "dense_rank": res["dense_rank"],
                "is_mandatory_qco": res["is_mandatory_qco"],
                "mandatory_scheme": qco_mandate["mandatory_scheme"] if qco_mandate else None,
                "qco_order_name": qco_mandate["order_name"] if qco_mandate else None,
                "qco_effective_date": qco_mandate.get("effective_date_parsed") or qco_mandate.get("effective_date") if qco_mandate else None,
                "qco_temporal_status": qco_mandate.get("temporal_status") if qco_mandate else None,
                "qco_notes": qco_mandate.get("notes") if qco_mandate else None,
                "product_scope_verified": qco_mandate.get("product_scope_verified", False) if qco_mandate else False,
                "applied_constraints": res["applied_rules"],
                "matched_terms": matched_terms
            }
            formatted_matches.append(match_payload)

        # Apply Domain Contrastive Reranking & Grade Matching
        reranked_matches = DomainReranker.rerank(query, formatted_matches, slots)
        return reranked_matches

    def search_historical_reference(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Explicitly searches superseded and withdrawn standards for historical audit and reference.
        Never to be returned as current/active recommendations.
        """
        results = self.search(
            query=query,
            top_k=top_k * 2,
            allow_superseded=True,
            status_filter=None,
            apply_qco_boost=False
        )
        historical = [r for r in results if r.get("status") in ("SUPERSEDED", "WITHDRAWN")]
        for r in historical:
            r["is_historical_reference_only"] = True
            r["audit_warning"] = (
                "This standard is SUPERSEDED or WITHDRAWN in the official BIS catalog. "
                "It is provided strictly for historical audit or contract verification and "
                "must NOT be cited as a current specification in new procurement tenders."
            )
        return historical[:top_k]


# Global singleton instance cache
_hybrid_retriever_instance: Optional[HybridRetriever] = None


def get_hybrid_retriever(
    data_dir: Optional[Path] = None,
    graph_service: Optional[GraphService] = None
) -> HybridRetriever:
    """Returns singleton HybridRetriever instance."""
    global _hybrid_retriever_instance
    if _hybrid_retriever_instance is None:
        _hybrid_retriever_instance = HybridRetriever(data_dir=data_dir, graph_service=graph_service)
    return _hybrid_retriever_instance
