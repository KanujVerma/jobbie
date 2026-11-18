"""Approved read-only GitHub commit and deployment evidence."""
from __future__ import annotations

from datetime import datetime, timezone
import http.client
import json
from pathlib import PurePosixPath
import re
from urllib.parse import urlencode

from .evidence import repository_allowed
from .storage import PrivateStore, Record

REPO = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}")
LOGIN = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}")
COMMIT = re.compile(r"[a-f0-9]{40}")
CODE_EXTENSIONS = {".py", ".rs", ".go", ".java", ".kt", ".swift", ".js", ".jsx", ".ts", ".tsx",
                   ".rb", ".c", ".cpp", ".h", ".cs", ".sql", ".sh"}
MAX_RESPONSE = 3 * 1024 * 1024


def repository_spec(value: dict) -> dict:
    keys = {"repository", "repository_id", "author", "author_id", "visibility", "stage"}
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("Repository approval fields are invalid")
    repo, login = value["repository"], value["author"]
    if not isinstance(repo, str) or not REPO.fullmatch(repo) or not isinstance(login, str) or not LOGIN.fullmatch(login):
        raise ValueError("Repository or author identifier is invalid")
    for key in ("repository_id", "author_id"):
        if type(value[key]) is not int or value[key] <= 0:
            raise ValueError("GitHub numeric identity is required")
    if value["visibility"] not in ("private", "public") or value["stage"] not in ("prototype", "unknown"):
        raise ValueError("Approval must declare privacy and a conservative stage")
    return value


class GitHubRead:
    def __init__(self, token: str | None):
        if token is not None and not re.fullmatch(r"[A-Za-z0-9_.-]{10,300}", token):
            raise ValueError("GitHub credential is invalid")
        self.token = token

    def __call__(self, path: str):
        if not path.startswith("/repos/"):
            raise ValueError("Invalid GitHub evidence endpoint")
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "Jobbie-owner-evidence"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        conn = http.client.HTTPSConnection("api.github.com", timeout=4)
        try:
            conn.request("GET", path, headers=headers)
            response = conn.getresponse()
            if response.status != 200:
                raise ValueError("GitHub evidence is unavailable")
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise ValueError("GitHub response exceeds evidence limit")
            return json.loads(raw)
        except (OSError, http.client.HTTPException, UnicodeError, json.JSONDecodeError, RecursionError):
            raise ValueError("GitHub evidence could not be read") from None
        finally:
            conn.close()


def _code_path(value: object) -> bool:
    if not isinstance(value, str) or not 1 <= len(value) <= 256 or re.search(r"[\x00-\x1f\x7f]", value):
        return False
    path = PurePosixPath(value)
    return (path.is_absolute() is False and ".." not in path.parts
            and path.suffix.casefold() in CODE_EXTENSIONS
            and not any(part.casefold() in {"docs", "vendor", "node_modules"} for part in path.parts))


class GitHubEvidence:
    def __init__(self, vault: PrivateStore, read):
        self.vault, self.read = vault, read

    def approve(self, data: dict, request_id: str, *, confirmed: bool) -> Record:
        if confirmed is not True:
            raise ValueError("Owner repository approval is required")
        return self.vault.put("repo_approval", repository_spec(data), request_id)

    def revoke(self, approval_id: str, request_id: str, *, confirmed: bool) -> Record:
        if confirmed is not True or self.vault.get("repo_approval", approval_id) is None:
            raise ValueError("Owner repository approval is unavailable")
        return self.vault.put("repo_revocation", {"approval_id": approval_id}, request_id, parent_id=approval_id)

    def _get(self, approval_id: str, path: str):
        if not repository_allowed(self.vault, approval_id):
            raise ValueError("Owner repository approval is unavailable")
        return self.read(path)

    def propose(self, approval_id: str, commit_sha: str, deployment_id: int | None = None) -> Record:
        if not isinstance(commit_sha, str) or not COMMIT.fullmatch(commit_sha):
            raise ValueError("An immutable commit SHA is required")
        approval = self.vault.get("repo_approval", approval_id)
        if approval is None or not repository_allowed(self.vault, approval_id):
            raise ValueError("Owner repository approval is unavailable")
        spec = approval.data
        name = spec["repository"]
        base = f"/repos/{name}"
        stable_id = f"github:{approval_id}:{commit_sha}:{deployment_id or 'commit'}"
        previous = self.vault.records("candidate_fact", parent_id=stable_id, limit=1)
        if previous:
            return previous[0]

        repo = self._get(approval_id, base)
        if (not isinstance(repo, dict) or type(repo.get("id")) is not int
                or repo["id"] != spec["repository_id"]
                or not isinstance(repo.get("full_name"), str) or repo["full_name"].casefold() != name.casefold()
                or repo.get("private") is not (spec["visibility"] == "private")):
            raise ValueError("Approved GitHub repository identity changed")
        data = self._get(approval_id, f"{base}/commits/{commit_sha}?per_page=100")
        author = data.get("author") if isinstance(data, dict) else None
        files = data.get("files") if isinstance(data, dict) else None
        if (not isinstance(author, dict) or type(author.get("id")) is not int or author["id"] != spec["author_id"]
                or not isinstance(author.get("login"), str) or author["login"].casefold() != spec["author"].casefold()
                or data.get("sha") != commit_sha or not isinstance(files, list)):
            raise ValueError("Commit authorship evidence is unavailable")
        code_paths = sorted({row["filename"] for row in files[:100] if isinstance(row, dict)
                             and row.get("status") in ("added", "modified", "renamed")
                             and _code_path(row.get("filename"))})
        if not code_paths:
            raise ValueError("Commit has no corroborating code change")
        commit = data.get("commit")
        verification = commit.get("verification", {}) if isinstance(commit, dict) else {}
        source = {"type": "github", "approval_id": approval_id, "commit": commit_sha, "author": author["login"],
                  "author_id": author["id"], "code_paths": code_paths, "repository_id": repo["id"],
                  "signature_verified": isinstance(verification, dict) and verification.get("verified") is True,
                  "url": f"https://github.com/{name}/commit/{commit_sha}",
                  "retrieved": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        stage = spec["stage"]
        if deployment_id is not None:
            source["deployment"] = self._deployment(approval_id, base, commit_sha, deployment_id)
            stage = "production"
        record = {"kind": "project_commit", "value": "GitHub attributes this code change to the approved account.",
                  "privacy": "owner-only", "protected": False, "source": source, "stage": stage}
        if not repository_allowed(self.vault, approval_id):
            raise ValueError("Owner repository approval was revoked")
        # The first observed timestamp remains the immutable evidence time on repeat.
        existing = self.vault.records("candidate_fact", parent_id=stable_id, limit=1)
        if existing:
            return existing[0]
        try:
            return self.vault.put("candidate_fact", record, stable_id, parent_id=stable_id)
        except ValueError:
            existing = self.vault.records("candidate_fact", parent_id=stable_id, limit=1)
            if existing:
                return existing[0]
            raise

    def _deployment(self, approval_id: str, base: str, commit: str, deployment_id: int) -> dict:
        if type(deployment_id) is not int or deployment_id <= 0:
            raise ValueError("Invalid deployment identity")
        deployment = self._get(approval_id, f"{base}/deployments/{deployment_id}")
        status_query = urlencode({"per_page": 1})
        statuses = self._get(approval_id, f"{base}/deployments/{deployment_id}/statuses?{status_query}")
        status = statuses[0] if isinstance(statuses, list) and statuses else None
        if (not isinstance(deployment, dict) or deployment.get("id") != deployment_id
                or deployment.get("sha") != commit or deployment.get("environment") != "production"
                or deployment.get("production_environment") is not True
                or deployment.get("transient_environment") is not False
                or not isinstance(status, dict) or status.get("state") != "success"
                or status.get("environment") != "production" or type(status.get("id")) is not int):
            raise ValueError("Pinned successful production deployment evidence is unavailable")
        return {"id": deployment_id, "status_id": status["id"], "environment": "production",
                "production_environment": True, "transient_environment": False}
