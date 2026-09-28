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
                        doc = {
                            "id": sid,
                            "is_number": is_num,
                            "title": item.get("title", ""),
                            "year": item.get("year"),
                            "status": item.get("status", "ACTIVE"),
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
        rrf_k: int = 60,
        apply_qco_boost: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Executes complete hybrid search pipeline:
        1. BM25 Sparse Search
        2. Dense Semantic Vector Search
        3. Reciprocal Rank Fusion (RRF)
        4. Exact Standard Number / Grade Match Boost
        5. Statutory QCO Regulatory Prioritization
        """
        if not query.strip():
            return []

        sparse_candidates = self.search_sparse(query, top_k=100)
        dense_candidates = self.search_dense(query, top_k=100)

        sparse_ranks: Dict[int, int] = {idx: rank + 1 for rank, (idx, _) in enumerate(sparse_candidates)}
        dense_ranks: Dict[int, int] = {idx: rank + 1 for rank, (idx, _) in enumerate(dense_candidates)}

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

            # Filters
            if status_filter and doc.get("status") != status_filter:
                continue
            if department_filter and department_filter.lower() not in doc.get("department", "").lower():
                continue

            r_sparse = sparse_ranks.get(idx, 999)
            r_dense = dense_ranks.get(idx, 999)

            # RRF formula: 1 / (k + rank)
            rrf_sparse = 1.0 / (rrf_k + r_sparse) if r_sparse <= 100 else 0.0
            rrf_dense = 1.0 / (rrf_k + r_dense) if r_dense <= 100 else 0.0
            base_rrf_score = rrf_sparse + rrf_dense

            # Regulatory QCO Mandate Check & Boost
            sid = doc["id"]
            qco_mandate = self.graph_service.check_qco_mandate(sid)
            is_mandatory = qco_mandate is not None

            score = base_rrf_score

            # Boost factor: mandatory QCO orders receive 30% boost in public procurement
            if apply_qco_boost and is_mandatory:
                score *= 1.30

            # Constraint & Environmental slot bonus
            c_bonus = ConstraintSlotService.evaluate_constraint_bonus(
                sid, doc.get("title", ""), doc.get("scope", ""), slots
            )
            score += c_bonus

            # Exact standard code match (e.g., user entered 'IS 2062' or 'IS 1786')
            doc_is_num = doc.get("is_number", "").upper()
            if exact_is_match_id and sid == exact_is_match_id:
                score += 2.0
            elif doc_is_num and doc_is_num in q_clean:
                score += 1.5

            # Material grade matches: e.g. 'Fe 500D' in IS 1786, 'E250' in IS 2062
            for kw in doc.get("keywords", []):
                if len(kw) >= 3 and kw.upper() in q_clean:
                    score += 0.25

            scored_results.append({
                "doc_idx": idx,
                "doc": doc,
                "score": score,
                "sparse_rank": r_sparse if r_sparse <= 100 else None,
                "dense_rank": r_dense if r_dense <= 100 else None,
                "base_rrf": base_rrf_score,
                "is_mandatory_qco": is_mandatory,
                "qco_mandate": qco_mandate
            })

        # Sort by final fused score descending
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        top_results = scored_results[:top_k]

        if not top_results:
            return []

        # Normalize top score to 1.0 scale
        max_score = max(r["score"] for r in top_results) or 1.0

        formatted_matches: List[Dict[str, Any]] = []
        q_tokens = DomainTokenizer.tokenize(query)

        for res in top_results:
            d = res["doc"]
            norm_score = round(min(1.0, res["score"] / max_score), 4)

            # Find matching terms
            doc_tokens = set(self.tokenized_corpus[res["doc_idx"]])
            matched_terms = [t for t in q_tokens if t in doc_tokens]

            match_payload = {
                "standard_id": d["id"],
                "is_number": d["is_number"],
                "title": d["title"],
                "year": d.get("year"),
                "status": d.get("status", "ACTIVE"),
                "department": d.get("department", ""),
                "committee": d.get("committee", ""),
                "score": norm_score,
                "sparse_rank": res["sparse_rank"],
                "dense_rank": res["dense_rank"],
                "is_mandatory_qco": res["is_mandatory_qco"],
                "mandatory_scheme": res["qco_mandate"]["mandatory_scheme"] if res["qco_mandate"] else None,
                "qco_order_name": res["qco_mandate"]["order_name"] if res["qco_mandate"] else None,
                "qco_effective_date": res["qco_mandate"].get("effective_date") if res["qco_mandate"] else None,
                "matched_terms": matched_terms
            }
            formatted_matches.append(match_payload)

        # Apply Domain Contrastive Reranking & Grade Matching
        reranked_matches = DomainReranker.rerank(query, formatted_matches, slots)
        return reranked_matches


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
