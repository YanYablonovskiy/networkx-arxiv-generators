from __future__ import annotations

import networkx as nx
from dataclasses import dataclass
from random import Random
from collections import defaultdict

# References:
# B.D. McKay and N.C. Wormald, Uniform generation of random regular graphs of
# moderate degree, J. Algorithms 11 (1990), 52–67.

def degree_sequence(
    G: nx.Graph, *, sort: bool = False, reverse: bool = True
) -> list[int]:
    if isinstance(G.degree, int):
        return [G.degree]
    else:
        seq = [int(d) for _, d in G.degree]
        if sort:
            seq.sort(reverse=reverse)
        return seq


'''
Our model of a graph G with vertex degrees k1,, . . . , kn,, is a set of
M = k1+,, . . . + kn, points arranged in cells of size k1, k2,. . . , kn. We take a partition
(called a pairing) P of the M points into M/2 parts (called pairs) of size 2 each.
The degrees of P are k1, . . . , kn. The vertices of G are identified with the cells
and the edges with the pairs; each edge of G joins the vertices in which the points
of the corresponding pair lie. A loop of P is a pair whose two points lie in the
same cell. A multiple pair is a maximal set of j S: 2 pairs each involving the same
two cells; this is a double pair if j = 2, a triple pair if j = 3, and a double loop
if the two cells are the same. The mate of a point is the other point in its pair.
(McKay-Wormald 1990)
'''


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


# Implement McKay–Wormald switchings and drivers (NOLOOPS, NODOUBLES, DEG).
# Note: This is a practical implementation of the described procedures.
# It performs valid forward switchings chosen uniformly among available
# candidates and always accepts the move (i.e., no Metropolis correction).
# If no valid switching exists at some stage, it restarts from a fresh random pairing.


def _degrees_from_cell_of_point(cell_of_point: list[int]) -> list[int]:
    if not cell_of_point:
        return []
    n = max(cell_of_point) + 1
    degs = [0] * n
    for c in cell_of_point:
        degs[c] += 1
    return degs


def _pairs_by_cellpair(
    pairing: PairingResult,
) -> tuple[
    dict[tuple[int, int], list[int]],
    dict[tuple[int, int], int],
    list[int],
]:
    """
    Build:
      - pairs_by_cp: unordered cell-pair -> list of pair indices
      - multiplicities: unordered cell-pair -> multiplicity
      - loops_by_cell: count of loops per cell
    """
    pairs_by_cp: dict[tuple[int, int], list[int]] = defaultdict(list)
    multiplicities: dict[tuple[int, int], int] = defaultdict(int)
    n_cells = max(pairing.cell_of_point) + 1 if pairing.cell_of_point else 0
    loops_by_cell = [0] * n_cells

    for idx, (p, q) in enumerate(pairing.pairs):
        u = pairing.cell_of_point[p]
        v = pairing.cell_of_point[q]
        if u == v:
            loops_by_cell[u] += 1
        key = (u, v) if u <= v else (v, u)
        pairs_by_cp[key].append(idx)
        multiplicities[key] += 1

    return pairs_by_cp, multiplicities, loops_by_cell


def _rebuild_pairs_from_mate(mate: list[int]) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    seen = [False] * len(mate)
    for i in range(len(mate)):
        if not seen[i]:
            j = mate[i]
            if j < 0:
                raise ValueError("Invalid mate array.")
            if i == j:
                raise ValueError("Self-loop at point pairing, invalid mate.")
            if seen[j]:
                # Already emitted by j
                seen[i] = True
                continue
            pairs.append((i, j))
            seen[i] = True
            seen[j] = True
    return pairs


def _apply_l_switching(
    pairing: PairingResult, loop_idx: int, e1_idx: int, e2_idx: int, debug: bool = False
) -> PairingResult:
    """
    Apply one forward l-switching on:
      L: loop pair (a,b) in cell X
      E1: non-loop (c,d) with cells Y,Z
      E2: non-loop (e,f) with cells U,V
    New pairs: (a,c) [X-Y], (b,e) [X-U], (d,f) [Z-V]
    """
    a, b = pairing.pairs[loop_idx]
    c, d = pairing.pairs[e1_idx]
    e, f = pairing.pairs[e2_idx]

    cell = pairing.cell_of_point
    if debug:
        X = cell[a]
        Y, Z = cell[c], cell[d]
        U, V = cell[e], cell[f]
        print(
            f"[l-switch] Apply: L@{loop_idx} cell={X}; E1@{e1_idx} cells=({Y},{Z}); "
            f"E2@{e2_idx} cells=({U},{V})"
        )

    new_mate = pairing.mate.copy()

    # Break and re-pair the six endpoints
    new_mate[a] = c
    new_mate[c] = a

    new_mate[b] = e
    new_mate[e] = b

    new_mate[d] = f
    new_mate[f] = d

    new_pairs = _rebuild_pairs_from_mate(new_mate)
    if debug:
        print("[l-switch] Complete: updated 3 pairs")
    return PairingResult(
        pairs=new_pairs, cell_of_point=pairing.cell_of_point, mate=new_mate
    )


def _find_random_l_switching_candidate(
    pairing: PairingResult, rng: Random, debug: bool = False
) -> tuple[int, int, int] | None:
    """
    Find a random valid forward l-switching candidate (loop_idx, e1_idx, e2_idx).
    Constraints:
      - loop is a single loop at its cell (no double loop)
      - e1 and e2 are non-loop pairs whose cell-pairs have multiplicity exactly 1
      - the five involved cells are all distinct (loop cell + 4 endpoints' cells)
      - the created cell-pairs do not already exist (to avoid creating multiple pairs)
    """
    pairs_by_cp, multiplicities, loops_by_cell = _pairs_by_cellpair(pairing)
    cell = pairing.cell_of_point
    existing_cp = set(multiplicities.keys())

    # Candidate loops: pair indices that are loops and their cell has exactly 1 loop
    loop_indices = [
        i
        for i, (p, q) in enumerate(pairing.pairs)
        if cell[p] == cell[q] and loops_by_cell[cell[p]] == 1
    ]

    # Candidate non-loop edges with multiplicity 1
    unique_edge_indices: list[int] = []
    for idx, (p, q) in enumerate(pairing.pairs):
        u, v = cell[p], cell[q]
        if u == v:
            continue
        key = (u, v) if u <= v else (v, u)
        if multiplicities.get(key, 0) == 1:
            unique_edge_indices.append(idx)
    if debug:
        print(
            f"[l-switch] Search: loops={len(loop_indices)}, "
            f"unique_edges={len(unique_edge_indices)}, max_trials=2000"
        )
    if not loop_indices or len(unique_edge_indices) < 2:
        if debug:
            print("[l-switch] No candidates available")
        return None

    rng.shuffle(loop_indices)
    rng.shuffle(unique_edge_indices)

    # Try a bounded number of random combinations
    max_trials = 2000
    for t in range(max_trials):
        if t and debug and t % 200 == 0:
            print(f"[l-switch] Trials={t}")
        if not loop_indices or len(unique_edge_indices) < 2:
            break
        L = rng.choice(loop_indices)
        a, b = pairing.pairs[L]
        X = cell[a]  # same as cell[b]

        e1_idx, e2_idx = rng.sample(unique_edge_indices, 2)
        c, d = pairing.pairs[e1_idx]
        e, f = pairing.pairs[e2_idx]
        Y, Z = cell[c], cell[d]
        U, V = cell[e], cell[f]

        # Distinctness constraints
        if len({X, Y, Z, U, V}) != 5:
            continue
        # Created cell-pairs must not exist yet

        def key_(u: int, v: int) -> tuple[int, int]:
            return (u, v) if u <= v else (v, u)

        if key_(X, Y) in existing_cp:
            continue
        if key_(X, U) in existing_cp:
            continue
        if key_(Z, V) in existing_cp:
            continue

        if debug:
            print(f"[l-switch] Found: L={L}, E1={e1_idx}, E2={e2_idx}")
        return (L, e1_idx, e2_idx)

    if debug:
        print("[l-switch] Search exhausted without success")
    return None


def _apply_d_switching(
    pairing: PairingResult, ab_idx: int, cd_idx: int, debug: bool = False
) -> PairingResult:
    """
    Apply a forward d-switching variant that reduces one double pair between cells A and B by 1:
      - Remove pair (a,b) between A,B and pair (c,d) between C,D with C,D not in {A,B}.
      - Add (a,d) and (c,b). This preserves degrees and eliminates one A-B edge.
    Preconditions must be validated by caller.
    """
    a, b = pairing.pairs[ab_idx]
    c, d = pairing.pairs[cd_idx]
    if debug:
        ca = pairing.cell_of_point[a]
        cb = pairing.cell_of_point[b]
        cc = pairing.cell_of_point[c]
        cd_cell = pairing.cell_of_point[d]
        print(
            f"[d-switch] Apply: ab_idx={ab_idx} cells=({ca},{cb}), "
            f"cd_idx={cd_idx} cells=({cc},{cd_cell})"
        )

    new_mate = pairing.mate.copy()

    # Re-pair the four endpoints
    new_mate[a] = d
    new_mate[d] = a

    new_mate[c] = b
    new_mate[b] = c

    new_pairs = _rebuild_pairs_from_mate(new_mate)
    if debug:
        print("[d-switch] Complete: updated 2 pairs")
    return PairingResult(
        pairs=new_pairs, cell_of_point=pairing.cell_of_point, mate=new_mate
    )


def _find_random_d_switching_candidate(
    pairing: PairingResult, rng: Random, debug: bool = False
) -> tuple[int, int] | None:
    """
    Find a random valid forward d-switching candidate (ab_idx, cd_idx).
    Constraints:
      - Choose a cell-pair (A,B) with multiplicity >= 2; pick one AB pair index as ab_idx.
      - Choose a non-loop pair (c,d) with multiplicity exactly 1 and cells C,D not in {A,B}.
      - The created pairs (A,D) and (C,B) must not already exist (to avoid creating multiple
        pairs).
      - No loops are created.
      - Destroyed/created pairs (except the AB chosen from a double) are not part of multiple
        pairs.
    """
    pairs_by_cp, multiplicities, loops_by_cell = _pairs_by_cellpair(pairing)
    cell = pairing.cell_of_point
    existing_cp = set(multiplicities.keys())

    # Find any double (or more) cell-pair
    double_keys = [
        cp for cp, mult in multiplicities.items() if cp[0] != cp[1] and mult >= 2
    ]

    # Non-loop unique edges (multiplicity == 1)
    unique_edge_indices: list[int] = []
    for idx, (p, q) in enumerate(pairing.pairs):
        u, v = cell[p], cell[q]
        if u == v:
            continue
        key = (u, v) if u <= v else (v, u)
        if multiplicities.get(key, 0) == 1:
            unique_edge_indices.append(idx)

    if debug:
        doubles_ct = sum(1 for cp in double_keys)
        print(
            f"[d-switch] Search: doubles={doubles_ct}, "
            f"unique_edges={len(unique_edge_indices)}, max_trials=4000"
        )

    if not double_keys or not unique_edge_indices:
        if debug:
            print("[d-switch] No candidates available")
        return None

    rng.shuffle(double_keys)
    rng.shuffle(unique_edge_indices)

    max_trials = 4000
    for t in range(max_trials):
        if t and debug and t % 250 == 0:
            print(f"[d-switch] Trials={t}")
        if not double_keys or not unique_edge_indices:
            break
        A, B = rng.choice(double_keys)
        ab_list = pairs_by_cp.get((A, B), [])
        if len(ab_list) < 2:
            continue
        ab_idx = rng.choice(ab_list)
        a, b = pairing.pairs[ab_idx]
        # Ensure orientation: a in A, b in B
        if not ((cell[a] == A and cell[b] == B) or (cell[a] == B and cell[b] == A)):
            if cell[a] == B and cell[b] == A:
                a, b = b, a  # swap to make (a in A, b in B)
            else:
                continue

        # Pick a unique non-loop pair cd away from A,B
        cd_idx = rng.choice(unique_edge_indices)
        c, d = pairing.pairs[cd_idx]
        C, D = cell[c], cell[d]
        if C in (A, B) or D in (A, B):
            continue
        if C == D:
            continue

        # Created pairs: (a,d): (A,D), (c,b): (C,B)

        def key_(u: int, v: int) -> tuple[int, int]:
            return (u, v) if u <= v else (v, u)

        if key_(A, D) in existing_cp:
            continue
        if key_(C, B) in existing_cp:
            continue

        if debug:
            print(
                f"[d-switch] Found: ab_idx={ab_idx} (A,B)=({A},{B}), "
                f"cd_idx={cd_idx} (C,D)=({C},{D})"
            )
        return (ab_idx, cd_idx)

    if debug:
        print("[d-switch] Search exhausted without success")
    return None


def no_loops(
    pairing: PairingResult,
    *,
    rng: Random | None = None,
    max_restarts: int = 500,
    debug: bool = False,
) -> PairingResult:
    """
    NOLOOPS(P): repeatedly apply forward l-switchings until no loops remain.
    If at some iteration no valid switching is found, restart from a fresh random pairing
    with the same degree sequence. Always accepts a valid switching.
    """
    local_rng = rng if isinstance(rng, Random) else Random(rng)
    degrees = _degrees_from_cell_of_point(pairing.cell_of_point)

    restarts = 0
    while True:
        _, _, loops_by_cell = _pairs_by_cellpair(pairing)
        total_loops = sum(loops_by_cell)
        if debug:
            print(f"[NOLOOPS] Loops remaining={total_loops}")
        if total_loops == 0:
            if debug:
                print("[NOLOOPS] Done, no loops")
            return pairing

        cand = _find_random_l_switching_candidate(pairing, local_rng, debug=debug)
        if cand is None:
            # Restart
            restarts += 1
            if debug:
                print(f"[NOLOOPS] Restart #{restarts}")
            if restarts > max_restarts:
                raise RuntimeError(
                    "NOLOOPS: too many restarts; failed to eliminate loops."
                )
            pairing = mckay_wormald_random_pairing(
                degrees, seed=local_rng, debug=debug
            )
            continue

        L, e1, e2 = cand
        new_pairing = _apply_l_switching(pairing, L, e1, e2, debug=debug)

        # Always accept in this practical implementation
        pairing = new_pairing


def no_doubles(
    pairing: PairingResult,
    *,
    rng: Random | None = None,
    max_restarts: int = 500,
    debug: bool = False,
) -> PairingResult:
    """
    NODOUBLES(P): repeatedly apply forward d-switchings until no double pairs remain.
    If at some iteration no valid switching is found, restart from a fresh random pairing
    with the same degree sequence. Always accepts a valid switching.
    """
    local_rng = rng if isinstance(rng, Random) else Random(rng)
    degrees = _degrees_from_cell_of_point(pairing.cell_of_point)

    restarts = 0
    while True:
        _, multiplicities, _ = _pairs_by_cellpair(pairing)
        doubles_ct = sum(
            1 for cp, mult in multiplicities.items() if cp[0] != cp[1] and mult >= 2
        )
        if debug:
            print(f"[NODOUBLES] Double cell-pairs remaining={doubles_ct}")
        if doubles_ct == 0:
            if debug:
                print("[NODOUBLES] Done, no doubles")
            return pairing

        cand = _find_random_d_switching_candidate(pairing, local_rng, debug=debug)
        if cand is None:
            # Restart
            restarts += 1
            if debug:
                print(f"[NODOUBLES] Restart #{restarts}")
            if restarts > max_restarts:
                raise RuntimeError(
                    "NODOUBLES: too many restarts; failed to eliminate double pairs."
                )
            pairing = mckay_wormald_random_pairing(degrees, seed=local_rng, debug=debug)
            pairing = no_loops(
                pairing, rng=local_rng, max_restarts=max_restarts, debug=debug
            )  # eliminate loops first
            continue

        ab_idx, cd_idx = cand
        pairing = _apply_d_switching(pairing, ab_idx, cd_idx, debug=debug)


def deg_generate_pairing(
    degrees: list[int],
    seed: int | Random | None = None,
    *,
    max_restarts: int = 10000,
    debug: bool = False,
) -> PairingResult:
    """
    DEG: Sample a random pairing with the given degrees, then eliminate loops and double pairs
    using NOLOOPS and NODOUBLES. Restarts from scratch if initial or intermediate constraints
    cannot be satisfied within reasonable attempts.
    """
    rng = seed if isinstance(seed, Random) else Random(seed)

    for attempt in range(1, max_restarts + 1):
        if debug:
            print(f"[DEG] Attempt {attempt}")
        # Initial random pairing
        P = mckay_wormald_random_pairing(degrees, seed=rng, debug=debug)

        # Basic initial checks (reject blatantly invalid states)
        try:
            P = no_loops(P, rng=rng, max_restarts=2000, debug=debug)
            P = no_doubles(P, rng=rng, max_restarts=2000, debug=debug)
            # Success
            if debug:
                print("[DEG] Success")
            return P
        except RuntimeError as e:
            if debug:
                print(f"[DEG] Restart due to: {e}")
            continue

    raise RuntimeError(
        "DEG: failed to generate a simple pairing within restart budget."
    )


def mckay_wormald_simple_graph(
    degrees: list[int], seed: int | Random | None = None, debug: bool = False
) -> nx.Graph:
    """
    Convenience: Generate a simple graph with the given degree sequence via the
    McKay–Wormald pairing model and switchings.
    """
    if debug:
        print(
            f"[simple_graph] Target degrees: n={len(degrees)}, sum={sum(degrees)}"
        )
    pairing = deg_generate_pairing(degrees, seed=seed, debug=debug)
    n = len(degrees)
    G: nx.Graph = nx.Graph()
    G.add_nodes_from(range(n))
    for p, q in pairing.pairs:
        u = pairing.cell_of_point[p]
        v = pairing.cell_of_point[q]
        if u == v:
            raise RuntimeError("Loops detected.")   # should not happen after NOLOOPS
        if G.has_edge(u, v):
            raise RuntimeError("Doubles detected.")  # should not happen after NODOUBLES
        G.add_edge(u, v)
    if debug:
        print(f"[simple_graph] Built: edges={G.number_of_edges()}")
    return G


def mckay_wormald_simple_graph_from_graph(
    G: nx.Graph, seed: int | Random | None = None, debug: bool = False
) -> nx.Graph:
    """
    Convenience: Given a graph, generate a simple random graph with the same degree
    sequence using the McKay–Wormald switching approach.
    """
    degs = degree_sequence(G, sort=False)
    if debug:
        print(
            f"[simple_from_graph] Input graph: n={G.number_of_nodes()}, "
            f"m={G.number_of_edges()}"
        )
    return mckay_wormald_simple_graph(degs, seed=seed, debug=debug)
