# Railway Network Centrality Analysis

This document contains the analysis of the rail network using Neo4j Graph Data Science.

## Setup

First, we project the graph into memory for analysis:

```cypher
CALL gds.graph.project(
  'railGraph',
  'Station',
  'NEXT_STOP'
)
```

## 1. Influence Analysis (PageRank)

Calculating the PageRank score for each station:

```cypher
CALL gds.pageRank.stream('railGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS Station, score
ORDER BY score DESC
LIMIT 10;
```

The following scores represent the "Influence" of stations. Lyon Part Dieu leads the ranking, followed closely by major terminals.

| Station | Score |
| :--- | :--- |
| **Lyon Part Dieu** | 8.94 |
| **Bordeaux Saint-Jean** | 8.28 |
| **Paris Montparnasse** | 7.61 |
| **Rennes** | 7.36 |
| **Saint-Pierre-des-Corps** | 7.10 |
| **Le Mans** | 7.06 |
| **Nantes** | 6.68 |
| **Angers Saint-Laud** | 6.54 |
| **Strasbourg** | 6.27 |
| **Lille Flandres** | 5.53 |

### Observations
*   **Lyon Part Dieu** remains the most influential node, confirming its role as a central crossroad.
*   **Paris Montparnasse** appears high in this ranking (3rd), suggesting it has strong incoming connections from other important nodes (likely the Atlantic line: Bordeaux, Rennes, Nantes).
*   The high scores for **Bordeaux**, **Rennes**, and **Nantes** confirm the strong "Atlantic" axis in this dataset.

### Deep Dive: Paris vs. Lyon Structure
While the dataset shows Paris Montparnasse as influential, the network topology often highlights a structural disparity between Paris and Lyon:

*   **Fragmentation**: "Paris" is split into multiple distinct stations (Gare de Lyon, Montparnasse, Nord, etc.) that are not connected in the rail graph. This naturally dilutes the score of any single "Paris" node compared to a unified hub.
*   **Hub vs. Terminus**: PageRank rewards nodes that act as "pass-through" funnels. Lyon Part Dieu is a central crossroad for North-South and East-West traffic. Paris stations typically act as "sinks" or endpoints, which can accumulate less transitive flow in specific projections.

## 2. Criticality Analysis (Betweenness Centrality)

Calculating Betweenness Centrality to identify bottlenecks:

```cypher
CALL gds.betweenness.stream('railGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS Station, score
ORDER BY score DESC
LIMIT 10;
```

Betweenness centrality identifies bridges or bottlenecks. The extremely high values for these smaller stations suggest they act as critical connectors, possibly in specific sub-graphs or line segments.

| Station | Score |
| :--- | :--- |
| **Vireux-Molhain** | 4.68e+31 |
| **Haybes** | 4.39e+31 |
| **Reims** | 4.32e+31 |
| **Paris Est** | 4.32e+31 |
| **Nouzonville** | 4.32e+31 |
| **Charleville-Mézières** | 4.32e+31 |
| **Bogny-sur-Meuse** | 4.32e+31 |
| **Rethel** | 4.32e+31 |
| **Monthermé** | 4.32e+31 |
| **Deville** | 4.32e+31 |

### Observations
*   **Anomaly Detection**: The values ($10^{31}$) are exceptionally high, which is unusual for standard Betweenness Centrality. This often indicates a "dumbbell" topology where a single line connects two massive, disconnected components, effectively funneling *all* possible shortest paths through that line.
*   **The "Ardennes" Line**: Many of these stations (Vireux-Molhain, Haybes, Charleville-Mézières) are on the same line in Northeastern France (Ardennes). This suggests this specific line might be the *only* link connecting a specific cluster of stations to the rest of the network in the dataset.

### Role of Bypass Hubs (General Topology)
Beyond the anomalies, key stations typically act as "bridges" in the French rail network:

*   **Key Bridges**: Stations like **Lyon Part Dieu**, **Marne-la-Vallée Chessy**, **St Pierre des Corps**, and **Massy TGV** are critical.
*   **Strategic Bypasses**: Stations like **Marne-la-Vallée (Disneyland)** and **Massy TGV** have high structural importance because they allow cross-country trains (e.g., Lille to Lyon) to bypass the congestion of central Paris terminals, effectively linking disjointed regions.
