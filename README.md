# randomizer

**Generate reproducible, auditable randomization lists for experiments and clinical trials:
simple, permuted blocks (with random block sizes), unequal ratios and stratified allocation.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Proper randomization and allocation concealment protect against selection bias, and CONSORT and
ARRIVE require reporting how the sequence was generated. "We used Excel's RAND()" is neither
reproducible nor auditable. With a recorded seed, anyone can regenerate the exact list, and
balanced blocks keep groups comparable even if recruitment stops early.

## Features

- `simple`: independent allocation (any number of arms, ratios)
- `blocks`: permuted blocks with randomly varying block sizes (e.g. 4 and 6) to hinder prediction
- `stratified`: block randomization within strata (site, sex, ...) from a CSV of units; each stratum
  has its own seed-derived stream, so adding a stratum never changes others
- Seed and method recorded in the output header; balance report per arm and stratum
- Numbered sequence IDs for sealed envelopes or web-based allocation

## Usage

```bash
pip install .
randomizer --seed TRIAL2026 --arms drug,placebo blocks 120 --blocks 4,6 -o allocation.csv
randomizer --seed 12345 --arms T,C --ratio 2,1 blocks 90 --blocks 3,6
randomizer --seed pilot --arms A,B,C stratified animals.csv --strata cage,sex -o allocated.csv
```

Keep the list (and seed) away from people who enrol participants to maintain concealment.

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
