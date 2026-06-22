"""
Generate figures for the paper.

Figures:
  1. Concept centrality comparison bar chart (old vs new, top 20 concepts)
  2. Network graph of concept co-occurrence (old system)
  3. Network graph of concept co-occurrence (new system)
  4. Scatter plot: old betweenness vs new betweenness (each point = concept)
  5. Worker-protective concept survival rate

Run: python3 scripts/analyse.py
Output: figures/
"""

import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

os.makedirs("figures", exist_ok=True)

TRADITION_COLOURS = {
    "worker_protective":   "#8b0000",
    "employer_protective": "#2f4f4f",
    "procedural":          "#4682b4",
    "definitional":        "#696969",
    "unknown":             "#aaaaaa",
}


def plot_centrality_comparison():
    path = "graphs/centrality_comparison.csv"
    if not os.path.exists(path):
        print("centrality_comparison.csv not found.")
        return

    df = pd.read_csv(path)
    # Top 20 by absolute change
    df["abs_change"] = df["bet_change"].abs()
    top = df.nlargest(20, "abs_change").sort_values("bet_change")

    fig, ax = plt.subplots(figsize=(10, 7))
    colours = ["#8b0000" if v < 0 else "#2e8b57" for v in top["bet_change"]]
    bars = ax.barh(top["concept"], top["bet_change"], color=colours)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Change in Betweenness Centrality (new minus old)")
    ax.set_title("Concepts Gaining and Losing Structural Importance\nIndian Labour Law Consolidation (44 Acts to 4 Codes)")
    red_patch   = mpatches.Patch(color="#8b0000", label="Lost importance in new system")
    green_patch = mpatches.Patch(color="#2e8b57", label="Gained importance in new system")
    ax.legend(handles=[red_patch, green_patch], fontsize=8)
    plt.tight_layout()
    plt.savefig("figures/centrality_change.png", dpi=150)
    plt.close()
    print("Saved: centrality_change.png")


def plot_scatter():
    path = "graphs/centrality_comparison.csv"
    if not os.path.exists(path):
        return
    df = pd.read_csv(path)
    df = df[(df["bet_old"] > 0) | (df["bet_new"] > 0)]

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(df["bet_old"], df["bet_new"], alpha=0.6, s=60, color="#4682b4")

    # Diagonal line (no change)
    lim = max(df["bet_old"].max(), df["bet_new"].max()) * 1.1
    ax.plot([0, lim], [0, lim], "k--", linewidth=0.8, alpha=0.5, label="No change")

    # Label outliers
    for _, row in df.iterrows():
        if abs(row["bet_change"]) > 0.05:
            ax.annotate(row["concept"],
                        (row["bet_old"], row["bet_new"]),
                        fontsize=7, alpha=0.8,
                        xytext=(5, 5), textcoords="offset points")

    ax.set_xlabel("Betweenness Centrality (old system)")
    ax.set_ylabel("Betweenness Centrality (new system)")
    ax.set_title("Concept Centrality: Old vs New Labour Law System\n(above diagonal = gained importance)")
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig("figures/centrality_scatter.png", dpi=150)
    plt.close()
    print("Saved: centrality_scatter.png")


def plot_concept_network(graph_path: str, title: str, out_name: str):
    if not os.path.exists(graph_path):
        print(f"Missing: {graph_path}")
        return

    G = nx.read_graphml(graph_path)
    if len(G.nodes) < 2:
        print(f"Graph too small: {graph_path}")
        return

    # Remove isolates for cleaner viz
    G.remove_nodes_from(list(nx.isolates(G)))

    pos = nx.spring_layout(G, weight="weight", seed=42, k=2.5)
    bet = nx.betweenness_centrality(G, weight="weight")

    node_sizes  = [max(100, bet.get(n, 0) * 5000 + 100) for n in G.nodes]
    edge_weights = [G[u][v].get("weight", 1) for u, v in G.edges]
    max_w = max(edge_weights) if edge_weights else 1
    edge_widths = [0.3 + 2.5 * w / max_w for w in edge_weights]

    fig, ax = plt.subplots(figsize=(14, 10))
    nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.3,
                           edge_color="#888888", ax=ax)
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes,
                           node_color="#4682b4", alpha=0.8, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=7, ax=ax)
    ax.set_title(title)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(f"figures/{out_name}", dpi=150)
    plt.close()
    print(f"Saved: {out_name}")


def summary_stats():
    print("\n── Summary Statistics ──")
    for path, label in [
        ("graphs/concept_graph_old.graphml", "Old system"),
        ("graphs/concept_graph_new.graphml", "New system"),
    ]:
        if os.path.exists(path):
            G = nx.read_graphml(path)
            bet = nx.betweenness_centrality(G, weight="weight")
            top5 = sorted(bet.items(), key=lambda x: -x[1])[:5]
            print(f"\n{label}: {G.number_of_nodes()} concepts, {G.number_of_edges()} edges")
            print("  Top 5 by betweenness:")
            for name, score in top5:
                print(f"    {name}: {score:.4f}")

    comp_path = "graphs/centrality_comparison.csv"
    if os.path.exists(comp_path):
        df = pd.read_csv(comp_path)
        absent = df[(df["old_provisions"] > 0) & (df["new_provisions"] == 0)]
        print(f"\nConcepts present in old system, absent in new: {len(absent)}")
        if not absent.empty:
            print(absent[["concept", "old_provisions", "bet_old"]].to_string(index=False))


if __name__ == "__main__":
    plot_centrality_comparison()
    plot_scatter()
    plot_concept_network(
        "graphs/concept_graph_old.graphml",
        "Labour Concept Network: Old System (4 Acts)",
        "concept_network_old.png"
    )
    plot_concept_network(
        "graphs/concept_graph_new.graphml",
        "Labour Concept Network: New System (4 Codes)",
        "concept_network_new.png"
    )
    summary_stats()
    print("\nAll figures saved to ./figures/")
