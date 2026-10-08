"""Tests for GitHub App client: env config, refusals, local bare-repo flow."""

import subprocess

import pytest

from healing.gitops.app import (
    ConfigError,
    GitHubAppConfig,
    LocalBareRepoClient,
    RefusedError,
    is_protected,
    reviews_valid,
)


def test_config_missing_env_fails_closed(monkeypatch) -> None:
    for v in ("GITHUB_APP_ID", "GITHUB_PRIVATE_KEY_PATH", "GITHUB_INSTALLATION_ID", "GITHUB_REPO"):
        monkeypatch.delenv(v, raising=False)
    with pytest.raises(ConfigError):
        GitHubAppConfig.from_env()


def test_config_reads_env_only(monkeypatch, tmp_path) -> None:
    key = tmp_path / "k.pem"
    key.write_text("fake-key")
    monkeypatch.setenv("GITHUB_APP_ID", "123")
    monkeypatch.setenv("GITHUB_PRIVATE_KEY_PATH", str(key))
    monkeypatch.setenv("GITHUB_INSTALLATION_ID", "456")
    monkeypatch.setenv("GITHUB_REPO", "o/r")
    cfg = GitHubAppConfig.from_env()
    assert (cfg.app_id, cfg.repo) == ("123", "o/r")


def test_refuses_main_and_protected() -> None:
    assert is_protected("main", ("main", "release/*"))
    assert is_protected("release/1", ("main", "release/*"))
    assert not is_protected("heal/login-7", ("main", "release/*"))


def test_self_approval_does_not_count_as_review() -> None:
    assert reviews_valid(["bot"], "bot") is False
    assert reviews_valid(["bot", "human"], "bot") is True
    assert reviews_valid([], "bot") is False


def make_repo(tmp_path):  # type: ignore[no-untyped-def]
    remote, work = tmp_path / "remote.git", tmp_path / "work"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True)
    subprocess.run(["git", "clone", str(remote), str(work)], check=True)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=work, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=work, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=work, check=True)
    (work / "README.md").write_text("hi\n")
    subprocess.run(["git", "add", "."], cwd=work, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=work, check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=work, check=True)
    return LocalBareRepoClient(str(remote), str(work))


def test_local_flow_branch_commit_pr_labels_comment(tmp_path) -> None:
    client = make_repo(tmp_path)
    client.create_branch("heal/login-7")
    sha = client.commit("heal/login-7", {"tests/t.py": "x = 1\n"}, "heal login")
    assert len(sha) == 40
    pr = client.open_pr("heal/login-7", "main", "Heal login", "body", ["auto-heal"])
    client.add_labels(pr, ["unverified"])
    client.comment(pr, "evidence")
    assert pr.labels == ["auto-heal", "unverified"]
    assert pr.comments == ["evidence"]


def test_local_refuses_protected_branch(tmp_path) -> None:
    client = make_repo(tmp_path)
    with pytest.raises(RefusedError):
        client.create_branch("main")
    with pytest.raises(RefusedError):
        client.open_pr("main", "main", "t", "b")
    # Protected patterns also cover release branches.
    assert is_protected("release/2.0", ("main", "release/*"))
