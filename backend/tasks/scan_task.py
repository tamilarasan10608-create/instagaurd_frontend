"""
Celery worker — handles the full scan pipeline asynchronously:
  1. Scrape Instagram images via Apify
  2. Fetch each image in memory (RAM-only — never saved to disk)
  3. Run steganography detection
  4. Persist results to PostgreSQL (commit after EVERY post so partial results are saved)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime, timezone
from celery import Celery
from celery.utils.log import get_task_logger
from config import get_settings
from utils.scraper import fetch_image_bytes

settings = get_settings()
logger = get_task_logger(__name__)

celery_app = Celery(
    "instaguard",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
)


@celery_app.task(bind=True, name="tasks.run_scan", max_retries=2, default_retry_delay=30)
def run_scan_task(self, scan_id: str):
    """Main scan task. scan_id is a UUID string."""
    from database import SessionLocal
    from models.scan import Scan, ScanStatus
    from models.post_result import PostResult
    from utils.scraper import scrape_instagram_posts
    from core.detector import analyze_image

    db = SessionLocal()
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            logger.error(f"Scan {scan_id} not found")
            return

        # ── Phase 1: Scrape ──────────────────────────────────────────────────
        scan.status = ScanStatus.SCRAPING
        db.commit()

        def scrape_progress(step: str, detail: str = ""):
            logger.info(f"[scan={scan_id[:8]}] [{step}] {detail}")

        # Fetch more to ensure we have enough images after skipping videos
        fetch_limit = scan.max_posts * 3 + 20
        raw_posts = scrape_instagram_posts(
            scan.instagram_username,
            max_posts=fetch_limit,
            progress_cb=scrape_progress,
        )

        # Filter out videos and keep exactly max_posts valid image posts
        valid_image_posts = []
        for p in raw_posts:
            if p.get("image_url", "").strip() and not p.get("is_video"):
                valid_image_posts.append(p)
                if len(valid_image_posts) >= scan.max_posts:
                    break
        
        posts = valid_image_posts

        # FIX: total_posts = exact number of valid images we will analyze
        scan.total_posts = len(posts)
        scan.status = ScanStatus.ANALYZING
        db.commit()
        logger.info(f"Filtered to {len(posts)} valid image posts for @{scan.instagram_username}")

        # ── Phase 2: Analyze ─────────────────────────────────────────────────
        # FIX: commit after EVERY post so partial results survive any crash
        durations = []
        post_index = 0

        for idx, post in enumerate(posts):
            image_url = post.get("image_url", "").strip()

            post_index += 1
            logger.info(f"  Analyzing post {idx+1}/{len(posts)} — {image_url[:60]}…")

            image_bytes = asyncio.run(fetch_image_bytes(image_url))
            if not image_bytes:
                logger.warning(f"  Could not fetch image for post {idx+1}, skipping")
                continue

            try:
                result = analyze_image(image_bytes)
            except Exception as e:
                logger.error(f"  Detection failed for post {idx+1}: {e}")
                del image_bytes
                continue
            finally:
                # RAM-only protocol: discard bytes immediately after use
                del image_bytes

            pr = PostResult(
                scan_id=scan_id,
                post_index=post_index,
                instagram_post_url=post.get("post_url", ""),
                image_url=image_url,
                thumbnail_b64=result["thumbnail_b64"],
                is_suspicious=result["is_suspicious"],
                confidence_score=result["confidence_score"],
                scan_duration_ms=result["scan_duration_ms"],
            )
            db.add(pr)

            if result["is_suspicious"]:
                scan.suspicious_count += 1
            else:
                scan.clean_count += 1

            scan.analyzed_posts += 1
            durations.append(result["scan_duration_ms"])

            # FIX: commit after every single post — partial results visible in UI immediately
            db.commit()
            logger.info(
                f"  Post {post_index}: {'SUSPICIOUS' if result['is_suspicious'] else 'clean'} "
                f"({result['confidence_score']*100:.1f}%)"
            )

        # ── Phase 3: Finalize ────────────────────────────────────────────────
        if durations:
            scan.avg_scan_duration_ms = sum(durations) / len(durations)
        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(
            f"Scan {scan_id} DONE. "
            f"Analyzed: {scan.analyzed_posts}/{scan.total_posts}  "
            f"Suspicious: {scan.suspicious_count}  Clean: {scan.clean_count}"
        )

    except Exception as exc:
        db.rollback()
        try:
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                scan.status = ScanStatus.FAILED
                scan.error_message = str(exc)[:1024]
                db.commit()
        except Exception:
            pass
        logger.exception(f"Scan {scan_id} failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()
