import pytest
from sqlalchemy import text

from app.tests.conftest import register_user


def H(client) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("nur_csrf")}


def save_cookies(client) -> dict[str, str]:
    return dict(client.cookies)


def use_cookies(client, cookies: dict[str, str]) -> None:
    client.cookies.clear()
    for name, value in cookies.items():
        client.cookies.set(name, value)


async def test_group_nur_room_council_and_private_memory_boundaries(client, app_engine):
    owner_response, _, _ = await register_user(client, chosen_name="Group Owner")
    owner_id = owner_response.json()["id"]
    owner_cookies = save_cookies(client)
    secret = await client.post(
        "/api/v1/journal",
        headers=H(client),
        json={"body": "Owner-private line that no room member may retrieve."},
    )
    assert secret.status_code == 201, secret.text

    group = await client.post(
        "/api/v1/community/rooms",
        headers=H(client),
        json={
            "title": "Build circle",
            "description": "A bounded room for one shared build.",
            "room_kind": "GROUP",
            "language_tag": "en",
        },
    )
    assert group.status_code == 201, group.text
    group_id = group.json()["id"]
    assert group.json()["current_user_role"] == "OWNER"
    assert "Private Talk" in group.json()["privacy"]

    client.cookies.clear()
    recipient_response, recipient_email, _ = await register_user(client, chosen_name="Group Member")
    recipient_id = recipient_response.json()["id"]
    recipient_cookies = save_cookies(client)

    client.cookies.clear()
    outsider_response, _, _ = await register_user(client, chosen_name="Outside Account")
    outsider_id = outsider_response.json()["id"]
    outsider_cookies = save_cookies(client)

    use_cookies(client, owner_cookies)
    membership = await client.post(
        f"/api/v1/community/rooms/{group_id}/members",
        headers=H(client),
        json={"email": recipient_email, "role": "MEMBER"},
    )
    assert membership.status_code == 201, membership.text

    owner_post = await client.post(
        f"/api/v1/community/rooms/{group_id}/posts",
        headers=H(client),
        json={"title": "Release evidence", "body": "Return one verified test result."},
    )
    assert owner_post.status_code == 201, owner_post.text
    demo_message = await client.post(
        f"/api/v1/community/rooms/{group_id}/messages",
        headers=H(client),
        json={"body": "DEMO: visible, persisted, and never rewarded.", "is_demo": True},
    )
    assert demo_message.status_code == 201, demo_message.text
    assert demo_message.json()["glow"]["status"] == "GLOW_GATED"
    assert demo_message.json()["glow"]["awarded_points"] == 0

    use_cookies(client, recipient_cookies)
    rooms = await client.get("/api/v1/community/rooms")
    assert rooms.status_code == 200, rooms.text
    assert [row["id"] for row in rooms.json()] == [group_id]
    assert rooms.json()[0]["current_user_role"] == "MEMBER"
    assert (await client.post(
        f"/api/v1/community/rooms/{group_id}/members",
        headers=H(client),
        json={"email": recipient_email, "role": "MEMBER"},
    )).status_code == 403

    member_message = await client.post(
        f"/api/v1/community/rooms/{group_id}/messages",
        headers=H(client),
        json={"body": "The acceptance test is green.", "language_tag": "en"},
    )
    assert member_message.status_code == 201, member_message.text
    assert member_message.json()["provenance_label"] == "MEMBER_WRITTEN"
    assert member_message.json()["glow"]["status"] == "AWARDED"
    assert member_message.json()["glow"]["awarded_points"] > 0
    member_post = await client.post(
        f"/api/v1/community/rooms/{group_id}/posts",
        headers=H(client),
        json={"title": "Member evidence", "body": "The persisted result is attached."},
    )
    assert member_post.status_code == 201, member_post.text
    comment = await client.post(
        f"/api/v1/community/rooms/{group_id}/posts/{owner_post.json()['id']}/comments",
        headers=H(client),
        json={"body": "Confirmed from my owned test account."},
    )
    assert comment.status_code == 201, comment.text
    reaction = await client.post(
        f"/api/v1/community/rooms/{group_id}/reactions",
        headers=H(client),
        json={
            "target_kind": "POST",
            "target_id": owner_post.json()["id"],
            "reaction": "USEFUL",
        },
    )
    assert reaction.status_code == 201, reaction.text

    private_journal = await client.get("/api/v1/journal")
    assert private_journal.status_code == 200
    assert all("Owner-private line" not in row["body"] for row in private_journal.json())
    actor_events = await client.get("/api/v1/cognition/events")
    assert actor_events.status_code == 200
    assert any(row["event_kind"] == "COMMUNITY_NOTE_CREATED" for row in actor_events.json())
    assert all("Owner-private line" not in (row["content_text"] or "") for row in actor_events.json())

    use_cookies(client, outsider_cookies)
    assert (await client.get("/api/v1/community/rooms")).json() == []
    assert (await client.get(f"/api/v1/community/rooms/{group_id}")).status_code == 404
    assert (await client.get(f"/api/v1/community/rooms/{group_id}/messages")).status_code == 404

    use_cookies(client, owner_cookies)
    council = await client.post(
        "/api/v1/community/rooms",
        headers=H(client),
        json={"title": "Release council", "room_kind": "COUNCIL"},
    )
    assert council.status_code == 201, council.text
    council_id = council.json()["id"]
    added = await client.post(
        f"/api/v1/community/rooms/{council_id}/members",
        headers=H(client),
        json={"email": recipient_email, "role": "MEMBER"},
    )
    assert added.status_code == 201, added.text

    use_cookies(client, recipient_cookies)
    position = await client.post(
        f"/api/v1/community/rooms/{council_id}/positions",
        headers=H(client),
        json={
            "position": "Release after the final browser proof.",
            "evidence": ["owned acceptance test"],
            "is_minority": True,
        },
    )
    assert position.status_code == 201, position.text
    denied_decision = await client.post(
        f"/api/v1/community/rooms/{council_id}/decision",
        headers=H(client),
        json={"decision": "A member must not finalize this."},
    )
    assert denied_decision.status_code == 403

    use_cookies(client, owner_cookies)
    decision = await client.post(
        f"/api/v1/community/rooms/{council_id}/decision",
        headers=H(client),
        json={
            "decision": "Return after WebKit proof is attached.",
            "rationale": "The evidence boundary is explicit.",
            "minority_opinion": "The member preferred one more browser pass.",
        },
    )
    assert decision.status_code == 201, decision.text
    summary = await client.get(f"/api/v1/community/rooms/{council_id}/summary")
    assert summary.status_code == 200, summary.text
    assert summary.json()["counts"] == {
        "messages": 0,
        "posts": 0,
        "comments": 0,
        "positions": 1,
        "decisions": 1,
        "members": 2,
    }
    assert summary.json()["external_public_feed"] == "not_connected"
    live = await client.get("/api/v1/universe/live")
    assert live.status_code == 200, live.text
    assert live.json()["community"]["status"] == "BOUNDED_GROUP_NUR_CONNECTED"
    assert live.json()["community"]["room_count"] == 2
    assert live.json()["community"]["external_public_feed_connected"] is False

    tables = [
        "community_rooms",
        "community_memberships",
        "community_messages",
        "community_posts",
        "community_comments",
        "community_reactions",
        "council_positions",
        "council_decisions",
    ]
    async with app_engine.connect() as connection:
        await connection.execute(
            text("SELECT set_config('app.current_user_id', :uid, false)"),
            {"uid": outsider_id},
        )
        flags = (await connection.execute(text("""
            SELECT relname, relrowsecurity, relforcerowsecurity
            FROM pg_class
            WHERE relname = ANY(:tables)
            ORDER BY relname
        """), {"tables": tables})).all()
        assert len(flags) == len(tables)
        assert all(row.relrowsecurity and row.relforcerowsecurity for row in flags)
        for table in tables:
            count = (await connection.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one()
            assert count == 0, f"Outsider could see rows in {table}"

    async with app_engine.connect() as connection:
        await connection.execute(
            text("SELECT set_config('app.current_user_id', :uid, false)"),
            {"uid": recipient_id},
        )
        with pytest.raises(Exception):
            await connection.execute(text("""
                INSERT INTO council_decisions(
                    room_id, room_owner_user_id, owner_user_id, decision
                ) VALUES (:room_id, :room_owner_user_id, :owner_user_id, 'forged')
            """), {
                "room_id": council_id,
                "room_owner_user_id": owner_id,
                "owner_user_id": recipient_id,
            })
