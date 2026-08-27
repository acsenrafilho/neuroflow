"""Tests for the Windows WSL launcher detection gate."""

from __future__ import annotations

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest
from neuroflow.windows_launcher.app import main as launcher_main
from neuroflow.windows_launcher.detect import (
    DisallowedWslArgumentError,
    decode_wsl_output,
    probe_wsl,
    validate_wsl_argv,
)
from neuroflow.windows_launcher.types import WSL_INSTALL_URL, WslState

_WSL_EXE = r"C:\Windows\System32\wsl.exe"
_FIND_WSL = "neuroflow.windows_launcher.detect._find_wsl_exe"
_RUN_WSL = "neuroflow.windows_launcher.detect._run_wsl"


def _utf16_le(text: str, *, bom: bool = True) -> bytes:
    encoded = text.encode("utf-16-le")
    return b"\xff\xfe" + encoded if bom else encoded


def _make_list_output(*lines: str, encoding: str = "utf16_bom") -> bytes:
    body = "\r\n".join(lines) + "\r\n"
    if encoding == "utf16_bom":
        return _utf16_le(body, bom=True)
    if encoding == "utf16_no_bom":
        return _utf16_le(body, bom=False)
    return body.encode("utf-8")


def _completed(stdout: bytes, *, returncode: int = 0) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess(
        args=["wsl"],
        returncode=returncode,
        stdout=stdout,
        stderr=b"",
    )


class TestDecodeWslOutput:
    def test_utf16_le_with_bom(self) -> None:
        raw = _utf16_le("  NAME   STATE   VERSION\r\n* Ubuntu Running 2\r\n")
        assert "Ubuntu Running 2" in decode_wsl_output(raw)

    def test_utf16_le_without_bom(self) -> None:
        raw = _utf16_le("* Ubuntu Running 2\r\n", bom=False)
        assert "Ubuntu Running 2" in decode_wsl_output(raw)

    def test_utf8(self) -> None:
        raw = b"  NAME   STATE   VERSION\n* Ubuntu Running 2\n"
        assert decode_wsl_output(raw) == "NAME   STATE   VERSION\n* Ubuntu Running 2"


class TestValidateWslArgv:
    def test_rejects_install(self) -> None:
        with pytest.raises(DisallowedWslArgumentError, match="--install"):
            validate_wsl_argv(["wsl.exe", "--install"])

    def test_allows_list_and_probe(self) -> None:
        validate_wsl_argv(["wsl.exe", "-l", "-v"])
        validate_wsl_argv(["wsl.exe", "-d", "Ubuntu", "--", "true"])


class TestProbeWsl:
    def test_wsl_missing_when_exe_not_found(self) -> None:
        with patch("neuroflow.windows_launcher.detect._find_wsl_exe", return_value=None):
            probe = probe_wsl()
        assert probe.state == WslState.WSL_MISSING
        assert probe.wsl_exe is None
        assert probe.microsoft_url == WSL_INSTALL_URL

    def test_wsl_present_no_ubuntu(self) -> None:
        listing = _make_list_output(
            "  NAME      STATE           VERSION",
            "* Debian    Running         2",
        )
        with (
            patch(_FIND_WSL, return_value=_WSL_EXE),
            patch(
                _RUN_WSL,
                return_value=_completed(listing),
            ),
        ):
            probe = probe_wsl()
        assert probe.state == WslState.WSL_PRESENT_NO_UBUNTU

    def test_ubuntu_stopped_does_not_probe_distro(self) -> None:
        listing = _make_list_output(
            "  NAME      STATE           VERSION",
            "* Ubuntu    Stopped         2",
        )
        with (
            patch(_FIND_WSL, return_value=_WSL_EXE),
            patch(
                _RUN_WSL,
                return_value=_completed(listing),
            ) as mock_run,
        ):
            probe = probe_wsl()
        assert probe.state == WslState.UBUNTU_STOPPED
        assert probe.distro == "Ubuntu"
        assert probe.wsl_version == 2
        assert mock_run.call_count == 1
        assert mock_run.call_args[0][1] == ["-l", "-v"]

    def test_ubuntu_running_when_true_succeeds(self) -> None:
        listing = _make_list_output(
            "  NAME      STATE           VERSION",
            "* Ubuntu    Running         2",
        )
        true_ok = subprocess.CompletedProcess(
            args=["wsl", "-d", "Ubuntu", "--", "true"],
            returncode=0,
            stdout=b"",
            stderr=b"",
        )

        def side_effect(_wsl_exe: str, args: list[str]) -> subprocess.CompletedProcess[bytes]:
            if args == ["-l", "-v"]:
                return _completed(listing)
            if args == ["-d", "Ubuntu", "--", "true"]:
                return true_ok
            raise AssertionError(f"unexpected args: {args}")

        with (
            patch(_FIND_WSL, return_value=_WSL_EXE),
            patch(_RUN_WSL, side_effect=side_effect),
        ):
            probe = probe_wsl()
        assert probe.state == WslState.UBUNTU_RUNNING

    def test_ubuntu_needs_user_setup_when_true_fails(self) -> None:
        listing = _make_list_output(
            "  NAME      STATE           VERSION",
            "* Ubuntu    Running         2",
        )
        true_fail = subprocess.CompletedProcess(
            args=["wsl", "-d", "Ubuntu", "--", "true"],
            returncode=1,
            stdout=b"",
            stderr=b"setup required",
        )

        def side_effect(_wsl_exe: str, args: list[str]) -> subprocess.CompletedProcess[bytes]:
            if args == ["-l", "-v"]:
                return _completed(listing)
            if args == ["-d", "Ubuntu", "--", "true"]:
                return true_fail
            raise AssertionError(f"unexpected args: {args}")

        with (
            patch(_FIND_WSL, return_value=_WSL_EXE),
            patch(_RUN_WSL, side_effect=side_effect),
        ):
            probe = probe_wsl()
        assert probe.state == WslState.UBUNTU_NEEDS_USER_SETUP

    def test_wsl_missing_on_not_installed_message(self) -> None:
        listing = b"The Windows Subsystem for Linux is not installed."
        with (
            patch(_FIND_WSL, return_value=_WSL_EXE),
            patch(
                _RUN_WSL,
                return_value=_completed(listing, returncode=1),
            ),
        ):
            probe = probe_wsl()
        assert probe.state == WslState.WSL_MISSING

    def test_does_not_accept_ubuntu_22_04(self) -> None:
        listing = _make_list_output(
            "  NAME            STATE           VERSION",
            "* Ubuntu-22.04    Running         2",
        )
        with (
            patch(_FIND_WSL, return_value=_WSL_EXE),
            patch(
                _RUN_WSL,
                return_value=_completed(listing),
            ),
        ):
            probe = probe_wsl()
        assert probe.state == WslState.WSL_PRESENT_NO_UBUNTU


class TestLauncherCli:
    def test_status_prints_state(self, capsys: pytest.CaptureFixture[str]) -> None:
        probe = MagicMock()
        probe.state = WslState.WSL_MISSING
        probe.message = "Install WSL."
        probe.microsoft_url = WSL_INSTALL_URL
        with patch("neuroflow.windows_launcher.app.probe_wsl", return_value=probe):
            code = launcher_main(["--status"])
        captured = capsys.readouterr().out
        assert code == 0
        assert "state=wsl_missing" in captured
        assert WSL_INSTALL_URL in captured

    def test_open_wsl_docs(self) -> None:
        with patch("neuroflow.windows_launcher.app.webbrowser.open") as mock_open:
            code = launcher_main(["--open-wsl-docs"])
        assert code == 0
        mock_open.assert_called_once_with(WSL_INSTALL_URL)

    def test_default_guide_on_non_windows(self, capsys: pytest.CaptureFixture[str]) -> None:
        probe = MagicMock()
        probe.state = WslState.WSL_MISSING
        probe.message = "Install WSL."
        probe.microsoft_url = WSL_INSTALL_URL
        with (
            patch("neuroflow.windows_launcher.app.probe_wsl", return_value=probe),
            patch("neuroflow.windows_launcher.notify.sys.platform", "linux"),
            patch("neuroflow.windows_launcher.app.notify_user") as mock_notify,
        ):
            code = launcher_main([])
        assert code == 0
        mock_notify.assert_called_once()
        assert "Install WSL." in capsys.readouterr().out

    def test_default_ready_state_no_messagebox(self) -> None:
        probe = MagicMock()
        probe.state = WslState.UBUNTU_RUNNING
        probe.message = "Ready."
        probe.microsoft_url = WSL_INSTALL_URL
        with (
            patch("neuroflow.windows_launcher.app.probe_wsl", return_value=probe),
            patch("neuroflow.windows_launcher.app.notify_user") as mock_notify,
        ):
            code = launcher_main([])
        assert code == 0
        mock_notify.assert_not_called()

    def test_never_imports_windll_on_non_windows(self) -> None:
        assert sys.platform != "win32"
        import neuroflow.windows_launcher.notify as notify_mod

        assert "windll" not in dir(notify_mod)
