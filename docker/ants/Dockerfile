# ANTs processing module (bootstrap stub).
# Replace base image with antsx/ants for real processing.
# License: see README.md and doc/licenses/ants.md
FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

LABEL org.opencontainers.image.title="neuroflow-ants"
LABEL org.opencontainers.image.description="ANTs stub module for BIDS-mounted pipelines"

ENV BIDS_ROOT=/data/bids
ENV SUBJECT=""
ENV SESSION=""
ENV PIPELINE_CONFIG_JSON="{}"

WORKDIR /pipeline

COPY entrypoint.sh /pipeline/entrypoint.sh
RUN chmod +x /pipeline/entrypoint.sh

ENTRYPOINT ["/pipeline/entrypoint.sh"]
