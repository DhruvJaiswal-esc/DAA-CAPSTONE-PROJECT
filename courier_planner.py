"""Mini-Courier Planner - DAA Capstone (ETCCDA302)
Pipeline: merge sort (priority) -> 0/1 knapsack DP (packing) ->
Dijkstra (shortest paths) -> nearest-neighbour TSP (route).
"""
import heapq, json, random, time
from dataclasses import dataclass

# ---------------- Phase 1: data design ----------------
@dataclass
class Parcel:
    pid: int
    weight: int      # kg, integer so DP table can index it
    value: int       # priority/revenue score (higher = more important)
    deadline: int    # hours from now (smaller = more urgent)
    dest: int        # node id in the customer graph

def make_graph(n, extra_edges=None, seed=1):
    """Connected undirected weighted graph as adjacency list {u: [(v, w), ...]}.
    Node 0 is the depot. A random spanning chain guarantees connectivity."""
    rnd = random.Random(seed)
    g = {i: [] for i in range(n)}
    def add(u, v, w):
        g[u].append((v, w)); g[v].append((u, w))
    order = list(range(1, n)); rnd.shuffle(order)
    prev = 0
    for v in order:
        add(prev, v, rnd.randint(2, 20)); prev = v
    for _ in range(extra_edges if extra_edges is not None else n * 2):
        u, v = rnd.sample(range(n), 2)
        add(u, v, rnd.randint(2, 20))
    return g

def make_parcels(m, n_nodes, seed=2):
    rnd = random.Random(seed)
    return [Parcel(i, rnd.randint(1, 15), rnd.randint(10, 100),
                   rnd.randint(1, 48), rnd.randint(1, n_nodes - 1)) for i in range(m)]

# ---------------- Phase 2: sorting + knapsack ----------------
def merge_sort(items, key):
    """Stable O(n log n) merge sort."""
    if len(items) <= 1:
        return items
    mid = len(items) // 2
    L, R = merge_sort(items[:mid], key), merge_sort(items[mid:], key)
    out, i, j = [], 0, 0
    while i < len(L) and j < len(R):
        if key(L[i]) <= key(R[j]): out.append(L[i]); i += 1
        else: out.append(R[j]); j += 1
    return out + L[i:] + R[j:]

def prioritize(parcels):
    """Earliest deadline first; ties broken by higher value."""
    return merge_sort(parcels, key=lambda p: (p.deadline, -p.value))

def knapsack(parcels, capacity):
    """0/1 knapsack DP. dp[i][w] = best value using first i parcels, capacity w.
    Time O(n*W), space O(n*W) (full table kept for backtracking/evidence)."""
    n = len(parcels)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        p = parcels[i - 1]
        for w in range(capacity + 1):
            dp[i][w] = dp[i - 1][w]
            if p.weight <= w:
                dp[i][w] = max(dp[i][w], dp[i - 1][w - p.weight] + p.value)
    chosen, w = [], capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            chosen.append(parcels[i - 1]); w -= parcels[i - 1].weight
    chosen.reverse()
    return dp[n][capacity], chosen, dp

# ---------------- Phase 3: graph algorithms ----------------
def dijkstra(g, src):
    """Binary-heap Dijkstra. O((V+E) log V). Returns (dist, parent)."""
    dist = {u: float("inf") for u in g}; parent = {src: None}
    dist[src] = 0; pq = [(0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]: continue
        for v, w in g[u]:
            if d + w < dist[v]:
                dist[v] = d + w; parent[v] = u
                heapq.heappush(pq, (dist[v], v))
    return dist, parent

def path_to(parent, t):
    p = []
    while t is not None: p.append(t); t = parent[t]
    return p[::-1]

def nearest_neighbour_route(g, depot, stops):
    """TSP approximation: from the current stop, always go to the closest
    unvisited stop (distances via Dijkstra), then return to the depot.
    O(k * (V+E) log V) for k stops. No fixed approximation ratio in general,
    but fast and usually within ~25% of optimal on metric instances."""
    stops, route, total, cur = set(stops) - {depot}, [depot], 0, depot
    cache = {}
    def sp(u):
        if u not in cache: cache[u] = dijkstra(g, u)
        return cache[u]
    while stops:
        dist, _ = sp(cur)
        nxt = min(stops, key=lambda s: dist[s])
        total += dist[nxt]; route.append(nxt); stops.remove(nxt); cur = nxt
    total += sp(cur)[0][depot]; route.append(depot)
    return route, total

def expand_route(g, route):
    """Full node-by-node path including intermediate roads."""
    full = [route[0]]
    for a, b in zip(route, route[1:]):
        _, par = dijkstra(g, a)
        full += path_to(par, b)[1:]
    return full

def plan(parcels, g, capacity, depot=0):
    t = {}
    s = time.perf_counter(); ordered = prioritize(parcels); t["sort"] = time.perf_counter() - s
    s = time.perf_counter(); best, chosen, dp = knapsack(ordered, capacity); t["knapsack"] = time.perf_counter() - s
    stops = sorted({p.dest for p in chosen})
    s = time.perf_counter(); route, length = nearest_neighbour_route(g, depot, stops); t["route"] = time.perf_counter() - s
    return dict(ordered=ordered, best=best, chosen=chosen, dp=dp, route=route, length=length, times=t)

def save_dataset(path, parcels, g):
    json.dump({"parcels": [p.__dict__ for p in parcels],
               "graph": {str(u): e for u, e in g.items()}}, open(path, "w"))

def load_dataset(path):
    d = json.load(open(path))
    return ([Parcel(**p) for p in d["parcels"]],
            {int(u): [tuple(e) for e in es] for u, es in d["graph"].items()})

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data/small.json"
    parcels, g = load_dataset(path)
    CAP = 30
    r = plan(parcels, g, CAP)
    print(f"Dataset: {path}  ({len(parcels)} parcels, {len(g)} nodes, capacity {CAP} kg)\n")
    print("Parcels sorted by deadline (id, weight, value, deadline, dest):")
    for p in r["ordered"]: print(f"  P{p.pid}: {p.weight}kg value={p.value} due={p.deadline}h -> node {p.dest}")
    print(f"\nKnapsack optimum value: {r['best']}")
    print("Selected parcels:", [f"P{p.pid}" for p in r["chosen"]],
          f"| total weight {sum(p.weight for p in r['chosen'])}/{CAP} kg")
    print("\nNearest-neighbour route:", " -> ".join(map(str, r["route"])))
    print("Route length:", r["length"])
    print("Full road path:", " -> ".join(map(str, expand_route(g, r["route"]))))
    print("\nRuntimes (s):", {k: f"{v:.6f}" for k, v in r["times"].items()})
