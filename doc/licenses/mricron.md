# MRIcron / dcm2niix license notice

[MRIcron](https://www.nitrc.org/projects/mricron) is Chris Rorden's NIfTI viewer. The DICOM to
NIfTI converter NeuroFlow launches is
[dcm2niix](https://github.com/rordenlab/dcm2niix), distributed under the
[BSD-2-Clause](https://github.com/rordenlab/dcm2niix/blob/master/license.txt) license.

NeuroFlow does not bundle the `dcm2niix` binary. Install it on the host (package manager, conda,
or a release next to MRIcron), then ensure it is on `PATH`, under `~/mricron/dcm2niix` or
`~/MRIcron/dcm2niix`, or set `NEUROFLOW_DCM2NIIX` to the absolute path of the executable.
