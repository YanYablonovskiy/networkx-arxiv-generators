import networkx as nx
import matplotlib.pyplot as plt
from nx_arxivgen.generators.mckay_wormald import mckay_wormald_simple_graph
from nx_arxivgen.generators.mckay_wormald import mckay_random_graph_encoding #type: ignore
test_deg_seq = [1, 1, 2, 3, 3, 2, 6, 6,7,8,6,1,2,3,4,5,6,7,8,9,10]

test : nx.Graph = mckay_wormald_simple_graph(test_deg_seq, debug=True)
nx.draw_spring(test, with_labels=True)
plt.show()

sample_graph = nx.generators.binomial_graph(20, 0.5)

sample_graph = nx.generators.binomial_graph(20, 0.5)

print(mckay_random_graph_encoding(sample_graph))