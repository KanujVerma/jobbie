"""Candidate fact proposals with immutable provenance and explicit owner decisions."""
from __future__ import annotations

import re

from .discord import Command, Interaction
from .storage import PrivateStore, Record

MAX_PROPOSALS = 250
SKILLS_LABEL = re.compile(r"^\s*(?:technical\s+skills|skills|languages|frameworks|tools|technologies)\s*:\s*", re.I)
PROTECTED = re.compile(r"\b(?:citizenship|citizen|immigration|visa|work authorization|sponsorship|"
                       r"residency|ethnicity|disability|religion|marital status)\b", re.I)
METRIC = re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|percent|thousand|million|users|customers|requests)\b|\d+%")
EXPERIENCE = re.compile(r"^(?:built|developed|created|implemented|contributed|maintained|worked|designed)\b", re.I)
EDUCATION = re.compile(r"\b(?:bachelor|master|degree|graduat(?:ed|ion|ing)|university)\b", re.I)
DATE = re.compile(r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
                  r"aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(19|20)\d{2}\b"
                  r"|\b(19|20)\d{2}[-/]\d{1,2}\b", re.I)
EMPLOYER = re.compile(r"\b(?:employer|employment at|worked at|engineer at|employed by)\b", re.I)
PROTECTED_KINDS = (("protected", PROTECTED), ("metric", METRIC), ("education", EDUCATION),
                   ("dates", DATE), ("employer", EMPLOYER))



class Evidence:
    def __init__(self, vault: PrivateStore):
        self.vault = vault

    def propose_resume(self, version_id: str) -> list[Record]:
        version = self.vault.resume(version_id)
        if version is None:
            raise ValueError("Owner resume version unavailable")
        proposals = []
        for line in re.finditer(r"[^\r\n]+", version.text):
            value = line.group().strip()
            if not value or len(value) > 800:
                continue
            start = line.start() + len(line.group()) - len(line.group().lstrip())
            protected_kind = next((kind for kind, pattern in PROTECTED_KINDS if pattern.search(value)), None)
            if protected_kind:
                spans = [(protected_kind, start, start + len(value), value)]
            elif label := SKILLS_LABEL.match(value):
                spans = []
                for item in re.finditer(r"[^,;|]+", value[label.end():]):
                    token = item.group().strip()
                    if not 1 <= len(token) <= 50 or not re.fullmatch(r"[\w .#+/()-]+", token):
                        continue
                    token_start = start + label.end() + item.start() + len(item.group()) - len(item.group().lstrip())
                    spans.append(("skill", token_start, token_start + len(token), token.casefold()))
            elif EXPERIENCE.match(value):
                spans = [("experience", start, start + len(value), value)]
            else:
                continue
            for kind, first, last, claim in spans:
                source = {"type": "resume", "version_id": version.id, "sha256": version.sha256,
                          "start": first, "end": last, "excerpt": version.text[first:last]}
                # Free-form experience lines may also contain employer names or dates.
                protected = kind != "skill"
                proposal = {"kind": kind, "value": "Protected source statement" if protected else claim,
                            "privacy": "owner-only", "source": source,
                            "protected": protected, "stage": "self-reported"}
                proposals.append(self.vault.put("candidate_fact", proposal, f"resume:{version.id}:{first}:{last}",
                                                parent_id=version.id, requires=("resume_version", version.id)))
                if len(proposals) >= MAX_PROPOSALS:
                    return proposals
        return proposals

    def _source_available(self, record: Record, resumes: dict) -> bool:
        source = record.data["source"]
        if source["type"] == "resume":
            key = source["version_id"]
            if key not in resumes:
                resumes[key] = self.vault.resume(key)
            version = resumes[key]
            return (version is not None and version.sha256 == source["sha256"]
                    and version.text[source["start"]:source["end"]] == source["excerpt"])
        if source["type"] == "github":
            return repository_allowed(self.vault, source["approval_id"])
        return False

    def decide(self, fact_id: str, action: str, request_id: str, *,
               confirm_protected: bool = False, replacement_id: str | None = None) -> Record:
        if action not in {"confirm", "revoke", "correct"}:
            raise ValueError("Unsupported fact decision")
        fact = self.vault.get("candidate_fact", fact_id)
        if fact is None:
            raise ValueError("Candidate fact unavailable")
        if action == "correct":
            replacement = self.vault.get("candidate_fact", replacement_id)
            if replacement is None or replacement.id == fact.id or replacement.data["kind"] != fact.data["kind"]:
                raise ValueError("Correction requires a distinct source-backed proposal of the same kind")
            chosen = replacement
        else:
            if replacement_id is not None:
                raise ValueError("Unexpected replacement")
            chosen = fact
        if action != "revoke":
            if not self._source_available(chosen, {}):
                raise ValueError("Candidate fact source unavailable")
            if chosen.data["protected"] and confirm_protected is not True:
                raise ValueError("Protected claim requires explicit confirmation")
        decision = {"fact_id": fact_id, "action": action, "replacement_id": replacement_id}
        return self.vault.put("fact_decision", decision, request_id)

    def inspect(self, fact_id: str) -> dict:
        record = self.vault.get("candidate_fact", fact_id)
        if record is None or not self._source_available(record, {}):
            raise ValueError("Candidate fact unavailable")
        payload = dict(record.data)
        if payload["protected"]:
            payload["source"] = {key: value for key, value in payload["source"].items() if key != "excerpt"}
        return {"id": record.id, **payload}

    def active(self, *, include_protected: bool = False) -> list[Record]:
        states: dict[str, bool] = {}
        for row in self.vault.records("fact_decision", limit=10_000):
            event = row.data
            states.setdefault(event["fact_id"], event["action"] == "confirm")
            if event["action"] == "correct":
                states.setdefault(event["replacement_id"], True)
        result, resumes = [], {}
        for fact_id, confirmed in states.items():
            if not confirmed:
                continue
            record = self.vault.get("candidate_fact", fact_id)
            if (record is not None and (include_protected or not record.data["protected"])
                    and self._source_available(record, resumes)):
                result.append(record)
        return result


def repository_allowed(vault: PrivateStore, approval_id: str) -> bool:
    return (vault.get("repo_approval", approval_id) is not None
            and not vault.records("repo_revocation", parent_id=approval_id, limit=1))


def evidence_commands(vault: PrivateStore) -> tuple[Command, ...]:
    def propose(request: Interaction) -> str:
        if request.owner != vault.owner:
            return "Resume evidence unavailable."
        try:
            proposals = Evidence(vault).propose_resume(request.options["version"])
        except ValueError:
            return "Resume version unavailable."
        return f"Created or recovered {len(proposals)} proposals. Review them in the private owner console."

    def approved(request: Interaction) -> str:
        if request.owner != vault.owner:
            return "Repositories unavailable."
        rows = [row for row in vault.records("repo_approval") if repository_allowed(vault, row.id)]
        public_names = [row.data["repository"] for row in rows if row.data["visibility"] == "public"]
        private_count = len(rows) - len(public_names)
        return "\n".join([f"Approved private repositories: {private_count}", *public_names])[:1800]

    return (
        Command(("resume", "propose"), "Extract private fact proposals", propose, ("version",), deferred=True),
        Command(("github", "repos"), "Show owner-approved GitHub repositories", approved),
    )
