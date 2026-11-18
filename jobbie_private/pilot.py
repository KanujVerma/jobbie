"""Prepare and supervise a Jobbie pilot without altering host or Funnel settings."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import getpass
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import re
import secrets
import signal
import stat
import subprocess
import sys
import time
import zipfile

from cryptography.fernet import Fernet
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from src.catalogue import Catalogue
from src.models import Job

from .discord import ReplyUnavailable, TOKEN, snowflake
from .pilot_http import listener
from .profile import DownloadRoute
from .server import InteractionApp, edit_original, endpoint_from_env
from .storage import PrivateStore

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PORT, DOWNLOAD_PORT = 18765, 18766
FIXTURES = ("synthetic-catalogue.sqlite", "synthetic-resume.pdf", "synthetic-resume.docx")
OWNER_MODES = {"profile-set", "facts-propose", "fact-inspect", "fact-decide", "resume-link",
               "resume-delete", "application-open", "application-status", "backup"}


def report(event: str, **fields):
    print(json.dumps({"event": event, **fields}, sort_keys=True), flush=True)


def private_root(raw: Path) -> Path:
    root = raw.expanduser().absolute()
    meta = root.lstat()
    if (root.resolve().is_relative_to(ROOT) or not stat.S_ISDIR(meta.st_mode)
            or meta.st_uid != os.getuid() or meta.st_mode & 0o077):
        raise ValueError("Pilot needs a dedicated owner-only directory outside Git")
    return root.resolve()


def write_new(path: Path, data: bytes) -> None:
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), "wb") as output:
        output.write(data)


def read_settings(root: Path, name: str) -> dict:
    path = root / name
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as source:
        meta = os.fstat(source.fileno())
        if not stat.S_ISREG(meta.st_mode) or meta.st_uid != os.getuid() or meta.st_mode & 0o077:
            raise ValueError("Unsafe pilot settings permissions")
        data = json.loads(source.read(4096))
    if not isinstance(data, dict):
        raise ValueError("Invalid pilot settings")
    return data


def seed_catalogue(path: Path) -> None:
    now = datetime.now(timezone.utc)
    job = Job(id="pilot-001", company="Synthetic Pilot Employer", title="Software Engineer I",
              location="San Francisco, CA", department="Engineering", category="Software",
              url="https://example.com/jobs/jobbie-pilot", source_platform="pilot",
              posted_at=None, detected_at=now, raw_text="Full-time software engineer. 0-2 years. Python and SQL.",
              role_type="entry-level", priority="normal", matched_keywords=(), source_job_id="pilot-001")
    with Catalogue(path, create=True) as catalogue:
        catalogue.start_run("local-pilot-fixture", now, origin="fixture")
        catalogue.observe_scan("local-pilot-fixture", "pilot-only", {"name": job.company, "enabled": True},
                               [job], status="complete", observed_at=now)


def sample_documents(root: Path) -> None:
    word = io.BytesIO()
    with zipfile.ZipFile(word, "w") as archive:
        archive.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        archive.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        archive.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Skills: Python</w:t></w:r></w:p></w:body></w:document>')
    write_new(root / "synthetic-resume.docx", word.getvalue())
    writer = PdfWriter()
    page = writer.add_blank_page(200, 200)
    name = NameObject
    font = DictionaryObject({name("/Type"): name("/Font"), name("/Subtype"): name("/Type1"),
                             name("/BaseFont"): name("/Helvetica")})
    page[name("/Resources")] = DictionaryObject({name("/Font"): DictionaryObject({name("/F1"): font})})
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 10 100 Td (Skills: Python) Tj ET")
    page[name("/Contents")] = writer._add_object(stream)
    rendered = io.BytesIO()
    writer.write(rendered)
    write_new(root / "synthetic-resume.pdf", rendered.getvalue())


def initialize(directory: Path) -> Path:
    directory = directory.expanduser().absolute()
    if directory.resolve().is_relative_to(ROOT):
        raise ValueError("Pilot directory must be outside the Git checkout")
    directory.mkdir(mode=0o700)
    root = private_root(directory)
    write_new(root / "credentials.json", json.dumps({
        "key": Fernet.generate_key().decode(), "download": secrets.token_urlsafe(36),
    }).encode())
    seed_catalogue(root / "synthetic-catalogue.sqlite")
    (root / "synthetic-catalogue.sqlite").chmod(0o400)
    sample_documents(root)
    write_new(root / "fixtures.json", json.dumps({
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in FIXTURES
    }).encode())
    return root


def identity(root: Path, fields: dict | None = None) -> dict:
    if fields is None:
        fields = read_settings(root, "discord.json")
    if (set(fields) != {"application", "public_key", "owner", "guild"}
            or not all(snowflake(fields[key]) for key in ("application", "owner", "guild"))
            or not isinstance(fields["public_key"], str)
            or not re.fullmatch(r"[0-9a-fA-F]{64}", fields["public_key"])):
        raise ValueError("Invalid private Discord identity")
    return fields


def runtime_env(root: Path, fields: dict | None = None) -> dict[str, str]:
    ids = identity(root, fields)
    private = read_settings(root, "credentials.json")
    pins = read_settings(root, "fixtures.json")
    for name in FIXTURES:
        path = root / name
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077
                or info.st_size > 8 * 1024 * 1024
                or hashlib.sha256(path.read_bytes()).hexdigest() != pins.get(name)):
            raise ValueError("Synthetic pilot fixture did not match its pin")
    allowed_uploads = {
        name: {"size": (root / name).stat().st_size, "sha256": pins[name]}
        for name in FIXTURES[1:]
    }
    return {
        "PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1", "PYTHON_DOTENV_DISABLED": "1",
        "JOBBIE_MAC_PARSER_SANDBOX": "1",
        "JOBBIE_PILOT_UPLOADS": json.dumps(allowed_uploads),
        "JOBBIE_PRIVATE_DB": str(root / "private.sqlite"),
        "JOBBIE_PRIVATE_KEY": private["key"],
        "JOBBIE_PRIVATE_DOWNLOAD_TOKEN": private["download"],
        "JOBBIE_DISCORD_APPLICATION_ID": ids["application"],
        "JOBBIE_DISCORD_PUBLIC_KEY": ids["public_key"],
        "JOBBIE_DISCORD_OWNER_ID": ids["owner"],
        "JOBBIE_DISCORD_GUILD_ID": ids["guild"],
        "JOBBIE_P3_CATALOGUE_PATH": str(root / "synthetic-catalogue.sqlite"),
    }


def verify_parser(root: Path) -> None:
    from .resume import DOCX, PDF, parse_resume
    for ext, kind in (("pdf", PDF), ("docx", DOCX)):
        if parse_resume(kind, (root / f"synthetic-resume.{ext}").read_bytes()) != "Skills: Python":
            raise ValueError("Pilot parser could not read the expected synthetic content")


def bounded_reply(application: str, token: str, reply: dict, expires: int) -> None:
    started = time.monotonic()
    payload = {"application": application, "token": token, "reply": reply, "expires": expires}
    try:
        result = subprocess.run([sys.executable, "-m", "jobbie_private.pilot", "_reply"], cwd=ROOT,
                                input=json.dumps(payload).encode(), env={"PATH": os.defpath},
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        report("discord_delivery", outcome="uncertain", ms=round(1000 * (time.monotonic() - started), 1))
        raise OSError("Discord delivery outcome uncertain") from None
    outcome = {0: "accepted", 3: "original_unavailable"}.get(result.returncode, "uncertain")
    report("discord_delivery", outcome=outcome, ms=round(1000 * (time.monotonic() - started), 1))
    if result.returncode == 3:
        raise ReplyUnavailable("Original interaction response unavailable")
    if result.returncode != 0:
        raise OSError("Discord delivery outcome uncertain")


def local_prompt(prompt: str) -> str:
    if not sys.stdin.isatty():
        raise ValueError("Use a local terminal for private setup")
    return getpass.getpass(prompt)


def register_commands(root: Path, env: dict[str, str]) -> None:
    fields = identity(root)
    token = local_prompt("Dedicated Discord pilot bot token (not stored): ")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{30,300}", token):
        raise ValueError("Pilot bot token is invalid")
    manifest = subprocess.check_output([sys.executable, "-m", "jobbie_private.server", "commands"],
                                       cwd=ROOT, env=env, timeout=10)
    desired = json.loads(manifest)
    path = f"/api/v10/applications/{fields['application']}/guilds/{fields['guild']}/commands"
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}

    def request(method, body=None):
        with_context = http.client.HTTPSConnection("discord.com", timeout=3)
        try:
            with_context.request(method, path, body=body, headers=headers)
            response = with_context.getresponse()
            if response.status != 200:
                raise ValueError(f"Discord pilot command API returned HTTP {response.status}")
            data = response.read(65_537)
        finally:
            with_context.close()
        if len(data) > 65_536:
            raise ValueError("Discord command response exceeded limit")
        value = json.loads(data)
        if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
            raise ValueError("Discord command response was invalid")
        return value

    current = request("GET")
    if current:
        # A dedicated pilot guild starts empty. Preserve any existing commands.
        raise ValueError("Pilot guild already has application commands")
    registered = request("PUT", manifest)
    if (len(registered) != len(desired) or
            {row.get("name") for row in registered} != {row["name"] for row in desired}):
        raise ValueError("Discord command receipt did not match the requested manifest")
    report("pilot_commands_registered", count=len(registered))


def child(role: str, port: int, *, offline: bool):
    vault = PrivateStore(Path(os.environ["JOBBIE_PRIVATE_DB"]), os.environ["JOBBIE_PRIVATE_KEY"].encode(),
                         os.environ["JOBBIE_DISCORD_OWNER_ID"])
    endpoint = endpoint_from_env(vault)
    if role != "worker":
        download = DownloadRoute(vault, os.environ["JOBBIE_PRIVATE_DOWNLOAD_TOKEN"]) if role == "downloads" else None
        with listener(InteractionApp(endpoint, download), port, downloads=download is not None,
                      report=report) as server:
            report("listener_ready", role=role, port=server.server_port)
            server.serve_forever()
        return
    def fixture_reply(_application, _token, _reply, _expires):
        report("fixture_reply", outcome="simulated")

    if offline:
        endpoint.commands.pop(("resume", "upload"), None)
    report("worker_ready", offline=offline)
    deliver = fixture_reply if offline else bounded_reply
    while True:
        start = time.monotonic()
        if endpoint.work_once(deliver):
            report("task_processed", ms=round(1000 * (time.monotonic() - start), 1))
        else:
            time.sleep(0.3)


def supervise(env: dict[str, str], *, offline: bool, ports=(PUBLIC_PORT, DOWNLOAD_PORT)) -> None:
    root = private_root(Path(env["JOBBIE_PRIVATE_DB"]).parent)
    lock_path = root / "supervisor.lock"
    with os.fdopen(os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600), "wb") as lock:
        meta = os.fstat(lock.fileno())
        if not stat.S_ISREG(meta.st_mode) or meta.st_uid != os.getuid() or meta.st_mode & 0o077:
            raise ValueError("Unsafe pilot supervisor lock")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _supervise(env, offline=offline, ports=ports)


def _signal_group(process: subprocess.Popen, sig: int) -> bool:
    """The leader owns a separate process group even after it exits."""
    try:
        os.killpg(process.pid, sig)
    except ProcessLookupError:
        return False
    except PermissionError:
        # macOS may return EPERM for a group containing only zombies. Check
        # numeric group membership without inspecting process names or arguments.
        listing = subprocess.check_output(["/bin/ps", "-axo", "pgid=,stat="], text=True, timeout=2)
        for line in listing.splitlines():
            group, state = line.split(maxsplit=1)
            if group == str(process.pid) and not state.startswith("Z"):
                raise
        return False
    return True


def _stop_groups(processes) -> None:
    groups = tuple(processes)
    for process in groups:
        _signal_group(process, signal.SIGTERM)

    deadline = time.monotonic() + 3
    remaining = groups
    while remaining:
        for process in remaining:
            process.poll()
        remaining = tuple(process for process in remaining if _signal_group(process, 0))
        if not remaining or time.monotonic() >= deadline:
            break
        time.sleep(0.05)

    for process in remaining:
        _signal_group(process, signal.SIGKILL)
    for process in groups:
        process.wait(timeout=3)


def _supervise(env: dict[str, str], *, offline: bool, ports) -> None:
    invocation = [sys.executable, "-m", "jobbie_private.pilot", "_child"]
    roles = {"http": ports[0], "downloads": ports[1], "worker": 0}
    processes: dict[str, subprocess.Popen] = {}
    restarts = dict.fromkeys(roles, 0)
    stopping = False

    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}
    try:
        while not stopping:
            for role, port in roles.items():
                if stopping:
                    break
                proc = processes.get(role)
                if proc is not None and proc.poll() is None:
                    continue
                if proc is not None:
                    _stop_groups((proc,))
                    restarts[role] += 1
                    if restarts[role] > 2:
                        raise RuntimeError("Pilot process restart limit reached")
                if stopping:
                    break
                args = [*invocation, role, "--port", str(port)]
                if offline:
                    args.append("--offline")
                processes[role] = subprocess.Popen(args, cwd=ROOT, env=env, stderr=subprocess.DEVNULL,
                                                   start_new_session=True)
                report("process_started", role=role, pid=processes[role].pid, restart=restarts[role])
            time.sleep(0.3)
    finally:
        try:
            _stop_groups(processes.values())
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)


def run_local(args, root: Path) -> None:
    if args.mode == "configure":
        fields = identity(root, {field: local_prompt(prompt).strip() for field, prompt in (
            ("application", "Pilot Discord application ID: "), ("public_key", "Pilot application Ed25519 public key: "),
            ("owner", "Allowed owner Discord user ID: "), ("guild", "Dedicated private pilot server ID: "),
        )})
        write_new(root / "discord.json", json.dumps(fields).encode())
        return
    env = runtime_env(root)
    if args.mode == "owner":
        values = args.arguments
        if not values or values[0] not in OWNER_MODES:
            raise ValueError("Owner operation is outside the synthetic pilot")
        subprocess.run([sys.executable, "-m", "jobbie_private.server", *values],
                       cwd=ROOT, env=env, check=True)
        return
    if args.mode == "register":
        register_commands(root, env)
        return
    if args.mode == "manifest":
        subprocess.run([sys.executable, "-m", "jobbie_private.server", "commands"],
                       cwd=ROOT, env=env, check=True)
        return
    os.environ["JOBBIE_MAC_PARSER_SANDBOX"] = "1"
    verify_parser(root)
    supervise(env, offline=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    for name in ("init", "configure", "manifest", "register", "run", "owner"):
        mode = modes.add_parser(name)
        mode.add_argument("directory", type=Path)
        if name in ("run", "register"):
            mode.add_argument("--approved-live-pilot", action="store_true", required=True)
        if name == "owner":
            mode.add_argument("arguments", nargs=argparse.REMAINDER)
    modes.add_parser("_reply")
    mode = modes.add_parser("_child")
    mode.add_argument("role", choices=("http", "downloads", "worker"))
    mode.add_argument("--port", type=int, required=True)
    mode.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    try:
        if args.mode == "init":
            initialize(args.directory)
            report("synthetic_pilot_prepared")
        elif args.mode == "_reply":
            payload = json.loads(sys.stdin.buffer.read(65537))
            if not snowflake(payload["application"]) or not TOKEN.fullmatch(payload["token"]):
                raise ValueError("Invalid Discord reply")
            try:
                edit_original(**payload)
            except ReplyUnavailable:
                raise SystemExit(3) from None
        elif args.mode == "_child":
            child(args.role, args.port, offline=args.offline)
        else:
            run_local(args, private_root(args.directory))
    except (ValueError, OSError, KeyError, RuntimeError, subprocess.SubprocessError):
        raise SystemExit("Pilot operation failed. Check private settings, port availability and host prerequisites.") from None


if __name__ == "__main__":
    main()
