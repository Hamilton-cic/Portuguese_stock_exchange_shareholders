# Portuguese Corporate Ownership Network
### A Graph Theory Analysis of Cross-Ownership and Interlocking Directorates in Portugal

---

## Overview

This project applies **network analysis** and **graph theory** to map the ownership structure and board interlocks of major Portuguese companies. The central hypothesis is that the Portuguese corporate elite forms a small-world network where a selective group of families, individuals, and foreign entities hold significant cross-ownership positions — and that this structure is visually and quantitatively identifiable through graph metrics.

The dataset covers **43 companies listed on Euronext Lisbon**, extended with **10 major unlisted firms**, their controlling shareholders, holding companies, board members, and key individuals — totalling **150+ nodes** and **300+ edges**.

---

## Research Questions

1. **Connectivity** — Is the Portuguese corporate network fully connected? What is its diameter?
2. **Centrality** — Which nodes (companies, people, or groups) are the most influential by degree, betweenness, and eigenvector centrality?
3. **Interlocking directorates** — Which individuals sit on multiple boards simultaneously, and what structural bridges do they create?
4. **Foreign capital** — What is the structural position of foreign shareholders (Fosun, Sonangol, China Three Gorges, etc.) in the network? Are they peripheral or central?
5. **Community structure** — Do natural clusters emerge by sector (energy, banking, construction, media)? What is the modularity of the network?
6. **Resilience** — Which nodes, if removed, would fragment the network most severely? (articulation points)
7. **Small-world effect** — What is the average shortest path between any two companies? Does Portugal exhibit the small-world property?

---

## Dataset

### Node Types

| Type | Description | Count (approx.) |
|---|---|---|
| `company` | Listed companies (Euronext Lisbon) + major unlisted firms | ~55 |
| `holding` | Private SGPS and intermediate holding companies | ~30 |
| `family` | Controlling family groups | ~10 |
| `person` | Board members, CEOs, key individuals | ~40 |
| `foreign` | Foreign shareholders and parent companies | ~15 |

### Edge Types

| Type | Description | Weight |
|---|---|---|
| `ownership` | Shareholder holds % of company | Percentage (0–100) |
| `board` | Person sits on board of company | 1 (or years of tenure) |
| `creditor` | Bank finances company | Estimated exposure |

### File Structure

```
project/
│
├── data/
│   ├── nodes.csv           # All nodes with attributes
│   ├── edges.csv           # All edges with weights and types
│   └── sources.md          # Data source log per company
│
├── scripts/
│   ├── build_dataset.py    # Add nodes/edges without duplicates
│   ├── metrics.py          # Compute centrality, clustering, paths
│   ├── communities.py      # Louvain community detection
│   └── export_gephi.py     # Export to .gexf for Gephi
│
├── gephi/
│   └── network.gephi       # Gephi project file
│
├── notebooks/
│   └── analysis.ipynb      # Full analysis notebook
│
└── README.md
```

### nodes.csv schema

```
id, label, type, sector, country, listed, notes
bcp, Millennium BCP, company, Banking, Portugal, yes, Largest private bank PT
fosun, Fosun International, foreign, Conglomerate, China, yes, HK Stock Exchange
```

### edges.csv schema

```
source, target, weight, edge_type, notes
fosun, bcp, 20.03, ownership, As of Dec 2024
nuno_amado, bcp, 1, board, Chairman 2022–2025
```

---

## Data Sources

### Primary sources (free)

| Source | What it provides | URL |
|---|---|---|
| **Euronext Lisbon** | Full list of listed companies, live prices | live.euronext.com/pt/markets/lisbon |
| **Company IR websites** | Shareholder structure, board composition | e.g. amorim.com/pt/investidores |
| **Annual Reports (PDF)** | Full corporate governance report incl. all board members | Search: `"company" "governo societário" 2024 filetype:pdf` |
| **CMVM Portal** | Qualified shareholdings (>5%) in listed companies | cmvm.pt |
| **Banco de Portugal** | Supervised banks, board members | bportugal.pt |

### Secondary sources (paid/partial)

| Source | What it provides | Cost |
|---|---|---|
| **Certidão Permanente** | Official registry extract for any Portuguese company | €25/company |
| **Racius / eInforma** | Shareholders and directors of private companies | €5–15/company |
| **Orbis (Bureau van Dijk)** | Comprehensive global ownership database | University access |

---

## Tools

| Tool | Purpose |
|---|---|
| **Python + NetworkX** | Graph construction, metric computation, algorithm implementation |
| **pandas** | Dataset management (nodes.csv / edges.csv) |
| **Gephi** | Visual layout (ForceAtlas2), community colouring, publication-quality output |
| **pdfplumber** | Extract board members from annual report PDFs |
| **matplotlib / seaborn** | Degree distribution plots, metric visualisations |

### Install dependencies

```bash
pip install networkx pandas matplotlib seaborn pdfplumber openpyxl
```

### Board extraction pipeline

The repository now includes a PDF-to-board-members pipeline for the 2024 governance reports.

Set your Gemini key in a local environment variable before running Pass 2:

```bash
set GEMINI_API_KEY=your_key_here
```

Do not commit `.env` or other local secret files.

---

## Graph Construction

```python
import networkx as nx
import pandas as pd

nodes = pd.read_csv('data/nodes.csv')
edges = pd.read_csv('data/edges.csv')

# Directed graph (ownership has direction: shareholder → company)
G = nx.DiGraph()

for _, row in nodes.iterrows():
    G.add_node(row['id'], **row.to_dict())

for _, row in edges.iterrows():
    G.add_edge(row['source'], row['target'],
               weight=row['weight'],
               edge_type=row['edge_type'])

print(f"Nodes: {G.number_of_nodes()}")
print(f"Edges: {G.number_of_edges()}")
print(f"Density: {nx.density(G):.4f}")
```

---

## Key Metrics

### Centrality

```python
# Degree centrality — most connected nodes
degree = nx.degree_centrality(G)

# Betweenness — nodes that bridge communities
betweenness = nx.betweenness_centrality(G, weight='weight')

# Eigenvector — influence via influential neighbours (like PageRank)
eigenvector = nx.eigenvector_centrality(G, weight='weight', max_iter=1000)

# Top 10 by betweenness
top10 = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
for node, score in top10:
    label = nodes.set_index('id').loc[node, 'label']
    print(f"{label:35s}  betweenness: {score:.4f}")
```

### Shortest Paths

```python
# Average shortest path (use undirected for reachability)
G_undirected = G.to_undirected()

if nx.is_connected(G_undirected):
    avg_path = nx.average_shortest_path_length(G_undirected)
    diameter = nx.diameter(G_undirected)
    print(f"Average shortest path: {avg_path:.2f}")
    print(f"Diameter: {diameter}")
else:
    # Work with largest connected component
    lcc = G_undirected.subgraph(max(nx.connected_components(G_undirected), key=len))
    print(f"Largest component: {lcc.number_of_nodes()} nodes")
    print(f"Average path (LCC): {nx.average_shortest_path_length(lcc):.2f}")
```

### Community Detection

```python
from networkx.algorithms.community import louvain_communities

communities = louvain_communities(G_undirected, seed=42)
print(f"Number of communities: {len(communities)}")

for i, community in enumerate(sorted(communities, key=len, reverse=True)):
    members = [nodes.set_index('id').loc[n, 'label']
               for n in community if n in nodes['id'].values]
    print(f"\nCommunity {i+1} ({len(community)} nodes):")
    print(", ".join(members[:8]))
```

### Articulation Points (resilience)

```python
# Nodes whose removal disconnects the graph
art_points = list(nx.articulation_points(G_undirected))
print(f"\nArticulation points ({len(art_points)}):")
for node in art_points:
    if node in nodes['id'].values:
        label = nodes.set_index('id').loc[node, 'label']
        print(f"  - {label}")
```

---

## Export to Gephi

```python
import networkx as nx

# Set visual attributes before export
for node in G.nodes():
    row = nodes[nodes['id'] == node]
    if not row.empty:
        G.nodes[node]['viz_color'] = {
            'company': '#534AB7',
            'holding': '#0F6E56',
            'foreign': '#993C1D',
            'person':  '#185FA5',
            'family':  '#854F0B'
        }.get(row['type'].values[0], '#888888')

nx.write_gexf(G, 'gephi/network.gexf')
print("Exported to gephi/network.gexf")
```

### Recommended Gephi settings

| Setting | Value |
|---|---|
| Layout | ForceAtlas2, LinLog mode ON, Prevent Overlap ON |
| Node size | Mapped to **Degree** or **Betweenness centrality** |
| Node colour | Mapped to **type** attribute |
| Edge weight | Mapped to **weight** (ownership %) |
| Edge filter | Filter by `edge_type` to toggle ownership vs board views |

---

## Expected Findings

Based on preliminary data, the network is expected to show:

- A **dense core** of Portuguese family-controlled groups (Amorim, Azevedo, Mello, Martins, Queiroz Pereira) highly interconnected through board interlocks
- **Fosun** as the most structurally significant foreign node, holding positions in BCP, Fidelidade, and Luz Saúde simultaneously
- The **Estado Português** as a hub connecting EDP, REN, CGD, TAP, and Novo Banco — a parallel network of public influence
- **Daenerys-style peripheral nodes**: Autoeuropa (100% VW), Delta Cafés (Nabeiro family) — large companies with almost no cross-connections to the main network
- A small-world average path length of **3–4 degrees of separation** between any two companies

---

## Methodology Notes

### Why directed graph?
Ownership has a clear direction (shareholder → company). Board membership could be modelled as undirected (mutual relationship) or as two directed edges. This project uses a **directed graph** for ownership edges and treats board edges as undirected for community detection purposes.

### Threshold for inclusion
Only shareholdings ≥ 2% are included as edges, consistent with the pre-2022 Portuguese legal disclosure threshold. Post-2022, the legal threshold moved to 5%, but historical reports preserve the 2% data.

### Handling offshore holdings
Several ownership chains pass through offshore vehicles (Netherlands BV, Luxembourg SARL, Cayman Islands funds). Where the ultimate beneficial owner is publicly disclosed (as required by Portuguese securities law for listed companies), the chain is traced to that person. Where it terminates offshore without disclosure, this is documented as a **methodological limitation** and noted in the edge's `notes` field.

### Unlisted companies
For unlisted companies, ownership data is obtained from the company's voluntary annual report, the Portuguese Commercial Registry (Certidão Permanente), or secondary sources (Racius, eInforma). Board composition is obtained from the same sources or from the Banco de Portugal supervised entities list.

---

## Limitations

- Data reflects a **static snapshot** (2024 annual reports). The network changes continuously as shareholdings shift.
- Shareholdings below the **5% disclosure threshold** are not captured for post-2022 data.
- Offshore holding chains may **truncate** where public disclosure ends.
- **Family relationships** between individuals are estimated from public sources (Forbes, press) and may be incomplete.
- Private companies that publish no annual report and have no significant connection to listed companies are excluded.

---

## References

- Battiston, S., et al. (2004). *Backbone of complex networks of corporations.* Physical Review E.
- Davis, G. F., et al. (2003). *The small world of the American corporate elite.* Strategic Organization.
- Fich, E. M., & White, L. J. (2003). *Why do CEOs reciprocally sit on each other's boards?* Journal of Corporate Finance.
- Euronext Lisbon — live.euronext.com
- CMVM — cmvm.pt
- Corticeira Amorim Shareholder Structure — amorim.com/en/investors
- Fidelidade Shareholders — fidelidade.pt/PT/a-fidelidade/investidores
- Forbes Portugal 50 Mais Ricos 2025

---

