"""Exclusive non-blocking lock so two double-clicks cannot start two portals."""

from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path
from types import TracebackType

LOCK_ENV = "NEUROFLOW_LAUNCHER_LOCK"


class LauncherLock:
    """Context manager for an exclusive launcher lock file.

    On Windows uses ``msvcrt.locking``; elsewhere uses ``fcntl.flock`` (CI).
    Acquire is non-blocking: if the lock is held, ``acquired`` is False.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path if path is not None else default_lock_path()
        self._fh: object | None = None
        self.acquired = False

    def __enter__(self) -> LauncherLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Keep the file handle open for the lock lifetime.
        self._fh = open(self.path, "a+b")  # noqa: SIM115
        try:
            self._lock_exclusive()
            self.acquired = True
        except OSError:
            self.acquired = False
            self._close()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self.acquired and self._fh is not None:
            with contextlib.suppress(OSError):
                self._unlock()
        self._close()
        self.acquired = False

    def _lock_exclusive(self) -> None:
        assert self._fh is not None
        if sys.platform == "win32":
            import msvcrt

            self._fh.seek(0)
            if self._fh.read(1) == b"":
                self._fh.write(b"0")
                self._fh.flush()
            self._fh.seek(0)
            msvcrt.locking(self._fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock(self) -> None:
        assert self._fh is not None
        if sys.platform == "win32":
            import msvcrt

            self._fh.seek(0)
            msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)

    def _close(self) -> None:
        if self._fh is not None:
            with contextlib.suppress(OSError):
                self._fh.close()
            self._fh = None


def default_lock_path() -> Path:
    """Resolve the lock file path (overridable via ``NEUROFLOW_LAUNCHER_LOCK``)."""
    override = os.environ.get(LOCK_ENV, "").strip()
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", "").strip()
        if local:
            return Path(local) / "NeuroFlow" / "launcher.lock"
        return Path.home() / "AppData" / "Local" / "NeuroFlow" / "launcher.lock"
    return Path.home() / ".cache" / "neuroflow" / "launcher.lock"
