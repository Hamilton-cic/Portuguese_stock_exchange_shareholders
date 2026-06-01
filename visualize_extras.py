# -*- coding: utf-8 -*-
"""
Extra figures requested for the final report:
  Fig C1 — Community visualization (nodes coloured by Louvain cluster)
  Fig C2 — Knn(k) for board + director networks
  Fig C3 — Degree distribution CCDF (log-log, publication quality)
  Fig C4 — c(k) clustering vs degree
"""

import os, math
from collections import defaultdict

import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms import bipartite
import community as community_louvain
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection

plt.rcParams["font.family"] = "DejaVu Sans"
os.makedirs("results", exist_ok=True)

# ── Data ────────────────────────────────────────────────────────────────────
df = pd.read_csv("boardmembers_2024.csv")
df = df.rename(columns={"name": "director"})
df = df.dropna(subset=["director", "company"]).drop_duplicates(subset=["director", "company"])

G_bip = nx.Graph()
G_bip.add_nodes_from(df["company"].unique(), bipartite=0)
G_bip.add_nodes_from(df["director"].unique(), bipartite=1)
for _, row in df.iterrows():
    G_bip.add_edge(row["company"], row["director"])

companies = {n for n, d in G_bip.nodes(data=True) if d.get("bipartite") == 0}
directors = {n for n, d in G_bip.nodes(data=True) if d.get("bipartite") == 1}
board_net    = bipartite.weighted_projected_graph(G_bip, companies)
director_net = bipartite.weighted_projected_graph(G_bip, directors)

ABBREVS = {
    "CTT Correios de Portugal": "CTT", "Caixa Geral de Depósitos": "CGD",
    "Corticeira Amorim": "Amorim", "The Navigator Company": "Navigator",
    "Jerónimo Martins": "J.Martins", "MEO / Altice Portugal": "MEO",
    "Grupo José de Mello": "J.de Mello", "Grupo Champalimaud": "Champal.",
    "Grupo Nabeiro / Delta Cafés": "Delta", "Grupo Alves Ribeiro": "Alves Rib.",
    "Millennium BCP": "BCP", "Grupo Pestana": "Pestana",
    "Grupo Vila Galé": "Vila Galé", "Grupo Solverde": "Solverde",
    "Super Bock Group": "Super Bock", "Vista Alegre Atlantis": "Vista Aleg.",
    "VdA - Vieira de Almeida": "VdA", "Rothschild & Co (Portugal)": "Rothschild",
    "Sagres / SCC": "Sagres", "Sonae SGPS": "Sonae",
    "EDP Renováveis": "EDP Renov.", "Galp Energia": "Galp",
    "Grupo Azevedos": "Azevedos", "Banco Montepio": "Montepio",
    "Banco Carregosa": "Carregosa", "Banco Finantia": "Finantia",
    "Banco Best": "Best", "Grupo Valouro": "Valouro",
    "SL Benfica": "Benfica", "Sporting CP": "Sporting", "FC Porto": "FC Porto",
    "Luz Saúde": "Luz Saúde", "Trofa Saúde": "Trofa Saúde",
    "Sonae MC": "Sonae MC", "Sonae Sierra": "S.Sierra",
    "Sumol+Compal": "Sumol", "OCP Portugal": "OCP",
    "Banco Big": "Banco Big", "Banco CTT": "B.CTT",
    "Morais Leitão": "Mor.Leitão", "Media Capital": "Media Cap.",
    "Media Livre": "Media Livre", "OK Teleseguros": "OK Teles.",
    "Grupo José de Mello": "J.de Mello", "ATRIUM BIRE SIGI": "Atrium",
    "CIAGEST - SIGI S.A": "Ciagest",
}

def abbrev(name):
    if name in ABBREVS:
        return ABBREVS[name]
    parts = name.split()
    if len(parts) <= 2:
        return name
    stop = {"de","da","do","dos","das","e","SGPS","S.A.","Grupo","Banco"}
    key = [p for p in parts if p not in stop]
    return key[0] if key else parts[0]


# ═══════════════════════════════════════════════════════════════════════════
# FIG C1 — Community visualization (board network, Louvain colours)
# ═══════════════════════════════════════════════════════════════════════════

def make_community_fig():
    print("\nGenerating Fig C1 — Community visualization...")

    partition = community_louvain.best_partition(board_net, weight="weight", random_state=42)
    modularity = community_louvain.modularity(partition, board_net, weight="weight")

    # Keep only the 5 largest communities by name; rest = "Other"
    from collections import Counter
    comm_sizes = Counter(partition.values())
    top5_ids   = {cid for cid, _ in comm_sizes.most_common(5)}

    # Community labels
    comm_labels = {
        # inferred from member composition
    }
    # We'll auto-label the top 5 as "Grupo X"
    top5_sorted = [cid for cid, _ in comm_sizes.most_common(5)]
    COMM_NAMES = [
        "Industriais / Família",
        "Financeiro / Seguros",
        "Utilities / Distribuição",
        "Universo Sonae",
        "ALTRI / Media",
    ]
    id_to_name = {cid: COMM_NAMES[i] for i, cid in enumerate(top5_sorted)}

    # Palette — distinct colours for top 5 + grey for singletons
    PALETTE = ["#2F57C9", "#E74C3C", "#27AE60", "#F39C12", "#8E44AD", "#aaaaaa"]
    def node_color(node):
        cid = partition[node]
        if cid in top5_ids:
            return PALETTE[top5_sorted.index(cid)]
        return PALETTE[5]

    pos = nx.spring_layout(board_net, seed=17, k=1.8, iterations=600, weight="weight")

    fig, ax = plt.subplots(figsize=(22, 16))
    ax.set_facecolor("#fafafa")
    fig.patch.set_facecolor("#fafafa")

    # Edges
    segs, alphas, lws = [], [], []
    for u, v, data in board_net.edges(data=True):
        w = data.get("weight", 1)
        segs.append([(pos[u][0], pos[u][1]), (pos[v][0], pos[v][1])])
        alphas.append(min(0.15 + w * 0.12, 0.7))
        lws.append(0.5 + w * 0.4)
    lc = LineCollection(segs, colors="#888888", linewidths=lws, alpha=0.45, zorder=1)
    ax.add_collection(lc)

    # Nodes
    for node in board_net.nodes():
        x, y   = pos[node]
        size   = max(400, G_bip.degree(node) * 75)
        color  = node_color(node)
        ax.scatter(x, y, s=size, c=color, edgecolors="white",
                   linewidths=1.2, zorder=2, alpha=0.93)
        lbl = abbrev(node)
        fs  = max(5, min(8.5, size / 130))
        ax.text(x, y, lbl, ha="center", va="center",
                fontsize=fs, fontweight="bold", color="white",
                fontfamily="DejaVu Sans", zorder=3)

    # Legend
    legend_handles = []
    for i, cid in enumerate(top5_sorted):
        members = [n for n, c in partition.items() if c == cid]
        lbl = f"{COMM_NAMES[i]}  ({len(members)} empresas)"
        legend_handles.append(mpatches.Patch(facecolor=PALETTE[i], label=lbl))
    others = sum(1 for c in partition.values() if c not in top5_ids)
    legend_handles.append(mpatches.Patch(facecolor=PALETTE[5],
                                         label=f"Clusters isolados  ({others} empresas)"))
    ax.legend(handles=legend_handles, loc="upper left", fontsize=11,
              framealpha=0.95, edgecolor="#cccccc", title="Comunidade (Louvain)",
              title_fontsize=11)

    ax.set_title(
        f"Rede de Empresas — Estrutura de Comunidades (Louvain Q = {modularity:.3f})\n"
        "Bolsa Portuguesa 2024 · nós coloridos por cluster",
        fontsize=15, pad=14,
    )
    ax.axis("off")
    all_x = [p[0] for p in pos.values()]
    all_y = [p[1] for p in pos.values()]
    pad = 0.07
    ax.set_xlim(min(all_x)-pad, max(all_x)+pad)
    ax.set_ylim(min(all_y)-pad, max(all_y)+pad)

    fig.tight_layout()
    path = "results/figC1_communities.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


# ═══════════════════════════════════════════════════════════════════════════
# FIG C2 — Knn(k): side-by-side Board + Director
# ═══════════════════════════════════════════════════════════════════════════

def make_knn_fig():
    print("\nGenerating Fig C2 — Knn(k)...")

    def knn_data(G):
        knn_dict  = nx.average_neighbor_degree(G)
        knn_by_k  = defaultdict(list)
        for node in G.nodes():
            knn_by_k[G.degree(node)].append(knn_dict[node])
        ks   = sorted(knn_by_k)
        knns = [np.mean(knn_by_k[k]) for k in ks]
        return np.array(ks, float), np.array(knns, float)

    ks_b, knn_b = knn_data(board_net)
    ks_d, knn_d = knn_data(director_net)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for ax, ks, knns, title, color, net in [
        (axes[0], ks_b, knn_b, "Board network  (empresas)", "#2F57C9", board_net),
        (axes[1], ks_d, knn_d, "Director network  (directores)", "#27AE60", director_net),
    ]:
        ax.scatter(ks, knns, s=60, c=color, edgecolors="white",
                   linewidths=0.5, zorder=3, alpha=0.85, label="Knn(k) observado")

        # Linear trend in log-log space
        mask = (ks > 0) & (knns > 0)
        if mask.sum() > 3:
            coeffs = np.polyfit(np.log(ks[mask]), np.log(knns[mask]), 1)
            slope  = coeffs[0]
            x_line = np.linspace(ks[mask].min(), ks[mask].max(), 100)
            y_line = np.exp(coeffs[1]) * x_line ** slope
            trend  = "assortativo" if slope > 0 else "dissortativo"
            ax.plot(x_line, y_line, "--", color="salmon", lw=1.5,
                    label=f"tendência  slope={slope:.2f}  ({trend})")

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("k  (grau do nó)", fontsize=12)
        ax.set_ylabel("Knn(k)  (grau médio dos vizinhos)", fontsize=12)
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

    r_b = nx.degree_assortativity_coefficient(board_net)
    r_d = nx.degree_assortativity_coefficient(director_net)
    fig.suptitle(
        f"Grau médio dos vizinhos Knn(k)  —  Board: r={r_b:.3f}  |  Director: r={r_d:.3f}",
        fontsize=14, y=1.01,
    )
    fig.tight_layout()
    path = "results/figC2_knn.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


# ═══════════════════════════════════════════════════════════════════════════
# FIG C3 — Degree distribution CCDF (publication quality)
# ═══════════════════════════════════════════════════════════════════════════

def make_ccdf_fig():
    print("\nGenerating Fig C3 — Degree distribution CCDF...")

    def ccdf(G):
        degrees = sorted([d for _, d in G.degree()], reverse=True)
        N = len(degrees)
        cumul = [i / N for i in range(1, N + 1)]
        return np.array(degrees, float), np.array(cumul, float)

    degs_b, ccdf_b = ccdf(board_net)
    degs_d, ccdf_d = ccdf(director_net)

    # Erdos-Renyi reference (Poisson)
    from scipy.stats import poisson
    def er_ccdf(G):
        N = G.number_of_nodes()
        E = G.number_of_edges()
        lam = 2 * E / N
        k_max = int(degs_b.max() * 2) if G is board_net else int(degs_d.max() * 1.5)
        ks = np.arange(0, k_max + 1)
        sf = 1 - poisson.cdf(ks - 1, lam)   # P(K >= k)
        return ks, sf, lam

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for ax, degs, ccdf_vals, G, color, title in [
        (axes[0], degs_b, ccdf_b, board_net,    "#2F57C9", "Board network  (empresas)"),
        (axes[1], degs_d, ccdf_d, director_net, "#27AE60", "Director network  (directores)"),
    ]:
        ks_er, sf_er, lam = er_ccdf(G)

        ax.semilogy(degs, ccdf_vals, "o", color=color, markersize=5,
                    alpha=0.85, label="Dados reais  P'(k)")
        ax.semilogy(ks_er, sf_er, "--", color="#aaaaaa", lw=1.5,
                    label=f"Poisson(λ={lam:.1f})  referência aleatória")

        # Power-law fit on the tail (degrees above median)
        mask = degs > np.median(degs[degs > 0])
        if mask.sum() > 4:
            log_k  = np.log(degs[mask])
            log_c  = np.log(ccdf_vals[mask])
            coeffs = np.polyfit(log_k, log_c, 1)
            slope  = coeffs[0]
            x_fit  = np.linspace(degs[mask].min(), degs[mask].max(), 100)
            y_fit  = np.exp(coeffs[1]) * x_fit ** slope
            ax.semilogy(x_fit, y_fit, "-", color="salmon", lw=1.5, alpha=0.8,
                        label=f"power-law fit  γ≈{abs(slope):.2f}")

        ax.set_xlabel("k  (grau)", fontsize=12)
        ax.set_ylabel("P'(k)  =  P(K ≥ k)", fontsize=12)
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

    fig.suptitle("Distribuição cumulativa de grau (CCDF)  —  dados reais vs. referência aleatória",
                 fontsize=14, y=1.01)
    fig.tight_layout()
    path = "results/figC3_ccdf_degree.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


# ═══════════════════════════════════════════════════════════════════════════
# FIG C4 — c(k): clustering vs degree — side-by-side
# ═══════════════════════════════════════════════════════════════════════════

def make_ck_fig():
    print("\nGenerating Fig C4 — c(k) clustering vs degree...")

    def ck_data(G):
        clust   = nx.clustering(G)
        ck_by_k = defaultdict(list)
        for node in G.nodes():
            k = G.degree(node)
            if k > 1:
                ck_by_k[k].append(clust[node])
        ks  = sorted(ck_by_k)
        cks = [np.mean(ck_by_k[k]) for k in ks]
        return np.array(ks, float), np.array(cks, float)

    ks_b, ck_b = ck_data(board_net)
    ks_d, ck_d = ck_data(director_net)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for ax, ks, cks, color, title in [
        (axes[0], ks_b, ck_b, "#2F57C9", "Board network  (empresas)"),
        (axes[1], ks_d, ck_d, "#27AE60", "Director network  (directores)"),
    ]:
        ax.scatter(ks, cks, s=60, c=color, edgecolors="white",
                   linewidths=0.5, zorder=3, alpha=0.85, label="c(k) observado")

        # 1/k reference line
        k_ref  = np.linspace(ks.min(), ks.max(), 100)
        scale  = np.mean(cks) * np.mean(ks)
        ax.plot(k_ref, scale / k_ref, "--", color="#aaaaaa", lw=1.5,
                label="c ~ 1/k  (hierárquico)")

        # Power-law fit in log-log
        mask = (ks > 0) & (cks > 0)
        if mask.sum() > 3:
            coeffs = np.polyfit(np.log(ks[mask]), np.log(cks[mask]), 1)
            slope  = coeffs[0]
            x_fit  = np.linspace(ks[mask].min(), ks[mask].max(), 100)
            y_fit  = np.exp(coeffs[1]) * x_fit ** slope
            ax.plot(x_fit, y_fit, "-", color="salmon", lw=1.5, alpha=0.8,
                    label=f"fit  slope={slope:.2f}")

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("k  (grau)", fontsize=12)
        ax.set_ylabel("c(k)  (coef. clustering médio)", fontsize=12)
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

    fig.suptitle("Coeficiente de clustering c(k) vs. grau  —  triângulo small-world",
                 fontsize=14, y=1.01)
    fig.tight_layout()
    path = "results/figC4_ck.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


# ── Run all ─────────────────────────────────────────────────────────────────
make_community_fig()
make_knn_fig()
make_ccdf_fig()
make_ck_fig()
print("\nDone — 4 figures saved to results/")
