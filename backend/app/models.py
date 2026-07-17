"""Imports every ORM model so Base.metadata is complete.

Alembic's env.py and the dev create_all() both import this module to discover
all tables. Add new model modules here as domains are built out.
"""

from app.common.base import Base  # noqa: F401
from app.modules.entitlements.models import Subscription  # noqa: F401
from app.modules.identity.models import (  # noqa: F401
    OtpChallenge,
    Profile,
    User,
    VerifiedAttributes,
)
from app.modules.intelligent.models import ConversationSignal  # noqa: F401
from app.modules.matchmaking.models import Match  # noqa: F401
from app.modules.structured.models import (  # noqa: F401
    AvailabilityWindow,
    DatePlan,
    DatePromptResponse,
    Message,
)
from app.modules.verification.models import (  # noqa: F401
    VerificationArtifact,
    VerificationCase,
    VerificationDecision,
)

__all__ = ["Base"]
