# -*- coding: utf-8 -*-
"""
Network analysis pipeline for boardmembers_2024.csv
Reproduces the methodology of Battiston & Catanzaro (2004)
"Statistical Properties of Corporate Board and Director Networks"
"""

import os
import math
import random
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms import bipartite
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import poisson

# ── Config ─────────────────────────────────────────────────────────────────
INPUT_CSV  = "boardmembers_2024.csv"
RESULTS    = "results"
DATASET_LABEL = "PT 2024"

os.makedirs(RESULTS, exist_ok=True)

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "font.size":        11,
})

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1 — Build bipartite graph
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 1 — Build bipartite graph")
print("="*60)

df = pd.read_csv(INPUT_CSV)
df.columns = df.columns.str.strip()
# CSV has 'name' (director) and 'company'
df = df.rename(columns={"name": "director"})
df = df.dropna(subset=["director", "company"])
df = df.drop_duplicates(subset=["director", "company"])

companies_list = df["company"].unique().tolist()
directors_list = df["director"].unique().tolist()

G_bipartite = nx.Graph()
G_bipartite.add_nodes_from(companies_list, bipartite=0)
G_bipartite.add_nodes_from(directors_list, bipartite=1)
for _, row in df.iterrows():
    G_bipartite.add_edge(row["company"], row["director"])

companies = set(n for n, d in G_bipartite.nodes(data=True) if d.get("bipartite") == 0)
directors = set(n for n, d in G_bipartite.nodes(data=True) if d.get("bipartite") == 1)

print(f"  Companies : {len(companies)}")
print(f"  Directors : {len(directors)}")
print(f"  Edges     : {G_bipartite.number_of_edges()}")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2 — One-mode projections
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 2 — One-mode projections")
print("="*60)

board_net    = bipartite.weighted_projected_graph(G_bipartite, companies)
director_net = bipartite.weighted_projected_graph(G_bipartite, directors)

print(f"  Board network    : {board_net.number_of_nodes()} nodes, {board_net.number_of_edges()} edges")
print(f"  Director network : {director_net.number_of_nodes()} nodes, {director_net.number_of_edges()} edges")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3 — Table 1 metrics
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 3 — Table 1 metrics")
print("="*60)

def compute_metrics(G, label):
    N  = G.number_of_nodes()
    E  = G.number_of_edges()

    # Giant component
    ccs = list(nx.connected_components(G))
    largest_cc = max(ccs, key=len)
    Nc = len(largest_cc)
    Nc_over_N = Nc / N
    G_giant = G.subgraph(largest_cc).copy()

    # k/kc
    k_avg = np.mean([d for _, d in G.degree()])
    kc    = N - 1
    k_over_kc_pct = (k_avg / kc) * 100

    # betweenness (on giant component only)
    bet_dict = nx.betweenness_centrality(G_giant, normalized=False)
    b_avg    = np.mean(list(bet_dict.values()))
    b_over_N = b_avg / N

    # clustering (whole network)
    C_bar = nx.average_clustering(G)

    # average shortest path (giant component)
    Nc_giant = G_giant.number_of_nodes()
    if Nc_giant > 2000:
        sample_nodes = random.sample(list(G_giant.nodes()), 500)
        lengths = []
        for src in sample_nodes:
            sp = nx.single_source_shortest_path_length(G_giant, src)
            lengths.extend(sp.values())
        d_avg = np.mean(lengths)
    else:
        d_avg = nx.average_shortest_path_length(G_giant)

    return {
        "label":       label,
        "N":           N,
        "E":           E,
        "Nc/N":        round(Nc_over_N, 3),
        "k/kc (%)":    round(k_over_kc_pct, 3),
        "b/N":         round(b_over_N, 3),
        "C":           round(C_bar, 3),
        "d":           round(d_avg, 2),
        # keep for later steps
        "_k_avg":      k_avg,
        "_G_giant":    G_giant,
        "_bet_dict":   bet_dict,
        "_Nc":         Nc,
    }

metrics_board    = compute_metrics(board_net,    f"{DATASET_LABEL} Board")
metrics_director = compute_metrics(director_net, f"{DATASET_LABEL} Director")

# Paper reference values
paper_rows = [
    {"label": "Board IT'86",    "N": 221,  "E": 1295,  "Nc/N": 0.97, "k/kc (%)": 5.29, "b/N": 0.736, "C": 0.356, "d": 3.6},
    {"label": "Board IT'02",    "N": 240,  "E": 636,   "Nc/N": 0.82, "k/kc (%)": 2.22, "b/N": 0.875, "C": 0.318, "d": 4.4},
    {"label": "Board US'99",    "N": 916,  "E": 3321,  "Nc/N": 0.87, "k/kc (%)": 1.57, "b/N": 1.080, "C": 0.376, "d": 4.6},
    {"label": "Director IT'86", "N": 2378, "E": 23603, "Nc/N": 0.92, "k/kc (%)": 0.84, "b/N": 1.116, "C": 0.899, "d": 2.7},
    {"label": "Director IT'02", "N": 1906, "E": 12815, "Nc/N": 0.84, "k/kc (%)": 0.71, "b/N": 1.206, "C": 0.915, "d": 3.6},
    {"label": "Director US'99", "N": 7680, "E": 55437, "Nc/N": 0.89, "k/kc (%)": 0.79, "b/N": 1.384, "C": 0.884, "d": 3.7},
]

display_keys = ["label", "N", "E", "Nc/N", "k/kc (%)", "b/N", "C", "d"]

def row_for_display(m):
    return {k: m[k] for k in display_keys}

table1_rows = [row_for_display(metrics_board), row_for_display(metrics_director)] + paper_rows
table1_df   = pd.DataFrame(table1_rows)
print("\n" + table1_df.to_string(index=False))
table1_df.to_csv(f"{RESULTS}/table1.csv", index=False)

# ═══════════════════════════════════════════════════════════════════════════
# STEP 4 — Small World check
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 4 — Small World check")
print("="*60)

def small_world_check(m, G, label):
    N     = m["N"]
    E     = m["E"]
    k_avg = m["_k_avg"]
    C_bar = m["C"]
    d     = m["d"]

    p        = (2 * E) / (N * (N - 1))
    C_random = p
    d_random = math.log(N) / math.log(k_avg) if k_avg > 1 else float("inf")
    ratio    = C_bar / C_random if C_random > 0 else float("inf")
    is_sw    = ratio > 10 and abs(d - d_random) / d_random < 1.0

    print(f"\n  {label}")
    print(f"    C_real={C_bar:.3f}  C_random={C_random:.4f}  ratio={ratio:.1f}x")
    print(f"    d_real={d:.2f}    d_random={d_random:.2f}")
    print(f"    => Small World: {'YES' if is_sw else 'NO'}")
    return {"label": label, "C_real": C_bar, "C_random": round(C_random, 5),
            "C_ratio": round(ratio, 1), "d_real": d, "d_random": round(d_random, 2),
            "small_world": is_sw}

sw_board    = small_world_check(metrics_board,    board_net,    f"{DATASET_LABEL} Board")
sw_director = small_world_check(metrics_director, director_net, f"{DATASET_LABEL} Director")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 5 — Figures 3 & 4: Edge weight distributions
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 5 — Edge weight distributions")
print("="*60)

def plot_edge_weights(G, fname, title):
    weights = [data["weight"] for _, _, data in G.edges(data=True)]
    cnt     = Counter(weights)
    xs      = sorted(cnt.keys())
    ys      = [cnt[x] for x in xs]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.semilogy(xs, ys, "o-", label=DATASET_LABEL, color="steelblue")
    ax.set_xlabel("w  (shared directors / boards)")
    ax.set_ylabel("# edges with weight w  (log)")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{RESULTS}/{fname}", dpi=150)
    plt.close(fig)
    print(f"  Saved {fname}  (max_w={max(xs)}, min_w={min(xs)})")

plot_edge_weights(director_net, "fig3_edge_weights_director.png",
                  "Edge weight distribution — Director network")
plot_edge_weights(board_net,    "fig4_edge_weights_board.png",
                  "Edge weight distribution — Board network")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 6 — Figure 5: Chairs distribution (boards per director)
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 6 — Chairs distribution")
print("="*60)

chairs_per_director = {d: G_bipartite.degree(d) for d in directors}
total_chairs = sum(G_bipartite.degree(c) for c in companies)
ratio_chairs = total_chairs / len(directors)
print(f"  Chairs ratio (total_chairs/directors) = {ratio_chairs:.4f}")
print(f"  Paper: US=1.2297, IT'02=1.2769, IT'86=1.3646")

chair_counts = Counter(chairs_per_director.values())
xs = sorted(chair_counts.keys())
ys = [chair_counts[x] for x in xs]

lambda_p = ratio_chairs - 1
k_range  = range(1, max(xs) + 2)
poisson_expected = [poisson.pmf(k, lambda_p) * len(directors) for k in k_range]

fig, ax = plt.subplots(figsize=(7, 5))
ax.loglog(xs, ys, "o", color="steelblue", label=DATASET_LABEL)
ax.loglog(list(k_range), poisson_expected, "--", color="salmon", label=f"Poisson(λ={lambda_p:.2f})")
ax.set_xlabel("Number of boards (chairs)")
ax.set_ylabel("Number of directors  (log)")
ax.set_title("Chairs distribution — boards per director")
ax.legend()
fig.tight_layout()
fig.savefig(f"{RESULTS}/fig5_chairs_distribution.png", dpi=150)
plt.close(fig)
print(f"  Saved fig5_chairs_distribution.png")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 7 — Figure 6: Board size distribution
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 7 — Board size distribution")
print("="*60)

board_sizes = [G_bipartite.degree(c) for c in companies]
mean_bs = np.mean(board_sizes)
max_bs  = max(board_sizes)
print(f"  Mean board size = {mean_bs:.2f}  (paper ~10)")
print(f"  Max  board size = {max_bs}        (paper ~30)")

bins = range(1, max_bs + 2)
fig, ax = plt.subplots(figsize=(7, 5))
ax.hist(board_sizes, bins=list(bins), density=True, color="steelblue",
        edgecolor="white", alpha=0.8)
ax.set_xlabel("Board size (number of directors)")
ax.set_ylabel("P(n)  — fraction of boards")
ax.set_title("Board size distribution")
fig.tight_layout()
fig.savefig(f"{RESULTS}/fig6_board_size_distribution.png", dpi=150)
plt.close(fig)
print(f"  Saved fig6_board_size_distribution.png")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 8 — Figures 7 & 8: Cumulative degree distributions (CCDF)
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 8 — Cumulative degree distributions")
print("="*60)

def plot_ccdf_degree(G, fname, title):
    degrees   = sorted([d for _, d in G.degree()], reverse=True)
    N_nodes   = len(degrees)
    cumul     = [i / N_nodes for i in range(1, N_nodes + 1)]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.semilogy(degrees, cumul, "o", color="steelblue", markersize=4, label=DATASET_LABEL)
    ax.set_xlabel("k  (degree)")
    ax.set_ylabel("P'(k)  — fraction of nodes with degree ≥ k  (log)")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{RESULTS}/{fname}", dpi=150)
    plt.close(fig)
    print(f"  Saved {fname}")

plot_ccdf_degree(director_net, "fig7_degree_dist_director.png",
                 "Cumulative degree distribution — Director network")
plot_ccdf_degree(board_net,    "fig8_degree_dist_board.png",
                 "Cumulative degree distribution — Board network")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 9 — Figures 9 & 10: Betweenness distributions
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 9 — Betweenness distributions")
print("="*60)

def plot_betweenness_dist(G_giant, N_total, fname, title):
    bet_dict   = nx.betweenness_centrality(G_giant, normalized=False)
    bet_values = sorted([v / N_total for v in bet_dict.values()], reverse=True)
    N_nodes    = len(bet_values)
    cumul      = [i / N_nodes for i in range(1, N_nodes + 1)]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.semilogy(bet_values, cumul, "o", color="steelblue", markersize=4, label=DATASET_LABEL)
    ax.set_xlabel("b/N  (normalised betweenness)")
    ax.set_ylabel("P'(b/N)  (log)")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{RESULTS}/{fname}", dpi=150)
    plt.close(fig)
    print(f"  Saved {fname}")

plot_betweenness_dist(metrics_director["_G_giant"], metrics_director["N"],
                      "fig9_betweenness_dist_director.png",
                      "Betweenness distribution — Director network")
plot_betweenness_dist(metrics_board["_G_giant"], metrics_board["N"],
                      "fig10_betweenness_dist_board.png",
                      "Betweenness distribution — Board network")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 10 — Figures 11 & 12: Betweenness vs degree
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 10 — Betweenness vs degree (power-law fit)")
print("="*60)

def plot_bet_vs_degree(G_giant, N_total, fname, title, expected_slope):
    bet_dict = nx.betweenness_centrality(G_giant, normalized=False)
    xs = np.array([G_giant.degree(n) for n in G_giant.nodes()])
    ys = np.array([bet_dict[n] / N_total for n in G_giant.nodes()])

    # filter zeros for log fit
    mask   = (xs > 0) & (ys > 0)
    xs_fit = xs[mask]
    ys_fit = ys[mask]
    coeffs = np.polyfit(np.log(xs_fit), np.log(ys_fit), 1)
    slope  = coeffs[0]
    print(f"  {title}: power-law slope = {slope:.2f}  (paper ~{expected_slope})")

    x_line = np.linspace(xs_fit.min(), xs_fit.max(), 100)
    y_line = np.exp(coeffs[1]) * x_line ** slope

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.loglog(xs, ys, "o", color="steelblue", markersize=4, alpha=0.7, label=DATASET_LABEL)
    ax.loglog(x_line, y_line, "--", color="salmon",
              label=f"fit slope={slope:.2f}  (paper~{expected_slope})")
    ax.set_xlabel("k  (degree, log)")
    ax.set_ylabel("b/N  (betweenness, log)")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{RESULTS}/{fname}", dpi=150)
    plt.close(fig)
    print(f"  Saved {fname}")

plot_bet_vs_degree(metrics_director["_G_giant"], metrics_director["N"],
                   "fig11_bet_vs_degree_director.png",
                   "Betweenness vs degree — Director network", 2.2)
plot_bet_vs_degree(metrics_board["_G_giant"], metrics_board["N"],
                   "fig12_bet_vs_degree_board.png",
                   "Betweenness vs degree — Board network", 1.5)

# ═══════════════════════════════════════════════════════════════════════════
# STEP 11 — Table 2: Assortativity
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 11 — Assortativity")
print("="*60)

r_board    = nx.degree_assortativity_coefficient(board_net)
r_director = nx.degree_assortativity_coefficient(director_net)

assort_rows = [
    {"Network": f"{DATASET_LABEL} Board",    "r": round(r_board, 3),    "Assortative": r_board > 0},
    {"Network": f"{DATASET_LABEL} Director", "r": round(r_director, 3), "Assortative": r_director > 0},
    {"Network": "Board IT'86",               "r": 0.12, "Assortative": True},
    {"Network": "Board IT'02",               "r": 0.32, "Assortative": True},
    {"Network": "Board US'99",               "r": 0.27, "Assortative": True},
    {"Network": "Director IT'86",            "r": 0.13, "Assortative": True},
    {"Network": "Director IT'02",            "r": 0.25, "Assortative": True},
    {"Network": "Director US'99",            "r": 0.27, "Assortative": True},
]
assort_df = pd.DataFrame(assort_rows)
print("\n" + assort_df.to_string(index=False))
assort_df.to_csv(f"{RESULTS}/table2_assortativity.csv", index=False)

# ═══════════════════════════════════════════════════════════════════════════
# STEP 12 — Figures 13 & 14: Knn(k)
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 12 — Average Nearest Neighbor Degree Knn(k)")
print("="*60)

def plot_knn(G, fname, title):
    knn_dict = nx.average_neighbor_degree(G)
    knn_by_k = defaultdict(list)
    for node in G.nodes():
        k = G.degree(node)
        knn_by_k[k].append(knn_dict[node])
    ks   = sorted(knn_by_k.keys())
    knns = [np.mean(knn_by_k[k]) for k in ks]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.loglog(ks, knns, "o", color="steelblue", markersize=5, label=DATASET_LABEL)
    ax.set_xlabel("k  (degree, log)")
    ax.set_ylabel("Knn(k)  (avg neighbour degree, log)")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{RESULTS}/{fname}", dpi=150)
    plt.close(fig)
    print(f"  Saved {fname}")

plot_knn(director_net, "fig13_knn_director.png",
         "Average Nearest Neighbour Degree — Director network")
plot_knn(board_net,    "fig14_knn_board.png",
         "Average Nearest Neighbour Degree — Board network")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 13 — Figures 15 & 16: c(k) clustering vs degree
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 13 — Clustering coefficient c(k)")
print("="*60)

def plot_ck(G, fname, title):
    # c(k) ~ 1/k is typical of hierarchical social networks (Barabási)
    # flat or slowly decreasing c(k) indicates clique structure — lobbies
    clust = nx.clustering(G)
    ck_by_k = defaultdict(list)
    for node in G.nodes():
        k = G.degree(node)
        ck_by_k[k].append(clust[node])
    ks  = sorted(k for k in ck_by_k if k > 0)
    cks = [np.mean(ck_by_k[k]) for k in ks]

    k_ref  = np.array(ks, dtype=float)
    inv_k  = 1.0 / k_ref

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.loglog(ks, cks, "o", color="steelblue", markersize=5, label=f"c(k) {DATASET_LABEL}")
    # scale 1/k to be visible
    scale = np.mean(cks) / np.mean(inv_k)
    ax.loglog(k_ref, scale * inv_k, "--", color="salmon", alpha=0.7, label="1/k reference")
    ax.set_xlabel("k  (degree, log)")
    ax.set_ylabel("c(k)  (clustering, log)")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{RESULTS}/{fname}", dpi=150)
    plt.close(fig)
    print(f"  Saved {fname}")

plot_ck(board_net,    "fig15_ck_board.png",    "Clustering vs degree — Board network")
plot_ck(director_net, "fig16_ck_director.png", "Clustering vs degree — Director network")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 14 — Lobbies
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 14 — Lobbies")
print("="*60)

boards_with_lobby = 0
lobby_details     = []

for c in companies:
    dirs = list(G_bipartite.neighbors(c))
    if len(dirs) < 2:
        continue
    found = False
    for i in range(len(dirs)):
        if found:
            break
        for j in range(i + 1, len(dirs)):
            d1, d2 = dirs[i], dirs[j]
            boards_d1 = set(G_bipartite.neighbors(d1)) - {c}
            boards_d2 = set(G_bipartite.neighbors(d2)) - {c}
            common = boards_d1 & boards_d2
            if common:
                boards_with_lobby += 1
                lobby_details.append({
                    "company": c,
                    "director1": d1,
                    "director2": d2,
                    "shared_other_boards": ", ".join(common),
                })
                found = True
                break

lobby_pct = (boards_with_lobby / len(companies)) * 100
print(f"  Companies with lobby >= 2 : {boards_with_lobby} / {len(companies)}  ({lobby_pct:.1f}%)")
print(f"  Paper: US=35%, IT'86=44%, IT'02=63%")

lobby_df = pd.DataFrame(lobby_details)
lobby_df.to_csv(f"{RESULTS}/lobbies.csv", index=False)
print(f"  Saved lobbies.csv  ({len(lobby_details)} entries)")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 15 — Final summary
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 15 — FINAL SUMMARY")
print("="*60)
print("\nTable 1 — Network metrics:")
print(table1_df.to_string(index=False))
print("\nTable 2 — Assortativity:")
print(assort_df.to_string(index=False))
print(f"\nLobbies: {lobby_pct:.1f}% of companies have a lobby >= 2  (paper: US=35%, IT'86=44%, IT'02=63%)")
print(f"\nSmall World — Board    : {'YES' if sw_board['small_world'] else 'NO'}")
print(f"Small World — Director : {'YES' if sw_director['small_world'] else 'NO'}")
print(f"\nAll figures saved to  ./{RESULTS}/")
print("="*60)
