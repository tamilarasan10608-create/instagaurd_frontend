"""
utils/hashing.py
================
Chain of Custody utility — deterministic SHA-256 hashing for scan reports.

Used in two ways:
  • hash_report_dict()  — hashes the structured JSON report data (dict → bytes → SHA-256)
  • hash_pdf_bytes()    — hashes the raw bytes of a generated PDF file
"""
import hashlib
import json
from typing import Union


def hash_report_dict(report_data: dict) -> str:
    """
    Generate a deterministic SHA-256 hash of a report data dictionary.

    The dict is serialized with sorted keys and no extra whitespace to ensure
    the same data always produces the same hash regardless of insertion order.
    Non-ASCII characters are handled via utf-8 encoding.

    Args:
        report_data: The structured report as a Python dict. Must be
                     JSON-serialisable (str, int, float, bool, None, list, dict).

    Returns:
        A 64-character lowercase hex string (SHA-256 digest).

    Example:
        >>> hash_report_dict({"scan_id": "abc", "suspicious": 3})
        'e3b0c44298fc1c149afb...'
    """
    # sort_keys=True + separators=(',', ':') gives a canonical byte sequence
    # ensure_ascii=False preserves unicode but we encode to utf-8 explicitly
    canonical_json: str = json.dumps(
        report_data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,   # handles datetime, UUID, Decimal etc. gracefully
    )
    raw_bytes: bytes = canonical_json.encode("utf-8")
    return hashlib.sha256(raw_bytes).hexdigest()


def hash_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Generate a SHA-256 hash of a PDF file's raw bytes.

    Use this when you need to prove the exported PDF itself has not been
    tampered with after generation (file-level chain of custody).

    Args:
        pdf_bytes: The raw bytes of the generated PDF (e.g. from fpdf2 output()).

    Returns:
        A 64-character lowercase hex string (SHA-256 digest).

    Example:
        >>> pdf_bytes = pdf.output()           # fpdf2
        >>> fingerprint = hash_pdf_bytes(pdf_bytes)
    """
    return hashlib.sha256(pdf_bytes).hexdigest()


def build_report_payload(scan) -> dict:
    """
    Build the canonical dict representation of a completed scan for hashing.

    Only includes fields that form the factual forensic record — not internal
    DB IDs or UI metadata that might change without affecting findings.

    Args:
        scan: A SQLAlchemy Scan ORM instance with .results loaded.

    Returns:
        A JSON-serialisable dict ready to be passed to hash_report_dict().
    """
    return {
        "scan_id":             str(scan.id),
        "instagram_username":  scan.instagram_username,
        "total_posts":         scan.total_posts,
        "analyzed_posts":      scan.analyzed_posts,
        "suspicious_count":    scan.suspicious_count,
        "clean_count":         scan.clean_count,
        "avg_scan_duration_ms": round(scan.avg_scan_duration_ms, 4),
        "completed_at":        scan.completed_at.isoformat() if scan.completed_at else None,
        "results": [
            {
                "post_index":         r.post_index,
                "instagram_post_url": r.instagram_post_url or "",
                "is_suspicious":      r.is_suspicious,
                "confidence_score":   round(r.confidence_score, 6),
                "scan_duration_ms":   round(r.scan_duration_ms, 4),
            }
            for r in sorted(scan.results, key=lambda r: r.post_index)
        ],
    }