from __future__ import annotations

import networkx as nx
from dataclasses import dataclass
from random import Random
from collections import defaultdict

def degree_sequence(G: nx.Graph, *, sort: bool = False, reverse: bool = True) -> list[int]:
    if isinstance(G.degree, int):
        return [G.degree]
    else:
        seq = [int(d) for _, d in G.degree]
        if sort:
            seq.sort(reverse=reverse)
        return seq


""" Our model of a graph G with vertex degrees k1,, . . . , kn,, is a set of
M = k1+,, . . . + kn, points arranged in cells of size k1, k2,. . . , kn. We take a partition
(called a pairing) P of the M points into M/2 parts (called pairs) of size 2
each. The degrees of P are k1, . . . , kn. The vertices of G are identified with
the cells and the edges with the pairs; each edge of G joins the vertices in
which the points of the corresponding pair lie. A loop of P is a pair whose
two points lie in the same cell. A multiple pair is a maximal set of j S: 2
pairs each involving the same two cells; this is a double pair if j = 2, a
triple pair if j = 3, and a double loop if the two cells are the same. The
mate of a point is the other point in its pair. (McKay-Wormald 1990) """

@dataclass(frozen=True)
class PairingResult:
    # Points are indexed 0..M-1; cell_of_point maps a point to its vertex (cell).
    pairs: list[tuple[int, int]]
    cell_of_point: list[int]
    mate: list[int]  # mate[p] is the other point paired with p

    def __str__(self) -> str:
        return self._format(max_items=8)

    def __repr__(self) -> str:
        return self._format(max_items=12, cls_name="PairingResult")

    def _format(self, *, max_items: int, cls_name: str | None = None) -> str:
        name = cls_name or self.__class__.__name__

        def fmt_list(xs: list[int] | list[tuple[int, int]]) -> str:
            n = len(xs)
            if n <= max_items:
                return repr(xs)
            head = ", ".join(repr(x) for x in xs[:max_items])
            return f"[{head}, ...] ({n} total)"

        M = len(self.mate)
        return (
            f"{name}(M={M}, "
            f"pairs={fmt_list(self.pairs)}, "
            f"cell_of_point={fmt_list(self.cell_of_point)}, "
            f"mate={fmt_list(self.mate)})"
        )


def _build_points_from_degrees(degrees: list[int]) -> list[int]:
    if any(k < 0 for k in degrees):
        raise ValueError("Degrees must be non-negative.")
    M = sum(degrees)
    if M % 2 != 0:
        raise ValueError("Sum of degrees must be even.")
    cell_of_point: list[int] = []
    for v, k in enumerate(degrees):
        cell_of_point.extend([v] * k)
    return cell_of_point


def mckay_wormald_random_pairing(
    degrees: list[int], seed: int | Random | None = None, debug: bool = False
) -> PairingResult:
    """
    Generate a random pairing (configuration) of points laid out in cells according to
    the given degree sequence, following the McKay–Wormald pairing model.

    - There are M = sum(degrees) points, arranged into n cells; cell v has size
      degrees[v].
    - A pairing is a partition of the M points into M/2 disjoint pairs.
    - A loop is a pair whose two points lie in the same cell.
    - A multiple pair is a set of j >= 2 pairs involving the same two cells.
      Special cases: double pair (j=2), triple pair (j=3), double loop when both
      cells coincide.

    Returns the raw pairing over points along with:
    - cell_of_point: maps each point to its cell (vertex index).
    - mate: for each point p, mate[p] is the other point in its pair.
    """
    rng = seed if isinstance(seed, Random) else Random(seed)
    cell_of_point = _build_points_from_degrees(degrees)
    M = len(cell_of_point)
    if debug:
        print(f"[random_pairing] Start: n={len(degrees)}, M={M}")
    if M == 0:
        if debug:
            print("[random_pairing] Empty degree sequence")
        return PairingResult(pairs=[], cell_of_point=[], mate=[])

    points = list(range(M))
    rng.shuffle(points)
    if debug:
        print(f"[random_pairing] Shuffled points (first 10): {points[:10]}")

    pairs: list[tuple[int, int]] = []
    mate: list[int] = [-1] * M
    for i in range(0, M, 2):
        p, q = points[i], points[i + 1]
        pairs.append((p, q))
        mate[p] = q
        mate[q] = p
    result = PairingResult(pairs=pairs, cell_of_point=cell_of_point, mate=mate)
    if debug:
        summary = pairing_summary(result, len(degrees))
        loops = summary["loops_total"]
        if isinstance(summary["multiplicities"], int):
            doubles = 0
        else:
            doubles = sum(
                True
                for (u, v), c in summary["multiplicities"].items()
                if u != v and c >= 2
            )
        if debug:
            print(
                f"[random_pairing] Done: pairs={len(pairs)}, loops={loops}, "
                f"doubled-cellpairs={doubles}"
            )
    return result


def mckay_random_graph_encoding(G: nx.Graph, seed: int | Random | None = None) -> PairingResult:
    """
    Generate a random pairing (configuration model realization) from the degree 
    sequence of the input graph, following the McKay–Wormald pairing model.
    - G: input graph (nx.Graph). Only the degree sequence is used; the actual edges 
      are ignored.
    - seed: optional random seed for reproducibility.
    Returns a random pairing over points along with:
    - cell_of_point: maps each point to its cell (vertex index).
    - mate: for each point p, mate[p] is the other point in its pair.
    """
    return mckay_wormald_random_pairing(degree_sequence(G), seed=seed)



def mckay_wormald_multigraph(
    degrees: list[int], seed: int | Random | None = None, debug: bool = False
) -> nx.MultiGraph:
    """
    Construct the multigraph induced by a random pairing of points according to
    the McKay–Wormald model. Nodes are 0..n-1. Loops and parallel edges are allowed.
    """
    if debug:
        print(
            f"[multigraph] Building from degrees: n={len(degrees)}, "
            f"sum={sum(degrees)}"
        )
    pairing = mckay_wormald_random_pairing(degrees, seed=seed, debug=debug)
    n = len(degrees)
    G: nx.MultiGraph = nx.MultiGraph()
    G.add_nodes_from(range(n))
    for p, q in pairing.pairs:
        u = pairing.cell_of_point[p]
        v = pairing.cell_of_point[q]
        G.add_edge(u, v)
    if debug:
        loops = sum(
            1 for u, v, k in G.edges(keys=True) if u == v
        )
        par_total = sum(
            max(0, G.number_of_edges(u, v) - 1)
            for u, v in G.edges()
        )
        print(
            f"[multigraph] Done: edges={G.number_of_edges()}, loops={loops}, "
            f"parallel_overcount={par_total}"
        )
    return G


def pairing_summary(
    pairing: PairingResult, n: int
) -> dict[str, int | dict[tuple[int, int], int]]:
    """
    Compute counts of loops and multiplicities over the induced cell pairs.
    Returns a dict with:
      - loops_total: total number of loops
      - double_pairs: count of unordered cell-pairs with multiplicity exactly 2 (u != v)
      - triple_pairs: count of unordered cell-pairs with multiplicity exactly 3 (u != v)
      - double_loops: count of cells with exactly 2 loops
      - multiplicities: dict mapping unordered cell-pair (u<=v) to its multiplicity
    """
    multiplicities: dict[tuple[int, int], int] = {}
    loops_by_cell: list[int] = [0] * n

    for p, q in pairing.pairs:
        u = pairing.cell_of_point[p]
        v = pairing.cell_of_point[q]
        key = (u, v) if u <= v else (v, u)
        multiplicities[key] = multiplicities.get(key, 0) + 1
        if u == v:
            loops_by_cell[u] += 1

    loops_total = sum(loops_by_cell)
    double_pairs = sum(
        1 for (u, v), c in multiplicities.items() if u != v and c == 2
    )
    triple_pairs = sum(
        1 for (u, v), c in multiplicities.items() if u != v and c == 3
    )
    double_loops = sum(1 for (u, v), c in multiplicities.items() if u == v and c == 2)

    return {
        "loops_total": loops_total,
        "double_pairs": double_pairs,
        "triple_pairs": triple_pairs,
        "double_loops": double_loops,
        "multiplicities": multiplicities,
    }


def mate_of(point: int, pairing: PairingResult) -> int:
    """
    Return the mate of a point in the pairing (the other point in its pair).
    """
    if point < 0 or point >= len(pairing.mate):
        raise IndexError("Point index out of range.")
    return pairing.mate[point]
