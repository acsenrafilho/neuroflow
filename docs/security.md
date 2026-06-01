# Security

## MVP posture

The bootstrap configuration has **no authentication**. The API is intended for **local development** or trusted lab networks only.

Do not expose an unauthenticated NeuroFlow instance to the public internet.

## Sensitive data

Neuroimaging datasets may contain **PHI** or identifiable research participants.

- Do not log file paths that include participant identifiers in production.
- Use least-privilege filesystem access for `NEUROFLOW_DATA_ROOT`.
- Keep `.env` out of version control (see `.env.example`).

## Subprocess execution

- Only **allowlisted** executables may be started (`recon-all` today).
- Never pass unsanitized user input into a shell; build `argv` lists in Python.
- Validate upload extensions and size limits before writing to disk.

## Future work

- API keys or OAuth2 for multi-user deployments
- Audit logging for tool runs
- Encryption at rest for archived job data
