# Security policy

## Supported versions

NeuroFlow is under active development (`0.1.x`). Security fixes are applied on
the default branch (`main`).

## Reporting a vulnerability

**Do not open a public GitHub issue** for security problems (remote code
execution, authentication bypass, data exposure, and similar).

Please report privately using
[GitHub Security Advisories](https://github.com/acsenrafilho/neuroflow/security/advisories/new).

You should receive an acknowledgement when the report is triaged. This is a
personal project with a single maintainer; response time may vary.

## Deployment posture

The default configuration has **no authentication**. The API is intended for
**local development** or a trusted lab network only.

Do not expose an unauthenticated NeuroFlow instance to the public internet.

Neuroimaging data may contain PHI or identifiable research participants. Do not
attach real subject identifiers, clinical images, or production logs to issues
or pull requests.

See [docs/security.md](docs/security.md) for subprocess allowlisting, logging
guidance, and planned hardening.
