from __future__ import annotations

import hashlib
import io
import re
import zipfile
import subprocess
import sys
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from .schemas import Passage, Source

MAX_BYTES = 8 * 1024 * 1024
MAX_TEXT = 60_000
MAX_PAGES = 30


def parse_source_isolated(name: str, raw: bytes) -> Source:
    """Bound parser execution time without retaining uploaded bytes on disk."""
    try:
        result = subprocess.run([sys.executable, "-m", "backend.app.ingestion_worker", name], input=raw, capture_output=True, timeout=25, cwd=Path(__file__).resolve().parents[2], creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        if result.returncode != 0:
            raise ValueError("The parser stopped unexpectedly. Export this source again or paste its text.")
        return Source.model_validate_json(result.stdout)
    except (subprocess.TimeoutExpired, ValueError):
        digest = hashlib.sha256(raw).hexdigest()
        return Source(id="doc_" + digest[:16], name=Path(name.replace("\\", "/")).name[:180], kind=Path(name).suffix.lstrip("."), content_hash=digest, status="failed", warnings=["The document parser stopped or exceeded its 25-second limit. Paste the relevant text or use a smaller document."])


def parse_source(name: str, raw: bytes) -> Source:
    name = Path(name.replace("\\", "/")).name[:180] or "Untitled source"
    ext = Path(name).suffix.lower()
    digest = hashlib.sha256(raw).hexdigest()
    source_id = "doc_" + digest[:16]
    source = Source(id=source_id, name=name, kind=ext.lstrip("."), content_hash=digest)
    try:
        if not raw:
            raise ValueError("The file is empty. Add a source with readable text.")
        if len(raw) > MAX_BYTES:
            raise ValueError("This source exceeds 8 MB. Use a smaller file or paste the relevant text.")
        blocks: list[tuple[str, str]] = []
        if ext in {".txt", ".md"}:
            text = raw.decode("utf-8-sig")
            blocks = [(f"Paragraph {i + 1}", x.strip()) for i, x in enumerate(re.split(r"\n\s*\n", text)) if x.strip()]
        elif ext == ".pdf":
            if not raw.startswith(b"%PDF"):
                raise ValueError("This file is not a valid PDF. Export it again or paste its text.")
            reader = PdfReader(io.BytesIO(raw))
            if reader.is_encrypted:
                raise ValueError("Password-protected PDFs are not supported. Upload an unlocked copy.")
            if len(reader.pages) > MAX_PAGES:
                raise ValueError("This PDF exceeds 30 pages. Split it into a smaller review.")
            for i, page in enumerate(reader.pages):
                # Bound known decoded stream length before extraction where metadata permits.
                contents = page.get_contents()
                if contents and len(contents.get_data()) > 12 * 1024 * 1024:
                    raise ValueError("A PDF page is too complex to parse safely. Paste its text instead.")
                text = page.extract_text() or ""
                if not text.strip():
                    source.warnings.append(f"Page {i + 1} has no extractable text; OCR is not enabled.")
                blocks += [(f"Page {i + 1}, passage {j + 1}", x.strip()) for j, x in enumerate(re.split(r"\n\s*\n", text)) if x.strip()]
        elif ext == ".docx":
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                if sum(x.file_size for x in archive.infolist()) > 24 * 1024 * 1024:
                    raise ValueError("The expanded DOCX is too large. Paste the relevant text instead.")
            document = Document(io.BytesIO(raw))
            from docx.table import Table
            from docx.text.paragraph import Paragraph
            for i, item in enumerate(document.iter_inner_content()):
                if isinstance(item, Paragraph) and item.text.strip():
                    blocks.append((f"Paragraph {i + 1}", item.text.strip()))
                elif isinstance(item, Table):
                    for r, row in enumerate(item.rows):
                        text = " | ".join(cell.text for cell in row.cells)
                        if text.strip():
                            blocks.append((f"Table {i + 1}, row {r + 1}", text))
            source.warnings.append("DOCX references use paragraphs and table rows. Headers, footers, comments, and tracked edits are not assessed.")
        else:
            raise ValueError("Use a PDF, DOCX, TXT, or Markdown file.")
        if not blocks:
            raise ValueError("No readable text was found. For scanned pages, paste the text or upload a text-based PDF.")
        if sum(len(x[1]) for x in blocks) > MAX_TEXT:
            raise ValueError("This source exceeds 60,000 characters. Split it or paste the relevant passages.")
        # Bound individual passages without discarding any content.
        for location, text in blocks:
            for part, offset in enumerate(range(0, len(text), 6000)):
                source.passages.append(Passage(id=f"{source_id}_p{len(source.passages) + 1}", document_id=source_id, location=location + (f", part {part + 1}" if len(text) > 6000 else ""), text=text[offset:offset + 6000]))
    except Exception as exc:
        source.status = "failed"
        source.passages = []
        source.warnings = [str(exc) if isinstance(exc, (ValueError, UnicodeError, zipfile.BadZipFile)) else "This document could not be parsed. Export it again or paste its text."]
    return source
