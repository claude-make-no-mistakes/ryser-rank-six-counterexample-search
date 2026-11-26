# Rank-six intersecting Ryser

Every finite intersecting six-partite, six-uniform hypergraph with cover number six has at least **23 edges**. The preceding public computation gave a lower bound of 22. The 22-edge case falls to a bound on the number of edges left after deleting two vertex stars, an integer enumeration of side degrees, and a congruence for repeated intersections. [Paper](paper.pdf) · [Proof source](paper.tex) · [Replay record](REPLAY.txt)

The lower bound also excludes a construction based on merging whole parallel line traces and splitting the other traces in the affine plane of order five.

The 23-edge search remains open. The degree and residual-star filters leave 313 profile systems, all with maximum degree eight, for a hypothetical counterexample at 23 edges. Initial and strengthened searches hit their conflict limits. These runs establish no SAT exclusions.

## Proof replay

Python 3.10 or later suffices, using only the standard library.

```sh
python replay.py
python transport.py 22
```

The first command computes lower bounds on repeated intersections by enumerating bounded integer tuples. The second independently computes minimum transportation collision costs using integer flow. Both close the 22-edge case. The residual check also has an alternative derivation in `residual.py`. The mathematical inputs are the 13-edge minimum for cover number five and the eight-edge structure for cover number four. [Aharoni, Barát, and Wanless, Theorem 2.7](https://arxiv.org/html/1409.4833v2#S2) · [Abu-Khazneh and Pokrovskiy, Lemma 2.1](https://arxiv.org/pdf/1409.4938#page=5) · [Previous 22-edge bound](https://github.com/HRK44/ryser-conjecture-22)

## Counterexample search

```sh
python frontier.py 23 --output frontier-23.json
python sat_search.py frontier-23.json 0 --conflicts 35000 --rounds 8 --output witness.json
python witness.py witness.json
```

The SAT script requires `python-sat==1.9.dev25` with CaDiCaL 1.9.5. Its inputs are a list of degree systems and a zero-based index. It searches for distinct intersecting rows and rules out any cover of size at most five that it finds. The witness script independently checks the rows and searches for an exact cover of size at most five. One edge always gives a cover of size six. The SAT script creates a witness file only when the exact check passes.
