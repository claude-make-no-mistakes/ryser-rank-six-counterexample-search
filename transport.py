"""Exact transportation collision bounds and side congruences."""

from collections import deque
from functools import cache
from itertools import combinations
from math import comb

from profiles import CROSS_RESIDUAL, survivors


@cache
def transport(a, b, edges, cap_three=False):
    """Return the minimum sum of binomial(cell, 2), or None if infeasible."""
    size_a, size_b = len(a), len(b)
    source, sink = size_a + size_b, size_a + size_b + 1
    graph = [[] for _ in range(sink + 1)]

    def add(u, v, capacity, cost):
        graph[u].append([v, len(graph[v]), capacity, cost])
        graph[v].append([u, len(graph[u]) - 1, 0, -cost])

    left, right = list(a), list(b)
    cost = 0
    for i, di in enumerate(a):
        for j, dj in enumerate(b):
            low = max(0, di + dj - (edges - CROSS_RESIDUAL))
            high = min(di, dj) - 1
            if cap_three and min(di, dj) == 3:
                high = 1
            if low > high:
                return None
            left[i] -= low
            right[j] -= low
            cost += comb(low, 2)
            for extra in range(low, high):
                add(i, size_a + j, 1, extra)
    if min(left + right) < 0:
        return None
    for i, value in enumerate(left):
        add(source, i, value, 0)
    for j, value in enumerate(right):
        add(size_a + j, sink, value, 0)

    for _ in range(sum(left)):
        distance = [float("inf")] * len(graph)
        predecessor = [None] * len(graph)
        distance[source] = 0
        pending = deque([source])
        queued = {source}
        while pending:
            u = pending.popleft()
            queued.remove(u)
            for k, (v, _, capacity, charge) in enumerate(graph[u]):
                if capacity and distance[u] + charge < distance[v]:
                    distance[v] = distance[u] + charge
                    predecessor[v] = (u, k)
                    if v not in queued:
                        queued.add(v)
                        pending.append(v)
        if predecessor[sink] is None:
            return None
        cost += distance[sink]
        v = sink
        while v != source:
            u, k = predecessor[v]
            _, inverse, _, _ = graph[u][k]
            graph[u][k][2] -= 1
            graph[v][inverse][2] += 1
            v = u
    return cost


def collision_data(system, edges, cap_three):
    pairs = {}
    for i, j in combinations(range(6), 2):
        a, b = sorted((system[i], system[j]))
        lower = transport(a, b, edges, cap_three)
        if lower is None:
            return None
        pairs[i, j] = lower
    return pairs


def scan(edges):
    _, _, systems = survivors(edges)
    print(f"edges={edges} systems entering transport={len(systems)}")
    before, after, open_systems = [], [], []
    for system in systems:
        redundancy = sum(comb(d, 2) for p in system for d in p) - comb(edges, 2)
        pairs = collision_data(system, edges, False)
        if pairs is None or sum(pairs.values()) > 2 * redundancy:
            continue
        before.append(system)
        cap_three = edges - 2 * sum(p.count(2) for p in system) <= 1
        if cap_three:
            pairs = collision_data(system, edges, True)
        if pairs is None or sum(pairs.values()) > 2 * redundancy:
            continue
        lower = sum(pairs.values())
        slack = 2 * redundancy - lower
        lower_on_sides = [sum(v for pair, v in pairs.items() if i in pair) for i in range(6)]
        # If slack is at most one, at most one pair can meet twice or three
        # times. Its redundancy is 1 or 2, respectively, modulo 3.
        if slack <= 1:
            exceptional = redundancy % 3
            if exceptional and slack == 0:
                reason = "redundancy is not divisible by three"
            elif not exceptional and any(
                not any(x % 3 == 0 for x in range(v, v + slack + 1)) for v in lower_on_sides
            ):
                reason = "a side collision count cannot be divisible by three"
            else:
                reason = None
        else:
            reason = None
        after.append(system)
        if reason is None:
            open_systems.append(system)
        if edges == 22:
            print(system, f"R={redundancy} min_T={lower} side_min={lower_on_sides}",
                  reason or "unresolved")
    print(f"transport={len(before)} degree_three={len(after)} unresolved={len(open_systems)}")
    return before, after, open_systems


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("edges", type=int)
    args = parser.parse_args()
    scan(args.edges)
