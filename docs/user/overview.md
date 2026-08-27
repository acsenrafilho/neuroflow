# Overview

NeuroFlow is a **facilitation portal** for neuroscience medical image processing. It gives you **one web page per CLI tool**: upload data, set parameters, preview the command, run the job on the local host, and follow the log.

It sits between your browser and neuroimaging software already installed on the machine (FreeSurfer, FSL, Spinal Cord Toolbox). The portal does not replace those packages and does not ship them in this repository.

## Objectives

- Make it easier to **configure and launch a single neuroimaging program** at a time, with a clear subject ID, job status, and CLI preview.
- Keep researcher data **on the host** under a subject-centered folder layout inspired by BIDS.
- Run only **allowlisted** executables, with arguments built from validated form fields rather than pasted shell strings.
- Stay small: no multi-tool pipeline composer, no database, and no Docker requirement in this repository.

## Who it is for

Researchers and lab operators who install vendor CLIs on Ubuntu/Debian (or **WSL2 Ubuntu on Windows**) and want a local web UI instead of assembling every command by hand.

## What NeuroFlow does not do

- It does **not** install FreeSurfer, FSL, SCT, or other packages.
- It does **not** chain stages into an automatic pipeline (for example TOPUP then EDDY). Run each stage as its own job.
- It does **not** authenticate users in the current MVP. Use localhost or a trusted lab network only.
- It does **not** expose ANTs, 3D Slicer, or ITK in the portal UI yet (code may exist; treat them as coming later).

## Where to read this guide

- **This site:** [Installation](installation.md) through [FAQ](faq.md), including [T1 cervical morphometry](sct-t1-morphometry.md).
- **In the running app:** [http://127.0.0.1:8000/help/](http://127.0.0.1:8000/help/) when the frontend is served.
- **OpenAPI (integrators):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
