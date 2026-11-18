import io
import zipfile

import pytest
from cryptography.fernet import Fernet

from jobbie_private.resume import DOCX, PDF, parse_resume
from jobbie_private.storage import PrivateStore
from jobbie_private.profile import DownloadRoute

OWNER = "100000000000000001"
OTHER = "100000000000000003"
TEXT = "Fictional Candidate builds Python services."
NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def docx(text=TEXT, *, xml=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        archive.writestr("word/document.xml", xml or f'<w:document xmlns:w="{NS}"><w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>')
    return stream.getvalue()


@pytest.fixture
def vault(tmp_path):
    return PrivateStore(tmp_path / "owner.sqlite", Fernet.generate_key(), OWNER)


def test_docx_document_is_extracted_in_worker():
    assert parse_resume(DOCX, docx()) == TEXT


@pytest.mark.parametrize("mime,body", [
    (PDF, b"%PDF-1.5\ninvalid"),
    (DOCX, b"%PDF-1.5\ninvalid"),
    ("text/plain", b"not a document"),
    (DOCX, b"PK\x03\x04" + b"x" * (5 * 1024 * 1024)),
])
def test_rejects_invalid_uploads(mime, body):
    with pytest.raises(ValueError):
        parse_resume(mime, body)


def test_docx_rejects_entity_and_zip_bomb():
    with pytest.raises(ValueError):
        parse_resume(DOCX, docx(xml=f'<!DOCTYPE root [<!ENTITY x "debug">]><w:document xmlns:w="{NS}">&x;</w:document>'))
    with pytest.raises(ValueError):
        parse_resume(DOCX, docx("x" * 2_100_000))


def test_repeated_resume_upload_is_idempotent_and_versions_are_immutable(vault):
    body = docx()
    first = vault.store_resume(DOCX, body, TEXT, "interaction-a")
    repeated = vault.store_resume(DOCX, body, TEXT, "interaction-a")
    next_version = vault.store_resume(DOCX, docx("Python and SQL"), "Python and SQL", "interaction-b")
    assert first.id == repeated.id and first.id != next_version.id
    assert vault.resume(first.id).text == TEXT
    with pytest.raises(ValueError):
        vault.store_resume(DOCX, docx("new bytes"), "new bytes", "interaction-a")
    assert TEXT.encode() not in vault.path.read_bytes()


def test_owner_isolation_delete_and_signed_download(vault):
    version = vault.store_resume(DOCX, docx(), TEXT, "interaction-a")
    signature = vault.sign_download(version.id, now=100)
    assert vault.authorize_download(version.id, signature, now=101) == version
    assert vault.authorize_download(version.id, signature, now=400) is None
    assert vault.authorize_download(version.id, signature[:-1] + "!", now=101) is None
    other = PrivateStore(vault.path, vault.key, OTHER)
    assert other.resume(version.id) is None
    assert other.authorize_download(version.id, signature, now=101) is None
    assert not other.delete_resume(version.id)
    assert vault.delete_resume(version.id)
    assert vault.authorize_download(version.id, signature, now=101) is None


def test_download_requires_separate_owner_bearer_and_expires(vault):
    source = docx()
    version = vault.store_resume(DOCX, source, TEXT, "interaction-a")
    signature = vault.sign_download(version.id, now=100)
    route = DownloadRoute(vault, "a" * 40, clock=lambda: 101)
    path = f"/private/resumes/{version.id}"
    assert route(path, "", signature)[0] == 404
    assert route(path, "Bearer " + "b" * 40, signature)[0] == 404
    status, headers, body = route(path, "Bearer " + "a" * 40, signature)
    assert status == 200 and body == source
    assert dict(headers)["Cache-Control"] == "no-store"


def test_saved_is_not_applied_and_status_is_explicit(vault):
    snapshot = vault.snapshot({"job_id": "fixture", "title": "Engineer",
                               "url": "https://careers.example.com/role/42"}, "snapshot")
    vault.save_job(snapshot.id)
    assert vault.applications() == []
    application = vault.create_application(snapshot.id, "review-intent")
    assert vault.applications()[0].status == "planning"
    with pytest.raises(ValueError, match="confirmation"):
        vault.record_attempt(application.id, "applied", "evt", confirmed=False)
    one = vault.record_attempt(application.id, "applied", "evt", confirmed=True)
    two = vault.record_attempt(application.id, "applied", "evt", confirmed=True)
    assert one.id == two.id
    assert len(vault.attempts(application.id)) == 1
    assert vault.applications()[0].status == "applied"


def test_encrypted_online_backup_is_restorable(vault):
    initial = vault.store_resume(DOCX, docx(), TEXT, "interaction-a")
    backup = vault.path.parent / "backup.sqlite"
    vault.backup(backup)
    assert TEXT.encode() not in backup.read_bytes()
    restored = PrivateStore(backup, vault.key, OWNER)
    assert restored.resume(initial.id) == initial
    with pytest.raises(FileExistsError):
        vault.backup(backup)


def test_pdf_document_is_extracted_in_worker():
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    name = NameObject
    writer = PdfWriter()
    page = writer.add_blank_page(200, 200)
    font = DictionaryObject({name("/Type"): name("/Font"), name("/Subtype"): name("/Type1"),
                             name("/BaseFont"): name("/Helvetica")})
    page[name("/Resources")] = DictionaryObject({name("/Font"): DictionaryObject({name("/F1"): font})})
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 10 100 Td (Fictional PDF sample) Tj ET")
    page[name("/Contents")] = writer._add_object(stream)
    buffer = io.BytesIO()
    writer.write(buffer)
    assert parse_resume(PDF, buffer.getvalue()) == "Fictional PDF sample"


@pytest.mark.parametrize("url", [
    "https://private.invalid/attachments/100000000000000001/100000000000000002/file.pdf",
    "https://cdn.discordapp.com@private.invalid/attachments/100000000000000001/100000000000000002/file.pdf",
    "https://cdn.discordapp.com/attachments/100000000000000001/100000000000000003/file.pdf",
    "https://cdn.discordapp.com:8888/attachments/100000000000000001/100000000000000002/file.pdf",
])
def test_attachment_rejects_unapproved_origins_and_ids(url, monkeypatch):
    from jobbie_private.resume import fetch_attachment

    def unexpected(*args, **kwargs):
        pytest.fail("unapproved request")

    monkeypatch.setattr("jobbie_private.resume.http.client.HTTPSConnection", unexpected)
    with pytest.raises(ValueError):
        fetch_attachment({"id": "100000000000000002", "content_type": PDF, "size": 50, "url": url})


def test_resume_attachment_command_uses_verified_resolved_file(vault, monkeypatch, tmp_path):
    from types import SimpleNamespace
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from jobbie_private.discord import DiscordEndpoint
    from jobbie_private.profile import private_commands
    from jobbie_private.tasks import TaskStore
    from tests.test_p3a_discord import APP, handle, interaction

    received = []
    candidate = docx()
    monkeypatch.setattr("jobbie_private.profile.fetch_attachment",
                        lambda attachment: (received.append(attachment) or DOCX, candidate))
    key = Ed25519PrivateKey.generate()
    store = TaskStore(tmp_path / "tasks.sqlite", vault.key)
    clock = SimpleNamespace(now=1_800_000_000)
    endpoint = DiscordEndpoint(key.public_key(), APP, OWNER, store, private_commands(vault),
                               clock=lambda: clock.now)
    rig = SimpleNamespace(key=key, clock=clock, endpoint=endpoint)
    document = interaction(name="resume", options=[{
        "type": 1, "name": "upload", "options": [{"name": "file", "type": 11, "value": APP}],
    }])
    assert handle(rig, document)[0] == 400
    document["data"]["resolved"] = {"attachments": {APP: {"id": APP, "size": len(candidate),
                                                           "content_type": DOCX, "url": "placeholder"}}}
    assert handle(rig, document)[1]["type"] == 5
    assert not received
    assert endpoint.work_once(lambda *_: None)
    assert received[0]["id"] == APP
    assert vault.records("resume_version")[0].data["text"] == TEXT


@pytest.mark.parametrize("progress", ["", "partial response"])
def test_attachment_fetch_has_a_total_process_deadline(tmp_path, monkeypatch, progress):
    import jobbie_private.resume as resume
    worker = tmp_path / "trickle.py"
    worker.write_text("import time\nprint(" + repr(progress) + ", flush=True)\ntime.sleep(10)\n")
    monkeypatch.setattr(resume, "ATTACHMENT_WORKER", worker, raising=False)
    monkeypatch.setattr(resume, "ATTACHMENT_TIMEOUT", 0.5, raising=False)
    monkeypatch.setattr(resume.http.client, "HTTPSConnection",
                        lambda *_args, **_kwargs: pytest.fail("worker network call ran in parent"))
    attachment = {
        "id": "100000000000000002", "content_type": PDF, "size": 50,
        "url": "https://cdn.discordapp.com/attachments/100000000000000001/100000000000000002/file.pdf",
    }
    with pytest.raises(ValueError, match="could not be read"):
        resume.fetch_attachment(attachment)


@pytest.mark.parametrize("legacy_database", [False, True])
def test_vault_rejects_wrong_key_before_writing_valid_data(vault, legacy_database):
    saved = vault.set_profile({"display_name": "Synthetic owner"}, "initial")
    if legacy_database:
        with vault.connect() as database:
            database.execute("DROP TABLE IF EXISTS jobbie_private_key_v1")
    with pytest.raises(ValueError, match="Private database encryption key"):
        PrivateStore(vault.path, Fernet.generate_key(), OWNER)
    recovered = PrivateStore(vault.path, vault.key, OWNER)
    assert recovered.profile() == saved
