import datetime as dt
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api.deps import Identity, Scoped, require_csrf
from app.living.catalog import SYSTEMS
from app.models import GlowAchievement, GlowBalance, GlowStreak, GlowTransaction
from app.services.glow_service import award_glow


router = APIRouter(prefix="/glow", tags=["glow"])


class GlowRewardIn(BaseModel):
    event_type: str = Field(min_length=1, max_length=80)
    source_kind: str = Field(min_length=1, max_length=80)
    source_id: uuid.UUID
    orbit_id: uuid.UUID | None = None
    idempotency_key: str = Field(min_length=8, max_length=240)


class GlowTransactionOut(BaseModel):
    id: uuid.UUID
    event_type: str
    source_kind: str
    source_id: uuid.UUID
    system_slug: str | None
    final_points: int
    reason: str
    created_at: dt.datetime
    model_config = {"from_attributes": True}


class GlowStreakOut(BaseModel):
    streak_key: str
    current_count: int
    best_count: int
    last_event_date: dt.date | None
    repairs_remaining: int
    model_config = {"from_attributes": True}


class GlowRewardOut(BaseModel):
    transaction_id: uuid.UUID
    event_type: str
    awarded_points: int
    balance: int
    lifetime_points: int
    idempotent_replay: bool
    streak: GlowStreakOut | None
    achievements_unlocked: list[str]


class GlowAchievementOut(BaseModel):
    achievement_key: str
    achievement_metadata: dict
    unlocked_at: dt.datetime
    model_config = {"from_attributes": True}


class GlowSummaryOut(BaseModel):
    balance: int
    lifetime_points: int
    today_points: int
    weekly_points: int
    level: int
    rank: str
    next_unlock: dict | None
    recent_transactions: list[GlowTransactionOut]
    streaks: list[GlowStreakOut]
    achievements: list[GlowAchievementOut]
    daily_quest: dict
    weekly_mission: dict


class ScoreboardRow(BaseModel):
    rank: int
    system_slug: str
    system_title: str
    score: int


class ScoreboardOut(BaseModel):
    scope: str
    period: str
    provenance_label: str
    rows: list[ScoreboardRow]


LEVELS = (
    (1, 0, "Orbit Seed"),
    (2, 50, "Ember"),
    (3, 150, "Star Builder"),
    (4, 350, "Orbit Keeper"),
    (5, 700, "Constellation"),
)


def _level_state(points: int) -> tuple[int, str, dict | None]:
    current = LEVELS[0]
    next_level = None
    for row in LEVELS:
        if points >= row[1]:
            current = row
        elif next_level is None:
            next_level = row
    next_unlock = (
        {
            "level": next_level[0],
            "rank": next_level[2],
            "threshold": next_level[1],
            "points_remaining": next_level[1] - points,
        }
        if next_level else None
    )
    return current[0], current[2], next_unlock


@router.post("/rewards", response_model=GlowRewardOut, status_code=201, dependencies=[Depends(require_csrf)])
async def reward(payload: GlowRewardIn, db: Scoped, identity: Identity) -> GlowRewardOut:
    owner_user_id, _ = identity
    result = await award_glow(
        db,
        owner_user_id=owner_user_id,
        event_type=payload.event_type,
        source_kind=payload.source_kind,
        source_id=payload.source_id,
        orbit_id=payload.orbit_id,
        idempotency_key=payload.idempotency_key,
    )
    await db.commit()
    return GlowRewardOut(
        transaction_id=result.transaction.id,
        event_type=result.transaction.event_type,
        awarded_points=result.transaction.final_points,
        balance=result.balance.balance,
        lifetime_points=result.balance.lifetime_points,
        idempotent_replay=result.idempotent_replay,
        streak=GlowStreakOut.model_validate(result.streak) if result.streak else None,
        achievements_unlocked=[row.achievement_key for row in result.achievements],
    )


@router.get("/summary", response_model=GlowSummaryOut)
async def summary(db: Scoped, identity: Identity) -> GlowSummaryOut:
    owner_user_id, _ = identity
    balance = (await db.execute(select(GlowBalance).where(
        GlowBalance.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    transactions = (await db.execute(select(GlowTransaction).where(
        GlowTransaction.owner_user_id == owner_user_id,
        GlowTransaction.reversed.is_(False),
    ).order_by(GlowTransaction.created_at.desc()).limit(20))).scalars().all()
    streaks = (await db.execute(select(GlowStreak).where(
        GlowStreak.owner_user_id == owner_user_id,
    ).order_by(GlowStreak.updated_at.desc()))).scalars().all()
    achievements = (await db.execute(select(GlowAchievement).where(
        GlowAchievement.owner_user_id == owner_user_id,
    ).order_by(GlowAchievement.unlocked_at.desc()))).scalars().all()
    now = dt.datetime.now(dt.timezone.utc)
    day_start = dt.datetime.combine(now.date(), dt.time.min, tzinfo=dt.timezone.utc)
    week_start = dt.datetime.combine(
        now.date() - dt.timedelta(days=now.weekday()),
        dt.time.min,
        tzinfo=dt.timezone.utc,
    )
    today_points = int((await db.execute(select(func.coalesce(
        func.sum(GlowTransaction.final_points), 0
    )).where(
        GlowTransaction.owner_user_id == owner_user_id,
        GlowTransaction.reversed.is_(False),
        GlowTransaction.created_at >= day_start,
    ))).scalar_one())
    weekly_points = int((await db.execute(select(func.coalesce(
        func.sum(GlowTransaction.final_points), 0
    )).where(
        GlowTransaction.owner_user_id == owner_user_id,
        GlowTransaction.reversed.is_(False),
        GlowTransaction.created_at >= week_start,
    ))).scalar_one())
    lifetime_points = balance.lifetime_points if balance else 0
    level, rank, next_unlock = _level_state(lifetime_points)
    return GlowSummaryOut(
        balance=balance.balance if balance else 0,
        lifetime_points=lifetime_points,
        today_points=today_points,
        weekly_points=weekly_points,
        level=level,
        rank=rank,
        next_unlock=next_unlock,
        recent_transactions=[GlowTransactionOut.model_validate(row) for row in transactions],
        streaks=[GlowStreakOut.model_validate(row) for row in streaks],
        achievements=[GlowAchievementOut.model_validate(row) for row in achievements],
        daily_quest={
            "key": "earn_verified_glow",
            "title": "Earn Glow from one persisted action.",
            "completed": today_points > 0,
            "progress": min(today_points, 1),
            "target": 1,
        },
        weekly_mission={
            "key": "return_three_moves",
            "title": "Return three source-linked actions this week.",
            "completed": len([row for row in transactions if row.created_at >= week_start]) >= 3,
            "progress": min(len([row for row in transactions if row.created_at >= week_start]), 3),
            "target": 3,
        },
    )


@router.get("/scoreboard", response_model=ScoreboardOut)
async def scoreboard(db: Scoped, identity: Identity) -> ScoreboardOut:
    """Private competition between the owner's seven Systems; no people leak."""
    owner_user_id, _ = identity
    scores = dict((await db.execute(select(
        GlowTransaction.system_slug,
        func.coalesce(func.sum(GlowTransaction.final_points), 0),
    ).where(
        GlowTransaction.owner_user_id == owner_user_id,
        GlowTransaction.reversed.is_(False),
        GlowTransaction.system_slug.is_not(None),
    ).group_by(GlowTransaction.system_slug))).all())
    ranked = sorted(
        ((system, int(scores.get(system.slug, 0))) for system in SYSTEMS),
        key=lambda row: (-row[1], row[0].title),
    )
    return ScoreboardOut(
        scope="OWNER_SYSTEMS",
        period="ALL_TIME",
        provenance_label="PERSISTED_GLOW_TRANSACTIONS",
        rows=[
            ScoreboardRow(
                rank=index,
                system_slug=system.slug,
                system_title=system.title,
                score=score,
            )
            for index, (system, score) in enumerate(ranked, start=1)
        ],
    )
