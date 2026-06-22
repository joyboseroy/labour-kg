"""
Build the Labour Law Knowledge Graph.

Node types:
  Act        - the parent legislation (old/new era)
  Provision  - individual section
  Concept    - legal concept (e.g. "retrenchment", "strike")

Edge types:
  HAS_PROVISION   Act -> Provision
  INVOKES         Provision -> Concept
  CROSS_REFS      Provision -> Provision
  SUPERSEDES      new Provision -> old Provision (concept-level bridge)

Outputs:
  graphs/labour_kg.graphml    (NetworkX, for analysis)
  graphs/concept_graph.graphml (concept-only projection, for centrality)

Run: python3 scripts/build_graph.py
"""

import os
import json
import networkx as nx
import pandas as pd
from collections import defaultdict

IN_PATH       = "data/processed/provisions_with_concepts.jsonl"
GRAPH_PATH    = "graphs/labour_kg.graphml"
CONCEPT_PATH  = "graphs/concept_graph.graphml"
os.makedirs("graphs", exist_ok=True)


def load_provisions() -> list:
    provisions = []
    with open(IN_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                provisions.append(json.loads(line))
    return provisions


def build_full_graph(provisions: list) -> nx.DiGraph:
    G = nx.DiGraph()

    # Add Act nodes
    acts_seen = set()
    for p in provisions:
        act_id = p["act"]
        if act_id not in acts_seen:
            G.add_node(act_id,
                       node_type="act",
                       era=p["era"],
                       short=p["short"])
            acts_seen.add(act_id)

    # Add Provision nodes and edges
    for p in provisions:
        prov_id = f"{p['act']}_s{p['section']}"
        G.add_node(prov_id,
                   node_type="provision",
                   act=p["act"],
                   era=p["era"],
                   short=p["short"],
                   section=p["section"],
                   title=p.get("title", ""),
                   orientation=p.get("orientation", "unknown"))

        # Act -> Provision
        G.add_edge(p["act"], prov_id, edge_type="HAS_PROVISION")

        # Provision -> Concept
        for concept in p.get("concepts", []):
            concept_id = f"concept::{concept.lower().strip()}"
            if not G.has_node(concept_id):
                G.add_node(concept_id,
                           node_type="concept",
                           label=concept.lower().strip())
            G.add_edge(prov_id, concept_id, edge_type="INVOKES")

    return G


def build_concept_graph(provisions: list) -> nx.Graph:
    """
    Concept-level co-occurrence graph.
    Two concepts connected if they appear in the same provision.
    Node attributes include era breakdown (how many old vs new provisions invoke it).
    """
    G = nx.Graph()

    concept_meta = defaultdict(lambda: {"old": 0, "new": 0, "provisions": set()})

    for p in provisions:
        concepts = [c.lower().strip() for c in p.get("concepts", [])]
        era = p["era"]
        prov_id = f"{p['act']}_s{p['section']}"

        for c in concepts:
            concept_meta[c][era] += 1
            concept_meta[c]["provisions"].add(prov_id)

    # Add nodes
    for concept, meta in concept_meta.items():
        G.add_node(concept,
                   node_type="concept",
                   old_count=meta["old"],
                   new_count=meta["new"],
                   total=meta["old"] + meta["new"],
                   n_provisions=len(meta["provisions"]))

    # Add edges from co-occurrence
    edge_weights = defaultdict(int)
    for p in provisions:
        concepts = list(set(c.lower().strip() for c in p.get("concepts", [])))
        from itertools import combinations
        for a, b in combinations(concepts, 2):
            key = tuple(sorted([a, b]))
            edge_weights[key] += 1

    for (a, b), w in edge_weights.items():
        if G.has_node(a) and G.has_node(b):
            G.add_edge(a, b, weight=w)

    return G


def compute_centrality_report(G_old: nx.Graph,
                               G_new: nx.Graph,
                               G_full: nx.Graph) -> pd.DataFrame:
    """
    Compare concept centrality between old and new systems.
    This is the core finding of the paper.
    """
    all_concepts = set(G_old.nodes) | set(G_new.nodes)

    bet_old = nx.betweenness_centrality(G_old, weight="weight") if len(G_old.nodes) > 1 else {}
    bet_new = nx.betweenness_centrality(G_new, weight="weight") if len(G_new.nodes) > 1 else {}
    deg_old = nx.degree_centrality(G_old) if len(G_old.nodes) > 1 else {}
    deg_new = nx.degree_centrality(G_new) if len(G_new.nodes) > 1 else {}

    rows = []
    for c in all_concepts:
        bo = round(bet_old.get(c, 0), 4)
        bn = round(bet_new.get(c, 0), 4)
        rows.append({
            "concept":          c,
            "bet_old":          bo,
            "bet_new":          bn,
            "bet_change":       round(bn - bo, 4),
            "deg_old":          round(deg_old.get(c, 0), 4),
            "deg_new":          round(deg_new.get(c, 0), 4),
            "old_provisions":   G_old.nodes[c].get("n_provisions", 0) if c in G_old else 0,
            "new_provisions":   G_new.nodes[c].get("n_provisions", 0) if c in G_new else 0,
            "status":           ("gained" if bn > bo else
                                 "lost"   if bn < bo else
                                 "stable" if bo > 0 else
                                 "absent"),
        })

    return pd.DataFrame(rows).sort_values("bet_change")


def main():
    if not os.path.exists(IN_PATH):
        print(f"Missing {IN_PATH} — run extract_concepts.py first.")
        return

    provisions = load_provisions()
    print(f"Loaded {len(provisions)} provisions with concepts.")

    # Full graph
    G_full = build_full_graph(provisions)
    nx.write_graphml(G_full, GRAPH_PATH)
    print(f"Full graph: {G_full.number_of_nodes()} nodes, {G_full.number_of_edges()} edges")

    # Concept graph (all provisions)
    G_concept = build_concept_graph(provisions)
    nx.write_graphml(G_concept, CONCEPT_PATH)
    print(f"Concept graph: {G_concept.number_of_nodes()} nodes, {G_concept.number_of_edges()} edges")

    # Split by era for comparison
    old_provisions = [p for p in provisions if p["era"] == "old"]
    new_provisions = [p for p in provisions if p["era"] == "new"]

    G_old = build_concept_graph(old_provisions)
    G_new = build_concept_graph(new_provisions)
    print(f"Old system graph: {G_old.number_of_nodes()} nodes, {G_old.number_of_edges()} edges")
    print(f"New system graph: {G_new.number_of_nodes()} nodes, {G_new.number_of_edges()} edges")

    nx.write_graphml(G_old, "graphs/concept_graph_old.graphml")
    nx.write_graphml(G_new, "graphs/concept_graph_new.graphml")

    # Centrality comparison — THE CORE FINDING
    report = compute_centrality_report(G_old, G_new, G_concept)
    report.to_csv("graphs/centrality_comparison.csv", index=False)

    print("\n── Concepts that LOST structural importance (old → new) ──")
    lost = report[report["status"] == "lost"].sort_values("bet_change")
    print(lost[["concept", "bet_old", "bet_new", "bet_change",
                "old_provisions", "new_provisions"]].head(15).to_string(index=False))

    print("\n── Concepts that GAINED structural importance ──")
    gained = report[report["status"] == "gained"].sort_values("bet_change", ascending=False)
    print(gained[["concept", "bet_old", "bet_new", "bet_change",
                  "old_provisions", "new_provisions"]].head(15).to_string(index=False))

    print("\n── Concepts ABSENT from new system ──")
    absent = report[(report["old_provisions"] > 0) & (report["new_provisions"] == 0)]
    print(absent[["concept", "bet_old", "old_provisions"]].to_string(index=False))


if __name__ == "__main__":
    main()
