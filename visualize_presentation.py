# -*- coding: utf-8 -*-
"""
5 focused presentation figures for insights
"""
import os, sys
import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms import bipartite
import community as community_louvain
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from scipy.stats import poisson

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.spines.top"]   = False
plt.rcParams["axes.spines.right"] = False
os.makedirs("results", exist_ok=True)

# ── Load data ────────────────────────────────────────────────────────────────
df = pd.read_csv("boardmembers_2024.csv")
df = df.rename(columns={"name": "director"})
df = df.dropna(subset=["director", "company"]).drop_duplicates(subset=["director", "company"])

G_bip = nx.Graph()
G_bip.add_nodes_from(df["company"].unique(), bipartite=0)
G_bip.add_nodes_from(df["director"].unique(), bipartite=1)
for _, row in df.iterrows():
    G_bip.add_edge(row["company"], row["director"])

companies = {n for n, d in G_bip.nodes(data=True) if d.get("bipartite") == 0}
directors  = {n for n, d in G_bip.nodes(data=True) if d.get("bipartite") == 1}
board_net  = bipartite.weighted_projected_graph(G_bip, companies)
dir_net    = bipartite.weighted_projected_graph(G_bip, directors)

N_b = board_net.number_of_nodes()
E_b = board_net.number_of_edges()
N_d = dir_net.number_of_nodes()
E_d = dir_net.number_of_edges()

# ════════════════════════════════════════════════════════════════════════════
# FIG I1 — Sparsity: Nc/N comparison across datasets
# ════════════════════════════════════════════════════════════════════════════
def make_fig_sparsity():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle("Rede de empresas — Portugal vs datasets de referência (Battiston & Catanzaro, 2004)",
                 fontsize=13, fontweight="bold", y=1.01)

    # Data from paper Table 1 + Portugal
    datasets = ["IT '86", "IT '02", "US '99", "PT '24"]
    colors   = ["#7fbbda", "#2F57C9", "#F39C12", "#E74C3C"]

    # Board network
    nc_n_board = [0.97, 0.82, 0.87, 0.558]
    kkc_board  = [5.29, 2.22, 1.57, 2.27]   # k/kc %
    C_board    = [0.356, 0.318, 0.376, 0.218]
    d_board    = [3.6, 4.4, 4.6, 3.87]

    ax = axes[0]
    bars = ax.bar(datasets, nc_n_board, color=colors, width=0.55, edgecolor="white", linewidth=1.2)
    ax.axhline(0.82, color="#2F57C9", lw=1.2, linestyle="--", alpha=0.5, label="IT '02 (referência)")
    for bar, v in zip(bars, nc_n_board):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.012, f"{v:.0%}",
                ha="center", va="bottom", fontsize=11, fontweight="bold",
                color="#E74C3C" if v < 0.7 else "black")
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Nc / N  (fracção de empresas no componente gigante)", fontsize=10)
    ax.set_title("Conectividade: fracção na componente gigante\n(Rede de empresas)", fontsize=11)
    ax.tick_params(labelsize=11)
    # Annotation
    ax.annotate("44% das empresas portuguesas\nnão têm nenhuma ligação\n(grau = 0)",
                xy=(3, 0.558), xytext=(2.2, 0.35),
                arrowprops=dict(arrowstyle="->", color="#E74C3C", lw=1.5),
                fontsize=9.5, color="#E74C3C",
                bbox=dict(boxstyle="round,pad=0.3", fc="#fff5f5", ec="#E74C3C", alpha=0.9))

    # Clustering comparison
    ax2 = axes[1]
    x = np.arange(len(datasets))
    width = 0.35
    b1 = ax2.bar(x - width/2, C_board, width, label="Rede de empresas (boards)", color=colors, edgecolor="white")
    C_dir = [0.899, 0.915, 0.884, 0.939]
    b2 = ax2.bar(x + width/2, C_dir, width, label="Rede de directores", color=colors,
                 edgecolor="white", alpha=0.55, hatch="///")
    for bar, v in zip(b1, C_board):
        ax2.text(bar.get_x()+bar.get_width()/2, v+0.01, f"{v:.3f}",
                 ha="center", va="bottom", fontsize=9, rotation=90)
    for bar, v in zip(b2, C_dir):
        ax2.text(bar.get_x()+bar.get_width()/2, v+0.01, f"{v:.3f}",
                 ha="center", va="bottom", fontsize=9, rotation=90)
    ax2.set_xticks(x); ax2.set_xticklabels(datasets, fontsize=11)
    ax2.set_ylabel("Coeficiente de clustering médio  C̄", fontsize=10)
    ax2.set_title("Clustering: Portugal tem o board C̄ mais baixo\nmas o director C̄ mais alto", fontsize=11)
    ax2.set_ylim(0, 1.15)
    solid_patch = mpatches.Patch(color="#888888", label="Rede de empresas")
    hatch_patch = mpatches.Patch(facecolor="#888888", hatch="///", alpha=0.55, label="Rede de directores")
    ax2.legend(handles=[solid_patch, hatch_patch], fontsize=9, loc="lower right")

    fig.tight_layout()
    path = "results/pres_I1_sparsity_clustering.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path}")


# ════════════════════════════════════════════════════════════════════════════
# FIG I2 — Community cliques: ALTRI/Cofina/Ramada + Fidelidade group
# ════════════════════════════════════════════════════════════════════════════
def make_fig_communities():
    fig, axes = plt.subplots(1, 2, figsize=(15, 7))
    fig.suptitle("Comunidades empresariais: alta conectividade interna por grupos familiares/empresariais",
                 fontsize=13, fontweight="bold", y=1.01)

    # ── Left: ALTRI cluster ──
    altri_companies = ["ALTRI SGPS", "Cofina SGPS", "RAMADA", "Media Livre", "Ibersol"]
    altri_sub = board_net.subgraph([n for n in board_net.nodes() if n in altri_companies]).copy()

    ax = axes[0]
    pos = nx.spring_layout(altri_sub, seed=5, k=2.5)
    edges = [(u,v,d) for u,v,d in altri_sub.edges(data=True)]
    max_w = max((d["weight"] for _,_,d in edges), default=1)

    for u,v,data in edges:
        w = data["weight"]
        lw = 1.5 + w * 1.8
        ax.plot([pos[u][0],pos[v][0]], [pos[u][1],pos[v][1]],
                color="#8E44AD", lw=lw, alpha=0.7, zorder=1, solid_capstyle="round")
        mx, my = (pos[u][0]+pos[v][0])/2, (pos[u][1]+pos[v][1])/2
        ax.text(mx, my, f"{w}", ha="center", va="center", fontsize=11, fontweight="bold",
                color="white", bbox=dict(boxstyle="round,pad=0.25", fc="#8E44AD", ec="none"))

    ABBR = {"ALTRI SGPS":"ALTRI","Cofina SGPS":"Cofina","RAMADA":"Ramada",
            "Media Livre":"Media\nLivre","Ibersol":"Ibersol"}
    for node, (x,y) in pos.items():
        deg = altri_sub.degree(node)
        size = 900 + deg * 200
        ax.scatter(x, y, s=size, c="#8E44AD", edgecolors="white", linewidths=2, zorder=3)
        ax.text(x, y, ABBR.get(node, node), ha="center", va="center",
                fontsize=10, fontweight="bold", color="white", zorder=4)

    # Key directors
    key_dirs = ["J.M. Matos Borges de Oliveira", "Paulo Fernandes",
                "Domingos Vieira de Matos", "Pedro M. Borges de Oliveira",
                "Ana M. Menéres de Mendonça"]
    ax.text(0.5, -0.08, "5 directores comuns (família Borges de Oliveira / Vieira de Matos):\n" +
            " · ".join(["J.M.Borges Oliveira","P.Fernandes","D.Vieira Matos","P.M.Borges Oliveira","A.Menéres Mendonça"]),
            ha="center", va="top", transform=ax.transAxes,
            fontsize=8.5, color="#8E44AD",
            bbox=dict(boxstyle="round,pad=0.4", fc="#f9f0ff", ec="#8E44AD", alpha=0.9))
    ax.set_title("Cluster ALTRI / Media\n(número = directores partilhados)", fontsize=11)
    ax.axis("off")

    # ── Right: Fidelidade / Mello group ──
    fin_companies = ["Fidelidade", "OK Teleseguros", "Luz Saúde", "Grupo José de Mello", "CUF",
                     "Trofa Saúde"]
    fin_nodes = [n for n in board_net.nodes() if any(n==c or n.startswith(c[:6]) for c in fin_companies)]
    # Also try partial match
    fin_exact = []
    for n in board_net.nodes():
        for c in fin_companies:
            if c.lower() in n.lower() or n.lower() in c.lower():
                fin_exact.append(n)
                break
    fin_sub = board_net.subgraph(list(set(fin_exact))).copy()

    ax2 = axes[1]
    if fin_sub.number_of_nodes() > 0:
        pos2 = nx.spring_layout(fin_sub, seed=7, k=2.5)
        for u,v,data in fin_sub.edges(data=True):
            w = data["weight"]
            lw = 1.5 + w * 1.8
            ax2.plot([pos2[u][0],pos2[v][0]], [pos2[u][1],pos2[v][1]],
                     color="#2F57C9", lw=lw, alpha=0.7, zorder=1)
            mx, my = (pos2[u][0]+pos2[v][0])/2, (pos2[u][1]+pos2[v][1])/2
            ax2.text(mx, my, f"{w}", ha="center", va="center", fontsize=11, fontweight="bold",
                     color="white", bbox=dict(boxstyle="round,pad=0.25", fc="#2F57C9", ec="none"))

        ABBR2 = {"Grupo José de Mello":"J.de Mello","CUF":"CUF","Fidelidade":"Fidelidade",
                 "OK Teleseguros":"OK\nTelesSeg","Luz Saúde":"Luz\nSaúde","Trofa Saúde":"Trofa\nSaúde"}
        for node, (x,y) in pos2.items():
            deg = fin_sub.degree(node)
            size = 900 + deg * 200
            ax2.scatter(x, y, s=size, c="#2F57C9", edgecolors="white", linewidths=2, zorder=3)
            lbl = ABBR2.get(node, node[:10])
            ax2.text(x, y, lbl, ha="center", va="center",
                     fontsize=9.5, fontweight="bold", color="white", zorder=4)

        ax2.text(0.5, -0.08,
                 "Champalimaud Group: Fidelidade + Luz Saúde (2 dir.) + OK Teleseguros (1 dir.)\n"
                 "J.de Mello + CUF (3 directores: Salvador J.de Mello, R.Galamba, R.Pires Diniz)",
                 ha="center", va="top", transform=ax2.transAxes,
                 fontsize=8.5, color="#2F57C9",
                 bbox=dict(boxstyle="round,pad=0.4", fc="#f0f4fb", ec="#2F57C9", alpha=0.9))

    ax2.set_title("Cluster Financeiro / Saúde\n(número = directores partilhados)", fontsize=11)
    ax2.axis("off")

    fig.tight_layout()
    path = "results/pres_I2_communities.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path}")


# ════════════════════════════════════════════════════════════════════════════
# FIG I3 — Chairs distribution vs Poisson + comparison
# ════════════════════════════════════════════════════════════════════════════
def make_fig_chairs():
    chairs = df.groupby("director")["company"].count()
    total = len(chairs)
    lambda_pt = chairs.mean()  # = chairs ratio

    max_k = 6
    observed = [(chairs == k).sum() / total for k in range(1, max_k+1)]
    poisson_p = [poisson.pmf(k, lambda_pt) for k in range(1, max_k+1)]
    # Poisson conditioned on ≥1 (since we only count directors who appear)
    poisson_cond = [p / (1 - poisson.pmf(0, lambda_pt)) for p in poisson_p]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle("Distribuição de 'chairs' (mandatos por director) — Portugal 2024",
                 fontsize=13, fontweight="bold")

    # Left: distribution
    ax = axes[0]
    x = np.arange(1, max_k+1)
    w = 0.38
    ax.bar(x - w/2, [o*100 for o in observed], w, label="Observado (Portugal '24)",
           color="#E74C3C", edgecolor="white")
    ax.bar(x + w/2, [p*100 for p in poisson_cond], w, label=f"Poisson esperado (λ={lambda_pt:.2f})",
           color="#aaaaaa", edgecolor="white", alpha=0.8)
    ax.set_xlabel("Número de boards por director (chairs)", fontsize=11)
    ax.set_ylabel("% de directores", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{k}" for k in range(1, max_k+1)])
    ax.legend(fontsize=10)
    ax.set_title(f"Observado vs Poisson\n(89.9% dos directores estão em apenas 1 board)", fontsize=10)
    # Annotate
    vals = [(chairs==k).sum() for k in range(1, 6)]
    for xi, (obs, poi) in enumerate(zip(observed, poisson_cond)):
        ax.text(xi+1-w/2, obs*100+0.3, f"{int(obs*total)}", ha="center", fontsize=9, color="#E74C3C")

    # Right: chairs ratio comparison
    ax2 = axes[1]
    ref_data = {
        "IT '86": 1.3646,
        "IT '02": 1.2769,
        "US '99": 1.2297,
        "PT '24": 1.1401,
    }
    colors_bar = ["#7fbbda","#2F57C9","#F39C12","#E74C3C"]
    bars = ax2.bar(list(ref_data.keys()), list(ref_data.values()),
                   color=colors_bar, width=0.55, edgecolor="white")
    for bar, (k, v) in zip(bars, ref_data.items()):
        ax2.text(bar.get_x()+bar.get_width()/2, v+0.005, f"{v:.4f}",
                 ha="center", va="bottom", fontsize=12, fontweight="bold",
                 color="#E74C3C" if k=="PT '24" else "black")
    ax2.set_ylim(1.05, 1.45)
    ax2.set_ylabel("Rácio chairs / directores", fontsize=11)
    ax2.set_title("Portugal tem o rácio mais baixo\nde todos os datasets de referência", fontsize=10)
    ax2.axhline(1.0, color="black", lw=0.8, linestyle=":")
    ax2.tick_params(labelsize=11)
    ax2.annotate("Mínimo histórico\n(menos interlocking)", xy=(3, 1.1401), xytext=(2.2, 1.11),
                 arrowprops=dict(arrowstyle="->", color="#E74C3C", lw=1.5),
                 fontsize=9, color="#E74C3C",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#fff5f5", ec="#E74C3C", alpha=0.9))

    fig.tight_layout()
    path = "results/pres_I3_chairs.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path}")


# ════════════════════════════════════════════════════════════════════════════
# FIG I4 — Degree distribution CCDF with plateau annotation
# ════════════════════════════════════════════════════════════════════════════
def make_fig_degree():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle("Distribuição de grau (CCDF) — o plateau revela a origem do clustering",
                 fontsize=13, fontweight="bold")

    for ax, (net, name, color) in zip(axes, [
        (dir_net,  "Rede de directores", "#2F57C9"),
        (board_net,"Rede de empresas",   "#E74C3C"),
    ]):
        degrees = sorted([d for _, d in net.degree()], reverse=True)
        N = len(degrees)
        ccdf = [(i+1)/N for i in range(N)]
        lam = np.mean(degrees)

        ax.semilogy(degrees, ccdf, "o-", color=color, ms=4, lw=1.8,
                    label="Observado", zorder=3)

        # Poisson reference
        k_range = np.arange(0, max(degrees)+1)
        poisson_ccdf = [1 - poisson.cdf(k-1, lam) for k in k_range]
        ax.semilogy(k_range, poisson_ccdf, "--", color="#888888", lw=1.5,
                    label=f"Poisson (λ={lam:.1f})", alpha=0.8)

        ax.set_xlabel("Grau k", fontsize=11)
        ax.set_ylabel("P'(k)  [CCDF]", fontsize=11)
        ax.set_title(name, fontsize=11)
        ax.legend(fontsize=9)

        # Annotate plateau for director network
        if "director" in name.lower():
            mean_board = df.groupby("company")["director"].count().mean()
            ax.axvline(mean_board, color="#27AE60", lw=1.8, linestyle=":",
                       label=f"Tamanho médio do board ≈{mean_board:.0f}")
            ax.text(mean_board+1, 0.3, f"Plateau até k≈{mean_board:.0f}\n(= tamanho médio do board)\nentrar num board de 9\ndá imediatamente 8 ligações",
                    fontsize=8.5, color="#27AE60",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#f0fff4", ec="#27AE60", alpha=0.9))
            ax.legend(fontsize=9)
        else:
            # Board network: annotate isolated fraction
            isolated = sum(1 for _, d in board_net.degree() if d == 0)
            ax.text(0.55, 0.85, f"{isolated}/{N_b} empresas\ncom grau 0\n(não conectadas)",
                    transform=ax.transAxes, fontsize=9, color="#E74C3C",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#fff5f5", ec="#E74C3C", alpha=0.9))

    fig.tight_layout()
    path = "results/pres_I4_degree_ccdf.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path}")


# ════════════════════════════════════════════════════════════════════════════
# FIG I5 — Hidden ownership: Martifer / Mota-Engil / Visabeira
# ════════════════════════════════════════════════════════════════════════════
def make_fig_ownership():
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.set_facecolor("#fafafa")
    fig.patch.set_facecolor("#fafafa")
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)

    ax.set_title(
        "Conexões ocultas: o network de directores não cobre relações de propriedade\n"
        "(Martifer · Mota-Engil · Grupo Visabeira)",
        fontsize=13, fontweight="bold", pad=14
    )

    # Node positions
    nodes = {
        "Mota-Engil":      (2.0, 5.2),
        "Martifer":        (5.0, 3.5),
        "Visabeira":       (8.0, 5.2),
        "Champalimaud\nHolding": (5.0, 6.2),
    }
    node_colors = {
        "Mota-Engil": "#E74C3C",
        "Martifer":   "#8E44AD",
        "Visabeira":  "#2F57C9",
        "Champalimaud\nHolding": "#888888",
    }
    node_sizes = {
        "Mota-Engil": 1600,
        "Martifer":   1400,
        "Visabeira":  1200,
        "Champalimaud\nHolding": 600,
    }

    def circle(ax, xy, size, color, label, fontsize=11):
        from matplotlib.patches import Circle
        r = (size ** 0.5) * 0.012
        c = Circle(xy, r, color=color, zorder=3, alpha=0.92)
        ax.add_patch(c)
        ax.text(xy[0], xy[1], label, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color="white", zorder=4)

    def arrow(ax, xy1, xy2, label, color, style="->", lw=2.5, ls="-", offset=(0,0.15)):
        ax.annotate("", xy=xy2, xytext=xy1,
                    arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                    linestyle=ls, connectionstyle="arc3,rad=0.1"))
        mx = (xy1[0]+xy2[0])/2 + offset[0]
        my = (xy1[1]+xy2[1])/2 + offset[1]
        ax.text(mx, my, label, ha="center", va="bottom", fontsize=9.5,
                color=color, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color, alpha=0.9))

    # Draw nodes
    for name, pos in nodes.items():
        circle(ax, pos, node_sizes[name], node_colors[name], name,
               fontsize=9 if "\n" in name else 11)

    # ─ Ownership arrows (dashed red)
    arrow(ax, nodes["Mota-Engil"], nodes["Martifer"],
          "Propriedade: ~37%\n(Mota-Engil é accionista\nde Martifer)",
          "#E74C3C", style="-|>", lw=2.5, ls="--", offset=(-0.3, 0.25))

    # ─ Director link: Nuno Terras Marques (Visabeira → Martifer)
    arrow(ax, nodes["Visabeira"], nodes["Martifer"],
          "1 director partilhado:\nNuno M.R. Terras Marques\n(Visabeira + Martifer)",
          "#2F57C9", style="-|>", lw=2.5, ls="-", offset=(0.4, 0.25))

    # ─ Family link (not a board link): Maria Sílvia → Mota family
    ax.annotate("", xy=nodes["Martifer"], xytext=nodes["Mota-Engil"],
                arrowprops=dict(arrowstyle="-|>", color="#F39C12", lw=2.0,
                                linestyle="dotted", connectionstyle="arc3,rad=-0.2"))
    ax.text(2.8, 4.0,
            "Maria Sílvia F. Vasconcelos da Mota\n(família Mota) → adm. não-exec. Martifer\nMAS não está formalmente no board\nda Mota-Engil neste dataset",
            ha="center", va="center", fontsize=9, color="#F39C12",
            bbox=dict(boxstyle="round,pad=0.35", fc="#fffbf0", ec="#F39C12", alpha=0.95))

    # ─ 0 directors label
    ax.text(5.0, 5.85,
            "0 directores partilhados\nentre Mota-Engil e Martifer\napesar dos 37% de propriedade",
            ha="center", va="center", fontsize=9.5, color="#555555",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#888888", ls="--", alpha=0.95))

    # Legend
    legend_items = [
        mpatches.Patch(facecolor="#E74C3C", label="Relação de propriedade (ownership)"),
        Line2D([0],[0], color="#2F57C9", lw=2.5, label="Director partilhado (board interlock)"),
        Line2D([0],[0], color="#F39C12", lw=2.0, linestyle="dotted", label="Ligação familiar (fora do scope do estudo)"),
    ]
    ax.legend(handles=legend_items, loc="lower center", fontsize=10,
              framealpha=0.97, edgecolor="#cccccc",
              title="Tipo de ligação", title_fontsize=10)

    # Footer note
    ax.text(5.0, 0.3,
            "Este estudo cobre apenas interlocking via directores partilhados.\n"
            "Ligações de propriedade (ownership) e ligações familiares requerem análise complementar.",
            ha="center", va="center", fontsize=9.5, color="#666666", style="italic")

    fig.tight_layout()
    path = "results/pres_I5_ownership.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path}")


# ── Run all ──────────────────────────────────────────────────────────────────
print("Generating presentation figures...")
make_fig_sparsity()
make_fig_communities()
make_fig_chairs()
make_fig_degree()
make_fig_ownership()
print("\nDone. All saved in results/")
