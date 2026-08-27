"""Safe wrappers around ``wsl.exe`` for the Windows launcher."""

from __future__ import annotations

import subprocess
from pathlib import PurePosixPath

from neuroflow.windows_launcher.types import APP_DIR_NAME, PORTAL_PIDFILE_NAME

WSL_LIST_TIMEOUT_SECONDS = 15
WSL_PROBE_TIMEOUT_SECONDS = 15
WSL_WAKE_TIMEOUT_SECONDS = 60
WSL_COPY_TIMEOUT_SECONDS = 180
WSL_STOP_TIMEOUT_SECONDS = 15

DISTRO = "Ubuntu"


def portal_pidfile_path(linux_home: str) -> str:
    """Return the absolute Linux path for the portal pidfile."""
    return f"{linux_home.rstrip('/')}/{APP_DIR_NAME}/{PORTAL_PIDFILE_NAME}"


_ALLOWED_WSL_FLAGS = frozenset(
    {
        "-l",
        "-v",
        "--list",
        "--verbose",
        "-d",
        DISTRO,
        "--",
    }
)

_DISALLOWED_WSL_META = frozenset(
    {
        "--install",
        "--unregister",
        "--shutdown",
        "--terminate",
        "--export",
        "--import",
        "--set-default-version",
        "--update",
        "--set-default",
    }
)


class DisallowedWslArgumentError(ValueError):
    """Raised when a subprocess argv contains a non-allowlisted wsl flag."""


def _is_safe_linux_path(path: str) -> bool:
    """Return True for absolute POSIX paths without ``..`` segments."""
    if not path or not path.startswith("/") or "\x00" in path:
        return False
    parts = PurePosixPath(path).parts
    return ".." not in parts


def _require_under_app_home(path: str, linux_home: str) -> None:
    """Ensure ``path`` is under ``<linux_home>/.neuroflow-app/``."""
    if not _is_safe_linux_path(path) or not _is_safe_linux_path(linux_home):
        raise DisallowedWslArgumentError(f"unsafe linux path: {path!r}")
    prefix = f"{linux_home.rstrip('/')}/.neuroflow-app/"
    if not path.startswith(prefix) and path != prefix.rstrip("/"):
        raise DisallowedWslArgumentError(f"path must be under {prefix!r}: {path!r}")


def _parse_positive_pid(raw: str) -> int | None:
    """Return an integer PID > 1, or None if invalid."""
    if not raw.isdigit():
        return None
    pid = int(raw)
    if pid <= 1:
        return None
    return pid


def _validate_after_separator(after: list[str], *, linux_home: str | None) -> None:
    """Validate the argv segment after ``wsl -d Ubuntu --``."""
    if not after:
        raise DisallowedWslArgumentError("empty command after --")

    if after == ["true"]:
        return

    if after == ["printenv", "HOME"]:
        return

    if after == ["uname", "-m"]:
        return

    if len(after) == 3 and after[0] == "wslpath" and after[1] == "-u":
        # Windows path as seen by wslpath; reject empty / null bytes only.
        if not after[2] or "\x00" in after[2]:
            raise DisallowedWslArgumentError("invalid wslpath argument")
        return

    if len(after) == 3 and after[0] == "test" and after[1] in {"-x", "-d", "-f"}:
        if linux_home is None:
            raise DisallowedWslArgumentError("linux_home required for test")
        _require_under_app_home(after[2], linux_home)
        return

    if len(after) == 2 and after[0] == "cat":
        if linux_home is None:
            raise DisallowedWslArgumentError("linux_home required for cat")
        expected = portal_pidfile_path(linux_home)
        if after[1] != expected:
            raise DisallowedWslArgumentError(f"cat only allowed for pidfile: {after[1]!r}")
        return

    if len(after) == 3 and after[0] == "kill" and after[1] in {"-TERM", "-KILL"}:
        if _parse_positive_pid(after[2]) is None:
            raise DisallowedWslArgumentError(f"unsafe kill pid: {after[2]!r}")
        return

    if len(after) == 3 and after[0] == "rm" and after[1] == "-f":
        if linux_home is None:
            raise DisallowedWslArgumentError("linux_home required for rm")
        expected = portal_pidfile_path(linux_home)
        if after[2] != expected:
            raise DisallowedWslArgumentError(f"rm only allowed for pidfile: {after[2]!r}")
        return

    if len(after) == 3 and after[0] == "mkdir" and after[1] == "-p":
        if linux_home is None:
            raise DisallowedWslArgumentError("linux_home required for mkdir")
        _require_under_app_home(after[2], linux_home)
        return

    if (
        len(after) == 4
        and after[0] == "cp"
        and after[1] == "-a"
        and after[2].endswith("/.")
        and after[3].endswith("/")
    ):
        if linux_home is None:
            raise DisallowedWslArgumentError("linux_home required for cp")
        src = after[2][:-2]  # strip /.
        dest = after[3].rstrip("/")
        if not _is_safe_linux_path(src):
            raise DisallowedWslArgumentError(f"unsafe cp source: {src!r}")
        _require_under_app_home(dest, linux_home)
        return

    if len(after) == 3 and after[0] == "chmod" and after[1] == "+x":
        if linux_home is None:
            raise DisallowedWslArgumentError("linux_home required for chmod")
        _require_under_app_home(after[2], linux_home)
        return

    # env NEUROFLOW_SKIP_BROWSER=1 [NEUROFLOW_PORTAL_PIDFILE=…] <elf>
    if after and after[0] == "env" and "NEUROFLOW_SKIP_BROWSER=1" in after[1:]:
        if linux_home is None:
            raise DisallowedWslArgumentError("linux_home required for env start")
        assignments = after[1:-1]
        elf = after[-1]
        if not assignments or assignments[0] != "NEUROFLOW_SKIP_BROWSER=1":
            raise DisallowedWslArgumentError(f"disallowed env start: {after!r}")
        allowed_keys = {"NEUROFLOW_SKIP_BROWSER", "NEUROFLOW_PORTAL_PIDFILE"}
        for item in assignments:
            if "=" not in item:
                raise DisallowedWslArgumentError(f"invalid env assignment: {item!r}")
            key, value = item.split("=", 1)
            if key not in allowed_keys:
                raise DisallowedWslArgumentError(f"disallowed env key: {key!r}")
            if key == "NEUROFLOW_SKIP_BROWSER" and value != "1":
                raise DisallowedWslArgumentError(f"invalid skip-browser value: {value!r}")
            if key == "NEUROFLOW_PORTAL_PIDFILE" and value != portal_pidfile_path(linux_home):
                raise DisallowedWslArgumentError(f"invalid pidfile path: {value!r}")
        _require_under_app_home(elf, linux_home)
        return

    raise DisallowedWslArgumentError(f"disallowed wsl command: {after!r}")


def validate_wsl_argv(argv: list[str], *, linux_home: str | None = None) -> None:
    """Ensure ``wsl.exe`` is only invoked with allowlisted arguments.

    For commands that touch paths under ``~/.neuroflow-app/``, pass
    ``linux_home`` from a prior ``printenv HOME`` in the same session.
    """
    if not argv:
        raise DisallowedWslArgumentError("empty argv")

    # Skip the executable itself (argv[0]).
    args = argv[1:]
    for arg in args:
        if arg in _DISALLOWED_WSL_META or (
            arg.startswith("--") and arg.split("=")[0] in _DISALLOWED_WSL_META
        ):
            raise DisallowedWslArgumentError(f"disallowed wsl flag: {arg}")

    if "--" in args:
        sep = args.index("--")
        before = args[:sep]
        after = args[sep + 1 :]
        for arg in before:
            if arg not in _ALLOWED_WSL_FLAGS:
                if arg.startswith("-"):
                    raise DisallowedWslArgumentError(f"disallowed wsl flag: {arg}")
                raise DisallowedWslArgumentError(f"disallowed wsl argument: {arg}")
        _validate_after_separator(after, linux_home=linux_home)
        return

    for arg in args:
        if arg in _ALLOWED_WSL_FLAGS:
            continue
        if arg.startswith("-"):
            raise DisallowedWslArgumentError(f"disallowed wsl flag: {arg}")
        raise DisallowedWslArgumentError(f"disallowed wsl argument: {arg}")


def run_wsl(
    wsl_exe: str,
    args: list[str],
    *,
    timeout: float = WSL_LIST_TIMEOUT_SECONDS,
    linux_home: str | None = None,
) -> subprocess.CompletedProcess[bytes]:
    """Run ``wsl.exe`` with capture; validates argv before spawn."""
    validate_wsl_argv([wsl_exe, *args], linux_home=linux_home)
    return subprocess.run(
        [wsl_exe, *args],
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def popen_wsl(
    wsl_exe: str,
    args: list[str],
    *,
    linux_home: str | None = None,
) -> subprocess.Popen[bytes]:
    """Start ``wsl.exe`` without capturing (attached console for the portal)."""
    validate_wsl_argv([wsl_exe, *args], linux_home=linux_home)
    return subprocess.Popen([wsl_exe, *args])  # noqa: S603 — argv validated above
