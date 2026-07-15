from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_current_user
from app.modules.identity.models import User

router = APIRouter(tags=["verification"])

_BLOCKED_DETAIL = (
    "Verification is not yet available: the background-check flow is blocked "
    "pending legal sign-off of the compliance requirements and vendor "
    "selection. See docs/compliance/background-checks.md."
)


@router.post("/verification-cases", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def start_verification(current: User = Depends(get_current_user)):
    """Placeholder — returns 501 by design until compliance sign-off.

    Wired now so the route exists and the block is explicit and testable,
    rather than a missing endpoint someone silently implements later.
    """
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _BLOCKED_DETAIL)
