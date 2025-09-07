import networkx as nx
from dataclasses import dataclass
from random import Random

def degree_sequence(
    G: nx.Graph,
    *,
    sort: bool = False,
    reverse: bool = True,
) -> list[int]: ...

@dataclass(frozen=True)
class PairingResult:
    pairs: list[tuple[int, int]]
    cell_of_point: list[int]
    mate: list[int]

def mckay_wormald_random_pairing(
    degrees: list[int],
    seed: int | Random | None = None,
    debug: bool = False,
) -> PairingResult: ...

def mckay_random_graph_encoding(
    G: nx.Graph,
    seed: int | Random | None = None,
) -> PairingResult: ...

def mckay_wormald_multigraph(
    degrees: list[int],
    seed: int | Random | None = None,
    debug: bool = False,
) -> nx.MultiGraph: ...

def pairing_summary(
    pairing: PairingResult,
    n: int,
) -> dict[
    str,
    int | dict[tuple[int, int], int],
]: ...

def mate_of(
    point: int,
    pairing: PairingResult,
) -> int: ...

def no_loops(
    pairing: PairingResult,
    *,
    rng: Random | None = None,
    max_restarts: int = 500,
    debug: bool = False,
) -> PairingResult: ...

def no_doubles(
    pairing: PairingResult,
    *,
    rng: Random | None = None,
    max_restarts: int = 500,
    debug: bool = False,
) -> PairingResult: ...

def deg_generate_pairing(
    degrees: list[int],
    seed: int | Random | None = None,
    *,
    max_restarts: int = 10000,
    debug: bool = False,
) -> PairingResult: ...

def mckay_wormald_simple_graph(
    degrees: list[int],
    seed: int | Random | None = None,
    debug: bool = False,
) -> nx.Graph: ...

def mckay_wormald_simple_graph_from_graph(
    G: nx.Graph,
    seed: int | Random | None = None,
    debug: bool = False,
) -> nx.Graph: ...
