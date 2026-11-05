"""GitHub App client: branches, commits, PRs, labels, comments, reverts.

Secrets come only from environment (app id, private key path,
installation id). Tests use LocalBareRepoClient (git CLI on a local
bare repo); no real GitHub calls in unit tests. The bot refuses to
push to main or protected branches. Plain code; models only propose.
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

BRANCH_RE = re.compile(r"^heal/[a-z0-9][a-z0-9/_.-]{0,99}$")
REVERT_RE = re.compile(r"^revert/[a-z0-9][a-z0-9/_.-]{0,99}$")
HEAL_LABELS = ("auto-heal", "verified", "unverified", "needs-human")


class ConfigError(Exception):
    pass


class RefusedError(Exception):
    pass


@dataclass(frozen=True)
class GitHubAppConfig:
    app_id: str
    private_key_path: str
    installation_id: str
    repo: str
    protected_branches: tuple[str, ...] = ("main", "master", "release/*")

    @staticmethod
    def from_env() -> GitHubAppConfig:
        app_id = os.getenv("GITHUB_APP_ID", "")
        key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH", "")
        installation = os.getenv("GITHUB_INSTALLATION_ID", "")
        repo = os.getenv("GITHUB_REPO", "")
        missing = [
            n
            for n, v in (
                ("GITHUB_APP_ID", app_id),
                ("GITHUB_PRIVATE_KEY_PATH", key_path),
                ("GITHUB_INSTALLATION_ID", installation),
                ("GITHUB_REPO", repo),
            )
            if not v
        ]
        if missing:
            raise ConfigError(f"missing env: {', '.join(missing)}")
        protected = tuple(
            p.strip()
            for p in os.getenv("PROTECTED_BRANCHES", "main,master,release/*").split(",")
            if p.strip()
        )
        return GitHubAppConfig(app_id, key_path, installation, repo, protected)


def is_protected(branch: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatchcase(branch, p) for p in patterns)


def check_branch_name(branch: str) -> None:
    if not BRANCH_RE.match(branch):
        raise RefusedError(f"bad heal branch name: {branch!r}")


def check_revert_branch_name(branch: str) -> None:
    if not REVERT_RE.match(branch):
        raise RefusedError(f"bad revert branch name: {branch!r}")


def reviews_valid(approvals: list[str], trigger_identity: str) -> bool:
    """A PR approved only by the triggering identity does NOT count."""
    others = [a for a in approvals if a != trigger_identity]
    return len(others) >= 1


@dataclass
class PullRequest:
    number: int
    branch: str
    base: str
    title: str
    body: str
    labels: list[str] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)


class GitHubClient(ABC):
    @abstractmethod
    def create_branch(self, branch: str, base: str = "main") -> None:
        raise NotImplementedError

    @abstractmethod
    def commit(self, branch: str, files: dict[str, str], message: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def open_pr(
        self, branch: str, base: str, title: str, body: str, labels: list[str] | None = None
    ) -> PullRequest:
        raise NotImplementedError

    @abstractmethod
    def add_labels(self, pr: PullRequest, labels: list[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    def comment(self, pr: PullRequest, text: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def open_revert_pr(self, pr: PullRequest, reason: str) -> PullRequest:
        raise NotImplementedError


class PyGithubClient(GitHubClient):
    """Real client (never constructed in unit tests)."""

    def __init__(self, config: GitHubAppConfig | None = None) -> None:
        self.config = config or GitHubAppConfig.from_env()
        with open(self.config.private_key_path, encoding="utf-8") as f:
            key = f.read()  # key exists and is readable; never logged
        if not key.strip():
            raise ConfigError("private key file is empty")
        from github import Auth, Github  # type: ignore[import-not-found]

        app_auth = Auth.AppAuth(int(self.config.app_id), key)
        install_auth = app_auth.get_installation_auth(int(self.config.installation_id))
        self._repo = Github(auth=install_auth).get_repo(self.config.repo)

    def _guard(self, branch: str) -> None:
        check_branch_name(branch)
        if is_protected(branch, self.config.protected_branches):
            raise RefusedError(f"refusing protected branch: {branch}")

    def create_branch(self, branch: str, base: str = "main") -> None:
        self._guard(branch)
        if is_protected(base, self.config.protected_branches) and base != "main":
            raise RefusedError(f"refusing protected base: {base}")
        ref = self._repo.get_git_ref(f"heads/{base}")
        self._repo.create_git_ref(f"refs/heads/{branch}", ref.object.sha)

    def commit(self, branch: str, files: dict[str, str], message: str) -> str:
        self._guard(branch)
        ref = self._repo.get_git_ref(f"heads/{branch}")
        base = self._repo.get_git_commit(ref.object.sha)
        tree = self._repo.create_git_tree(
            [
                __import__("github").InputGitTreeElement(p, "100644", "blob", c)
                for p, c in files.items()
            ],
            base.tree,
        )
        commit = self._repo.get_git_commit(self._repo.create_git_commit(message, tree, [base]).sha)
        ref.edit(commit.sha)
        return commit.sha

    def open_pr(
        self, branch: str, base: str, title: str, body: str, labels: list[str] | None = None
    ) -> PullRequest:
        self._guard(branch)
        if is_protected(branch, self.config.protected_branches):
            raise RefusedError(f"refusing protected branch: {branch}")
        pr = self._repo.create_pull(base, branch, title=title, body=body)
        for label in labels or []:
            pr.add_to_labels(label)
        return PullRequest(pr.number, branch, base, title, body, list(labels or []))

    def add_labels(self, pr: PullRequest, labels: list[str]) -> None:
        self._repo.get_pull(pr.number).add_to_labels(*labels)
        pr.labels.extend(labels)

    def comment(self, pr: PullRequest, text: str) -> None:
        self._repo.get_pull(pr.number).create_issue_comment(text)
        pr.comments.append(text)

    def open_revert_pr(self, pr: PullRequest, reason: str) -> PullRequest:
        revert = f"revert/{pr.branch.replace('/', '-')}"
        if is_protected(revert, self.config.protected_branches):
            raise RefusedError(f"refusing protected branch: {revert}")
        rp = self._repo.create_pull(
            pr.base,
            pr.branch,
            title=f"Revert {pr.title}",
            body=f"Reverts #{pr.number}.\n\n{reason}",
        )
        return PullRequest(rp.number, revert, pr.base, rp.title, rp.body, ["revert"])


class LocalBareRepoClient(GitHubClient):
    """Test double: git CLI against a local bare repo. No network."""

    def __init__(
        self, remote: str, workdir: str, protected: tuple[str, ...] = ("main", "master")
    ) -> None:
        self.remote = remote
        self.workdir = workdir
        self.protected = protected
        self.prs: list[PullRequest] = []
        self._n = 0

    def _git(self, *args: str) -> str:
        out = subprocess.run(
            ["git", *args], cwd=self.workdir, check=True, capture_output=True, text=True
        )
        return out.stdout.strip()

    def _guard(self, branch: str) -> None:
        check_branch_name(branch)
        if is_protected(branch, self.protected):
            raise RefusedError(f"refusing protected branch: {branch}")

    def create_branch(self, branch: str, base: str = "main") -> None:
        self._guard(branch)
        self._git("checkout", "-B", branch, base)

    def commit(self, branch: str, files: dict[str, str], message: str) -> str:
        self._guard(branch)
        self._git("checkout", branch)
        for path, content in files.items():
            full = os.path.join(self.workdir, path)
            os.makedirs(os.path.dirname(full) or self.workdir, exist_ok=True)
            with open(full, "w", encoding="utf-8") as f:
                f.write(content)
            self._git("add", path)
        self._git(
            "-c",
            "user.email=heal-bot@example.com",
            "-c",
            "user.name=heal-bot",
            "commit",
            "-m",
            message,
        )
        sha = self._git("rev-parse", "HEAD")
        self._git("push", "origin", branch)
        return sha

    def open_pr(
        self, branch: str, base: str, title: str, body: str, labels: list[str] | None = None
    ) -> PullRequest:
        self._guard(branch)
        self._n += 1
        pr = PullRequest(self._n, branch, base, title, body, list(labels or []))
        self.prs.append(pr)
        return pr

    def add_labels(self, pr: PullRequest, labels: list[str]) -> None:
        pr.labels.extend(labels)

    def comment(self, pr: PullRequest, text: str) -> None:
        pr.comments.append(text)

    def open_revert_pr(self, pr: PullRequest, reason: str) -> PullRequest:
        revert = f"revert/{pr.branch.replace('/', '-')}"
        check_revert_branch_name(revert)
        if is_protected(revert, self.protected):
            raise RefusedError(f"refusing protected branch: {revert}")
        self._git("checkout", "-B", revert, pr.base)
        self._git("checkout", revert)
        self._git("revert", "--no-commit", f"origin/{pr.branch}")
        self._git(
            "-c",
            "user.email=heal-bot@example.com",
            "-c",
            "user.name=heal-bot",
            "commit",
            "-m",
            f"Revert {pr.title}",
        )
        self._git("push", "origin", revert)
        rp = PullRequest(
            self._n + 1,
            revert,
            pr.base,
            f"Revert {pr.title}",
            f"Reverts #{pr.number}.\n\n{reason}",
            ["revert"],
        )
        self._n += 1
        self.prs.append(rp)
        return rp
