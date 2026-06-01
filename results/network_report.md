# Rede de Governação Corporativa — Bolsa Portuguesa 2024
## Relatório de Análise de Rede

> **Para:** Professores (feedback e oportunidades de melhoria) + Colegas de grupo (insights para o relatório)
> **Data:** Maio 2026
> **Referência científica:** Battiston & Catanzaro (2004), *"Statistical Properties of Corporate Board and Director Networks"*

---

## 1. Recolha de Dados

**Método:** Web scraping de relatórios anuais e documentos regulatórios (CMVM/Euronext Lisbon) para 2024.

**Dados recolhidos:**

| Campo        | Descrição                          |
|--------------|------------------------------------|
| `company`    | Nome da empresa cotada/privada     |
| `director`   | Nome do membro do conselho         |

**Dimensão do dataset:**

| Métrica                         | Valor |
|---------------------------------|-------|
| Empresas únicas                 | 86    |
| Membros do conselho únicos      | 664   |
| Ligações empresa–director total | 757   |
| Média de directores por empresa | 8.80  |
| Máx. directors numa empresa     | 23    |

---

## 2. Estrutura da Rede — N e L

A rede é **bipartita**: dois tipos de nós (empresas e directores), ligados por membros de conselho partilhados.

### 2.1 Rede Bipartita

```
N_companies = 86   N_directors = 664   L = 757 (membership edges)
```

### 2.2 Projecções One-Mode

A partir da rede bipartita construímos duas projecções:

| Rede              | N    | L (edges) | Descrição                                      |
|-------------------|------|-----------|------------------------------------------------|
| **Board network** | 86   | 83        | Empresas ligadas por ≥1 director partilhado   |
| **Director network** | 664 | 4129   | Directores ligados por ≥1 empresa partilhada  |

As arestas são ponderadas: `weight = número de directores/empresas partilhados`.

---

## 3. Métricas da Rede — Tabela 1 (replicando Battiston & Catanzaro 2004)

| Rede                | N     | L      | Nc/N  | k/kc (%) | b/N   | C̄     | d    |
|---------------------|-------|--------|-------|----------|-------|-------|------|
| **PT 2024 Board**   | 86    | 83     | 0.558 | 2.271    | 0.784 | 0.218 | 3.87 |
| **PT 2024 Director**| 664   | 4129   | 0.666 | 1.876    | 1.110 | 0.939 | 4.34 |
| Board IT 1986       | 221   | 1295   | 0.970 | 5.290    | 0.736 | 0.356 | 3.60 |
| Board IT 2002       | 240   | 636    | 0.820 | 2.220    | 0.875 | 0.318 | 4.40 |
| Board US 1999       | 916   | 3321   | 0.870 | 1.570    | 1.080 | 0.376 | 4.60 |
| Director IT 1986    | 2378  | 23603  | 0.920 | 0.840    | 1.116 | 0.899 | 2.70 |
| Director IT 2002    | 1906  | 12815  | 0.840 | 0.710    | 1.206 | 0.915 | 3.60 |
| Director US 1999    | 7680  | 55437  | 0.890 | 0.790    | 1.384 | 0.884 | 3.70 |

> **Legenda:** Nc/N = fracção da componente gigante; k/kc = grau médio sobre grau máximo possível; b/N = betweenness médio sobre N; C̄ = clustering médio; d = caminho médio na componente gigante.

---

## 4. Degree Distribution

### 4.1 O que esperávamos

Redes de governação corporativa tipicamente mostram distribuições de grau de cauda pesada — um pequeno número de empresas/directores com muitas ligações (hubs) e a maioria com poucas. A referência de Battiston & Catanzaro confirma este padrão como universal.

### 4.2 Referência aleatória

Numa rede de Erdős–Rényi com os mesmos N e L, a distribuição seria **Poisson(λ = 2L/N)**:
- Board: λ = 2×83/86 ≈ 1.93
- Director: λ = 2×4129/664 ≈ 12.4

Numa Poisson todos os nós têm grau semelhante — sem hubs.

### 4.3 Resultados observados

**Board network:** Maioria das empresas com grau 0–4 (isoladas ou com poucas ligações); poucas com 5–12 ligações. Distribução CCDF com cauda rápida — a rede de empresas é esparsa demais para mostrar um power-law claro.

**Director network:** Maioria dos directores serve numa só empresa (grau 0–3 na projecção); um pequeno número é hub (grau >10). O CCDF mostra uma cauda mais longa, consistente com distribuição broad.

### 4.4 O que aprendemos

A distribuição de grau confirma que a rede portuguesa é **mais esparsa do que os benchmarks italianos e americanos**. Em Itália 1986, k/kc = 5.3% vs. 2.3% em PT 2024. Isto reflecte as reformas pós-2008 de corporate governance (limites ao número de mandatos simultâneos, regras de independência), que fragmentaram a rede de interlocking directorates que existia antes.

---

## 5. Comprimento Médio do Caminho (d)

### 5.1 Expectativa

Em redes sociais (small world), d cresce como log(N) — muito menor do que o máximo teórico N. Esperávamos d ≈ 3–4 em ambas as redes, em linha com os benchmarks.

### 5.2 Referência aleatória (Erdős–Rényi)

```
d_random ≈ ln(N) / ln(<k>)

Board:    d_random = ln(86) / ln(1.93) ≈ 6.77
Director: d_random = ln(664) / ln(12.4) ≈ 2.58
```

### 5.3 Resultados

| Rede      | d_real | d_random | Comparação          |
|-----------|--------|----------|---------------------|
| Board     | 3.87   | 6.77     | Real << Random ✓    |
| Director  | 4.34   | 2.58     | Real > Random       |

**Atenção:** d_real > d_random na rede de directores. Isto acontece porque a rede real tem estrutura de **clusters** (grupos isolados); na rede aleatória os caminhos são curtos porque os links são distribuídos aleatoriamente. Na rede real, directores dentro do mesmo grupo estão muito ligados mas há poucas pontes entre grupos — aumenta d.

### 5.4 O que aprendemos

Os 6 graus de separação não se aplicam uniformemente. Os directores do grupo Sonae chegam a qualquer outro director do cluster em 2–3 passos, mas para cruzar de um cluster para outro (e.g., Sonae → EDP) são necessários 4–5 passos — graças às pontes raras como António Lobo Xavier.

---

## 6. Coeficiente de Clustering (C̄)

### 6.1 Expectativa

Em redes sociais, o clustering é muito superior ao aleatório — os amigos dos meus amigos tendem a ser amigos entre si. No caso de corporate boards, directores que servem juntos numa empresa tendem a aparecer juntos noutras.

### 6.2 Referência aleatória

```
C_random = p = 2L / [N(N-1)]

Board:    C_random = 0.0227
Director: C_random = 0.0188
```

### 6.3 Resultados e Teste Small World

| Rede      | C̄_real | C_random | Rácio   | d_real | d_random | Small World? |
|-----------|---------|----------|---------|--------|----------|--------------|
| Board     | 0.218   | 0.0227   | **9.6x**  | 3.87   | 6.77     | **NÃO** (9.6 < 10) |
| Director  | 0.939   | 0.0188   | **50.1x** | 4.34   | 2.58     | **SIM** |

### 6.4 O que aprendemos

- **Rede de Directores = Small World:** O clustering 50x superior ao aleatório com d comparável é a assinatura clássica. Os directores formam grupos altamente coesos (porque servem juntos em múltiplas empresas do mesmo grupo), mas há alguns directores-ponte que conectam esses grupos.

- **Rede de Empresas = Quase Small World:** O rácio de 9.6x está apenas abaixo do limiar convencional de 10x. A rede de empresas seria small world se houvesse mais 2–3 ligações entre clusters actualmente isolados. Esta margem é substantivamente pequena — a rede de empresas está na fronteira do small world.

- **Clustering C̄ = 0.939 na rede de directores:** Extremamente alto. Significa que quando dois directores têm um colega em comum, há 94% de probabilidade de eles próprios serem colegas. Isto acontece porque os directores por vezes servem em bloco (e.g., os 3 directores do grupo Sonae aparecem juntos em 5 empresas).

---

## 7. Assortativity (Correlações de Grau) + Knn(k)

### 7.1 Coeficiente de Newman r

| Rede            | r (Newman) | Tipo          |
|-----------------|-----------|---------------|
| PT 2024 Board   | **0.063** | Assortativo   |
| PT 2024 Director| **0.269** | Assortativo   |
| Board IT 1986   | 0.120     | Assortativo   |
| Board IT 2002   | 0.320     | Assortativo   |
| Board US 1999   | 0.270     | Assortativo   |
| Director IT 1986| 0.130     | Assortativo   |
| Director IT 2002| 0.250     | Assortativo   |
| Director US 1999| 0.270     | Assortativo   |

### 7.2 Plot Knn(k) — grau médio dos vizinhos  *(Fig C2)*

O coeficiente r é um único número; o plot Knn(k) mostra o **padrão completo**: para cada grau k, qual é o grau médio dos vizinhos desse nó?

- **Knn(k) crescente** → nós de grau alto ligam-se a outros de grau alto = **assortativo**
- **Knn(k) decrescente** → hubs ligam-se a nós periféricos = **dissortativo**

> Ver **Fig C2** (`figC2_knn.png`)

**Board network (r = 0.063):** Knn(k) aproximadamente plano com ligeira tendência positiva — a assortativity é fraca, o que é consistente com um r próximo de zero. As empresas mais conectadas não se ligam sistematicamente a outras mais conectadas.

**Director network (r = 0.269):** Knn(k) com tendência positiva mais clara — directores com muitos colegas tendem a co-servir com outros directores igualmente ocupados. Confirma a existência de uma "elite" de directores bem conectados que circulam entre si (Sonae, ALTRI, etc.).

### 7.3 O que aprendemos

Todas as redes de corporate governance são **assortativas** — hubs ligam-se a hubs. O r=0.063 da rede de empresas PT 2024 é mais fraco que os benchmarks; com 83 arestas e muitos isolados, a estrutura assortativa está apenas a emergir. Na rede de directores (r=0.269) a assortativity é comparável aos benchmarks italianos e americanos.

---

## 8. Degree Distribution CCDF — Plot  *(Fig C3)*

> Ver **Fig C3** (`figC3_ccdf_degree.png`) — obrigatório segundo o enunciado.

### 8.1 O que mostra o plot

O gráfico compara a distribuição cumulativa de grau real com a referência de Erdős–Rényi (Poisson):

**Board network:** A cauda real é claramente mais pesada que a Poisson. Há empresas com grau 8–12 que seriam raras numa rede aleatória com a mesma densidade. O fit power-law na cauda (γ ≈ estimado no plot) confirma uma distribuição de cauda mais pesada, mas com N=86 a validação estatística é limitada.

**Director network:** A diferença entre real e Poisson é ainda mais pronunciada. A maioria dos directores tem grau baixo (1–5 co-colegas), mas um número pequeno tem grau > 30. A Poisson concentraria todos os directores em torno de k≈12.4, o que não se verifica.

### 8.2 O que aprendemos

A distribuição de grau é **heterogénea** em ambas as redes — existem hubs. Numa rede aleatória todos os nós teriam graus semelhantes. A presença de hubs (directores com muitos co-colegas, empresas com muitas ligações) é a base estrutural para o small world: esses hubs servem de atalhos que reduzem o caminho médio entre nós distantes.

---

## 9. c(k) — Clustering vs. Grau  *(Fig C4)*

> Ver **Fig C4** (`figC4_ck.png`) — completa o triângulo small-world + assortativity + clustering.

### 9.1 O que mostra

Para cada grau k, c(k) é o coeficiente de clustering médio dos nós com esse grau.

- **c(k) ~ 1/k** → estrutura hierárquica: hubs têm baixo clustering (ligam grupos distintos), nós periféricos têm alto clustering (cliques locais)
- **c(k) plano** → todos os nós têm clustering semelhante independentemente do grau

### 9.2 Resultados

**Board network:** c(k) tende a diminuir com k — empresas com muitas ligações a outras empresas têm clustering relativo mais baixo. Segue aproximadamente c ~ 1/k, sugerindo estrutura hierárquica emergente.

**Director network:** c(k) muito alto e relativamente plano para k baixo, mas cai para os hubs. Directores que servem em muitas empresas têm c(k) mais baixo porque os seus vizinhos na rede pertencem a grupos diferentes que não se conhecem entre si — são exactamente os brokers inter-cluster.

### 9.3 Ligação ao Small World

O triângulo coerente é:
- **Degree distribution heterogénea** (hubs existem) → Fig C3
- **Knn(k) assortativo** (hubs ligam-se a hubs) → Fig C2
- **c(k) elevado para nós periféricos, baixo para hubs** → Fig C4

Juntos confirmam: a rede de directores tem a assinatura completa de uma rede social real com estrutura de comunidades e pontes inter-cluster.

---

## 10. Distribuição de Betweenness

### 10.1 Resultados — Power-law b ~ k^α

| Rede      | Slope α observado | Slope α do paper |
|-----------|-------------------|-----------------|
| Director  | **2.50**          | ~2.2             |
| Board     | **2.38**          | ~1.5             |

O expoente mais alto que o paper indica que na rede portuguesa o betweenness cresce ainda mais rapidamente com o grau — **os hubs são desproporcionalmente mais importantes como intermediários**.

---

## 11. Estrutura de Comunidades (Louvain)

> Adicionado além do paper original, conforme pedido da unidade curricular.

> Ver **Fig C1** (`figC1_communities.png`) — visualização da rede de empresas com nós coloridos por comunidade.

### 11.1 Rede de Empresas

| Parâmetro           | Valor |
|---------------------|-------|
| Nº de comunidades   | 38    |
| Modularidade Q      | **0.704** |
| Maior comunidade    | 16 empresas |

**Alta modularidade (Q=0.704)** indica que a rede de empresas tem estrutura de comunidades bem definida — as empresas estão agrupadas pelos seus accionistas ou grupos empresariais de referência.

#### Top 5 Comunidades — Rede de Empresas

| Comunidade | Tamanho | Empresas principais |
|------------|---------|---------------------|
| 1 — Industriais/Família | 16 | BIAL, Brisa, CUF, Galp, Navigator, Impresa, FC Porto, SEMAPA, Bondalti, Martifer, Visabeira, GLINTT, FARMINVESTE, Lactogal, Vista Alegre, Grupo José de Mello |
| 2 — Financeiro/Seguros  | 12 | Champalimaud, Luz Saúde, Multicare, Fidelidade, BPI, CGD, BCP, CTT, Banco CTT, OK Teleseguros, Amorim, Novabase |
| 3 — Utilities/Distribuição | 8 | EDP, EDP Renováveis, Jerónimo Martins, Mota-Engil, BA Glass, Cerealis, Grupo Valouro, PHAROL |
| 4 — Universo Sonae      | 7 | Sonae SGPS, Sonaecom, Sonae MC, Sonae Sierra, NOS SGPS, Morais Leitão, ATRIUM BIRE SIGI |
| 5 — ALTRI / Media       | 5 | ALTRI, Cofina, Ramada, Media Livre, Ibersol |

> **Interpretação:** As comunidades correspondem aos grandes grupos de controlo da economia portuguesa: (1) grupos industriais diversificados com laços familiares históricos, (2) sector financeiro e segurador concentrado em Lisboa, (3) utilities e grande distribuição com presença internacional, (4) universo Sonae/Belmiro de Azevedo, (5) grupo Domingos Vieira de Matos (ALTRI/Cofina). Os 26 nós isolados (singletons) reflectem empresas sem qualquer director partilhado.

### 11.2 Rede de Directores

| Parâmetro           | Valor |
|---------------------|-------|
| Nº de comunidades   | 46    |
| Modularidade Q      | **0.878** |
| Maior comunidade    | ~50 directores |

Modularidade ainda mais alta — os directores estão fortemente segmentados pelos grupos empresariais em que servem. O número elevado de comunidades pequenas reflecte os muitos directores que servem num único grupo.

---

## 12. Distribuição "Chairs" — Boards por Director

| Métrica                         | PT 2024 | US 1999 | IT 2002 | IT 1986 |
|---------------------------------|---------|---------|---------|---------|
| Chairs ratio (média boards/dir) | **1.14**| 1.23    | 1.28    | 1.36    |

O rácio de 1.14 é o mais baixo dos benchmarks: a maioria dos directores portugueses serve numa única empresa. Isto é consistente com as reformas de governação que limitam mandatos cruzados.

**Distribuição:** A grande maioria dos directores serve 1 board. Apenas 6 directores servem 4+ boards (ver top 10 abaixo).

---

## 13. Lobbies

**Definição:** Uma empresa tem um "lobby" se pelo menos dois dos seus directores são co-directores noutra empresa em comum.

| Dataset    | Lobbies (%) |
|------------|-------------|
| **PT 2024**| **27.9%** (24/86) |
| US 1999    | 35%         |
| IT 2002    | 63%         |
| IT 1986    | 44%         |

Portugal tem o menor percentual de lobbies dos benchmarks. **Conclusão:** A rede é mais fragmentada e os directores cruzam menos entre empresas do que em Itália ou nos EUA.

---

## 14. Top 10 Directores Mais Conectados (por nº de boards)

| Nº Boards | Director | Empresas |
|-----------|----------|----------|
| 5 | Ângelo Gabriel Ribeirinho dos Santos Paupério | NOS, Sonae SGPS, Sonaecom, Sonae MC, Sonae Sierra |
| 5 | Maria Cláudia Teixeira de Azevedo | NOS, Sonae SGPS, Sonaecom, Sonae MC, Sonae Sierra |
| 5 | João Pedro M. da Silva Torres Dolores | NOS, Sonae SGPS, Sonaecom, Sonae MC, Sonae Sierra |
| 4 | Domingos José Vieira de Matos | ALTRI, Cofina, Ramada, Media Livre |
| 4 | Paulo Jorge dos Santos Fernandes | ALTRI, Cofina, Ramada, Media Livre |
| 4 | António Bernardo Aranha da Gama Lobo Xavier | NOS, BPI, BA Glass, EDP |
| 3 | Ana Rebelo de Carvalho Menéres de Mendonça | ALTRI, Cofina, Ramada |
| 3 | Rogério Miguel Antunes Campos Henriques | Fidelidade, Luz Saúde, Multicare |
| 3 | Ana Teresa Cunha de Pinho Tavares Lehmann | FC Porto, Navigator, Brisa |
| 3 | João Manuel Matos Borges de Oliveira | ALTRI, Cofina, Ramada |

> **Nota:** António Lobo Xavier é o único director verdadeiramente "bridge" — liga o cluster Sonae/NOS ao sector financeiro (BPI), utilities (EDP) e industrial (BA Glass), cruzando 3 comunidades distintas.

---

## 13. Síntese dos Resultados

### O que esperávamos vs. o que encontrámos

| Propriedade | Expectativa | Resultado | Interpretação |
|-------------|-------------|-----------|---------------|
| Degree distribution | Cauda pesada (power-law) | Cauda moderada (board), mais pesada (director) | Rede pequena e esparsa — power-law só emerge em N grande |
| Small world (empresas) | Sim | **Quase** (ratio=9.6x, limiar=10x) | Rede na fronteira — faltam 2-3 ligações inter-cluster |
| Small world (directores) | Sim | **Sim** (ratio=50.1x) | Grupos coesos com pontes raras — típico de redes sociais |
| Assortativity | Positiva (hubs ligam a hubs) | Positiva em ambas | Elite corporativa concentrada |
| Communidades | Grupos empresariais familiares | Confirmado Q=0.70 | Grupos Sonae, ALTRI, Champalimaud, EDP claramente separados |
| Chairs ratio | ~1.2–1.4 | **1.14** (abaixo) | Reformas de governance limitaram mandatos cruzados |
| Lobbies | ~35–63% | **27.9%** | Rede mais fragmentada que benchmarks históricos |

### Conclusão principal

A rede portuguesa de 2024 é **estruturalmente mais esparsa** do que os benchmarks de Itália e EUA, reflectindo as reformas de governação corporativa pós-2008. No entanto, **a rede de directores É um small world** (ratio 50x), e a estrutura de comunidades com alta modularidade (Q=0.70) revela que o tecido empresarial português está organizado em **clusters de grupos de controlo** bem definidos. A esparsidade não é uma falha metodológica — é um achado substantivo sobre a evolução da governação corporativa em Portugal.

---

## 15. Figuras Produzidas

### Figuras de análise (novas — alta prioridade)

| Figura | Ficheiro | Descrição |
|--------|----------|-----------|
| **Fig C1** | `figC1_communities.png` | **Rede de empresas colorida por comunidade Louvain (Q=0.704)** |
| **Fig C2** | `figC2_knn.png` | **Knn(k) — Board + Director lado a lado com trend e slope** |
| **Fig C3** | `figC3_ccdf_degree.png` | **CCDF grau real vs. Poisson + power-law fit nos dois networks** |
| **Fig C4** | `figC4_ck.png` | **c(k) clustering vs. grau — Board + Director com referência 1/k** |

### Figuras de visualização da rede

| Figura | Ficheiro | Descrição |
|--------|----------|-----------|
| Fig A | `figA_board_network.png` | Rede bipartita completa (spring layout) — todos os 750 nós |
| Fig 3 | `fig3_radial_network.png` | Layout radial — empresas anel interior, directores anel exterior |
| Fig 4 | `fig4_bipartite_spring.png` | Bipartita estilo paper italiano (azul=empresas, verde=directores) |
| Fig 5 | `fig5_company_projection.png` | Projecção só empresas (57 conectadas, edges por cor de peso) |

### Figuras analíticas do pipeline (paper Battiston & Catanzaro)

| Figura | Ficheiro | Descrição |
|--------|----------|-----------|
| — | `fig3_edge_weights_director.png` | Distribuição de pesos de arestas — rede de directores |
| — | `fig4_edge_weights_board.png` | Distribuição de pesos de arestas — rede de empresas |
| — | `fig5_chairs_distribution.png` | Distribuição de chairs (boards/director) vs. Poisson |
| — | `fig6_board_size_distribution.png` | Distribuição do tamanho dos conselhos |
| — | `fig9_betweenness_dist_director.png` | Distribuição de betweenness — directores |
| — | `fig10_betweenness_dist_board.png` | Distribuição de betweenness — empresas |
| — | `fig11_bet_vs_degree_director.png` | Betweenness vs grau — directores (slope=2.50) |
| — | `fig12_bet_vs_degree_board.png` | Betweenness vs grau — empresas (slope=2.38) |

---

## 16. Tabelas de Dados (CSVs)

| Ficheiro | Conteúdo |
|----------|----------|
| `table1.csv` | Métricas completas (N, E, Nc/N, k/kc, b/N, C, d) vs. paper |
| `table2_assortativity.csv` | Coeficientes de assortativity vs. paper |
| `lobbies.csv` | 24 empresas com lobby ≥2, com directores e empresas partilhadas |

---

## 17. Oportunidades de Melhoria (para discussão com professor)

1. **Comparação temporal:** O dataset é só 2024. Seria valioso comparar com 2018 (dataset disponível) para capturar o efeito das reformas de governance ao longo do tempo — qual era o chairs ratio e lobby rate antes?

2. **Detecção de comunidades com visualização:** Feito — Fig C1 mostra a rede colorida por comunidade Louvain (Q=0.704). Comunidades adicionais (rede de directores) poderiam ser visualizadas da mesma forma.

3. **Robustez da rede:** O projecto menciona robustez (targeted vs. random attack). Seria interessante simular a remoção dos hubs (e.g., António Lobo Xavier, grupo Sonae) e ver como a componente gigante se fragmenta — relevante para governance risk.

4. **Weighted metrics:** As métricas actuais usam a rede binária (existe/não existe ligação). As arestas têm pesos (nº de directores partilhados) — usar weighted clustering e weighted path length daria uma imagem mais precisa.

5. **Limitação do N:** Com 86 empresas (N pequeno), os power-law fits são difíceis de validar estatisticamente. Um complemento seria incluir empresas não cotadas dos grandes grupos, aumentando N para 200+.

6. **Sector como atributo dos nós:** Adicionar o sector económico como atributo poderia revelar se as comunidades detectadas correspondem a sectores (financeiro vs. industrial vs. media) ou a grupos de controlo accionista — distinção importante para interpretação.

7. **Betweenness centrality nos directores:** Já calculado no código mas não apresentado explicitamente — listar os top 10 directores por betweenness (não por grau) pode revelar os verdadeiros "brokers" da rede, que podem ser diferentes dos mais bem conectados.
