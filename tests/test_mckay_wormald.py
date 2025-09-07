import networkx as nx
import matplotlib.pyplot as plt
from nx_arxivgen.generators.mckay_wormald import mckay_wormald_simple_graph
from nx_arxivgen.generators.mckay_wormald import mckay_wormald_simple_graph_from_graph
import random
from nx_arxivgen.generators.mckay_wormald import mckay_random_graph_encoding  # type: ignore


def random_int_list_with_even_sum(
    n: int, low: int = 0, high: int = 10, seed: int | None = None
) -> list[int]:
    """
    Generate a list of n integers in [low, high] whose total sum is even.
    """
    if n <= 0:
        return []
    if low > high:
        raise ValueError("low must be <= high")

    rng = random.Random(seed)
    vals = [rng.randint(low, high) for _ in range(n)]
    if (sum(vals) & 1) == 1:
        # Flip parity while staying within bounds if possible
        if vals[-1] < high:
            vals[-1] += 1
        elif vals[-1] > low:
            vals[-1] -= 1
        else:
            # low == high and sum is odd -> impossible to adjust within bounds
            raise ValueError("Cannot produce even sum with fixed value bounds when n*low is odd.")
    return vals


def test() -> None:
    test_deg_seq = [1, 1, 2, 3, 3, 2, 6, 6, 7, 8, 6, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    test: nx.Graph = mckay_wormald_simple_graph(test_deg_seq, debug=True)
    nx.draw_random(test, with_labels=True)
    plt.show()

    test_deg_seq_rand = random_int_list_with_even_sum(30, 0, 10, seed=42)

    test_rand: nx.Graph = mckay_wormald_simple_graph(test_deg_seq_rand, debug=True)
    print(test_rand)
    nx.draw(test_rand, with_labels=True, pos=nx.kamada_kawai_layout(test_rand))
    plt.show()

    sample_graph = nx.generators.binomial_graph(20, 0.5)

    sample_graph = nx.generators.binomial_graph(20, 0.5)

    print(mckay_wormald_simple_graph_from_graph(sample_graph))

    print(mckay_random_graph_encoding(sample_graph))


test()
