# FSL processing module

NeuroFlow runs FSL tools in a **dedicated container** with the BIDS dataset mounted read-only.

## Bootstrap stub

The committed `Dockerfile` is a **lightweight stub** for local smoke tests (`docker compose run fsl`). For real processing, change the base image to a community build such as `fslcourse/fsl` and accept the [FSL license](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslLicense).

## Contract

| Variable | Description |
|----------|-------------|
| `BIDS_ROOT` | Host path mounted at `/data/bids` |
| `SUBJECT` | BIDS subject label (without `sub-`) |
| `SESSION` | Optional session label |
| `PIPELINE_CONFIG_JSON` | Small JSON config (parameters, steps) |

## Inputs / outputs

- **Inputs:** BIDS raw or preprocessed data under `/data/bids`
- **Outputs:** Write to `/data/bids/derivatives/neuroflow-fsl/` (created by orchestration layer)

## Example

```bash
export NEUROFLOW_BIDS_ROOT=./data/sample
docker compose build fsl
docker compose run --rm fsl
```

See [doc/licenses/fsl.md](../../doc/licenses/fsl.md).
