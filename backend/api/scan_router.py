from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io

from database import get_db
from models.user import User
from models.scan import Scan, ScanStatus
from models.post_result import PostResult
from utils.auth import get_current_user
from utils.hashing import hash_report_dict, hash_pdf_bytes, build_report_payload
from api.schemas import StartScanRequest, ScanOut, ScanDetailOut, SealResponse
from tasks.scan_task import run_scan_task, execute_scan

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.post("", response_model=ScanOut, status_code=202)
def start_scan(
    body: StartScanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scan = Scan(
        user_id=current_user.id,
        instagram_username=body.instagram_username,
        max_posts=body.max_posts,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    try:
        task = run_scan_task.delay(str(scan.id))
        scan.celery_task_id = task.id
    except Exception:
        import threading
        t = threading.Thread(target=execute_scan, args=(str(scan.id),), daemon=True)
        t.start()
        scan.celery_task_id = "local-thread"

    db.commit()
    db.refresh(scan)
    return ScanOut.model_validate(scan)


@router.get("", response_model=List[ScanOut])
def list_scans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scans = (
        db.query(Scan)
        .filter(Scan.user_id == current_user.id)
        .order_by(Scan.created_at.desc())
        .limit(100)
        .all()
    )
    return [ScanOut.model_validate(s) for s in scans]


@router.get("/{scan_id}", response_model=ScanDetailOut)
def get_scan(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scan = db.query(Scan).filter(
        Scan.id == scan_id, Scan.user_id == current_user.id
    ).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return ScanDetailOut.model_validate(scan)


@router.delete("/{scan_id}", status_code=204)
def delete_scan(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scan = db.query(Scan).filter(
        Scan.id == scan_id, Scan.user_id == current_user.id
    ).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    db.delete(scan)
    db.commit()


@router.get("/{scan_id}/export")
def export_report(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export forensic PDF. Auto-seals the scan on first export."""
    scan = db.query(Scan).filter(
        Scan.id == scan_id, Scan.user_id == current_user.id
    ).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status != ScanStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Scan not yet completed")

    if not scan.report_hash:
        payload = build_report_payload(scan)
        scan.report_hash = hash_report_dict(payload)
        db.commit()

    pdf_bytes = _generate_pdf(scan, current_user, report_hash=scan.report_hash)

    if not scan.pdf_hash:
        scan.pdf_hash = hash_pdf_bytes(pdf_bytes)
        db.commit()

    filename = f"instaguard_{scan.instagram_username}_{scan.created_at.strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Report-Hash": scan.report_hash,
            "X-PDF-Hash": scan.pdf_hash,
            "Access-Control-Expose-Headers": "X-Report-Hash, X-PDF-Hash",
        },
    )


@router.post("/{scan_id}/seal", response_model=SealResponse)
def seal_scan(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Chain of Custody — seal a completed scan (idempotent)."""
    scan = db.query(Scan).filter(
        Scan.id == scan_id, Scan.user_id == current_user.id
    ).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status != ScanStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Only completed scans can be sealed")

    if scan.report_hash and scan.pdf_hash:
        return SealResponse(
            scan_id=scan.id,
            report_hash=scan.report_hash,
            pdf_hash=scan.pdf_hash,
            sealed_at=scan.completed_at,
            message="Already sealed — returning existing chain of custody hashes.",
        )

    payload = build_report_payload(scan)
    report_hash = hash_report_dict(payload)
    pdf_bytes = _generate_pdf(scan, current_user)
    pdf_hash = hash_pdf_bytes(pdf_bytes)

    scan.report_hash = report_hash
    scan.pdf_hash = pdf_hash
    db.commit()

    return SealResponse(
        scan_id=scan.id,
        report_hash=report_hash,
        pdf_hash=pdf_hash,
        sealed_at=scan.completed_at,
        message="Scan sealed. SHA-256 hashes committed to database.",
    )


# =============================================================================
#  PDF Generator
# =============================================================================

def _generate_pdf(scan: Scan, investigator: User, report_hash: str = "") -> bytes:
    import base64, tempfile, os
    from fpdf import FPDF
    from datetime import timezone, timedelta

    IST = timezone(timedelta(hours=5, minutes=30))

    def _fmt(dt):
        if not dt:
            return "N/A"
        return dt.astimezone(IST).strftime("%d %b %Y  %H:%M IST")

    # Project theme palette
    C_BG       = (8,   12,  20)    # #080c14
    C_CARD     = (13,  18,  32)    # #0d1220
    C_BORDER   = (26,  34,  53)    # #1a2235
    C_BLUE     = (59,  130, 246)   # #3b82f6
    C_BLUE_DIM = (30,  58,  138)   # dimmed blue
    C_GREEN    = (34,  197, 94)    # #22c55e
    C_RED      = (239, 68,  68)    # #ef4444
    C_TEXT     = (241, 245, 249)   # #f1f5f9
    C_MUTED    = (148, 163, 184)   # #94a3b8

    # ------------------------------------------------------------------
    # PDF class with themed header / footer
    # ------------------------------------------------------------------
    class PDF(FPDF):
        def header(self):
            self.set_fill_color(*C_BG)
            self.rect(0, 0, 210, 22, "F")
            self.set_fill_color(*C_BLUE)
            self.rect(0, 0, 4, 22, "F")
            self.set_y(6)
            self.set_x(8)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*C_TEXT)
            self.cell(100, 8, "INSTAGUARD  |  FORENSIC DETECTION REPORT", ln=False)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*C_MUTED)
            self.cell(0, 8, f"CONFIDENTIAL  //  Page {self.page_no()}", align="R", ln=True)
            self.set_draw_color(*C_BLUE)
            self.set_line_width(0.4)
            self.line(0, 22, 210, 22)
            self.ln(4)

        def footer(self):
            self.set_y(-14)
            self.set_fill_color(*C_BG)
            self.rect(0, self.get_y() - 2, 210, 16, "F")
            self.set_draw_color(*C_BORDER)
            self.set_line_width(0.2)
            self.line(0, self.get_y(), 210, self.get_y())
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*C_MUTED)
            self.cell(
                0, 10,
                f"InstaGuard Forensic Platform  |  Generated {_fmt(scan.completed_at)}  |  RESTRICTED",
                align="C",
            )

    pdf = PDF()
    pdf.set_margins(12, 28, 12)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ------------------------------------------------------------------
    # Hero title bar
    # ------------------------------------------------------------------
    pdf.set_fill_color(*C_CARD)
    pdf.rect(12, pdf.get_y(), 186, 30, "F")
    pdf.set_fill_color(*C_BLUE)
    pdf.rect(12, pdf.get_y(), 3, 30, "F")
    y0 = pdf.get_y() + 4
    pdf.set_xy(18, y0)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*C_TEXT)
    pdf.cell(0, 10, f"@{scan.instagram_username}", ln=True)
    pdf.set_x(18)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0, 7, "Steganography Forensic Analysis Report", ln=True)
    pdf.ln(6)

    # ------------------------------------------------------------------
    # Report Metadata
    # ------------------------------------------------------------------
    _pdf_section(pdf, "REPORT METADATA", C_BG, C_BLUE, C_TEXT)
    meta_rows = [
        ("Target Account",   f"@{scan.instagram_username}"),
        ("Investigator",     f"{investigator.full_name}  ({investigator.email})"),
        ("Scan ID",          str(scan.id)),
        ("Started (IST)",    _fmt(scan.created_at)),
        ("Completed (IST)",  _fmt(scan.completed_at)),
        ("Posts Requested",  str(scan.max_posts)),
    ]
    if report_hash:
        meta_rows += [
            ("Report Hash (SHA-256)", report_hash[:32] + "..."),
            ("Full Hash",             report_hash),
        ]
    for k, v in meta_rows:
        _pdf_kv(pdf, k, v, C_CARD, C_MUTED, C_TEXT, C_BORDER)
    pdf.ln(5)

    # ------------------------------------------------------------------
    # Analysis Summary
    # ------------------------------------------------------------------
    _pdf_section(pdf, "ANALYSIS SUMMARY", C_BG, C_BLUE, C_TEXT)
    total = scan.analyzed_posts or 0
    susp  = scan.suspicious_count or 0
    clean = scan.clean_count or 0
    avg   = scan.avg_scan_duration_ms or 0.0
    rate  = f"{(susp / total * 100):.1f}%" if total > 0 else "N/A"
    _pdf_kv(pdf, "Total Posts Scraped",  str(scan.total_posts or 0), C_CARD, C_MUTED, C_TEXT,              C_BORDER)
    _pdf_kv(pdf, "Images Analyzed",      str(total),                 C_CARD, C_MUTED, C_TEXT,              C_BORDER)
    _pdf_kv(pdf, "Suspicious Posts",     str(susp),                  C_CARD, C_MUTED, C_RED if susp else C_TEXT, C_BORDER)
    _pdf_kv(pdf, "Clean Posts",          str(clean),                 C_CARD, C_MUTED, C_GREEN,             C_BORDER)
    _pdf_kv(pdf, "Detection Rate",       rate,                       C_CARD, C_MUTED, C_RED if susp else C_GREEN, C_BORDER)
    _pdf_kv(pdf, "Avg Scan Time",        f"{avg:.1f} ms / image",    C_CARD, C_MUTED, C_TEXT,              C_BORDER)
    pdf.ln(5)

    # ------------------------------------------------------------------
    # Verdict banner
    # ------------------------------------------------------------------
    _pdf_section(pdf, "VERDICT", C_BG, C_BLUE, C_TEXT)
    if susp > 0:
        pdf.set_fill_color(60, 10, 10)
        pdf.set_draw_color(*C_RED)
        pdf.set_text_color(*C_RED)
        verdict = f"[!]  SUSPICIOUS CONTENT DETECTED  -  {susp} post{'s' if susp != 1 else ''} flagged"
    else:
        pdf.set_fill_color(10, 40, 20)
        pdf.set_draw_color(*C_GREEN)
        pdf.set_text_color(*C_GREEN)
        verdict = "[OK]  ALL POSTS CLEAR  -  No steganographic payload detected"
    pdf.set_line_width(0.5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.rect(12, pdf.get_y(), 186, 13, "FD")
    pdf.set_x(12)
    pdf.cell(186, 13, f"  {verdict}", ln=True)
    pdf.ln(6)

    # ------------------------------------------------------------------
    # Suspicious posts detail
    # ------------------------------------------------------------------
    suspicious_results = [r for r in scan.results if r.is_suspicious]
    if suspicious_results:
        _pdf_section(pdf, f"SUSPICIOUS POSTS  ({len(suspicious_results)} items)", C_BG, C_BLUE, C_TEXT)
        tmp_files = []

        for r in suspicious_results:
            if pdf.get_y() > 240:
                pdf.add_page()

            thumb_path = None
            if r.thumbnail_b64:
                try:
                    img_data = base64.b64decode(r.thumbnail_b64)
                    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
                    tmp.write(img_data)
                    tmp.close()
                    thumb_path = tmp.name
                    tmp_files.append(thumb_path)
                except Exception:
                    thumb_path = None

            block_y = pdf.get_y()
            block_h = 32
            pdf.set_fill_color(*C_CARD)
            pdf.rect(12, block_y, 186, block_h, "F")
            pdf.set_fill_color(*C_RED)
            pdf.rect(12, block_y, 2, block_h, "F")

            if thumb_path:
                try:
                    pdf.image(thumb_path, x=16, y=block_y + 3, w=26, h=26)
                except Exception:
                    thumb_path = None

            tx = 46 if thumb_path else 18
            pdf.set_xy(tx, block_y + 4)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*C_RED)
            conf = r.confidence_score or 0.0
            pdf.cell(0, 6, f"Post #{r.post_index}   Confidence: {conf * 100:.1f}%", ln=True)

            pdf.set_x(tx)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*C_MUTED)
            url = (r.instagram_post_url or r.image_url or "N/A")[:90]
            pdf.cell(0, 5, url, ln=True)

            pdf.set_x(tx)
            dur = r.scan_duration_ms or 0.0
            pdf.cell(0, 5, f"Scan time: {dur:.1f} ms   |   Detected: {_fmt(r.created_at)}", ln=True)

            pdf.set_y(block_y + block_h + 3)

        for p in tmp_files:
            try:
                os.unlink(p)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Complete results table
    # ------------------------------------------------------------------
    pdf.add_page()
    _pdf_section(pdf, "COMPLETE RESULTS TABLE", C_BG, C_BLUE, C_TEXT)

    COL     = [12, 30, 28, 116]
    HEADERS = ["#", "Status", "Confidence", "Post URL / Detected (IST)"]

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(*C_BLUE_DIM)
    pdf.set_text_color(*C_TEXT)
    pdf.set_draw_color(*C_BORDER)
    pdf.set_line_width(0.15)
    pdf.set_x(12)
    for w, h in zip(COL, HEADERS):
        pdf.cell(w, 8, f" {h}", border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 7)
    even = True
    for r in scan.results:
        even = not even
        conf = r.confidence_score or 0.0
        url  = (r.instagram_post_url or r.image_url or "")[:70]
        det  = _fmt(r.created_at)

        if r.is_suspicious:
            pdf.set_fill_color(50, 12, 12)
        else:
            pdf.set_fill_color(16, 22, 36) if even else pdf.set_fill_color(*C_CARD)

        status_text = "SUSPICIOUS" if r.is_suspicious else "Clean"
        url_cell    = f"{url}  |  {det}"
        row = [str(r.post_index), status_text, f"{conf * 100:.1f}%", url_cell]

        pdf.set_x(12)
        for i, (w, val) in enumerate(zip(COL, row)):
            if i == 1:  # Status column coloring
                pdf.set_text_color(*C_RED) if r.is_suspicious else pdf.set_text_color(*C_GREEN)
            else:
                pdf.set_text_color(*C_MUTED)
            pdf.cell(w, 6, f" {val}", border=1, fill=True)
        pdf.ln()

    return bytes(pdf.output())


# =============================================================================
#  Helpers — called by _generate_pdf above
# =============================================================================

def _pdf_section(pdf, title: str, bg, accent, text_col):
    """Dark-themed section header with left accent stripe."""
    pdf.set_fill_color(*bg)
    pdf.rect(12, pdf.get_y(), 186, 10, "F")
    pdf.set_fill_color(*accent)
    pdf.rect(12, pdf.get_y(), 2, 10, "F")
    pdf.set_x(17)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*text_col)
    pdf.cell(0, 10, title, ln=True)
    pdf.ln(1)


def _pdf_kv(pdf, key: str, value: str, bg, key_col, val_col, border_col):
    """Two-column key/value row with dark card background."""
    pdf.set_fill_color(*bg)
    pdf.set_draw_color(*border_col)
    pdf.set_line_width(0.1)
    pdf.set_x(12)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*key_col)
    pdf.cell(52, 7, f"  {key}", border="B", fill=True)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*val_col)
    pdf.cell(134, 7, f"  {value}", border="B", fill=True, ln=True)
