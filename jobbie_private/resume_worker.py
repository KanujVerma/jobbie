"""Isolated parser process. Receives a bounded document on stdin."""
from io import BytesIO
import resource
import sys
import xml.etree.ElementTree as ET
import zipfile

MAX_UPLOAD = 5 * 1024 * 1024
MAX_XML = 2 * 1024 * 1024
MAX_TEXT = 100_000
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
CT = "{http://schemas.openxmlformats.org/package/2006/content-types}"


def xml_from(archive, name):
    member = archive.getinfo(name)
    if member.file_size > MAX_XML:
        raise ValueError("Oversized XML")
    data = archive.read(member)
    if b"\x00" in data or b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("Unsafe XML")
    return ET.fromstring(data)


def docx(data):
    with zipfile.ZipFile(BytesIO(data)) as archive:
        members = archive.infolist()
        names = set(archive.namelist())
        if (len(members) > 128 or len(names) != len(members)
                or sum(member.file_size for member in members) > 16 * 1024 * 1024
                or any(member.flag_bits & 1 for member in members)
                or "word/vbaProject.bin" in names):
            raise ValueError("Unsafe archive")
        types = xml_from(archive, "[Content_Types].xml")
        if not any(el.attrib.get("PartName") == "/word/document.xml" and
                   el.attrib.get("ContentType") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
                   for el in types.findall(CT + "Override")):
            raise ValueError("Invalid DOCX content type")
        document = xml_from(archive, "word/document.xml")
        if document.tag != W + "document":
            raise ValueError("Invalid DOCX root")
        return "\n".join("".join(node.text or "" for node in paragraph.iter(W + "t"))
                         for paragraph in document.iter(W + "p"))


def pdf(data):
    from pypdf import PdfReader, apply_configuration
    with apply_configuration(maximum_declared_stream_length=4 * 1024 * 1024):
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted or not 1 <= len(reader.pages) <= 25:
            raise ValueError("Unsupported PDF")
        parts = []
        total = 0
        for page in reader.pages:
            value = page.extract_text() or ""
            total += len(value)
            if total > MAX_TEXT:
                raise ValueError("Excess PDF text")
            parts.append(value)
        return "\n".join(parts)


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (4, 4))
    if sys.platform.startswith("linux"):
        resource.setrlimit(resource.RLIMIT_AS, (384 * 1024 * 1024, 384 * 1024 * 1024))
    data = sys.stdin.buffer.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise ValueError("Upload too large")
    text = pdf(data) if sys.argv[1] == "application/pdf" else docx(data)
    text = text.replace("\x00", "").strip()
    if not 0 < len(text) <= MAX_TEXT:
        raise ValueError("Text unavailable")
    sys.stdout.buffer.write(text.encode("utf-8"))


if __name__ == "__main__":
    main()
