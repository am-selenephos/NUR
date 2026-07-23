import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import exists, func, select

from app.api.deps import Identity, Scoped, require_csrf
from app.living.catalog import SYSTEMS
from app.models import (
    GlowAchievement,
    GlowBalance,
    GlowLevelDefinition,
    GlowQuest,
    GlowQuestDefinition,
    GlowReversal,
    GlowRewardDefinition,
    GlowRewardRedemption,
    GlowStreak,
    GlowStreakDefinition,
    GlowTransaction,
    GlowUserLevel,
    Profile,
)
from app.services.glow_service import (
    award_glow,
    calendar_window,
    claim_quest,
    redeem_reward,
    repair_streak,
    sync_quests,
)
from app.services.engagement_policy import engagement_cue


router = APIRouter(tags=["glow"])


class IdempotencyIn(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=240)


class GlowRewardIn(BaseModel):
    event_type: str = Field(min_length=1, max_length=80)
    source_kind: str = Field(min_length=1, max_length=80)
    source_id: uuid.UUID
    orbit_id: uuid.UUID | None = None
    idempotency_key: str = Field(min_length=8, max_length=240)


class GlowAwardStreakOut(BaseModel):
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
    streak: GlowAwardStreakOut | None
    achievements_unlocked: list[str]


class GlowTransactionOut(BaseModel):
    id: uuid.UUID
    event_type: str
    source_kind: str
    source_id: uuid.UUID
    source_event_id: uuid.UUID
    system_slug: str | None
    base_points: int
    multiplier: float
    multiplier_reason: str
    rule_version: int
    final_points: int
    reason: str
    timezone: str
    local_date: dt.date
    created_at: dt.datetime
    reversed_at: dt.datetime | None = None
    reversal_reason: str | None = None


class GlowStreakOut(BaseModel):
    id: uuid.UUID
    streak_key: str
    title: str
    current_count: int
    best_count: int
    last_event_date: dt.date | None
    timezone: str
    checkpoint_count: int
    next_reward_at: int
    grace_until: dt.datetime | None
    repairs_remaining: int
    repair_cost: int
    state_reason: str


class GlowAchievementOut(BaseModel):
    achievement_key: str
    achievement_metadata: dict
    unlocked_at: dt.datetime


class GlowSummaryOut(BaseModel):
    balance: int
    lifetime_points: int
    spent_points: int
    reversal_debt: int
    today_points: int
    weekly_points: int
    level: int
    rank: str
    next_unlock: dict | None
    constellation: dict
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


def _active(transaction_id) -> object:
    return ~exists(select(GlowReversal.id).where(GlowReversal.transaction_id == transaction_id))


async def _timezone(db: Scoped, owner_user_id: uuid.UUID) -> str:
    return (
        await db.execute(select(Profile.timezone).where(Profile.user_id == owner_user_id))
    ).scalar_one_or_none() or "UTC"


async def _level_state(
    db: Scoped,
    owner_user_id: uuid.UUID,
    lifetime_points: int,
) -> tuple[int, str, dict | None, dict]:
    definitions = (
        await db.execute(
            select(GlowLevelDefinition)
            .where(GlowLevelDefinition.active.is_(True))
            .order_by(GlowLevelDefinition.threshold)
        )
    ).scalars().all()
    projection = (
        await db.execute(
            select(GlowUserLevel).where(GlowUserLevel.owner_user_id == owner_user_id)
        )
    ).scalar_one_or_none()
    current = definitions[0]
    next_level = None
    for definition in definitions:
        if lifetime_points >= definition.threshold:
            current = definition
        elif next_level is None:
            next_level = definition
    next_unlock = None
    if next_level:
        next_unlock = {
            "level": next_level.level,
            "rank": next_level.title,
            "threshold": next_level.threshold,
            "points_remaining": next_level.threshold - lifetime_points,
            "unlock": next_level.unlock_metadata,
        }
    return (
        projection.level if projection else current.level,
        current.title,
        next_unlock,
        {"stage": current.level_key, **current.unlock_metadata},
    )


async def _transaction_out(db: Scoped, row: GlowTransaction) -> GlowTransactionOut:
    reversal = (
        await db.execute(
            select(GlowReversal).where(GlowReversal.transaction_id == row.id)
        )
    ).scalar_one_or_none()
    return GlowTransactionOut(
        id=row.id,
        event_type=row.event_type,
        source_kind=row.source_kind,
        source_id=row.source_id,
        source_event_id=row.source_event_id,
        system_slug=row.system_slug,
        base_points=row.base_points,
        multiplier=float(row.multiplier),
        multiplier_reason=row.multiplier_reason,
        rule_version=row.rule_version,
        final_points=row.final_points,
        reason=row.reason,
        timezone=row.timezone,
        local_date=row.local_date,
        created_at=row.created_at,
        reversed_at=reversal.reversed_at if reversal else None,
        reversal_reason=reversal.reason if reversal else None,
    )


async def _streaks(db: Scoped, owner_user_id: uuid.UUID) -> list[GlowStreakOut]:
    rows = (
        await db.execute(
            select(GlowStreak, GlowStreakDefinition)
            .join(
                GlowStreakDefinition,
                GlowStreakDefinition.streak_key == GlowStreak.streak_key,
            )
            .where(GlowStreak.owner_user_id == owner_user_id)
            .order_by(GlowStreak.current_count.desc(), GlowStreak.updated_at.desc())
        )
    ).all()
    return [
        GlowStreakOut(
            id=streak.id,
            streak_key=streak.streak_key,
            title=definition.title,
            current_count=streak.current_count,
            best_count=streak.best_count,
            last_event_date=streak.last_event_date,
            timezone=streak.timezone,
            checkpoint_count=streak.checkpoint_count,
            next_reward_at=streak.next_reward_at,
            grace_until=streak.grace_until,
            repairs_remaining=streak.repairs_remaining,
            repair_cost=definition.repair_cost,
            state_reason=streak.state_reason,
        )
        for streak, definition in rows
    ]


def _quest_out(quest: GlowQuest, definition: GlowQuestDefinition) -> dict:
    return {
        "id": quest.id,
        "key": definition.quest_key,
        "title": definition.title,
        "cadence": definition.cadence,
        "difficulty": definition.difficulty,
        "rationale": definition.rationale,
        "target_event_types": definition.target_event_types,
        "progress": min(quest.progress_count, quest.target_count),
        "target": quest.target_count,
        "completed": quest.status in {"COMPLETED", "CLAIMED"},
        "claimed": quest.status == "CLAIMED",
        "status": quest.status,
        "reward_points": definition.reward_points,
        "period_start": quest.period_start,
        "period_end": quest.period_end,
        "timezone": quest.timezone,
        "rule_version": definition.rule_version,
    }


@router.post(
    "/glow/rewards",
    response_model=GlowRewardOut,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def award_reward(
    payload: GlowRewardIn,
    db: Scoped,
    identity: Identity,
) -> GlowRewardOut:
    """Backward-compatible award endpoint backed by the hardened G09 ledger."""
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
        streak=(
  GlowAwardStreakOut.model_validate(result.streak)
  if result.streak
  else None
        ),
        achievements_unlocked=[row.achievement_key for row in result.achievements],
    )


@router.get("/glow/summary", response_model=GlowSummaryOut)
async def summary(db: Scoped, identity: Identity) -> GlowSummaryOut:
    owner_user_id, _ = identity
    quests = await sync_quests(db, owner_user_id=owner_user_id)
    balance = (
        await db.execute(
            select(GlowBalance).where(GlowBalance.owner_user_id == owner_user_id)
        )
    ).scalar_one_or_none()
    transactions = (
        await db.execute(
            select(GlowTransaction)
            .where(
                GlowTransaction.owner_user_id == owner_user_id,
                _active(GlowTransaction.id),
            )
            .order_by(GlowTransaction.created_at.desc())
            .limit(20)
        )
    ).scalars().all()
    timezone_name = await _timezone(db, owner_user_id)
    now = dt.datetime.now(dt.UTC)
    day = calendar_window(now, timezone_name, "DAILY")
    week = calendar_window(now, timezone_name, "WEEKLY")
    today_points = int(
        (
            await db.execute(
                select(func.coalesce(func.sum(GlowTransaction.final_points), 0)).where(
                    GlowTransaction.owner_user_id == owner_user_id,
                    GlowTransaction.created_at >= day.start,
                    GlowTransaction.created_at < day.end,
                    _active(GlowTransaction.id),
                )
            )
        ).scalar_one()
    )
    weekly_points = int(
        (
            await db.execute(
                select(func.coalesce(func.sum(GlowTransaction.final_points), 0)).where(
                    GlowTransaction.owner_user_id == owner_user_id,
                    GlowTransaction.created_at >= week.start,
                    GlowTransaction.created_at < week.end,
                    _active(GlowTransaction.id),
                )
            )
        ).scalar_one()
    )
    lifetime_points = balance.lifetime_points if balance else 0
    level, rank, next_unlock, constellation = await _level_state(
        db, owner_user_id, lifetime_points
    )
    achievements = (
        await db.execute(
            select(GlowAchievement)
            .where(
                GlowAchievement.owner_user_id == owner_user_id,
                GlowAchievement.revoked_at.is_(None),
            )
            .order_by(GlowAchievement.unlocked_at.desc())
        )
    ).scalars().all()
    daily_quests = [_quest_out(*item) for item in quests if item[1].cadence == "DAILY"]
    weekly_quests = [_quest_out(*item) for item in quests if item[1].cadence == "WEEKLY"]
    transaction_rows = [await _transaction_out(db, row) for row in transactions]
    streak_rows = await _streaks(db, owner_user_id)
    await db.commit()
    return GlowSummaryOut(
        balance=balance.balance if balance else 0,
        lifetime_points=lifetime_points,
        spent_points=balance.spent_points if balance else 0,
        reversal_debt=balance.reversal_debt if balance else 0,
        today_points=today_points,
        weekly_points=weekly_points,
        level=level,
        rank=rank,
        next_unlock=next_unlock,
        constellation=constellation,
        recent_transactions=transaction_rows,
        streaks=streak_rows,
        achievements=[
            GlowAchievementOut(
                achievement_key=row.achievement_key,
                achievement_metadata=row.achievement_metadata,
                unlocked_at=row.unlocked_at,
            )
            for row in achievements
        ],
        daily_quest=daily_quests[0] if daily_quests else {},
        weekly_mission=weekly_quests[0] if weekly_quests else {},
    )


@router.get("/glow/transactions", response_model=list[GlowTransactionOut])
async def transactions(
    db: Scoped,
    identity: Identity,
    include_reversed: bool = True,
    limit: int = 50,
) -> list[GlowTransactionOut]:
    owner_user_id, _ = identity
    query = select(GlowTransaction).where(
        GlowTransaction.owner_user_id == owner_user_id
    )
    if not include_reversed:
        query = query.where(_active(GlowTransaction.id))
    rows = (
        await db.execute(
            query.order_by(GlowTransaction.created_at.desc()).limit(min(max(limit, 1), 100))
        )
    ).scalars().all()
    return [await _transaction_out(db, row) for row in rows]


@router.get("/glow/levels")
async def levels(db: Scoped, identity: Identity) -> dict:
    owner_user_id, _ = identity
    balance = (
        await db.execute(
            select(GlowBalance).where(GlowBalance.owner_user_id == owner_user_id)
        )
    ).scalar_one_or_none()
    definitions = (
        await db.execute(
            select(GlowLevelDefinition)
            .where(GlowLevelDefinition.active.is_(True))
            .order_by(GlowLevelDefinition.threshold)
        )
    ).scalars().all()
    current, rank, next_unlock, constellation = await _level_state(
        db, owner_user_id, balance.lifetime_points if balance else 0
    )
    return {
        "current_level": current,
        "current_rank": rank,
        "next_unlock": next_unlock,
        "constellation": constellation,
        "definitions": [
            {
                "level": row.level,
                "key": row.level_key,
                "title": row.title,
                "threshold": row.threshold,
                "unlock": row.unlock_metadata,
            }
            for row in definitions
        ],
    }


@router.get("/glow/engagement-cue")
async def cue(db: Scoped, identity: Identity) -> dict:
    owner_user_id, _ = identity
    await sync_quests(db, owner_user_id=owner_user_id)
    result = await engagement_cue(db, owner_user_id=owner_user_id)
    await db.commit()
    return result


@router.get("/streaks", response_model=list[GlowStreakOut])
async def streaks(db: Scoped, identity: Identity) -> list[GlowStreakOut]:
    owner_user_id, _ = identity
    return await _streaks(db, owner_user_id)


@router.post(
    "/streaks/{streak_id}/repair",
    dependencies=[Depends(require_csrf)],
)
async def repair(
    streak_id: uuid.UUID,
    payload: IdempotencyIn,
    db: Scoped,
    identity: Identity,
) -> dict:
    owner_user_id, _ = identity
    result = await repair_streak(
        db,
        owner_user_id=owner_user_id,
        streak_id=streak_id,
        idempotency_key=payload.idempotency_key,
    )
    streak_rows = await _streaks(db, owner_user_id)
    streak_row = next(row for row in streak_rows if row.id == streak_id)
    await db.commit()
    return {
        "repair_id": result.repair.id,
        "status": result.repair.status,
        "cost_points": result.repair.cost_points,
        "balance": result.balance.balance,
        "streak": streak_row.model_dump(),
        "idempotent_replay": result.idempotent_replay,
    }


@router.get("/quests")
async def quests(db: Scoped, identity: Identity) -> list[dict]:
    owner_user_id, _ = identity
    rows = await sync_quests(db, owner_user_id=owner_user_id)
    await db.commit()
    return [_quest_out(quest, definition) for quest, definition in rows]


@router.post(
    "/quests/{quest_id}/claim",
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def claim(
    quest_id: uuid.UUID,
    payload: IdempotencyIn,
    db: Scoped,
    identity: Identity,
) -> dict:
    owner_user_id, _ = identity
    result = await claim_quest(
        db,
        owner_user_id=owner_user_id,
        quest_id=quest_id,
        idempotency_key=payload.idempotency_key,
    )
    await db.commit()
    return {
        "transaction_id": result.transaction.id,
        "awarded_points": result.transaction.final_points,
        "balance": result.balance.balance,
        "lifetime_points": result.balance.lifetime_points,
        "idempotent_replay": result.idempotent_replay,
    }


@router.get("/achievements", response_model=list[GlowAchievementOut])
async def achievements(db: Scoped, identity: Identity) -> list[GlowAchievementOut]:
    owner_user_id, _ = identity
    rows = (
        await db.execute(
            select(GlowAchievement)
            .where(
                GlowAchievement.owner_user_id == owner_user_id,
                GlowAchievement.revoked_at.is_(None),
            )
            .order_by(GlowAchievement.unlocked_at.desc())
        )
    ).scalars().all()
    return [
        GlowAchievementOut(
            achievement_key=row.achievement_key,
            achievement_metadata=row.achievement_metadata,
            unlocked_at=row.unlocked_at,
        )
        for row in rows
    ]


@router.get("/glow/rewards")
async def rewards(db: Scoped, identity: Identity) -> dict:
    owner_user_id, _ = identity
    balance = (
        await db.execute(
            select(GlowBalance).where(GlowBalance.owner_user_id == owner_user_id)
        )
    ).scalar_one_or_none()
    definitions = (
        await db.execute(
            select(GlowRewardDefinition)
            .where(GlowRewardDefinition.active.is_(True))
            .order_by(GlowRewardDefinition.cost_points)
        )
    ).scalars().all()
    owned = set(
        (
            await db.execute(
                select(GlowRewardRedemption.reward_key).where(
                    GlowRewardRedemption.owner_user_id == owner_user_id,
                    GlowRewardRedemption.status == "REDEEMED",
                )
            )
        ).scalars().all()
    )
    return {
        "balance": balance.balance if balance else 0,
        "reversal_debt": balance.reversal_debt if balance else 0,
        "items": [
            {
                "reward_key": row.reward_key,
                "title": row.title,
                "category": row.category,
                "cost_points": row.cost_points,
                "minimum_level": row.minimum_level,
                "metadata": row.reward_metadata,
                "owned": row.reward_key in owned,
            }
            for row in definitions
        ],
    }


@router.post(
    "/glow/rewards/{reward_key}/redeem",
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def redeem(
    reward_key: str,
    payload: IdempotencyIn,
    db: Scoped,
    identity: Identity,
) -> dict:
    owner_user_id, _ = identity
    result = await redeem_reward(
        db,
        owner_user_id=owner_user_id,
        reward_key=reward_key,
        idempotency_key=payload.idempotency_key,
    )
    await db.commit()
    return {
        "redemption_id": result.redemption.id,
        "reward_key": result.redemption.reward_key,
        "cost_points": result.redemption.cost_points,
        "balance": result.balance.balance,
        "idempotent_replay": result.idempotent_replay,
    }


async def _system_scoreboard(db: Scoped, owner_user_id: uuid.UUID) -> ScoreboardOut:
    scores = dict(
        (
            await db.execute(
                select(
                    GlowTransaction.system_slug,
                    func.coalesce(func.sum(GlowTransaction.final_points), 0),
                )
                .where(
                    GlowTransaction.owner_user_id == owner_user_id,
                    GlowTransaction.system_slug.is_not(None),
                    _active(GlowTransaction.id),
                )
                .group_by(GlowTransaction.system_slug)
            )
        ).all()
    )
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


@router.get("/leaderboards/{scope}", response_model=ScoreboardOut)
async def leaderboard(scope: str, db: Scoped, identity: Identity) -> ScoreboardOut:
    owner_user_id, _ = identity
    if scope != "systems":
        raise HTTPException(
            422,
            "Only the private owner Systems board is live; social boards require explicit opt-in.",
        )
    return await _system_scoreboard(db, owner_user_id)


@router.get("/glow/scoreboard", response_model=ScoreboardOut)
async def scoreboard(db: Scoped, identity: Identity) -> ScoreboardOut:
    owner_user_id, _ = identity
    return await _system_scoreboard(db, owner_user_id)
