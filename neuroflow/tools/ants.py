"""ANTs tool parameter mapping and job launcher."""

from __future__ import annotations

import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from neuroflow.config import Settings
from neuroflow.services.datasets import DatasetStore, modality_for_module, normalize_subject_id
from neuroflow.services.job_kill import is_job_cancelled, skip_if_cancelled
from neuroflow.services.jobs import JobStore
from neuroflow.tools.base import build_env, resolve_executable
from neuroflow.tools.fsl import (
    infer_nifti_suffix,
    output_prefix_for_batch,
    strip_nifti_extension,
)
from neuroflow.tools.registry import get_module

ANTS_TOOL_ID = "ants"

VALID_MODULE_IDS = frozenset(
    {
        "ants-n4",
        "ants-registration",
        "ants-apply-transforms",
        "ants-registration-syn",
        "ants-registration-syn-quick",
        "ants-atropos",
        "ants-image-math",
        "ants-sccan",
        "ants-kelly-kapowski",
        "ants-motion-corr",
        "ants-denoise",
        "ants-transform-info",
        "ants-jacobian",
        "ants-cortical-thickness",
        "ants-brain-extraction",
        "ants-template-construction",
        "ants-resample",
        "ants-threshold",
        "ants-smooth",
        "ants-convert",
        "ants-measure-similarity",
        "ants-joint-fusion",
    }
)

ROLE_INPUT = "input"
ROLE_FIXED = "fixed"
ROLE_MOVING = "moving"
ROLE_MASK = "mask"
ROLE_TRANSFORM = "transform"
ROLE_REFERENCE = "reference"
ROLE_TEMPLATE = "template"
ROLE_BRAIN = "brain"
ROLE_PROB_MASK = "prob_mask"
ROLE_ATLAS = "atlas"
ROLE_ATLAS_LABELS = "atlas_labels"
ROLE_COHORT = "cohort"
ROLE_WEIGHT = "weight"
ROLE_TRANSFORM2 = "transform2"
ROLE_TRANSFORM3 = "transform3"
ROLE_GRAY_MATTER = "gray_matter"
ROLE_WHITE_MATTER = "white_matter"
ROLE_INITIAL_TRANSFORM = "initial_transform"
ROLE_FIXED_MASK = "fixed_mask"
ROLE_MOVING_MASK = "moving_mask"

NIFTI_SUFFIXES: tuple[str, ...] = (".nii.gz", ".nii")

IMAGE_MATH_OPERATIONS = frozenset(
    {
        "m",
        "sum",
        "normalize",
        "Grad",
        "Sigma",
        "PadImage",
        "Sharpen",
        "D",
        "M",
        "G",
        "L",
        "MorphologicalGradient",
        "Dilate",
        "Erode",
        "GetLargestComponent",
        "TruncateImageIntensity",
        "ReflectImage",
        "ExtractSlice",
    }
)

MODULE_REQUIRED_ROLES: dict[str, tuple[str, ...]] = {
    "ants-n4": (ROLE_INPUT,),
    "ants-registration": (ROLE_FIXED, ROLE_MOVING),
    "ants-apply-transforms": (ROLE_MOVING, ROLE_REFERENCE, ROLE_TRANSFORM),
    "ants-registration-syn": (ROLE_FIXED, ROLE_MOVING),
    "ants-registration-syn-quick": (ROLE_FIXED, ROLE_MOVING),
    "ants-atropos": (ROLE_INPUT,),
    "ants-image-math": (ROLE_INPUT,),
    "ants-sccan": (ROLE_INPUT,),
    "ants-kelly-kapowski": (ROLE_INPUT,),
    "ants-motion-corr": (ROLE_INPUT,),
    "ants-denoise": (ROLE_INPUT,),
    "ants-transform-info": (ROLE_TRANSFORM,),
    "ants-jacobian": (ROLE_TRANSFORM,),
    "ants-cortical-thickness": (ROLE_INPUT, ROLE_TEMPLATE, ROLE_BRAIN, ROLE_MASK),
    "ants-brain-extraction": (ROLE_INPUT, ROLE_TEMPLATE, ROLE_PROB_MASK),
    "ants-template-construction": (ROLE_INPUT,),
    "ants-resample": (ROLE_INPUT, ROLE_REFERENCE),
    "ants-threshold": (ROLE_INPUT,),
    "ants-smooth": (ROLE_INPUT,),
    "ants-convert": (ROLE_INPUT,),
    "ants-measure-similarity": (ROLE_FIXED, ROLE_MOVING),
    "ants-joint-fusion": (ROLE_INPUT, ROLE_ATLAS, ROLE_ATLAS_LABELS),
}

_MODULE_BATCH_DRIVER: dict[str, str | None] = {
    "ants-n4": ROLE_INPUT,
    "ants-motion-corr": ROLE_INPUT,
    "ants-denoise": ROLE_INPUT,
    "ants-atropos": ROLE_INPUT,
    "ants-image-math": ROLE_INPUT,
    "ants-sccan": ROLE_INPUT,
    "ants-kelly-kapowski": ROLE_INPUT,
    "ants-threshold": ROLE_INPUT,
    "ants-smooth": ROLE_INPUT,
    "ants-convert": ROLE_INPUT,
    "ants-resample": ROLE_INPUT,
}

MODULE_PRIMARY_EXECUTABLE: dict[str, str] = {
    "ants-n4": "N4BiasFieldCorrection",
    "ants-registration": "antsRegistration",
    "ants-apply-transforms": "antsApplyTransforms",
    "ants-registration-syn": "antsRegistrationSyN.sh",
    "ants-registration-syn-quick": "antsRegistrationSyNQuick.sh",
    "ants-atropos": "Atropos",
    "ants-image-math": "ImageMath",
    "ants-sccan": "sccan",
    "ants-kelly-kapowski": "KellyKapowski",
    "ants-motion-corr": "antsMotionCorr",
    "ants-denoise": "DenoiseImage",
    "ants-transform-info": "antsTransformInfo",
    "ants-jacobian": "CreateJacobianDeterminantImage",
    "ants-cortical-thickness": "antsCorticalThickness.sh",
    "ants-brain-extraction": "antsBrainExtraction.sh",
    "ants-template-construction": "antsMultivariateTemplateConstruction2.sh",
    "ants-resample": "ResampleImage",
    "ants-threshold": "ThresholdImage",
    "ants-smooth": "SmoothImage",
    "ants-convert": "ConvertImage",
    "ants-measure-similarity": "MeasureImageSimilarity",
    "ants-joint-fusion": "antsJointFusion",
}


class AntsJobParams(BaseModel):
    module_id: str
    output_prefix: str = Field(default="result", min_length=1, max_length=128)
    parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("module_id")
    @classmethod
    def validate_module_id(cls, value: str) -> str:
        if value not in VALID_MODULE_IDS:
            raise ValueError(f"Unknown ANTs module: {value}")
        return value

    @field_validator("output_prefix")
    @classmethod
    def validate_output_prefix(cls, value: str) -> str:
        cleaned = value.strip()
        stem = strip_nifti_extension(cleaned)
        if not stem or not stem.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Output prefix must contain only letters, numbers, underscores, and hyphens"
            )
        return cleaned


def required_roles(module_id: str) -> tuple[str, ...]:
    return MODULE_REQUIRED_ROLES.get(module_id, ())


def group_uploads_into_batch(
    module_id: str,
    files_by_role: dict[str, list[Path]],
) -> list[dict[str, Path]]:
    needed = required_roles(module_id)
    if not needed:
        raise ValueError(f"Unknown module: {module_id}")

    if module_id == "ants-template-construction":
        paths = files_by_role.get(ROLE_INPUT, [])
        if not paths:
            raise ValueError("At least one cohort image is required")
        return [{ROLE_COHORT: paths}]

    missing = [role for role in needed if not files_by_role.get(role)]
    if missing:
        raise ValueError(f"Missing required file role(s): {', '.join(missing)}")

    driver = _MODULE_BATCH_DRIVER.get(module_id)
    if driver is not None and driver in needed:
        driver_paths = files_by_role[driver]
        n = len(driver_paths)
        if n == 0:
            raise ValueError(f"No files uploaded for batch role: {driver}")

        for role in needed:
            if role == driver:
                continue
            count = len(files_by_role.get(role, []))
            if count not in (1, n):
                raise ValueError(
                    f"Role '{role}' has {count} file(s); expected 1 shared or {n} "
                    f"(one per batch item with '{driver}')"
                )

        items: list[dict[str, Path]] = []
        for index in range(n):
            item = {driver: driver_paths[index]}
            for role in needed:
                if role == driver:
                    continue
                paths = files_by_role[role]
                item[role] = paths[index] if len(paths) == n else paths[0]
            items.append(item)
        return items

    counts = {role: len(files_by_role[role]) for role in needed}
    unique = set(counts.values())
    if len(unique) != 1:
        raise ValueError(
            "For batch processing, each required role must have the same number of files "
            f"(got {dict(counts)})"
        )
    n = counts[needed[0]]
    return [{role: files_by_role[role][index] for role in needed} for index in range(n)]


def _output_image_path(
    out_dir: Path,
    output_prefix: str,
    files: dict[str, Path],
    *,
    suffix: str | None = None,
) -> Path:
    base = strip_nifti_extension(output_prefix)
    ext = suffix or infer_nifti_suffix(files, role_priority=(ROLE_INPUT, ROLE_MOVING, ROLE_FIXED))
    return out_dir / f"{base}{ext}"


def _bracket_pair(path_a: Path, path_b: Path) -> list[str]:
    return ["[", str(path_a.resolve()), ",", str(path_b.resolve()), "]"]


def _opt_flag(name: str, value: Any) -> list[str]:
    if value is None or value == "":
        return []
    return [name, str(value)]


def _registration_transform(parameters: dict[str, Any]) -> str:
    custom = parameters.get("transform")
    if custom:
        return str(custom)
    preset = parameters.get("transform_preset", "rigid")
    if preset == "syn":
        return "SyN[0.1,3,0]"
    if preset == "affine":
        return "Affine[0.1]"
    return "Rigid[0.1]"


def _registration_metric(
    parameters: dict[str, Any],
    fixed: Path,
    moving: Path,
) -> str:
    metric_full = parameters.get("metric_full") or parameters.get("metric")
    if metric_full and "[" in str(metric_full):
        template = str(metric_full)
    elif metric_full:
        template = f"{metric_full}[{{fixed}},{{moving}},1,32]"
    else:
        template = "MI[{fixed},{moving},1,32]"
    return template.replace("{fixed}", str(fixed)).replace("{moving}", str(moving))


def _similarity_metric(
    parameters: dict[str, Any],
    fixed: Path,
    moving: Path,
) -> str:
    metric_full = parameters.get("metric_full")
    if metric_full:
        return str(metric_full).replace("{fixed}", str(fixed)).replace("{moving}", str(moving))
    metric = parameters.get("metric", "MI")
    if metric == "MSQ":
        metric = "MeanSquares"
    return f"{metric}[{fixed},{moving},1,32]"


def _atropos_initialization(parameters: dict[str, Any]) -> str:
    init_type = parameters.get("initialization", "Random")
    n_classes = parameters.get("n_classes", 3)
    return f"{init_type}[{n_classes}]"


def _n4_bspline(parameters: dict[str, Any]) -> list[str]:
    distance = parameters.get("spline_distance", 180)
    order = parameters.get("spline_order")
    if order is not None and order != "":
        return ["-b", "[", str(distance), ",", str(order), "]"]
    return ["-b", "[", str(distance), "]"]


def primary_executable(module_id: str) -> str:
    return MODULE_PRIMARY_EXECUTABLE[module_id]


def ensure_module_available(settings: Settings, module_id: str) -> str:
    executable = primary_executable(module_id)
    if resolve_executable(settings, executable) is None:
        raise FileNotFoundError(
            f"{executable} was not found on PATH. "
            "Install ANTs binaries or set NEUROFLOW_ANTSPATH / ANTSPATH."
        )
    return executable


def build_argv(
    *,
    module_id: str,
    files: dict[str, Path],
    work_dir: Path,
    output_prefix: str,
    parameters: dict[str, Any],
    settings: Settings,
) -> list[str]:
    """Build argv for a single ANTs command. Paths must be absolute."""
    del settings
    out_dir = work_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    base = strip_nifti_extension(output_prefix)
    dim = str(parameters.get("dimension", 3))

    if module_id == "ants-n4":
        corrected = _output_image_path(out_dir, f"{base}_corrected", files)
        bias = _output_image_path(out_dir, f"{base}_bias", files)
        verbose = str(parameters.get("verbose", 1))
        argv = [
            "N4BiasFieldCorrection",
            "-d",
            dim,
            "-v",
            verbose,
            "-s",
            str(parameters.get("shrink_factor", 4)),
            *_n4_bspline(parameters),
            "-c",
            "[",
            str(parameters.get("convergence", "50x50x50x50,0.0")),
            "]",
            "-i",
            str(files[ROLE_INPUT].resolve()),
            "-o",
            *_bracket_pair(corrected, bias),
        ]
        if ROLE_MASK in files:
            argv.extend(["-x", str(files[ROLE_MASK].resolve())])
        if ROLE_WEIGHT in files:
            argv.extend(["-w", str(files[ROLE_WEIGHT].resolve())])
        if parameters.get("rescale_intensities"):
            argv.extend(["-r", "1"])
        argv.extend(_opt_flag("-t", parameters.get("histogram_sharpening")))
        return argv

    if module_id == "ants-registration":
        fixed = files[ROLE_FIXED].resolve()
        moving = files[ROLE_MOVING].resolve()
        prefix = str(out_dir / base)
        argv = [
            "antsRegistration",
            "-d",
            dim,
            "-o",
            "[",
            f"{prefix},",
            f"{prefix}Warp.nii.gz,",
            f"{prefix}InverseWarp.nii.gz",
            "]",
            "-t",
            _registration_transform(parameters),
            "-m",
            _registration_metric(parameters, fixed, moving),
            "-c",
            "[",
            str(parameters.get("convergence", "1000x1000x1000,1e-6,10")),
            "]",
            "-f",
            str(parameters.get("shrink_factors", "4x2x1")),
            "-s",
            str(parameters.get("smoothing_sigmas", "2x1x0vox")),
        ]
        argv.extend(_opt_flag("-n", parameters.get("interpolation", "Linear")))
        if parameters.get("histogram_matching"):
            argv.append("-u")
        argv.extend(_opt_flag("-w", parameters.get("winsorize")))
        argv.extend(_opt_flag("--random-seed", parameters.get("random_seed")))
        if parameters.get("use_float"):
            argv.append("--float")
        fixed_mask = files.get(ROLE_FIXED_MASK)
        moving_mask = files.get(ROLE_MOVING_MASK)
        if fixed_mask or moving_mask:
            fixed_part = str(fixed_mask.resolve()) if fixed_mask else "NULL"
            moving_part = str(moving_mask.resolve()) if moving_mask else "NULL"
            argv.extend(["-x", "[", fixed_part, ",", moving_part, "]"])
        return argv

    if module_id == "ants-apply-transforms":
        output = _output_image_path(out_dir, base, files)
        interpolation = parameters.get("interpolation")
        if not interpolation and parameters.get("linear"):
            interpolation = "Linear"
        argv = [
            "antsApplyTransforms",
            "-d",
            dim,
            "-i",
            str(files[ROLE_MOVING].resolve()),
            "-r",
            str(files[ROLE_REFERENCE].resolve()),
            "-o",
            str(output),
        ]
        for role in (ROLE_TRANSFORM, ROLE_TRANSFORM2, ROLE_TRANSFORM3):
            if role in files:
                argv.extend(["-t", str(files[role].resolve())])
        argv.extend(_opt_flag("-n", interpolation or "Linear"))
        argv.extend(_opt_flag("-f", parameters.get("default_value")))
        argv.extend(_opt_flag("-u", parameters.get("output_data_type")))
        if parameters.get("verbose"):
            argv.extend(["-v", "1"])
        return argv

    if module_id == "ants-registration-syn":
        prefix = str(out_dir / base)
        argv = [
            "antsRegistrationSyN.sh",
            "-d",
            dim,
            "-f",
            str(files[ROLE_FIXED].resolve()),
            "-m",
            str(files[ROLE_MOVING].resolve()),
            "-o",
            prefix,
            "-t",
            str(parameters.get("transform_type", "s")),
        ]
        argv.extend(_opt_flag("-n", parameters.get("n_threads")))
        if ROLE_INITIAL_TRANSFORM in files:
            argv.extend(["-i", str(files[ROLE_INITIAL_TRANSFORM].resolve())])
        return argv

    if module_id == "ants-registration-syn-quick":
        prefix = str(out_dir / base)
        argv = [
            "antsRegistrationSyNQuick.sh",
            "-d",
            dim,
            "-f",
            str(files[ROLE_FIXED].resolve()),
            "-m",
            str(files[ROLE_MOVING].resolve()),
            "-o",
            prefix,
            "-t",
            str(parameters.get("transform_type", "s")),
        ]
        argv.extend(_opt_flag("-n", parameters.get("n_threads")))
        if ROLE_INITIAL_TRANSFORM in files:
            argv.extend(["-i", str(files[ROLE_INITIAL_TRANSFORM].resolve())])
        return argv

    if module_id == "ants-atropos":
        prefix = str(out_dir / base)
        seg = out_dir / f"{base}_seg.nii.gz"
        argv = [
            "Atropos",
            "-d",
            dim,
            "-a",
            str(files[ROLE_INPUT].resolve()),
            "-i",
            _atropos_initialization(parameters),
            "-c",
            str(parameters.get("convergence", "5,0.001")),
            "-o",
            "[",
            str(seg),
            ",",
            f"{prefix}_prob%02d.nii.gz",
            "]",
        ]
        if ROLE_MASK in files:
            argv.extend(["-x", str(files[ROLE_MASK].resolve())])
        argv.extend(_opt_flag("-k", parameters.get("likelihood_model")))
        argv.extend(_opt_flag("-m", parameters.get("mrf")))
        argv.extend(_opt_flag("-p", parameters.get("posterior_formulation")))
        argv.extend(_opt_flag("-b", parameters.get("bspline")))
        if parameters.get("verbose"):
            argv.extend(["-v", "1"])
        return argv

    if module_id == "ants-image-math":
        operation = parameters.get("operation", "m")
        if operation not in IMAGE_MATH_OPERATIONS:
            raise ValueError(f"Unsupported ImageMath operation: {operation}")
        output = _output_image_path(out_dir, base, files)
        argv = [
            "ImageMath",
            dim,
            str(files[ROLE_INPUT].resolve()),
            str(output),
            operation,
        ]
        if parameters.get("operand"):
            argv.append(str(parameters["operand"]))
        return argv

    if module_id == "ants-sccan":
        output = str(out_dir / base)
        argv = [
            "sccan",
            str(files[ROLE_INPUT].resolve()),
            "-o",
            output,
            "--sparse",
            str(parameters.get("sparse", 0.05)),
        ]
        argv.extend(_opt_flag("-p", parameters.get("n_permutations")))
        argv.extend(_opt_flag("-i", parameters.get("iterations")))
        argv.extend(_opt_flag("-n", parameters.get("n_eigenvectors")))
        argv.extend(_opt_flag("-s", parameters.get("smoother")))
        if ROLE_MASK in files:
            argv.extend(["--mask", str(files[ROLE_MASK].resolve())])
        return argv

    if module_id == "ants-kelly-kapowski":
        output = _output_image_path(out_dir, base, files)
        argv = [
            "KellyKapowski",
            "-d",
            dim,
            "-s",
            str(files[ROLE_INPUT].resolve()),
            "-o",
            str(output),
        ]
        if ROLE_GRAY_MATTER in files:
            argv.extend(["-g", str(files[ROLE_GRAY_MATTER].resolve())])
        if ROLE_WHITE_MATTER in files:
            argv.extend(["-w", str(files[ROLE_WHITE_MATTER].resolve())])
        argv.extend(_opt_flag("-c", parameters.get("convergence")))
        argv.extend(_opt_flag("-r", parameters.get("gradient_step")))
        argv.extend(_opt_flag("-l", parameters.get("smoothing_variance")))
        if parameters.get("verbose"):
            argv.extend(["-v", "1"])
        return argv

    if module_id == "ants-motion-corr":
        prefix = str(out_dir / base)
        argv = [
            "antsMotionCorr",
            "-d",
            dim,
            "-a",
            str(files[ROLE_INPUT].resolve()),
            "-o",
            prefix,
        ]
        argv.extend(_opt_flag("-n", parameters.get("n_images")))
        if parameters.get("use_histogram_matching"):
            argv.append("--use-histogram-matching")
        argv.extend(_opt_flag("-m", parameters.get("metric")))
        argv.extend(_opt_flag("-t", parameters.get("transform")))
        argv.extend(_opt_flag("-i", parameters.get("iterations")))
        argv.extend(_opt_flag("-f", parameters.get("shrink_factors")))
        argv.extend(_opt_flag("-s", parameters.get("smoothing_sigmas")))
        argv.extend(_opt_flag("-p", parameters.get("interpolation")))
        if parameters.get("verbose"):
            argv.extend(["-v", "1"])
        return argv

    if module_id == "ants-denoise":
        output = _output_image_path(out_dir, base, files)
        argv = [
            "DenoiseImage",
            "-d",
            dim,
            "-i",
            str(files[ROLE_INPUT].resolve()),
            "-o",
            str(output),
            "-n",
            str(parameters.get("noise_model", "Rician")),
        ]
        if ROLE_MASK in files:
            argv.extend(["-x", str(files[ROLE_MASK].resolve())])
        argv.extend(_opt_flag("-s", parameters.get("shrink_factor")))
        argv.extend(_opt_flag("-p", parameters.get("patch_radius")))
        argv.extend(_opt_flag("-r", parameters.get("search_radius")))
        if parameters.get("verbose"):
            argv.extend(["-v", "1"])
        return argv

    if module_id == "ants-transform-info":
        argv = ["antsTransformInfo", str(files[ROLE_TRANSFORM].resolve())]
        if parameters.get("verbose"):
            argv.extend(["-v", "1"])
        return argv

    if module_id == "ants-jacobian":
        output = _output_image_path(out_dir, base, files)
        argv = [
            "CreateJacobianDeterminantImage",
            dim,
            str(files[ROLE_TRANSFORM].resolve()),
            str(output),
            str(parameters.get("do_log", 0)),
        ]
        if parameters.get("use_geometric") is not None:
            argv.append(str(int(parameters["use_geometric"])))
        if parameters.get("deformation_gradient"):
            argv.append("1")
        return argv

    if module_id == "ants-brain-extraction":
        prefix = str(out_dir / base)
        argv = [
            "antsBrainExtraction.sh",
            "-d",
            dim,
            "-a",
            str(files[ROLE_INPUT].resolve()),
            "-e",
            str(files[ROLE_TEMPLATE].resolve()),
            "-m",
            str(files[ROLE_PROB_MASK].resolve()),
            "-o",
            prefix,
        ]
        if ROLE_MASK in files:
            argv.extend(["-f", str(files[ROLE_MASK].resolve())])
        argv.extend(_opt_flag("-c", parameters.get("tissue_classification")))
        argv.extend(_opt_flag("-q", parameters.get("single_precision")))
        argv.extend(_opt_flag("-s", parameters.get("suffix")))
        argv.extend(_opt_flag("-k", parameters.get("keep_temp")))
        if parameters.get("debug_mode"):
            argv.extend(["-z", "1"])
        return argv

    if module_id == "ants-cortical-thickness":
        prefix = str(out_dir / base)
        priors = parameters.get("priors_pattern", f"{prefix}_priors%02d.nii.gz")
        argv = [
            "antsCorticalThickness.sh",
            "-d",
            dim,
            "-a",
            str(files[ROLE_INPUT].resolve()),
            "-e",
            str(files[ROLE_TEMPLATE].resolve()),
            "-t",
            str(files[ROLE_BRAIN].resolve()),
            "-f",
            str(files[ROLE_MASK].resolve()),
            "-m",
            str(files[ROLE_MASK].resolve()),
            "-p",
            priors,
            "-o",
            prefix,
        ]
        argv.extend(_opt_flag("-k", parameters.get("keep_temp")))
        argv.extend(_opt_flag("-q", parameters.get("single_precision")))
        argv.extend(_opt_flag("-s", parameters.get("suffix")))
        return argv

    if module_id == "ants-template-construction":
        cohort_paths = files[ROLE_COHORT]
        list_path = work_dir / "cohort_list.txt"
        list_path.write_text(
            "\n".join(str(path.resolve()) for path in cohort_paths),
            encoding="utf-8",
        )
        prefix = str(out_dir / base)
        argv = [
            "antsMultivariateTemplateConstruction2.sh",
            "-d",
            dim,
            "-o",
            prefix,
            "-g",
            str(parameters.get("gradient_step", 0.2)),
        ]
        argv.extend(_opt_flag("-a", parameters.get("image_statistic")))
        argv.extend(_opt_flag("-A", parameters.get("sharpening")))
        argv.extend(_opt_flag("-i", parameters.get("iterations")))
        argv.extend(_opt_flag("-s", parameters.get("subsample")))
        argv.append(str(list_path))
        return argv

    if module_id == "ants-resample":
        output = _output_image_path(out_dir, base, files)
        interp_map = {"0": "0", "1": "1", "2": "2", "3": "3", "4": "4"}
        interpolation = parameters.get("interpolation", "Linear")
        if interpolation in interp_map:
            interpolation = interp_map[interpolation]
        argv = [
            "ResampleImage",
            dim,
            str(files[ROLE_INPUT].resolve()),
            str(files[ROLE_REFERENCE].resolve()),
            str(output),
            str(interpolation),
        ]
        if parameters.get("pixel_type") is not None and parameters.get("pixel_type") != "":
            argv.append(str(parameters.get("pixel_type")))
        return argv

    if module_id == "ants-threshold":
        output = _output_image_path(out_dir, base, files)
        mode = parameters.get("mode", "inclusive")
        if mode == "otsu":
            argv = [
                "ThresholdImage",
                dim,
                str(files[ROLE_INPUT].resolve()),
                str(output),
                "Otsu",
                str(parameters.get("n_thresholds", 1)),
            ]
            if ROLE_MASK in files:
                argv.append(str(files[ROLE_MASK].resolve()))
            return argv
        if mode == "kmeans":
            argv = [
                "ThresholdImage",
                dim,
                str(files[ROLE_INPUT].resolve()),
                str(output),
                "Kmeans",
                str(parameters.get("n_thresholds", 3)),
            ]
            if ROLE_MASK in files:
                argv.append(str(files[ROLE_MASK].resolve()))
            return argv
        return [
            "ThresholdImage",
            dim,
            str(files[ROLE_INPUT].resolve()),
            str(output),
            str(parameters.get("lower", 0)),
            str(parameters.get("upper", 1)),
            str(parameters.get("inside_value", 1)),
            str(parameters.get("outside_value", 0)),
        ]

    if module_id == "ants-smooth":
        output = _output_image_path(out_dir, base, files)
        argv = [
            "SmoothImage",
            dim,
            str(files[ROLE_INPUT].resolve()),
            str(output),
            str(parameters.get("sigma", 1.0)),
        ]
        if parameters.get("sigma_in_spacing_units"):
            argv.append("1")
        if parameters.get("median_filter"):
            argv.append("1")
        return argv

    if module_id == "ants-convert":
        output = _output_image_path(out_dir, base, files)
        return [
            "ConvertImage",
            dim,
            str(files[ROLE_INPUT].resolve()),
            str(output),
            str(parameters.get("pixel_type", "float")),
        ]

    if module_id == "ants-measure-similarity":
        fixed = files[ROLE_FIXED].resolve()
        moving = files[ROLE_MOVING].resolve()
        argv = [
            "MeasureImageSimilarity",
            "-d",
            dim,
            "-m",
            _similarity_metric(parameters, fixed, moving),
        ]
        if ROLE_MASK in files:
            argv.extend(["-x", str(files[ROLE_MASK].resolve())])
        if parameters.get("verbose"):
            argv.extend(["-v", "1"])
        return argv

    if module_id == "ants-joint-fusion":
        prefix = str(out_dir / base)
        argv = [
            "antsJointFusion",
            "-d",
            dim,
            "-t",
            str(files[ROLE_INPUT].resolve()),
            "-g",
            str(files[ROLE_ATLAS].resolve()),
            "-l",
            str(files[ROLE_ATLAS_LABELS].resolve()),
            "-o",
            prefix,
            "-c",
            str(parameters.get("n_classes", 6)),
        ]
        argv.extend(_opt_flag("-a", parameters.get("alpha")))
        argv.extend(_opt_flag("-b", parameters.get("beta")))
        argv.extend(_opt_flag("-p", parameters.get("patch_radius")))
        argv.extend(_opt_flag("-s", parameters.get("search_radius")))
        argv.extend(_opt_flag("-m", parameters.get("patch_metric")))
        if ROLE_MASK in files:
            argv.extend(["-x", str(files[ROLE_MASK].resolve())])
        if parameters.get("verbose"):
            argv.extend(["-v", "1"])
        return argv

    raise ValueError(f"No argv builder for module: {module_id}")


def output_path_kind(module_id: str) -> Literal["prefix", "image", "directory", "none"]:
    if module_id in {"ants-transform-info", "ants-measure-similarity"}:
        return "none"
    if module_id in {
        "ants-registration",
        "ants-registration-syn",
        "ants-registration-syn-quick",
        "ants-motion-corr",
        "ants-cortical-thickness",
        "ants-brain-extraction",
        "ants-template-construction",
        "ants-joint-fusion",
        "ants-sccan",
    }:
        return "prefix"
    return "image"


def _shell_quote(part: str) -> str:
    if not part or any(c in part for c in " \t\n\"'$\\"):
        return '"' + part.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return part


def _run_one_ants(
    *,
    settings: Settings,
    store: JobStore,
    job_id: str,
    argv: list[str],
    cwd: Path,
    scan_index: int,
    scan_total: int,
    label: str,
) -> int:
    executable = resolve_executable(settings, argv[0])
    if executable is None:
        raise FileNotFoundError(f"Executable not found on PATH: {argv[0]}")

    env = build_env(settings)
    cmd = [str(executable), *argv[1:]]
    preview = " ".join(_shell_quote(part) for part in cmd)

    store.append_log(
        ANTS_TOOL_ID,
        job_id,
        f"\n=== Run {scan_index}/{scan_total}: {label} ===\n$ {preview}\n\n",
    )
    store.update_meta(
        ANTS_TOOL_ID,
        job_id,
        batch_current_index=scan_index,
        command=cmd,
        command_preview=preview,
    )

    log_path = store.log_path(ANTS_TOOL_ID, job_id)
    with log_path.open("a", encoding="utf-8") as log_file:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        store.update_meta(ANTS_TOOL_ID, job_id, pid=proc.pid)
        if proc.stdout:
            for line in proc.stdout:
                log_file.write(line)
                log_file.flush()
        return proc.wait()


def launch_ants_job(
    *,
    settings: Settings,
    store: JobStore,
    job_id: str,
    module_id: str,
    batch_items: list[dict[str, Path]],
    output_prefix: str,
    parameters: dict[str, Any],
    workspace: str,
    subject_id: str,
) -> list[str]:
    """Run one or more ANTs commands sequentially in a background job."""
    if not batch_items:
        raise ValueError("At least one input set is required")

    ensure_module_available(settings, module_id)
    subject_id = normalize_subject_id(subject_id)
    datasets = DatasetStore(settings)
    modality = modality_for_module(ANTS_TOOL_ID, module_id)
    for item_files in batch_items:
        for path in item_files.values():
            datasets.stage_input(
                workspace=workspace,
                subject_id=subject_id,
                modality=modality,
                source=path,
            )

    module_def = get_module(module_id)
    estimated_hours = module_def.estimated_hours_per_scan if module_def else 1.0
    batch_total = len(batch_items)
    estimated_total_seconds = int(batch_total * estimated_hours * 3600)

    job_dir = store.job_dir(ANTS_TOOL_ID, job_id)
    derivative = datasets.derivative_dir(workspace, subject_id, ANTS_TOOL_ID, module_id)
    datasets.link_job_output_to_derivatives(job_dir / "output", derivative)

    first_files = batch_items[0]
    first_prefix = output_prefix_for_batch(
        output_prefix,
        first_files,
        module_id,
        index=0,
        batch_total=batch_total,
    )
    first_argv = build_argv(
        module_id=module_id,
        files=first_files,
        work_dir=job_dir,
        output_prefix=first_prefix,
        parameters=parameters,
        settings=settings,
    )
    preview = " ".join(_shell_quote(part) for part in first_argv)
    if batch_total > 1:
        preview = f"{preview}  (+{batch_total - 1} more run(s) queued)"

    batch_meta = []
    for index, item_files in enumerate(batch_items):
        driver = _MODULE_BATCH_DRIVER.get(module_id)
        label_path = item_files.get(driver or required_roles(module_id)[0])
        filename = label_path.name if label_path else f"run-{index + 1}"
        batch_meta.append(
            {
                "filename": filename,
                "subject_id": subject_id,
                "status": "pending",
                "started_at": None,
                "finished_at": None,
                "error_message": None,
            }
        )

    all_input_names = [path.name for item in batch_items for path in item.values()]
    store.update_meta(
        ANTS_TOOL_ID,
        job_id,
        command=first_argv,
        command_preview=preview,
        workspace=workspace,
        subject_id=subject_id,
        dataset_output_dir=str(derivative),
        parameters={
            "module_id": module_id,
            "workspace": workspace,
            "subject_id": subject_id,
            "output_prefix": output_prefix,
            "output_path_kind": output_path_kind(module_id),
            **parameters,
        },
        batch_items=batch_meta,
        batch_current_index=0,
        batch_total=batch_total,
        estimated_total_seconds=estimated_total_seconds,
        input_files=all_input_names,
        started_at=datetime.now(timezone.utc).isoformat(),
        status="running",
    )

    log_path = store.log_path(ANTS_TOOL_ID, job_id)
    log_path.write_text("", encoding="utf-8")

    def _run_batch() -> None:
        exit_code = 0
        for index, item_files in enumerate(batch_items):
            if skip_if_cancelled(store, ANTS_TOOL_ID, job_id):
                return

            prefix = output_prefix_for_batch(
                output_prefix,
                item_files,
                module_id,
                index=index,
                batch_total=batch_total,
            )
            argv = build_argv(
                module_id=module_id,
                files=item_files,
                work_dir=job_dir,
                output_prefix=prefix,
                parameters=parameters,
                settings=settings,
            )
            driver = _MODULE_BATCH_DRIVER.get(module_id)
            label_path = item_files.get(driver or required_roles(module_id)[0])
            label = label_path.name if label_path else f"run-{index + 1}"

            if index < len(batch_meta):
                batch_meta[index]["status"] = "running"
                batch_meta[index]["started_at"] = datetime.now(timezone.utc).isoformat()
                store.update_meta(
                    ANTS_TOOL_ID,
                    job_id,
                    batch_items=batch_meta,
                    batch_current_index=index + 1,
                )

            exit_code = _run_one_ants(
                settings=settings,
                store=store,
                job_id=job_id,
                argv=argv,
                cwd=job_dir,
                scan_index=index + 1,
                scan_total=batch_total,
                label=label,
            )

            finished = datetime.now(timezone.utc).isoformat()
            if index < len(batch_meta):
                batch_meta[index]["finished_at"] = finished
                batch_meta[index]["status"] = "completed" if exit_code == 0 else "failed"
                if exit_code != 0:
                    batch_meta[index]["error_message"] = f"Exit code {exit_code}"
                store.update_meta(ANTS_TOOL_ID, job_id, batch_items=batch_meta)

            if skip_if_cancelled(store, ANTS_TOOL_ID, job_id):
                return

            if exit_code != 0:
                break

        if is_job_cancelled(store.read_meta(ANTS_TOOL_ID, job_id)):
            return

        status = "completed" if exit_code == 0 else "failed"
        store.update_meta(
            ANTS_TOOL_ID,
            job_id,
            status=status,
            exit_code=exit_code,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )

    thread = threading.Thread(target=_run_batch, daemon=True)
    thread.start()
    return first_argv
