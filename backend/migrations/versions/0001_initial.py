"""initial schema — identity, entitlements, verification

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-15

Covers the v1 tables the backend implements today. Matchmaking, Conversation,
Date Progression, and Intelligent-domain tables from the data model are not
included yet — they get their own migrations as those modules are built.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.common.base import GUID
from app.common.enums import (
    AccountState,
    BillingCycle,
    CriminalCheckStatus,
    Eligibility,
    IncomePercentileTier,
    Plan,
    SubscriptionStatus,
    UserStatus,
    VerificationCaseType,
    VerificationState,
)

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("phone", sa.String(32), unique=True),
        sa.Column(
            "status", sa.Enum(UserStatus, name="user_status"), nullable=False
        ),
        sa.Column(
            "account_state",
            sa.Enum(AccountState, name="account_state"),
            nullable=False,
        ),
        *_timestamps(),
    )

    op.create_table(
        "profiles",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column(
            "user_id",
            GUID(),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("display_name", sa.String(120)),
        sa.Column("bio", sa.Text()),
        sa.Column("prompts", sa.JSON()),
        sa.Column("photos", sa.JSON()),
        sa.Column("interests", sa.JSON()),
        sa.Column("dining_preferences", sa.JSON()),
        sa.Column("latitude", sa.Numeric(9, 6)),
        sa.Column("longitude", sa.Numeric(9, 6)),
        sa.Column("city_market", sa.String(80)),
        *_timestamps(),
    )

    op.create_table(
        "verified_attributes",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column(
            "user_id",
            GUID(),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("identity_verified", sa.Boolean(), nullable=False),
        sa.Column(
            "criminal_check_status",
            sa.Enum(CriminalCheckStatus, name="criminal_check_status"),
            nullable=False,
        ),
        sa.Column(
            "income_percentile_tier",
            sa.Enum(IncomePercentileTier, name="income_percentile_tier"),
        ),
        sa.Column("education_level", sa.String(80)),
        sa.Column(
            "eligibility", sa.Enum(Eligibility, name="eligibility"), nullable=False
        ),
        *_timestamps(),
    )

    op.create_table(
        "otp_challenges",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("destination", sa.String(320), nullable=False),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("code_hash", sa.String(128), nullable=False),
        sa.Column("consumed", sa.Boolean(), nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan", sa.Enum(Plan, name="plan"), nullable=False),
        sa.Column(
            "billing_cycle",
            sa.Enum(BillingCycle, name="billing_cycle"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(SubscriptionStatus, name="subscription_status"),
            nullable=False,
        ),
        sa.Column("activation_fee_paid_at", sa.DateTime(timezone=True)),
        sa.Column("current_period_start", sa.DateTime(timezone=True)),
        sa.Column("current_period_end", sa.DateTime(timezone=True)),
        *_timestamps(),
    )

    op.create_table(
        "verification_cases",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "case_type",
            sa.Enum(VerificationCaseType, name="verification_case_type"),
            nullable=False,
        ),
        sa.Column(
            "state",
            sa.Enum(VerificationState, name="verification_state"),
            nullable=False,
        ),
        sa.Column("vendor", sa.String(80)),
        sa.Column("vendor_reference_id", sa.String(128)),
        sa.Column("disclosure_presented_at", sa.DateTime(timezone=True)),
        sa.Column("authorization_captured_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )

    op.create_table(
        "verification_decisions",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column(
            "verification_case_id",
            GUID(),
            sa.ForeignKey("verification_cases.id"),
            nullable=False,
        ),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("decided_by", sa.String(16), nullable=False),
        sa.Column("reason_code", sa.String(80)),
        *_timestamps(),
    )

    op.create_table(
        "verification_artifacts",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column(
            "verification_case_id",
            GUID(),
            sa.ForeignKey("verification_cases.id"),
            nullable=False,
        ),
        sa.Column("artifact_type", sa.String(32), nullable=False),
        sa.Column("storage_ref", sa.Text(), nullable=False),
        sa.Column("retention_expires_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )


def downgrade() -> None:
    for table in (
        "verification_artifacts",
        "verification_decisions",
        "verification_cases",
        "subscriptions",
        "otp_challenges",
        "verified_attributes",
        "profiles",
        "users",
    ):
        op.drop_table(table)
