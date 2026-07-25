"""Tool registry tests."""

from neuroflow.tools.registry import get_tool, list_tools


def test_registry_lists_freesurfer() -> None:
    tools = list_tools()
    assert any(t.id == "freesurfer" for t in tools)


def test_portal_only_hides_ants() -> None:
    portal = list_tools(portal_only=True)
    ids = {t.id for t in portal}
    assert ids == {"freesurfer", "fsl"}


def test_get_unknown_tool() -> None:
    assert get_tool("nonexistent") is None
