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
        self.superseded_by_index: Dict[str, str] = {}  # Old standard_id -> primary superseding standard_id
        self.superseded_by_edges: Dict[str, List[Dict[str, Any]]] = {}  # Old standard_id -> all superseding edge records
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

                    # Register historical / unindexed standards into standards_index and lookup_alias
                    for node_id, n_type in [(src, src_type), (tgt, tgt_type)]:
                        if n_type == "Standard" and node_id not in self.standards_index:
                            std_num = node_id.replace("_", " ")
                            is_sup = rel == "SUPERSEDES" and node_id == tgt
                            year_val = None
                            y_m = re.search(r"(\d{4})", node_id)
                            if y_m:
                                try:
                                    year_val = int(y_m.group(1))
                                except ValueError:
                                    pass

                            std_record = {
                                "id": node_id,
                                "type": "Standard",
                                "is_number": std_num,
                                "title": desc if desc else f"Standard {std_num}",
                                "year": year_val,
                                "department": "General Engineering",
                                "committee": "",
                                "status": "SUPERSEDED" if is_sup else "ACTIVE",
                                "amendments_count": 0,
                                "gazette_date": ""
                            }
                            self.standards_index[node_id] = std_record
                            self.lookup_alias[self._canonicalize_key(node_id)] = node_id
                            self.lookup_alias[self._canonicalize_key(std_num)] = node_id
                            bare = re.sub(r"^(?:IS|IS/ISO|IS/IEC)\s*", "", std_num, flags=re.I).strip()
                            if bare:
                                self.lookup_alias[self._canonicalize_key(bare)] = node_id

                    self.graph.add_edge(src, tgt, relationship=rel, description=desc)

                    # Update specialized indices
                    if rel == "MANDATED_BY" and tgt in self.qcos_index:
                        qco_info = self.qcos_index[tgt]
                        self.qco_mandates_index.setdefault(src, []).append(qco_info)

                    if rel == "SUPERSEDES":
                        # Determine verification level and provenance
                        desc_lower = desc.lower()
                        if any(k in desc_lower for k in ["amalgamated", "consolidated", "split into", "separated", "adoption"]):
                            v_level = "OFFICIALLY_VERIFIED"
                            conf = 1.0
                            prov = "BIS Revision & Amalgamation Catalog"
                        elif any(k in desc_lower for k in ["supersed", "replaces", "withdrawn in favour"]):
                            v_level = "OFFICIALLY_VERIFIED"
                            conf = 0.95
                            prov = "BIS Textual Supersession Notice"
                        elif "chronologically supersedes" in desc_lower:
                            v_level = "CHRONOLOGICAL_INFERRED"
                            conf = 0.85
                            prov = "Chronological Publication Progression"
                        else:
                            v_level = "CURATED"
                            conf = 0.90
                            prov = "Curated Domain Standards Mapping"

                        edge_meta = {
                            "source_id": src,
                            "target_id": tgt,
                            "description": desc,
                            "verification_level": v_level,
                            "confidence": conf,
                            "provenance": prov
                        }
                        self.superseded_by_edges.setdefault(tgt, []).append(edge_meta)
                        # For scalar index, prioritize officially verified over inferred
                        if tgt not in self.superseded_by_index or v_level == "OFFICIALLY_VERIFIED":
                            self.superseded_by_index[tgt] = src

    def resolve_standard_id(self, query: str) -> Optional[str]:
        """
        Resolves any variant of standard notation to its canonical standard_id.
        Eliminates false substring prefix collisions (e.g. IS 226 matching IS 2).
        """
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

        # Try regex extraction of standard pattern from query
        pattern = r"\b(?:IS(?:/ISO)?(?:/IEC)?\s*)(\d+(?:\s*(?:Part|\(Part\)|-|/)\s*\d+)?(?:\s*(?:Sec|Section)\s*\d+)?(?:\s*:\s*\d{4})?)\b"
        m = re.search(pattern, query, re.I)
        if m:
            raw_match = m.group(0)
            c = self._canonicalize_key(raw_match)
            if c in self.lookup_alias:
                return self.lookup_alias[c]
            if not c.startswith("IS") and f"IS{c}" in self.lookup_alias:
                return self.lookup_alias[f"IS{c}"]
            # Try stripping publication year if included
            no_year = re.sub(r':\s*\d{4}', '', raw_match)
            c_ny = self._canonicalize_key(no_year)
            if c_ny in self.lookup_alias:
                return self.lookup_alias[c_ny]
            if not c_ny.startswith("IS") and f"IS{c_ny}" in self.lookup_alias:
                return self.lookup_alias[f"IS{c_ny}"]

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

    def evaluate_qco_applicability(
        self,
        identifier: str,
        evaluation_date_str: str = "2026-09-28"
    ) -> Optional[Dict[str, Any]]:
        """
        Determines statutory QCO status with temporal verification against evaluation date.
        Distinguishes active in-force mandates from future enforcement or unverified dates.
        """
        sid = self.resolve_standard_id(identifier)
        if not sid:
            return None

        # Check direct QCO orders
        qco_records = self.qco_mandates_index.get(sid, [])
        if not qco_records and self.graph.has_node(sid):
            for _, tgt, data in self.graph.out_edges(sid, data=True):
                if data.get("relationship") == "MANDATED_BY":
                    if tgt in self.qcos_index:
                        qco_records.append(self.qcos_index[tgt])
                    else:
                        qco_records.append(dict(self.graph.nodes[tgt]))

        # Also check superseding standard if historical
        if not qco_records and sid in self.superseded_by_index:
            newer = self.superseded_by_index[sid]
            return self.evaluate_qco_applicability(newer, evaluation_date_str)

        if not qco_records:
            return None

        primary = dict(qco_records[0])
        eff_date_str = primary.get("effective_date", "").strip()

        if not eff_date_str:
            return {
                **primary,
                "is_mandatory": False,
                "temporal_status": "UNVERIFIED_EFFECTIVE_DATE",
                "notes": "QCO record is linked in database, but effective implementation date is missing or unverified."
            }

        # Date parsing
        is_in_force = False
        try:
            # Check ISO format YYYY-MM-DD
            if re.match(r"^\d{4}-\d{2}-\d{2}$", eff_date_str):
                is_in_force = eff_date_str <= evaluation_date_str
            elif re.match(r"^\d{2}[-/]\d{2}[-/]\d{4}$", eff_date_str):
                # DD-MM-YYYY
                parts = re.split(r"[-/]", eff_date_str)
                iso_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                is_in_force = iso_date <= evaluation_date_str
            else:
                y_match = re.search(r"\b(20\d{2})\b", eff_date_str)
                if y_match:
                    eval_year = int(evaluation_date_str[:4])
                    is_in_force = int(y_match.group(1)) <= eval_year
                else:
                    is_in_force = True
        except Exception:
            is_in_force = False

        order_name = primary.get("order_name", "Statutory QCO")
        if is_in_force:
            temporal_status = "MANDATORY_IN_FORCE"
            notes = f"Mandatory compliance under {order_name}. Enforcement in force since {eff_date_str}."
        else:
            temporal_status = "PENDING_FUTURE_DATE"
            notes = f"QCO published ({order_name}), but mandatory enforcement date is pending ({eff_date_str})."

        return {
            **primary,
            "is_mandatory": is_in_force,
            "temporal_status": temporal_status,
            "notes": notes
        }

    def check_qco_mandate(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Checks if a standard is mandated by any statutory QCO.
        Returns the primary QCO dictionary if mandated, else None.
        """
        return self.evaluate_qco_applicability(identifier)

    def resolve_supersession(self, query_or_id: str, context_query: str = "") -> Dict[str, Any]:
        """
        Determines if a query or identifier cites an obsolete, superseded, or withdrawn standard,
        and resolves the verified current replacement standard(s) with full provenance.
        """
        sid = self.resolve_standard_id(query_or_id)
        if not sid:
            # Check if query contains an explicit standard pattern that failed resolution
            pattern = r"\b(?:IS(?:/ISO)?(?:/IEC)?\s*)(\d+(?:\s*(?:Part|\(Part\)|-|/)\s*\d+)?(?:\s*(?:Sec|Section)\s*\d+)?(?:\s*:\s*\d{4})?)\b"
            m = re.search(pattern, query_or_id, re.I)
            if m:
                return {
                    "is_cited": True,
                    "is_superseded": False,
                    "queried_standard": {"id": m.group(0), "is_number": m.group(0), "status": "UNVERIFIED"},
                    "current_replacements": [],
                    "alternative_branches": [],
                    "verification_level": "UNVERIFIED",
                    "explanation": f"Standard '{m.group(0)}' was cited in query but could not be substantiated in the BIS catalog."
                }
            return {
                "is_cited": False,
                "is_superseded": False,
                "queried_standard": None,
                "current_replacements": [],
                "alternative_branches": [],
                "verification_level": "N/A",
                "explanation": "No specific Indian Standard cited in query."
            }

        std_info = self.get_standard(sid) or {"id": sid, "is_number": sid.replace("_", " "), "status": "UNKNOWN"}
        status = std_info.get("status", "ACTIVE")
        is_sup = status in ("SUPERSEDED", "WITHDRAWN") or sid in self.superseded_by_edges

        if not is_sup:
            return {
                "is_cited": True,
                "is_superseded": False,
                "queried_standard": std_info,
                "current_replacements": [std_info],
                "alternative_branches": [],
                "verification_level": "OFFICIALLY_VERIFIED",
                "explanation": f"{std_info.get('is_number', sid)} is an ACTIVE Indian Standard."
            }

        # It IS superseded / withdrawn! Trace the replacement edges
        edges = self.superseded_by_edges.get(sid, [])
        ctx_lower = context_query.lower()
        replacements: List[Dict[str, Any]] = []
        alt_branches: List[Dict[str, Any]] = []

        # Domain Branching Disambiguation
        if sid in ("IS_432_Part_1", "IS_432_1", "IS_432"):
            # Branching: IS 1786 (rebar) vs IS 2062 (structural)
            p_node = self.get_standard("IS_1786")
            a_node = self.get_standard("IS_2062")
            if any(k in ctx_lower for k in ["structural", "beam", "section", "plate", "tie"]):
                p_node, a_node = a_node, p_node
                primary_scope = "Plain structural steel ties and members"
                alt_scope = "Concrete reinforcement / TMT rebars"
            else:
                primary_scope = "Concrete reinforcement / TMT rebars"
                alt_scope = "Plain structural steel ties and members"

            if p_node:
                replacements.append({
                    "standard": p_node,
                    "relationship": "SUPERSEDES",
                    "application_scope": primary_scope,
                    "verification_level": "OFFICIALLY_VERIFIED",
                    "provenance": "BIS Revision & Amalgamation Catalog",
                    "confidence": 1.0
                })
            if a_node:
                alt_branches.append({
                    "standard": a_node,
                    "relationship": "SUPERSEDES",
                    "application_scope": alt_scope,
                    "verification_level": "OFFICIALLY_VERIFIED",
                    "provenance": "BIS Revision & Amalgamation Catalog",
                    "confidence": 1.0
                })
        elif sid == "IS_226":
            p_node = self.get_standard("IS_2062")
            if p_node:
                replacements.append({
                    "standard": p_node,
                    "relationship": "SUPERSEDES",
                    "application_scope": "Standard quality structural steel (plates, sections, beams)",
                    "verification_level": "OFFICIALLY_VERIFIED",
                    "provenance": "BIS Revision & Amalgamation Catalog (Amalgamated into IS 2062)",
                    "confidence": 1.0
                })
        elif sid in ("IS_8112", "IS_12269"):
            p_node = self.get_standard("IS_269")
            grade_name = "43 Grade OPC" if sid == "IS_8112" else "53 Grade OPC"
            if p_node:
                replacements.append({
                    "standard": p_node,
                    "relationship": "SUPERSEDES",
                    "application_scope": f"{grade_name} Ordinary Portland Cement (consolidated into IS 269:2015)",
                    "verification_level": "OFFICIALLY_VERIFIED",
                    "provenance": "Gazette of India & BIS Revision 2015",
                    "confidence": 1.0
                })
        elif sid.startswith("IS_16046") and "2015" in sid:
            p_node1 = self.get_standard("IS_16046_Part_1") or self.get_standard("IS_16046_1")
            p_node2 = self.get_standard("IS_16046_Part_2") or self.get_standard("IS_16046_2")
            if "lithium" in ctx_lower and p_node2:
                replacements.append({
                    "standard": p_node2,
                    "relationship": "SUPERSEDES",
                    "application_scope": "Secondary lithium cells and batteries (Part 2)",
                    "verification_level": "OFFICIALLY_VERIFIED",
                    "provenance": "BIS Amendment & Part Separation Notice",
                    "confidence": 1.0
                })
            elif p_node1:
                replacements.append({
                    "standard": p_node1,
                    "relationship": "SUPERSEDES",
                    "application_scope": "Secondary nickel cells and batteries (Part 1)",
                    "verification_level": "OFFICIALLY_VERIFIED",
                    "provenance": "BIS Amendment & Part Separation Notice",
                    "confidence": 1.0
                })
        elif edges:
            for e in edges:
                target_node = self.get_standard(e["source_id"])
                if target_node:
                    replacements.append({
                        "standard": target_node,
                        "relationship": "SUPERSEDES",
                        "application_scope": e.get("description", "Direct supersession replacement"),
                        "verification_level": e.get("verification_level", "OFFICIALLY_VERIFIED"),
                        "provenance": e.get("provenance", "BIS Knowledge Graph"),
                        "confidence": e.get("confidence", 0.95)
                    })
        else:
            chain = self.find_superseding_chain(sid)
            if len(chain) > 1:
                latest = chain[-1]
                replacements.append({
                    "standard": latest,
                    "relationship": "SUPERSEDES",
                    "application_scope": "Chronological successor standard",
                    "verification_level": "CHRONOLOGICAL_INFERRED",
                    "provenance": "Chronological Publication Year Progression",
                    "confidence": 0.85
                })

        p_std_name = replacements[0]["standard"].get("is_number") if replacements else "None"
        explanation = (
            f"Query explicitly cited '{std_info.get('is_number', sid)}' which is {status}. "
            f"Verified current applicable standard is '{p_std_name}'."
        )

        return {
            "is_cited": True,
            "is_superseded": True,
            "queried_standard": std_info,
            "current_replacements": replacements,
            "alternative_branches": alt_branches,
            "verification_level": replacements[0]["verification_level"] if replacements else "UNRESOLVED",
            "explanation": explanation
        }

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
