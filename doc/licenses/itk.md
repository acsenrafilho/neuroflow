# ITK / CSIM Toolkits license notice

[ITK](https://itk.org/) (Insight Toolkit) and the [CSIM ITK repository](https://github.com/CSIM-Toolkits/ITK) are distributed under their own license terms. Review the ITK and CSIM project licenses before using these tools in production.

NeuroFlow does not bundle ITK or CSIM binaries. Native ITK modules require locally compiled executables configured in `config/itk-binaries.json` (see `config/itk-binaries.example.json`).

## Simple Filters (3D Slicer worker)

The **Simple Filters** entry under the ITK package uses **3D Slicer** on the host. Simple Filters is a **built-in** Slicer module (Filtering → Simple Filters), not a separate extension. Slicer is subject to its own license; see [doc/licenses/slicer.md](slicer.md).

Official documentation:

- CSIM ITK: https://github.com/CSIM-Toolkits/ITK/tree/master
- Simple Filters: https://slicer.readthedocs.io/en/latest/user_guide/modules/simplefilters.html#simple-filters
