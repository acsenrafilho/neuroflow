# Security

## MVP posture

The bootstrap configuration has **no authentication**. The API is intended for **local development** or trusted lab networks only.

Do not expose an unauthenticated NeuroFlow instance to the public internet.

## Sensitive data

Neuroimaging datasets may contain **PHI** or identifiable research participants.

- Do not log file paths that include participant identifiers in production.
- Use least-privilege filesystem access for `NEUROFLOW_BIDS_ROOT`.
- Keep `.env` out of version control (see `.env.example`).

## Docker

- Mount BIDS data **read-only** where possible.
- Pin image digests for production pipelines.
- Document third-party licenses (FSL, ANTs) before deploying official tool images.

## Future work

- API keys or OAuth2 for multi-user deployments
- Audit logging for pipeline runs
- Encryption at rest for archived datasets
