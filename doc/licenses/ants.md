# ANTs license notice

[ANTs](https://github.com/ANTsX/ANTs) (Advanced Normalization Tools) is distributed under its own license terms. Review the license in the [ANTsX repository](https://github.com/ANTsX/ANTs) before using release binaries in production.

NeuroFlow does not bundle ANTs binaries. Install precompiled Linux/macOS/Windows builds from the [ANTs releases page](https://github.com/ANTsX/ANTs/releases) or build from source, then add the `bin` directory to `PATH` or set `NEUROFLOW_ANTSPATH` (or host `ANTSPATH`) so the API and job runner can find tools such as `antsRegistration` and `N4BiasFieldCorrection`.

Official usage examples: [ANTs wiki](https://github.com/ANTsX/ANTs/wiki).
