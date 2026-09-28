"""
Knowledge Graph Service for Manak-SpecEngine.
Provides dual Neo4j driver and high-performance in-memory NetworkX graph engine
for querying BIS standards, normative citations, testing methods, and statutory QCO mandates.
"""

import os
import re
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import networkx as nx

# Optional Neo4j Driver
try:
    from neo4j import GraphDatabase, Driver
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False
    Driver = Any


class GraphService:
    """
    Unified Knowledge Graph Service supporting both Neo4j and In-Memory NetworkX fallback.
    Automatically populates from data/final_nodes_standards.csv, data/final_nodes_qcos.csv,
    and data/final_edges_all.csv.
    """

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None
    ):
        self.data_dir = data_dir or (Path(__file__).resolve().parent.parent.parent.parent / "data")
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "")
        self.neo4j_driver: Optional[Driver] = None
        self.use_neo4j = False

        # In-Memory Graph and Indices
        self.graph = nx.MultiDiGraph()
        self.standards_index: Dict[str, Dict[str, Any]] = {}
        self.qcos_index: Dict[str, Dict[str, Any]] = {}
        self.lookup_alias: Dict[str, str] = {}  # Normalized string -> canonical node ID
        self.superseded_by_index: Dict[str, str] = {}  # Old standard_id -> superseding standard_id
        self.qco_mandates_index: Dict[str, List[Dict[str, Any]]] = {}  # standard_id -> list of QCOs

        self._init_neo4j()
        self._load_in_memory_graph()

    def _init_neo4j(self) -> None:
        """Attempts connection to Neo4j if configured and available."""
        if HAS_NEO4J and self.neo4j_uri and self.neo4j_password:
            try:
                driver = GraphDatabase.driver(
                    self.neo4j_uri,
                    auth=(self.neo4j_user, self.neo4j_password),
                    connection_timeout=2.0
                )
                driver.verify_connectivity()
                self.neo4j_driver = driver
                self.use_neo4j = True
            except Exception:
                self.neo4j_driver = None
                self.use_neo4j = False

    def _canonicalize_key(self, text: str) -> str:
        """Produces a normalized lookup key for resilient mapping."""
        if not text:
            return ""
        cleaned = text.upper().strip()
        # Collapse separators (spaces, underscores, slashes, dashes, colons, parens)
        cleaned = re.sub(r"[\s\(\)/:\-_]+", "", cleaned)
        return cleaned

    def _load_in_memory_graph(self) -> None:
        """Loads standards nodes, QCO nodes, and relationship edges into NetworkX."""
        standards_file = self.data_dir / "final_nodes_standards.csv"
        qcos_file = self.data_dir / "final_nodes_qcos.csv"
        edges_file = self.data_dir / "final_edges_all.csv"

        # 1. Load Standards
        if standards_file.exists():
            with open(standards_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sid = row.get("standard_id", "").strip()
                    if not sid:
                        continue
                    node_data = {
                        "id": sid,
                        "type": "Standard",
                        "is_number": row.get("is_number", "").strip(),
                        "title": row.get("title", "").strip(),
                        "year": int(row.get("year")) if row.get("year", "").isdigit() else None,
                        "department": row.get("department", "").strip(),
                        "committee": row.get("committee", "").strip(),
                        "status": row.get("status", "ACTIVE").strip().upper(),
                        "amendments_count": int(row.get("amendments_count")) if row.get("amendments_count", "").isdigit() else 0,
                        "gazette_date": row.get("gazette_date", "")
                    }
                    self.standards_index[sid] = node_data
                    self.graph.add_node(sid, **node_data)

                    # Populate aliases for resilient lookups
                    self.lookup_alias[self._canonicalize_key(sid)] = sid
                    is_num = row.get("is_number", "")
                    if is_num:
                        self.lookup_alias[self._canonicalize_key(is_num)] = sid
                        # Also index bare numbers (e.g. '2062' -> 'IS_2062')
                        bare = re.sub(r"^(?:IS|IS/ISO|IS/IEC)\s*", "", is_num, flags=re.I).strip()
                        if bare:
                            self.lookup_alias[self._canonicalize_key(bare)] = sid

        # 2. Load QCOs
        if qcos_file.exists():
            with open(qcos_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    qid = row.get("qco_id", "").strip()
                    if not qid:
                        continue
                    node_data = {
                        "id": qid,
                        "type": "QCO",
                        "order_name": row.get("order_name", "").strip(),
                        "gazette_no": row.get("gazette_no", "").strip(),
                        "effective_date": row.get("effective_date", "").strip(),
                        "mandatory_scheme": row.get("mandatory_scheme", "Scheme-I").strip(),
                        "ministry_id": row.get("ministry_id", "").strip(),
                        "penal_clause": row.get("penal_clause", "").strip()
                    }
                    self.qcos_index[qid] = node_data
                    self.graph.add_node(qid, **node_data)
                    self.lookup_alias[self._canonicalize_key(qid)] = qid
                    order_name = row.get("order_name", "")
                    if order_name:
                        self.lookup_alias[self._canonicalize_key(order_name)] = qid

        # 3. Load Edges
        if edges_file.exists():
            with open(edges_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    src = row.get("source", "").strip()
                    tgt = row.get("target", "").strip()
                    rel = row.get("relationship", "").strip()
                    src_type = row.get("source_type", "Standard").strip()
                    tgt_type = row.get("target_type", "Standard").strip()
                    desc = row.get("description", "").strip()

                    if not src or not tgt or not rel:
                        continue

                    # Ensure nodes exist in graph even if only mentioned in edge
                    if not self.graph.has_node(src):
                        self.graph.add_node(src, id=src, type=src_type, is_number=src.replace("_", " "))
                    if not self.graph.has_node(tgt):
                        self.graph.add_node(tgt, id=tgt, type=tgt_type, is_number=tgt.replace("_", " "))

                    self.graph.add_edge(src, tgt, relationship=rel, description=desc)

                    # Update specialized indices
                    if rel == "MANDATED_BY" and tgt in self.qcos_index:
                        qco_info = self.qcos_index[tgt]
                        self.qco_mandates_index.setdefault(src, []).append(qco_info)

                    if rel == "SUPERSEDES":
                        # src SUPERSEDES tgt => tgt is SUPERSEDED_BY src
                        self.superseded_by_index[tgt] = src

    def resolve_standard_id(self, query: str) -> Optional[str]:
        """Resolves any variant of standard notation to its canonical standard_id."""
        if not query:
            return None
        norm_key = self._canonicalize_key(query)
        if norm_key in self.lookup_alias:
            return self.lookup_alias[norm_key]

        # Try prefixing with IS
        if not norm_key.startswith("IS"):
            with_is = f"IS{norm_key}"
            if with_is in self.lookup_alias:
                return self.lookup_alias[with_is]

        # Substring / fuzzy prefix match
        for k, sid in self.lookup_alias.items():
            if k == norm_key or (len(norm_key) >= 4 and (k.startswith(norm_key) or norm_key.startswith(k))):
                return sid

        return None

    def get_standard(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Retrieves standard metadata by standard_id, is_number, or alias."""
        sid = self.resolve_standard_id(identifier)
        if sid and sid in self.standards_index:
            return dict(self.standards_index[sid])
        if sid and self.graph.has_node(sid):
            return dict(self.graph.nodes[sid])
        return None

    def get_qco(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Retrieves QCO order metadata by ID or name."""
        norm_key = self._canonicalize_key(identifier)
        qid = self.lookup_alias.get(norm_key, identifier)
        if qid in self.qcos_index:
            return dict(self.qcos_index[qid])
        return None

    def check_qco_mandate(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Checks if a standard is mandated by any statutory QCO.
        Returns the primary QCO dictionary if mandated, else None.
        """
        sid = self.resolve_standard_id(identifier)
        if not sid:
            return None

        # Check direct index
        if sid in self.qco_mandates_index and self.qco_mandates_index[sid]:
            return self.qco_mandates_index[sid][0]

        # Check graph outgoing MANDATED_BY edges
        if self.graph.has_node(sid):
            for _, tgt, data in self.graph.out_edges(sid, data=True):
                if data.get("relationship") == "MANDATED_BY":
                    if tgt in self.qcos_index:
                        return self.qcos_index[tgt]
                    return dict(self.graph.nodes[tgt])

        # Also check if any superseding standard is mandated
        if sid in self.superseded_by_index:
            newer_sid = self.superseded_by_index[sid]
            return self.check_qco_mandate(newer_sid)

        return None

    def find_superseding_chain(self, identifier: str) -> List[Dict[str, Any]]:
        """
        Traces the historical replacement chain if a standard is superseded or withdrawn.
        Returns ordered list of historical and superseding standards.
        """
        sid = self.resolve_standard_id(identifier)
        if not sid:
            return []

        chain = []
        curr = sid
        visited = set()

        while curr and curr not in visited:
            visited.add(curr)
            node_data = self.get_standard(curr) or {"id": curr, "is_number": curr.replace("_", " "), "status": "UNKNOWN"}
            chain.append(node_data)
            # Find next superseding node
            curr = self.superseded_by_index.get(curr)

        return chain

    def get_1hop_neighbors(self, identifier: str, direction: str = "both") -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieves all 1-hop connected nodes categorized by relationship type.
        """
        sid = self.resolve_standard_id(identifier)
        if not sid or not self.graph.has_node(sid):
            return {
                "normative_references": [],
                "test_methods": [],
                "qco_mandates": [],
                "supersedes": [],
                "superseded_by": [],
                "referenced_by": []
            }

        categorized: Dict[str, List[Dict[str, Any]]] = {
            "normative_references": [],
            "test_methods": [],
            "qco_mandates": [],
            "supersedes": [],
            "superseded_by": [],
            "referenced_by": []
        }

        # Outgoing edges
        if direction in ("out", "both"):
            for _, tgt, data in self.graph.out_edges(sid, data=True):
                rel = data.get("relationship")
                node_info = dict(self.graph.nodes[tgt])
                node_info["relationship"] = rel
                node_info["description"] = data.get("description", "")

                if rel == "NORMATIVE_REF":
                    categorized["normative_references"].append(node_info)
                elif rel == "TESTED_BY":
                    categorized["test_methods"].append(node_info)
                elif rel == "MANDATED_BY":
                    categorized["qco_mandates"].append(node_info)
                elif rel == "SUPERSEDES":
                    categorized["supersedes"].append(node_info)

        # Incoming edges
        if direction in ("in", "both"):
            for src, _, data in self.graph.in_edges(sid, data=True):
                rel = data.get("relationship")
                node_info = dict(self.graph.nodes[src])
                node_info["relationship"] = f"INCOMING_{rel}"
                node_info["description"] = data.get("description", "")

                if rel in ("NORMATIVE_REF", "TESTED_BY"):
                    categorized["referenced_by"].append(node_info)
                elif rel == "SUPERSEDES":
                    categorized["superseded_by"].append(node_info)
                elif rel == "MANDATED_BY":
                    categorized["qco_mandates"].append(node_info)

        return categorized

    def get_2hop_neighborhood(self, identifier: str, max_nodes: int = 50) -> Dict[str, Any]:
        """
        Expands 2 hops around the target standard for interactive UI visualization (React Flow format).
        Returns { 'nodes': [...], 'links': [...] }.
        """
        sid = self.resolve_standard_id(identifier)
        if not sid or not self.graph.has_node(sid):
            return {"nodes": [], "links": []}

        nodes_map: Dict[str, Dict[str, Any]] = {}
        links_list: List[Dict[str, Any]] = []
        visited_nodes: Set[str] = {sid}
        visited_edges: Set[Tuple[str, str, str]] = set()

        # Add root node
        root_data = dict(self.graph.nodes[sid])
        root_data["is_root"] = True
        nodes_map[sid] = root_data

        # Queue of (node_id, current_hop)
        queue = [(sid, 0)]

        while queue and len(nodes_map) < max_nodes:
            curr_node, hop = queue.pop(0)
            if hop >= 2:
                continue

            # Traverse outgoing
            for _, tgt, data in self.graph.out_edges(curr_node, data=True):
                rel = data.get("relationship", "REL")
                edge_key = (curr_node, tgt, rel)
                if edge_key not in visited_edges:
                    visited_edges.add(edge_key)
                    links_list.append({
                        "source": curr_node,
                        "target": tgt,
                        "relationship": rel,
                        "description": data.get("description", "")
                    })

                if tgt not in nodes_map and len(nodes_map) < max_nodes:
                    tgt_data = dict(self.graph.nodes[tgt])
                    tgt_data["hop"] = hop + 1
                    nodes_map[tgt] = tgt_data
                    queue.append((tgt, hop + 1))

            # Traverse incoming (only for hop 0 to keep graph relevant)
            if hop == 0:
                for src, _, data in self.graph.in_edges(curr_node, data=True):
                    rel = data.get("relationship", "REL")
                    edge_key = (src, curr_node, rel)
                    if edge_key not in visited_edges:
                        visited_edges.add(edge_key)
                        links_list.append({
                            "source": src,
                            "target": curr_node,
                            "relationship": rel,
                            "description": data.get("description", "")
                        })

                    if src not in nodes_map and len(nodes_map) < max_nodes:
                        src_data = dict(self.graph.nodes[src])
                        src_data["hop"] = 1
                        nodes_map[src] = src_data
                        queue.append((src, 1))

        # Format nodes for React Flow / D3 graph rendering
        formatted_nodes = []
        for nid, ndata in nodes_map.items():
            label = ndata.get("is_number") or ndata.get("order_name") or ndata.get("title") or nid
            node_type = ndata.get("type", "Standard")
            status = ndata.get("status", "ACTIVE")
            formatted_nodes.append({
                "id": nid,
                "label": label,
                "title": ndata.get("title") or ndata.get("order_name", ""),
                "type": node_type,
                "status": status,
                "department": ndata.get("department", ""),
                "year": ndata.get("year"),
                "is_root": ndata.get("is_root", False),
                "hop": ndata.get("hop", 0)
            })

        return {
            "root_id": sid,
            "total_nodes": len(formatted_nodes),
            "total_links": len(links_list),
            "nodes": formatted_nodes,
            "links": links_list
        }

    def get_subgraph_for_standards(
        self,
        identifiers: List[str],
        include_qcos: bool = True,
        max_nodes: int = 60
    ) -> Dict[str, Any]:
        """
        Builds a combined connected subgraph linking multiple candidate standards.
        """
        all_nodes: Dict[str, Dict[str, Any]] = {}
        all_links: List[Dict[str, Any]] = []
        seen_edges: Set[Tuple[str, str, str]] = set()

        root_sids = []
        for ident in identifiers:
            sid = self.resolve_standard_id(ident)
            if sid and self.graph.has_node(sid):
                root_sids.append(sid)
                ndata = dict(self.graph.nodes[sid])
                ndata["is_root"] = True
                all_nodes[sid] = ndata

        # Connect inter-standard relationships and QCOs
        for sid in root_sids:
            for _, tgt, data in self.graph.out_edges(sid, data=True):
                rel = data.get("relationship")
                if not include_qcos and rel == "MANDATED_BY":
                    continue
                edge_key = (sid, tgt, rel)
                if edge_key not in seen_edges and len(all_nodes) < max_nodes:
                    seen_edges.add(edge_key)
                    all_links.append({
                        "source": sid,
                        "target": tgt,
                        "relationship": rel,
                        "description": data.get("description", "")
                    })
                    if tgt not in all_nodes:
                        all_nodes[tgt] = dict(self.graph.nodes[tgt])

        formatted_nodes = [
            {
                "id": nid,
                "label": d.get("is_number") or d.get("order_name") or nid,
                "title": d.get("title") or d.get("order_name", ""),
                "type": d.get("type", "Standard"),
                "status": d.get("status", "ACTIVE"),
                "is_root": d.get("is_root", False)
            }
            for nid, d in all_nodes.items()
        ]

        return {
            "total_nodes": len(formatted_nodes),
            "total_links": len(all_links),
            "nodes": formatted_nodes,
            "links": all_links
        }

    def stats(self) -> Dict[str, Any]:
        """Returns graph topological metrics and node counts."""
        rel_counts: Dict[str, int] = {}
        for _, _, data in self.graph.edges(data=True):
            r = data.get("relationship", "UNKNOWN")
            rel_counts[r] = rel_counts.get(r, 0) + 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "standards_nodes": len(self.standards_index),
            "qcos_nodes": len(self.qcos_index),
            "relationship_breakdown": rel_counts,
            "neo4j_connected": self.use_neo4j
        }


# Global singleton instance cache
_graph_service_instance: Optional[GraphService] = None


def get_graph_service(data_dir: Optional[Path] = None) -> GraphService:
    """Returns the singleton GraphService instance."""
    global _graph_service_instance
    if _graph_service_instance is None:
        _graph_service_instance = GraphService(data_dir=data_dir)
    return _graph_service_instance
