import datetime as dt

from sqlalchemy import text

from app.tests.conftest import register_user


def H(client) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("nur_csrf")}


async def test_today_system_goal_schedule_glow_and_timeline_are_one_persisted_flow(client):
    await register_user(client, chosen_name="Living System Owner")

    initial_systems = (await client.get("/api/v1/systems")).json()["systems"]
    assert [row["title"] for row in initial_systems] == [
        "Quiet Ambition",
        "Rebuild",
        "Study",
        "Money",
        "Body",
        "Connection",
        "Creation",
    ]
    assert all(row["progress_percent"] == 0 for row in initial_systems)

    diagnostic = await client.post(
        "/api/v1/systems/quiet-ambition/diagnostics",
        headers=H(client),
        json={
            "answers": {"private_direction": "Ship one real NUR slice."},
            "ratings": {"clarity": 8, "protection": 6, "movement": 5},
            "blockers": ["scope expansion"],
            "strengths": ["continuity"],
        },
    )
    assert diagnostic.status_code == 201
    assert diagnostic.json()["score"] == 63
    assert diagnostic.json()["glow"]["awarded_points"] == 3

    goal = await client.post(
        "/api/v1/goals",
        headers=H(client),
        json={
            "system_slug": "quiet-ambition",
            "title": "Ship the persisted daily operating slice",
            "why": "Turn private direction into verified movement.",
        },
    )
    assert goal.status_code == 201
    assert goal.json()["glow"]["awarded_points"] == 8

    objective = await client.post(
        f"/api/v1/goals/{goal.json()['id']}/objectives",
        headers=H(client),
        json={"title": "Complete one real end-to-end action"},
    )
    assert objective.status_code == 201
    assert objective.json()["glow"]["awarded_points"] == 6

    action = await client.post(
        "/api/v1/systems/quiet-ambition/actions",
        headers=H(client),
        json={
            "title": "Run the real owner journey test",
            "goal_id": goal.json()["id"],
            "objective_id": objective.json()["id"],
            "diagnostic_id": diagnostic.json()["id"],
            "effort_minutes": 20,
        },
    )
    assert action.status_code == 201
    action_id = action.json()["id"]

    schedule = await client.post(
        "/api/v1/schedules",
        headers=H(client),
        json={
            "system_slug": "quiet-ambition",
            "title": "Run the real owner journey test",
            "scheduled_for": dt.datetime.now(dt.UTC).isoformat(),
            "duration_minutes": 20,
            "goal_id": goal.json()["id"],
            "objective_id": objective.json()["id"],
            "system_action_id": action_id,
        },
    )
    assert schedule.status_code == 201
    assert schedule.json()["glow"]["awarded_points"] == 5

    missed = await client.post(
        "/api/v1/today/miss-action",
        headers=H(client),
        json={"action_id": action_id},
    )
    assert missed.status_code == 200
    assert missed.json()["action"]["status"] == "MISSED"
    assert missed.json()["glow"]["awarded_points"] == 0

    returned = await client.post(
        "/api/v1/today/complete-action",
        headers=H(client),
        json={"action_id": action_id},
    )
    assert returned.status_code == 200
    assert returned.json()["action"]["status"] == "COMPLETED"
    assert returned.json()["glow"]["awarded_points"] == 6
    assert returned.json()["return_glow"]["awarded_points"] == 7
    assert returned.json()["today"]["completed_today"][0]["id"] == action_id

    checkin = await client.post(
        "/api/v1/today/check-in",
        headers=H(client),
        json={
            "energy": 8,
            "pain": 2,
            "sleep_quality": 7,
            "nourishment": 8,
            "movement": 6,
            "emotional_load": 3,
            "clarity": 8,
            "note": "Capacity is real and measured.",
        },
    )
    assert checkin.status_code == 200
    assert checkin.json()["glow"]["awarded_points"] == 2
    assert checkin.json()["today"]["body"]["score"] > 0
    assert checkin.json()["today"]["mind"]["score"] > 0
    assert checkin.json()["today"]["body"]["sources"]["today_checkin"] is not None

    same_day = await client.post(
        "/api/v1/today/check-in",
        headers=H(client),
        json={
            "energy": 7,
            "pain": 2,
            "sleep_quality": 7,
            "nourishment": 8,
            "movement": 7,
            "emotional_load": 3,
            "clarity": 8,
        },
    )
    assert same_day.status_code == 200
    assert same_day.json()["glow"]["idempotent_replay"] is True

    detail = (await client.get("/api/v1/systems/quiet-ambition")).json()
    assert detail["progress_percent"] > 0
    assert detail["progress_sources"]["completed_actions"] == 1
    assert detail["progress_sources"]["glow_points"] == 35
    assert detail["prediction"]["provenance_label"] == "DETERMINISTIC_INFERENCE"

    glow = (await client.get("/api/v1/glow/summary")).json()
    assert glow["lifetime_points"] == 37
    assert glow["today_points"] == 37
    assert glow["level"] == 1
    assert glow["rank"] == "Orbit Seed"
    assert glow["achievements"][0]["achievement_key"] == "first_glow"

    scoreboard = (await client.get("/api/v1/glow/scoreboard")).json()
    assert scoreboard["provenance_label"] == "PERSISTED_GLOW_TRANSACTIONS"
    assert scoreboard["rows"][0]["system_slug"] == "quiet-ambition"
    assert scoreboard["rows"][0]["score"] == 35
    body = next(row for row in scoreboard["rows"] if row["system_slug"] == "body")
    assert body["score"] == 2

    timeline = (await client.get("/api/v1/universe/timeline")).json()["items"]
    timeline_kinds = {row["kind"] for row in timeline}
    assert {
        "SYSTEM_DIAGNOSTIC_RECORDED",
        "GOAL_CREATED",
        "OBJECTIVE_CREATED",
        "SCHEDULE_CREATED",
        "SYSTEM_ACTION_MISSED",
        "SYSTEM_ACTION_COMPLETED",
        "TODAY_CHECKIN",
    } <= timeline_kinds


async def test_make_easier_preserves_lineage_and_only_rewards_completed_replacement(client):
    await register_user(client)
    original = await client.post(
        "/api/v1/systems/body/actions",
        headers=H(client),
        json={"title": "Exercise for one hour", "effort_minutes": 60},
    )
    easier = await client.post(
        "/api/v1/today/make-easier",
        headers=H(client),
        json={
            "action_id": original.json()["id"],
            "title": "Stretch for five minutes",
            "effort_minutes": 5,
        },
    )
    assert easier.status_code == 201
    body = easier.json()
    assert body["original"]["status"] == "CANCELLED"
    assert body["replacement"]["easier_from_id"] == original.json()["id"]
    assert body["glow"]["awarded_points"] == 0

    complete = await client.post(
        "/api/v1/today/complete-action",
        headers=H(client),
        json={"action_id": body["replacement"]["id"]},
    )
    assert complete.status_code == 200
    assert complete.json()["glow"]["awarded_points"] == 6


async def test_map_future_timeline_and_feasibility_are_derived_and_persisted(client):
    await register_user(client, chosen_name="Map Owner")
    await client.post(
        "/api/v1/today/check-in",
        headers=H(client),
        json={
            "energy": 8,
            "pain": 2,
            "sleep_quality": 8,
            "nourishment": 8,
            "movement": 7,
            "emotional_load": 3,
            "clarity": 8,
        },
    )
    goal = await client.post(
        "/api/v1/goals",
        headers=H(client),
        json={"system_slug": "body", "title": "Protect enough energy to keep moving"},
    )
    future = dt.datetime.now(dt.UTC) + dt.timedelta(days=3)
    schedule = await client.post(
        "/api/v1/schedules",
        headers=H(client),
        json={
            "system_slug": "body",
            "title": "Review the capacity trend",
            "scheduled_for": future.isoformat(),
            "goal_id": goal.json()["id"],
        },
    )
    assert schedule.status_code == 201

    assessment = await client.post(
        "/api/v1/feasibility",
        headers=H(client),
        json={
            "system_slug": "body",
            "subject_kind": "ACTION",
            "title": "Twenty minute recovery walk",
            "desired_outcome": "Support energy without exceeding capacity.",
            "capacity_required": 40,
            "time_required_minutes": 20,
            "time_available_minutes": 30,
            "money_required_cents": 0,
            "money_available_cents": 0,
            "risk_level": "LOW",
        },
    )
    assert assessment.status_code == 201
    assert assessment.json()["result"] == "FEASIBLE"
    assert assessment.json()["current_capacity"] >= 40
    assert assessment.json()["glow"]["awarded_points"] == 5
    assert assessment.json()["source_refs"] == ["today.body"]

    prediction = await client.post(
        "/api/v1/map/predict-path",
        headers=H(client),
        json={
            "system_slug": "body",
            "path_type": "easier",
            "goal_id": goal.json()["id"],
            "horizon_days": 14,
        },
    )
    assert prediction.status_code == 201
    assert prediction.json()["status"] == "OPEN"
    assert prediction.json()["expected_observation"]["path_type"] == "easier"
    assert prediction.json()["provenance_label"] == "DETERMINISTIC_HYPOTHESIS"

    graph = (await client.get("/api/v1/map")).json()
    assert graph["provenance_label"] == "OWNER_LEDGER_DERIVED_GRAPH"
    node_ids = {row["id"] for row in graph["nodes"]}
    assert "nur" in node_ids
    assert {f"system:{slug}" for slug in (
        "quiet-ambition", "rebuild", "study", "money", "body", "connection", "creation"
    )} <= node_ids
    assert f"goal:{goal.json()['id']}" in node_ids
    assert f"prediction:{prediction.json()['id']}" in node_ids
    assert any(edge["kind"] == "SYSTEM_TO_GOAL" for edge in graph["edges"])

    rebuilt = await client.post("/api/v1/map/rebuild", headers=H(client))
    assert rebuilt.status_code == 200
    assert rebuilt.json()["rebuild"]["status"] == "REBUILT_FROM_OWNER_LEDGER"

    timeline = (await client.get("/api/v1/universe/timeline")).json()["items"]
    future_item = next(row for row in timeline if row["id"] == schedule.json()["id"])
    assert future_item["lane"] == "future"
    assert future_item["kind"] == "SCHEDULE_DUE"
    assert any(row["kind"] == "PREDICTION_MADE" for row in timeline)
    assert any(row["kind"] == "FEASIBILITY_CREATED" for row in timeline)

    insights = (await client.get("/api/v1/universe/insights-summary")).json()
    assert insights["counts"]["feasibility_assessments"] == 1
    assert insights["feasibility"][0]["result"] == "FEASIBLE"


async def test_living_tables_force_rls_and_hide_every_foreign_owner_row(
    client, app_engine
):
    owner_a, _, _ = await register_user(client, chosen_name="Owner A")
    goal = await client.post(
        "/api/v1/goals",
        headers=H(client),
        json={"system_slug": "study", "title": "Owner A private goal"},
    )
    action = await client.post(
        "/api/v1/systems/study/actions",
        headers=H(client),
        json={"title": "Owner A private action", "goal_id": goal.json()["id"]},
    )
    await client.post(
        "/api/v1/systems/study/diagnostics",
        headers=H(client),
        json={"ratings": {"clarity": 5}},
    )
    await client.post(
        "/api/v1/schedules",
        headers=H(client),
        json={
            "system_slug": "study",
            "title": "Owner A private schedule",
            "scheduled_for": dt.datetime.now(dt.UTC).isoformat(),
            "goal_id": goal.json()["id"],
            "system_action_id": action.json()["id"],
        },
    )
    await client.post(
        "/api/v1/today/check-in",
        headers=H(client),
        json={
            "energy": 5,
            "pain": 5,
            "sleep_quality": 5,
            "nourishment": 5,
            "movement": 5,
            "emotional_load": 5,
            "clarity": 5,
        },
    )

    client.cookies.clear()
    owner_b, _, _ = await register_user(client, chosen_name="Owner B")
    assert (await client.get("/api/v1/goals")).json() == []
    denied = await client.patch(
        f"/api/v1/system-actions/{action.json()['id']}",
        headers=H(client),
        json={"status": "COMPLETED"},
    )
    assert denied.status_code == 404

    tables = [
        "goals",
        "objectives",
        "system_diagnostics",
        "system_actions",
        "scheduled_actions",
        "today_checkins",
        "glow_achievements",
        "feasibility_assessments",
    ]
    async with app_engine.connect() as conn:
        await conn.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": owner_b.json()["id"]},
        )
        counts = {
            table: (await conn.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one()
            for table in tables
        }
        forced = dict((await conn.execute(text("""
            SELECT relname, relforcerowsecurity
            FROM pg_class
            WHERE relname = ANY(:tables)
        """), {"tables": tables})).all())
        await conn.rollback()

    assert all(value == 0 for value in counts.values())
    assert set(forced) == set(tables)
    assert all(forced.values())
    assert owner_a.json()["id"] != owner_b.json()["id"]
