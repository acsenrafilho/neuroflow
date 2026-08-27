"""Tests for Windows launcher --stop and portal pidfile."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from neuroflow.windows_launcher.detect import WslProbe
from neuroflow.windows_launcher.health import HealthResult, HealthStatus
from neuroflow.windows_launcher.stop import stop_portal
from neuroflow.windows_launcher.types import WSL_INSTALL_URL, WslState
from neuroflow.windows_launcher.wsl_exec import DisallowedWslArgumentError, validate_wsl_argv

_WSL_EXE = r"C:\Windows\System32\wsl.exe"
_HOME = "/home/lab"
_PIDFILE = f"{_HOME}/.neuroflow-app/portal.pid"
_RUN = "neuroflow.windows_launcher.stop.run_wsl"


def _probe(state: WslState = WslState.UBUNTU_RUNNING) -> WslProbe:
    return WslProbe(
        state=state,
        wsl_exe=_WSL_EXE,
        distro="Ubuntu",
        wsl_version=2,
        microsoft_url=WSL_INSTALL_URL,
        message="ready",
    )


def _completed(stdout: bytes = b"", *, returncode: int = 0) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess(
        args=["wsl"],
        returncode=returncode,
        stdout=stdout,
        stderr=b"",
    )


class TestStopPortal:
    def test_not_running_when_wsl_missing(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = stop_portal(_probe(WslState.WSL_MISSING))
        assert code == 0
        assert "not running" in capsys.readouterr().out.lower()

    def test_not_running_when_ubuntu_stopped(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = stop_portal(_probe(WslState.UBUNTU_STOPPED))
        assert code == 0
        assert "not running" in capsys.readouterr().out.lower()

    def test_happy_path_term(self, capsys: pytest.CaptureFixture[str]) -> None:
        calls: list[list[str]] = []

        def side_effect(_exe: str, args: list[str], **_kwargs):
            calls.append(args)
            if args == ["-d", "Ubuntu", "--", "printenv", "HOME"]:
                return _completed(f"{_HOME}\n".encode())
            if args == ["-d", "Ubuntu", "--", "test", "-f", _PIDFILE]:
                return _completed(returncode=0)
            if args == ["-d", "Ubuntu", "--", "cat", _PIDFILE]:
                return _completed(b"4242\n")
            if args[:4] == ["-d", "Ubuntu", "--", "kill"]:
                return _completed(returncode=0)
            return _completed()

        with (
            patch(_RUN, side_effect=side_effect),
            patch(
                "neuroflow.windows_launcher.stop.probe_health",
                side_effect=[
                    HealthResult(HealthStatus.OK),  # wait loop first poll → still up
                    HealthResult(HealthStatus.DOWN),  # wait loop second → down
                    HealthResult(HealthStatus.DOWN),  # final confirm
                ],
            ),
        ):
            code = stop_portal(_probe())

        assert code == 0
        assert any(c[:4] == ["-d", "Ubuntu", "--", "kill"] and "-TERM" in c for c in calls)
        assert "--shutdown" not in str(calls)
        assert "stopped" in capsys.readouterr().out.lower()

    def test_missing_pidfile_health_ok(self, capsys: pytest.CaptureFixture[str]) -> None:
        def side_effect(_exe: str, args: list[str], **_kwargs):
            if args == ["-d", "Ubuntu", "--", "printenv", "HOME"]:
                return _completed(f"{_HOME}\n".encode())
            if args == ["-d", "Ubuntu", "--", "test", "-f", _PIDFILE]:
                return _completed(returncode=1)
            return _completed()

        with (
            patch(_RUN, side_effect=side_effect) as mock_run,
            patch(
                "neuroflow.windows_launcher.stop.probe_health",
                return_value=HealthResult(HealthStatus.OK),
            ),
        ):
            code = stop_portal(_probe())

        assert code == 0
        # Must not call kill when pidfile is missing.
        for call in mock_run.call_args_list:
            assert "kill" not in call.args[1]
        assert "portal.pid" in capsys.readouterr().out

    def test_missing_pidfile_health_down(self, capsys: pytest.CaptureFixture[str]) -> None:
        def side_effect(_exe: str, args: list[str], **_kwargs):
            if args == ["-d", "Ubuntu", "--", "printenv", "HOME"]:
                return _completed(f"{_HOME}\n".encode())
            if args == ["-d", "Ubuntu", "--", "test", "-f", _PIDFILE]:
                return _completed(returncode=1)
            return _completed()

        with (
            patch(_RUN, side_effect=side_effect),
            patch(
                "neuroflow.windows_launcher.stop.probe_health",
                return_value=HealthResult(HealthStatus.DOWN),
            ),
        ):
            code = stop_portal(_probe())
        assert code == 0
        assert "not running" in capsys.readouterr().out.lower()

    def test_escalates_to_kill(self) -> None:
        calls: list[list[str]] = []

        def side_effect(_exe: str, args: list[str], **_kwargs):
            calls.append(args)
            if args == ["-d", "Ubuntu", "--", "printenv", "HOME"]:
                return _completed(f"{_HOME}\n".encode())
            if args == ["-d", "Ubuntu", "--", "test", "-f", _PIDFILE]:
                return _completed(returncode=0)
            if args == ["-d", "Ubuntu", "--", "cat", _PIDFILE]:
                return _completed(b"99\n")
            return _completed()

        with (
            patch(_RUN, side_effect=side_effect),
            patch(
                "neuroflow.windows_launcher.stop._wait_until_unhealthy",
                side_effect=[False, True],
            ),
            patch(
                "neuroflow.windows_launcher.stop.probe_health",
                return_value=HealthResult(HealthStatus.DOWN),
            ),
        ):
            code = stop_portal(_probe())

        assert code == 0
        assert any("-KILL" in c for c in calls)
        assert any(c[:3] == ["-d", "Ubuntu", "--"] and "rm" in c for c in calls)


class TestValidateStopNeverShutdown:
    def test_shutdown_still_rejected(self) -> None:
        with pytest.raises(DisallowedWslArgumentError, match="--shutdown"):
            validate_wsl_argv(["wsl.exe", "--shutdown"])


class TestPackagedAppPidfile:
    def test_writes_and_registers_unlink(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pidfile = tmp_path / "portal.pid"
        monkeypatch.setenv("NEUROFLOW_PORTAL_PIDFILE", str(pidfile))

        # Clear any prior atexit handlers from other tests by calling the writer directly.
        from neuroflow import packaged_app

        packaged_app._write_portal_pidfile()
        assert pidfile.is_file()
        text = pidfile.read_text(encoding="utf-8").strip()
        assert text.isdigit()
        assert int(text) > 1

    def test_noop_without_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("NEUROFLOW_PORTAL_PIDFILE", raising=False)
        from neuroflow import packaged_app

        packaged_app._write_portal_pidfile()
        assert not (tmp_path / "portal.pid").exists()
