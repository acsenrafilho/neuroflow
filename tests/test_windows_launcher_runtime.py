"""Tests for Windows launcher Phase 2 runtime (payload, health, start)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from neuroflow.windows_launcher.detect import WslProbe
from neuroflow.windows_launcher.health import (
    HealthResult,
    HealthStatus,
    probe_health,
    wait_until_healthy,
)
from neuroflow.windows_launcher.payload import (
    PayloadError,
    ensure_payload_installed,
    resolve_payload_dir,
)
from neuroflow.windows_launcher.runtime import launch
from neuroflow.windows_launcher.types import PORTAL_URL, WSL_INSTALL_URL, WslState

_WSL_EXE = r"C:\Windows\System32\wsl.exe"
_HOME = "/home/lab"
_VER = "0.0.1"
_DEST = f"{_HOME}/.neuroflow-app/{_VER}"
_ELF = f"{_DEST}/neuroflow"


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


def _make_onedir(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "neuroflow").write_bytes(b"\x7fELF")
    (root / "_internal").mkdir()
    (root / "_internal" / "marker").write_text("ok", encoding="utf-8")
    return root


class TestResolvePayload:
    def test_env_override(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        payload = _make_onedir(tmp_path / "linux-payload")
        monkeypatch.setenv("NEUROFLOW_LINUX_PAYLOAD", str(payload))
        assert resolve_payload_dir() == payload.resolve()

    def test_missing_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        missing = tmp_path / "nope"
        monkeypatch.setenv("NEUROFLOW_LINUX_PAYLOAD", str(missing))
        with pytest.raises(PayloadError, match="not found"):
            resolve_payload_dir()

    def test_missing_elf(self, tmp_path: Path) -> None:
        bad = tmp_path / "linux-payload"
        bad.mkdir()
        (bad / "_internal").mkdir()
        with pytest.raises(PayloadError, match="neuroflow"):
            resolve_payload_dir(str(bad))


class TestEnsurePayloadInstalled:
    def test_skips_copy_when_installed(self, tmp_path: Path) -> None:
        windows_dir = _make_onedir(tmp_path / "linux-payload")
        calls: list[list[str]] = []

        def side_effect(_exe: str, args: list[str], **_kwargs):
            calls.append(args)
            if args == ["-d", "Ubuntu", "--", "printenv", "HOME"]:
                return _completed(f"{_HOME}\n".encode())
            if args[:4] == ["-d", "Ubuntu", "--", "test"]:
                return _completed(returncode=0)
            raise AssertionError(f"unexpected: {args}")

        with patch("neuroflow.windows_launcher.payload.run_wsl", side_effect=side_effect):
            paths = ensure_payload_installed(_WSL_EXE, windows_dir, version=_VER)

        assert paths.linux_elf == _ELF
        assert not any(a[3] == "cp" for a in calls if len(a) > 3)

    def test_copy_argv_order_when_missing(self, tmp_path: Path) -> None:
        windows_dir = _make_onedir(tmp_path / "linux-payload")
        src_unix = "/mnt/c/payload"
        seen: list[list[str]] = []

        def side_effect(_exe: str, args: list[str], **_kwargs):
            seen.append(args)
            if args == ["-d", "Ubuntu", "--", "printenv", "HOME"]:
                return _completed(f"{_HOME}\n".encode())
            if args[:4] == ["-d", "Ubuntu", "--", "test"]:
                return _completed(returncode=1)
            if args[:4] == ["-d", "Ubuntu", "--", "wslpath"]:
                return _completed(f"{src_unix}\n".encode())
            if args[3] in {"mkdir", "cp", "chmod"}:
                return _completed()
            raise AssertionError(f"unexpected: {args}")

        with patch("neuroflow.windows_launcher.payload.run_wsl", side_effect=side_effect):
            ensure_payload_installed(_WSL_EXE, windows_dir, version=_VER)

        verbs = [a[3] for a in seen if len(a) > 3 and a[0] == "-d"]
        # printenv, test, test, wslpath, mkdir, cp, chmod
        assert "wslpath" in verbs
        assert verbs.index("mkdir") < verbs.index("cp") < verbs.index("chmod")
        cp_args = next(a for a in seen if len(a) > 3 and a[3] == "cp")
        assert cp_args[4:] == ["-a", f"{src_unix}/.", f"{_DEST}/"]


class TestHealth:
    def test_ok_json(self) -> None:
        body = json.dumps({"status": "ok", "version": "0.0.1"}).encode()

        class _Resp:
            status = 200

            def read(self) -> bytes:
                return body

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        with patch(
            "neuroflow.windows_launcher.health.urllib.request.urlopen",
            return_value=_Resp(),
        ):
            result = probe_health()
        assert result.status == HealthStatus.OK
        assert result.version == "0.0.1"

    def test_port_busy_when_tcp_open(self) -> None:
        with (
            patch(
                "neuroflow.windows_launcher.health.urllib.request.urlopen",
                side_effect=OSError("refused-ish"),
            ),
            patch("neuroflow.windows_launcher.health._tcp_port_open", return_value=True),
        ):
            result = probe_health()
        assert result.status == HealthStatus.PORT_BUSY

    def test_wait_succeeds_on_poll_n(self) -> None:
        sequence = [
            HealthResult(HealthStatus.DOWN),
            HealthResult(HealthStatus.DOWN),
            HealthResult(HealthStatus.OK, version="0.0.1"),
        ]

        with patch(
            "neuroflow.windows_launcher.health.probe_health",
            side_effect=sequence,
        ):
            result = wait_until_healthy(
                budget_seconds=5,
                interval_seconds=0,
                sleep=lambda _s: None,
            )
        assert result.status == HealthStatus.OK

    def test_wait_timeout(self) -> None:
        with patch(
            "neuroflow.windows_launcher.health.probe_health",
            return_value=HealthResult(HealthStatus.DOWN, detail="down"),
        ):
            result = wait_until_healthy(
                budget_seconds=0.01,
                interval_seconds=0,
                sleep=lambda _s: None,
            )
        assert result.status == HealthStatus.DOWN


class TestLaunch:
    def test_idempotent_opens_browser_only(self) -> None:
        with (
            patch(
                "neuroflow.windows_launcher.runtime.probe_health",
                return_value=HealthResult(HealthStatus.OK),
            ),
            patch("neuroflow.windows_launcher.runtime.webbrowser.open") as mock_open,
            patch("neuroflow.windows_launcher.runtime.ensure_payload_installed") as mock_copy,
            patch("neuroflow.windows_launcher.runtime.popen_wsl") as mock_popen,
        ):
            code = launch(_probe(), wait_on_process=False)
        assert code == 0
        mock_open.assert_called_once_with(PORTAL_URL)
        mock_copy.assert_not_called()
        mock_popen.assert_not_called()

    def test_port_busy_before_start(self) -> None:
        with (
            patch(
                "neuroflow.windows_launcher.runtime.probe_health",
                return_value=HealthResult(HealthStatus.PORT_BUSY),
            ),
            patch("neuroflow.windows_launcher.runtime.notify_user") as mock_notify,
            patch("neuroflow.windows_launcher.runtime.popen_wsl") as mock_popen,
        ):
            code = launch(_probe(), wait_on_process=False)
        assert code == 1
        mock_notify.assert_called_once()
        mock_popen.assert_not_called()

    def test_payload_missing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NEUROFLOW_LINUX_PAYLOAD", str(tmp_path / "missing"))
        with (
            patch(
                "neuroflow.windows_launcher.runtime.probe_health",
                return_value=HealthResult(HealthStatus.DOWN),
            ),
            patch("neuroflow.windows_launcher.runtime.notify_user") as mock_notify,
            patch("neuroflow.windows_launcher.runtime._wake_ubuntu", return_value=True),
        ):
            code = launch(_probe(WslState.UBUNTU_STOPPED), wait_on_process=False)
        assert code == 1
        mock_notify.assert_called_once()

    def test_start_poll_open(self, tmp_path: Path) -> None:
        windows_dir = _make_onedir(tmp_path / "linux-payload")
        paths = MagicMock()
        paths.linux_home = _HOME
        paths.linux_elf = _ELF
        proc = MagicMock()
        proc.wait.return_value = 0

        with (
            patch(
                "neuroflow.windows_launcher.runtime.probe_health",
                return_value=HealthResult(HealthStatus.DOWN),
            ),
            patch(
                "neuroflow.windows_launcher.runtime.ensure_payload_installed",
                return_value=paths,
            ) as mock_ensure,
            patch("neuroflow.windows_launcher.runtime.popen_wsl", return_value=proc) as mock_popen,
            patch(
                "neuroflow.windows_launcher.runtime.wait_until_healthy",
                return_value=HealthResult(HealthStatus.OK),
            ),
            patch("neuroflow.windows_launcher.runtime.webbrowser.open") as mock_open,
            patch("neuroflow.windows_launcher.runtime._wake_ubuntu", return_value=True),
        ):
            # ensure_payload_installed is mocked; still assert call path
            _ = windows_dir
            code = launch(_probe(WslState.UBUNTU_STOPPED), wait_on_process=False)

        assert code == 0
        mock_ensure.assert_called_once()
        mock_popen.assert_called_once()
        argv = mock_popen.call_args[0][1]
        assert "NEUROFLOW_SKIP_BROWSER=1" in argv
        assert _ELF in argv
        assert "--install" not in argv
        assert "--shutdown" not in argv
        mock_open.assert_called_once_with(PORTAL_URL)

    def test_health_timeout(self) -> None:
        paths = MagicMock()
        paths.linux_home = _HOME
        paths.linux_elf = _ELF
        proc = MagicMock()

        with (
            patch(
                "neuroflow.windows_launcher.runtime.probe_health",
                return_value=HealthResult(HealthStatus.DOWN),
            ),
            patch(
                "neuroflow.windows_launcher.runtime.ensure_payload_installed",
                return_value=paths,
            ),
            patch("neuroflow.windows_launcher.runtime.popen_wsl", return_value=proc),
            patch(
                "neuroflow.windows_launcher.runtime.wait_until_healthy",
                return_value=HealthResult(HealthStatus.DOWN, detail="timeout"),
            ),
            patch("neuroflow.windows_launcher.runtime.notify_user") as mock_notify,
        ):
            code = launch(_probe(), wait_on_process=False)
        assert code == 1
        proc.terminate.assert_called_once()
        mock_notify.assert_called_once()


class TestPackagedAppSkipBrowser:
    def test_skip_browser_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NEUROFLOW_SKIP_BROWSER", "1")
        from neuroflow.packaged_app import _skip_browser

        assert _skip_browser() is True

        monkeypatch.setenv("NEUROFLOW_SKIP_BROWSER", "yes")
        assert _skip_browser() is True

        monkeypatch.delenv("NEUROFLOW_SKIP_BROWSER", raising=False)
        assert _skip_browser() is False
