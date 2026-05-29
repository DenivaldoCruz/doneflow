from pathlib import Path


def test_ci_workflow_creates_release_tag_only_after_push_to_main() -> None:
    """Ensure CI creates release tags only for merges pushed to main."""
    workflow = Path(".github/workflows/ci.yml")
    content = workflow.read_text(encoding="utf-8")

    assert "permissions:" in content
    assert "contents: write" in content
    assert "fetch-depth: 0" in content
    assert "Generate release tag name" in content
    assert "Create release tag" in content
    assert "github.event_name == 'push' && github.ref == 'refs/heads/main'" in content
    assert "release-$(date -u +'%Y%m%d%H%M%S')-${SHORT_SHA}" in content
    assert 'git push origin "${TAG_NAME}"' in content
