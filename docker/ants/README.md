# ANTs processing module

NeuroFlow runs ANTs in a **dedicated container** with the BIDS dataset mounted read-only.

## Bootstrap stub

The committed `Dockerfile` is a **lightweight stub**. For production, use the official [`antsx/ants`](https://hub.docker.com/r/antsx/ants) image (see ANTs license).

## Contract

| Variable | Description |
|----------|-------------|
| `BIDS_ROOT` | Host path mounted at `/data/bids` |
| `SUBJECT` | BIDS subject label (without `sub-`) |
| `SESSION` | Optional session label |
| `PIPELINE_CONFIG_JSON` | Small JSON config |

## Inputs / outputs

- **Inputs:** BIDS data under `/data/bids`
- **Outputs:** `/data/bids/derivatives/neuroflow-ants/`

## Example

```bash
export NEUROFLOW_BIDS_ROOT=./data/sample
docker compose build ants
docker compose run --rm ants
```

See [doc/licenses/ants.md](../../doc/licenses/ants.md).
