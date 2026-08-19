# Data and privacy

Neuroimaging data may contain PHI or identifiable research participants. Treat every job folder as sensitive.

## Local-only MVP

The bootstrap configuration has **no authentication**. The API is intended for local development or trusted lab networks only. Do not expose an unauthenticated NeuroFlow instance to the public internet.

## Practical habits

- Prefer coded subject IDs (for example `sub-001`) over real names in paths and forms.
- Keep `.env` out of version control; start from `.env.example`.
- Restrict filesystem permissions on `NEUROFLOW_DATA_ROOT` and the datasets root.
- Assume logs and job metadata may contain paths or parameters—handle retention accordingly.

## Subprocess safety

Only allowlisted executables may be started. Arguments are built server-side from validated form fields—never pasted as raw shell strings from the browser.

Operators and developers: see [Security](../security.md) for posture and future hardening ideas.
