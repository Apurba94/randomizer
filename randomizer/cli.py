"""Command-line interface for randomizer."""
import argparse
import csv
import datetime
import json
import secrets
import sys

from .core import balance_report, permuted_blocks, sequence_table, simple, stratified


def main(argv=None):
    ap = argparse.ArgumentParser(prog="randomizer", description="Reproducible randomization lists.")
    ap.add_argument("--arms", default="A,B", help="comma-separated arm names")
    ap.add_argument("--ratio", help="allocation ratio, e.g. 2,1")
    ap.add_argument("--seed", help="seed (recorded in the output); random if omitted")
    out = argparse.ArgumentParser(add_help=False)
    out.add_argument("-o", "--output", help="CSV output file (default stdout)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("simple", parents=[out])
    s.add_argument("n", type=int)
    b = sub.add_parser("blocks", parents=[out])
    b.add_argument("n", type=int)
    b.add_argument("--blocks", default="4", help="block sizes, e.g. 4,6")
    st = sub.add_parser("stratified", parents=[out], help="allocate units from a CSV within strata")
    st.add_argument("csvfile")
    st.add_argument("--strata", required=True, help="comma-separated stratum columns")
    st.add_argument("--blocks", default="4")
    args = ap.parse_args(argv)

    seed = args.seed or secrets.token_hex(4)
    arms = [a.strip() for a in args.arms.split(",")]
    ratio = [int(x) for x in args.ratio.split(",")] if args.ratio else None
    fh = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout
    w = csv.writer(fh)
    meta = "# randomizer seed=%s arms=%s ratio=%s method=%s generated=%s" % (
        seed, ",".join(arms), args.ratio or "1:1", args.cmd, datetime.datetime.now().isoformat(timespec="seconds"))
    fh.write(meta + "\n")
    if args.cmd == "simple":
        allocs = simple(args.n, arms, seed, ratio)
        w.writerow(["sequence", "arm"])
        w.writerows((sid, arm) for sid, arm, _ in sequence_table(allocs))
        rep = balance_report(allocs)
    elif args.cmd == "blocks":
        allocs = permuted_blocks(args.n, arms, [int(x) for x in args.blocks.split(",")], seed, ratio)
        w.writerow(["sequence", "arm", "block"])
        w.writerows(sequence_table(allocs))
        rep = balance_report([a for a, _, _ in allocs])
    else:
        with open(args.csvfile, encoding="utf-8-sig", newline="") as cf:
            r = csv.DictReader(cf)
            units, fields = list(r), r.fieldnames
        keys = [k.strip() for k in args.strata.split(",")]
        allocs = stratified(units, keys, arms, [int(x) for x in args.blocks.split(",")], seed, ratio)
        w.writerow(fields + ["arm", "stratum", "block"])
        w.writerows([a[f] for f in fields] + [a["arm"], a["stratum"], a["block"]] for a in allocs)
        rep = balance_report(allocs, by="stratum")
    if args.output:
        fh.close()
    print(json.dumps(rep, indent=1), file=sys.stderr)
    print("seed: %s (keep it to reproduce this list)" % seed, file=sys.stderr)
    return 0
