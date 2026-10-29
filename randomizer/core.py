"""Simple, permuted-block and stratified block randomization with a recorded seed."""
import itertools
import random
from collections import Counter


def _arms(arms, ratio):
    ratio = list(ratio or [1] * len(arms))
    if len(ratio) != len(arms):
        raise ValueError("ratio must have one entry per arm")
    return [a for a, r in zip(arms, ratio) for _ in range(int(r))]


def simple(n, arms=("A", "B"), seed=None, ratio=None):
    """Independent allocation for each unit (coin flipping); can be unbalanced in small samples."""
    rng = random.Random(seed)
    pool = _arms(arms, ratio)
    return [rng.choice(pool) for _ in range(n)]


def permuted_blocks(n, arms=("A", "B"), block_sizes=(4,), seed=None, ratio=None, rng=None):
    """Permuted block randomization; block size chosen at random from block_sizes for each block
    (random block sizes make the sequence harder to predict). Returns list of (arm, block_no, block_size)."""
    rng = rng or random.Random(seed)
    unit = _arms(arms, ratio)
    for b in block_sizes:
        if b % len(unit):
            raise ValueError("block size %d is not a multiple of %d (sum of ratio)" % (b, len(unit)))
    out, block = [], 0
    while len(out) < n:
        block += 1
        size = rng.choice(list(block_sizes))
        seq = unit * (size // len(unit))
        rng.shuffle(seq)
        out += [(a, block, size) for a in seq]
    return out[:n]


def stratified(units, strata_keys, arms=("A", "B"), block_sizes=(4,), seed=None, ratio=None):
    """Block randomization within each stratum. units: list of dicts with an 'id' and stratum fields.

    Each stratum gets its own independent stream derived from the master seed, so adding a stratum
    never changes allocations in the others."""
    master = random.Random(seed)
    stream_seeds = {}
    seqs, pos = {}, Counter()
    out = []
    for u in units:
        s = tuple(str(u.get(k, "")) for k in strata_keys)
        if s not in seqs:
            stream_seeds[s] = "%s|%s" % (seed, "|".join(s)) if seed is not None else master.random()
            seqs[s] = permuted_blocks(10 ** 4, arms, block_sizes, ratio=ratio, rng=random.Random(stream_seeds[s]))
        arm, block, size = seqs[s][pos[s]]
        pos[s] += 1
        out.append(dict(u, arm=arm, stratum="/".join(s), block=block))
    return out


def balance_report(allocs, by=None):
    """Counts per arm overall and (optionally) within each value of `by`."""
    arms = Counter(a["arm"] if isinstance(a, dict) else a for a in allocs)
    rep = {"overall": dict(sorted(arms.items()))}
    if by:
        groups = {}
        for a in allocs:
            groups.setdefault(a[by], Counter())[a["arm"]] += 1
        rep["by_" + by] = {g: dict(sorted(c.items())) for g, c in sorted(groups.items())}
    return rep


def sequence_table(allocs, start=1, prefix="R"):
    """Numbered allocation list for envelopes / IWRS: (sequence id, arm, block)."""
    return [("%s%03d" % (prefix, i), a[0] if isinstance(a, tuple) else a, a[1] if isinstance(a, tuple) else "")
            for i, a in enumerate(allocs, start)]
