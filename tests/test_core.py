import csv
import io
import os
import tempfile
import unittest
from collections import Counter
from contextlib import redirect_stderr

from randomizer.cli import main
from randomizer.core import balance_report, permuted_blocks, simple, stratified


class RandomizationTests(unittest.TestCase):
    def test_reproducible(self):
        self.assertEqual(simple(20, seed=42), simple(20, seed=42))
        self.assertEqual(permuted_blocks(20, seed="trial-1"), permuted_blocks(20, seed="trial-1"))
        self.assertNotEqual(permuted_blocks(40, seed=1), permuted_blocks(40, seed=2))

    def test_blocks_are_balanced(self):
        allocs = permuted_blocks(60, ("A", "B", "C"), block_sizes=(3, 6), seed=7)
        by_block = {}
        for arm, block, size in allocs:
            by_block.setdefault(block, []).append(arm)
        for block, arms in list(by_block.items())[:-1]:
            c = Counter(arms)
            self.assertEqual(len(set(c.values())), 1, "block %d unbalanced: %s" % (block, c))
        self.assertLessEqual(abs(Counter(a for a, _, _ in allocs)["A"] - 20), 3)

    def test_ratio(self):
        c = Counter(a for a, _, _ in permuted_blocks(30, ("T", "C"), (3, 6), seed=3, ratio=(2, 1)))
        self.assertEqual((c["T"], c["C"]), (20, 10))
        with self.assertRaises(ValueError):
            permuted_blocks(10, ("T", "C"), (4,), ratio=(2, 1))

    def test_stratified_independent_streams(self):
        units = [{"id": str(i), "site": "N" if i % 2 else "S", "sex": "F"} for i in range(16)]
        a = stratified(units, ["site", "sex"], seed=99)
        more = units + [{"id": "x", "site": "E", "sex": "M"}]
        b = stratified(more, ["site", "sex"], seed=99)
        self.assertEqual([u["arm"] for u in a], [u["arm"] for u in b[:16]])
        rep = balance_report(a, by="stratum")
        self.assertEqual(rep["by_stratum"]["N/F"], {"A": 4, "B": 4})

    def test_cli_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "list.csv")
            with redirect_stderr(io.StringIO()) as err:
                main(["--seed", "abc", "--arms", "drug,placebo", "blocks", "8", "-o", out])
            self.assertIn("seed: abc", err.getvalue())
            with open(out, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
            self.assertTrue(lines[0].startswith("# randomizer seed=abc"))
            rows = list(csv.reader(lines[2:]))
            self.assertEqual(Counter(r[1] for r in rows), {"drug": 4, "placebo": 4})


if __name__ == "__main__":
    unittest.main()
