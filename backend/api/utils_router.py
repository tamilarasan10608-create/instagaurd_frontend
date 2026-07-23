"""
api/utils_router.py
Exposes utility endpoints ported from the Flask app:
  GET /api/test-cookie  →  validates the Instagram session cookie (no Apify credit)
"""
from fastapi import APIRouter, Depends
from utils.scraper import validate_instagram_cookie
from utils.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/api/utils", tags=["utils"])


@router.get("/test-cookie")
def test_cookie(current_user: User = Depends(get_current_user)):
    """
    Quick-check the INSTAGRAM_SESSION_ID cookie stored in .env.
    No Apify credits consumed.
    """
    result = validate_instagram_cookie()
    status_code = 200 if result["ok"] else 401
    from fastapi.responses import JSONResponse
    return JSONResponse(content=result, status_code=status_code)
