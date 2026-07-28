import json

from sqlalchemy import text

from app.i18n.provider import TranslationProviderResult, get_translation_provider
from app.tests.conftest import register_user


def H(client) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("nur_csrf")}


def save_cookies(client) -> dict[str, str]:
    return dict(client.cookies)


def use_cookies(client, cookies: dict[str, str]) -> None:
    client.cookies.clear()
    for name, value in cookies.items():
        client.cookies.set(name, value)


class CommunityTranslationProvider:
    name = "community-test-provider"
    version = "community-test-provider:v1"

    async def translate(self, **kwargs) -> TranslationProviderResult:
        return TranslationProviderResult(
            available=True,
            provider=self.name,
            model="community-test-model",
            provider_version=self.version,
            translated_text=f"FR: {kwargs['source_text']}",
            detected_source_locale=kwargs["source_locale"] or "en",
        )


async def test_community_social_reconnect_feed_relationships_and_translation(client):
    owner_response, _, _ = await register_user(client, chosen_name="Social Room Owner")
    owner_id = owner_response.json()["id"]
    owner_cookies = save_cookies(client)

    client.cookies.clear()
    author_response, author_email, _ = await register_user(
        client, chosen_name="Social Room Author"
    )
    author_id = author_response.json()["id"]
    author_cookies = save_cookies(client)

    client.cookies.clear()
    reader_response, reader_email, _ = await register_user(
        client, chosen_name="Social Room Reader"
    )
    reader_id = reader_response.json()["id"]
    reader_cookies = save_cookies(client)

    use_cookies(client, owner_cookies)
    room = await client.post(
        "/api/v1/community/rooms",
        headers=H(client),
        json={"title": "Persisted signal room", "room_kind": "COMMUNITY"},
    )
    assert room.status_code == 201, room.text
    room_id = room.json()["id"]
    for email in (author_email, reader_email):
        member = await client.post(
            f"/api/v1/community/rooms/{room_id}/members",
            headers=H(client),
            json={"email": email, "role": "MEMBER"},
        )
        assert member.status_code == 201, member.text
    promoted = await client.patch(
        f"/api/v1/community/rooms/{room_id}/members/{author_id}",
        headers=H(client),
        json={"role": "MODERATOR"},
    )
    assert promoted.status_code == 200, promoted.text
    assert promoted.json()["role"] == "MODERATOR"

    pubsub = client.app.state.redis.pubsub()
    await pubsub.subscribe(f"nur:community:room:{room_id}")
    try:
        subscribed = await pubsub.get_message(
            ignore_subscribe_messages=False,
            timeout=1,
        )
        assert subscribed["type"] == "subscribe"
        first = await client.post(
            f"/api/v1/community/rooms/{room_id}/messages",
            headers=H(client),
            json={"body": "Owner sequence one."},
        )
        assert first.status_code == 201, first.text
        assert first.json()["sequence"] == 1
        assert first.json()["realtime_signal"] == "PUBLISHED"
        realtime = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1)
        assert json.loads(realtime["data"]) == {"room_id": room_id, "sequence": 1}
    finally:
        await pubsub.aclose()

    use_cookies(client, author_cookies)
    second = await client.post(
        f"/api/v1/community/rooms/{room_id}/messages",
        headers=H(client),
        json={"body": "Author sequence two."},
    )
    assert second.status_code == 201, second.text
    assert second.json()["sequence"] == 2
    post = await client.post(
        f"/api/v1/community/rooms/{room_id}/posts",
        headers=H(client),
        json={"title": "Persisted evidence", "body": "The first body is reviewable."},
    )
    assert post.status_code == 201, post.text
    post_id = post.json()["id"]
    revised = await client.patch(
        f"/api/v1/community/rooms/{room_id}/content/POST/{post_id}",
        headers=H(client),
        json={
            "title": "Persisted evidence revised",
            "body": "The corrected body remains attributable.",
            "reason": "Clarified after evidence review.",
        },
    )
    assert revised.status_code == 200, revised.text
    assert revised.json()["revision_number"] == 2
    assert revised.json()["status"] == "EDITED"
    revisions = await client.get(
        f"/api/v1/community/rooms/{room_id}/content/POST/{post_id}/revisions"
    )
    assert revisions.status_code == 200, revisions.text
    assert revisions.json()[0]["previous_body"] == "The first body is reviewable."

    use_cookies(client, reader_cookies)
    third = await client.post(
        f"/api/v1/community/rooms/{room_id}/messages",
        headers=H(client),
        json={"body": "Reader sequence three."},
    )
    assert third.status_code == 201, third.text
    assert third.json()["sequence"] == 3
    sync = await client.get(
        f"/api/v1/community/rooms/{room_id}/messages/sync?after_sequence=1"
    )
    assert sync.status_code == 200, sync.text
    assert [row["sequence"] for row in sync.json()["messages"]] == [2, 3]
    assert sync.json()["latest_sequence"] == 3
    assert sync.json()["has_more"] is False
    assert sync.json()["wait_state"] == "NOT_REQUESTED"

    saved = await client.post(
        f"/api/v1/community/rooms/{room_id}/saves",
        headers=H(client),
        json={"target_kind": "POST", "target_id": post_id},
    )
    assert saved.status_code == 201, saved.text
    assert saved.json()["idempotent_replay"] is False
    feed = await client.get("/api/v1/community/feed")
    assert feed.status_code == 200, feed.text
    assert [row["target_id"] for row in feed.json()["items"]] == [post_id]
    assert feed.json()["items"][0]["saved"] is True
    assert feed.json()["items"][0]["rank_explanation"]["candidate_source"] == (
        "PERSISTED_SHARED_ROOM_MEMBERSHIP"
    )
    assert feed.json()["release_state"] == "COHORT_ONLY"
    assert feed.json()["public_discovery"] is False
    assert feed.json()["next_offset"] is None

    muted = await client.post(
        "/api/v1/community/relationships",
        headers=H(client),
        json={"target_email": author_email, "relationship_kind": "MUTE"},
    )
    assert muted.status_code == 200, muted.text
    assert (await client.get("/api/v1/community/feed")).json()["items"] == []
    unmuted = await client.delete(
        f"/api/v1/community/relationships/MUTE/{author_id}", headers=H(client)
    )
    assert unmuted.status_code == 200, unmuted.text
    followed = await client.post(
        "/api/v1/community/relationships",
        headers=H(client),
        json={"target_email": author_email, "relationship_kind": "FOLLOW"},
    )
    assert followed.status_code == 200, followed.text
    assert followed.json()["connected"] is False

    use_cookies(client, author_cookies)
    reciprocal = await client.post(
        "/api/v1/community/relationships",
        headers=H(client),
        json={"target_email": reader_email, "relationship_kind": "FOLLOW"},
    )
    assert reciprocal.status_code == 200, reciprocal.text
    assert reciprocal.json()["connected"] is True

    use_cookies(client, reader_cookies)
    client.app.dependency_overrides[get_translation_provider] = CommunityTranslationProvider
    try:
        translated = await client.post(
            "/api/v1/translations",
            headers=H(client),
            json={
                "source_object_type": "COMMUNITY_POST",
                "source_object_id": post_id,
                "source_locale": "en",
                "target_locale": "fr",
                "content_type": "COMMUNITY_POST",
                "allow_external_provider": True,
            },
        )
        assert translated.status_code == 200, translated.text
        assert translated.json()["source_text"] == "The corrected body remains attributable."
        assert translated.json()["translated_text"].startswith("FR:")
        assert translated.json()["moderation_context_preserved"] is True
        assert translated.json()["can_view_original"] is True
    finally:
        client.app.dependency_overrides.pop(get_translation_provider, None)

    blocked = await client.post(
        "/api/v1/community/relationships",
        headers=H(client),
        json={"target_email": author_email, "relationship_kind": "BLOCK"},
    )
    assert blocked.status_code == 200, blocked.text
    assert blocked.json()["connected"] is False
    blocked_follow = await client.post(
        "/api/v1/community/relationships",
        headers=H(client),
        json={"target_email": author_email, "relationship_kind": "FOLLOW"},
    )
    assert blocked_follow.status_code == 409
    assert (await client.get("/api/v1/community/feed")).json()["items"] == []

    use_cookies(client, owner_cookies)
    leaderboard = await client.get(f"/api/v1/community/rooms/{room_id}/leaderboard")
    assert leaderboard.status_code == 200, leaderboard.text
    by_user = {row["user_id"]: row for row in leaderboard.json()["entries"]}
    assert by_user[author_id]["persisted_contributions"]["posts"] == 1
    assert by_user[reader_id]["persisted_contributions"]["messages"] == 1
    assert leaderboard.json()["truth_contract"].startswith("Counts include persisted")

    removed = await client.delete(
        f"/api/v1/community/rooms/{room_id}/members/{reader_id}", headers=H(client)
    )
    assert removed.status_code == 204, removed.text
    use_cookies(client, reader_cookies)
    assert (await client.get(f"/api/v1/community/rooms/{room_id}")).status_code == 404
    assert owner_id != author_id != reader_id


async def test_community_moderation_actions_sanctions_appeals_and_rls(
    client, app_engine
):
    owner_response, _, _ = await register_user(client, chosen_name="Moderation Owner")
    owner_id = owner_response.json()["id"]
    owner_cookies = save_cookies(client)

    client.cookies.clear()
    moderator_response, moderator_email, _ = await register_user(
        client, chosen_name="Moderation Reviewer"
    )
    moderator_id = moderator_response.json()["id"]
    moderator_cookies = save_cookies(client)

    client.cookies.clear()
    author_response, author_email, _ = await register_user(
        client, chosen_name="Moderation Subject"
    )
    author_id = author_response.json()["id"]
    author_cookies = save_cookies(client)

    client.cookies.clear()
    reporter_response, reporter_email, _ = await register_user(
        client, chosen_name="Moderation Reporter"
    )
    reporter_id = reporter_response.json()["id"]
    reporter_cookies = save_cookies(client)

    client.cookies.clear()
    outsider_response, _, _ = await register_user(client, chosen_name="Moderation Outsider")
    outsider_id = outsider_response.json()["id"]
    outsider_cookies = save_cookies(client)

    use_cookies(client, owner_cookies)
    room = await client.post(
        "/api/v1/community/rooms",
        headers=H(client),
        json={"title": "Reviewable moderation room", "room_kind": "COMMUNITY"},
    )
    assert room.status_code == 201, room.text
    room_id = room.json()["id"]
    for email, role in (
        (moderator_email, "MODERATOR"),
        (author_email, "MEMBER"),
        (reporter_email, "MEMBER"),
    ):
        added = await client.post(
            f"/api/v1/community/rooms/{room_id}/members",
            headers=H(client),
            json={"email": email, "role": role},
        )
        assert added.status_code == 201, added.text

    use_cookies(client, author_cookies)
    post = await client.post(
        f"/api/v1/community/rooms/{room_id}/posts",
        headers=H(client),
        json={"title": "Reported claim", "body": "This claim needs a bounded review."},
    )
    assert post.status_code == 201, post.text
    post_id = post.json()["id"]

    use_cookies(client, reporter_cookies)
    report = await client.post(
        f"/api/v1/community/rooms/{room_id}/reports",
        headers=H(client),
        json={
            "target_kind": "POST",
            "target_id": post_id,
            "category": "MISINFORMATION",
            "details": "Please verify the persisted claim and its source.",
        },
    )
    assert report.status_code == 201, report.text
    report_id = report.json()["id"]
    assert report.json()["status"] == "OPEN"
    assert report.json()["response_overdue"] is False
    assert (
        await client.get(f"/api/v1/community/rooms/{room_id}/moderation/queue")
    ).status_code == 403

    use_cookies(client, moderator_cookies)
    queue = await client.get(f"/api/v1/community/rooms/{room_id}/moderation/queue")
    assert queue.status_code == 200, queue.text
    assert [row["id"] for row in queue.json()["reports"]] == [report_id]
    action_response = await client.post(
        f"/api/v1/community/rooms/{room_id}/moderation/reports/{report_id}/actions",
        headers=H(client),
        json={
            "action_kind": "HIDE_CONTENT",
            "rationale": "Hide during review; preserve the audit and appeal path.",
        },
    )
    assert action_response.status_code == 201, action_response.text
    action_id = action_response.json()["action"]["id"]
    assert action_response.json()["report"]["status"] == "ACTIONED"

    use_cookies(client, reporter_cookies)
    posts = await client.get(f"/api/v1/community/rooms/{room_id}/posts")
    assert posts.status_code == 200, posts.text
    assert posts.json() == []

    use_cookies(client, author_cookies)
    action = await client.get(f"/api/v1/community/moderation/actions/{action_id}")
    assert action.status_code == 200, action.text
    assert action.json()["action_kind"] == "HIDE_CONTENT"
    appeal = await client.post(
        f"/api/v1/community/moderation/actions/{action_id}/appeals",
        headers=H(client),
        json={"body": "The claim should return with its source clarification."},
    )
    assert appeal.status_code == 201, appeal.text
    appeal_id = appeal.json()["id"]

    use_cookies(client, owner_cookies)
    appeals = await client.get(
        f"/api/v1/community/rooms/{room_id}/moderation/appeals"
    )
    assert appeals.status_code == 200, appeals.text
    assert appeals.json()["appeals"][0]["id"] == appeal_id
    reviewed = await client.post(
        f"/api/v1/community/rooms/{room_id}/moderation/appeals/{appeal_id}/review",
        headers=H(client),
        json={
            "outcome": "OVERTURNED",
            "rationale": "The clarification resolves the bounded concern.",
        },
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["appeal"]["status"] == "OVERTURNED"
    assert reviewed.json()["action"]["status"] == "REVERSED"
    assert reviewed.json()["report"]["status"] == "CLOSED"
    assert reviewed.json()["independent_reviewer"] is True

    use_cookies(client, reporter_cookies)
    restored = await client.get(f"/api/v1/community/rooms/{room_id}/posts")
    assert [row["id"] for row in restored.json()] == [post_id]

    use_cookies(client, author_cookies)
    second_post = await client.post(
        f"/api/v1/community/rooms/{room_id}/posts",
        headers=H(client),
        json={"title": "Noisy post", "body": "A second persisted moderation target."},
    )
    assert second_post.status_code == 201, second_post.text

    use_cookies(client, reporter_cookies)
    second_report = await client.post(
        f"/api/v1/community/rooms/{room_id}/reports",
        headers=H(client),
        json={
            "target_kind": "POST",
            "target_id": second_post.json()["id"],
            "category": "SPAM",
        },
    )
    assert second_report.status_code == 201, second_report.text

    use_cookies(client, moderator_cookies)
    mute_action = await client.post(
        f"/api/v1/community/rooms/{room_id}/moderation/reports/"
        f"{second_report.json()['id']}/actions",
        headers=H(client),
        json={
            "action_kind": "MUTE_MEMBER",
            "rationale": "Pause contributions while the spam report is appealed.",
            "duration_hours": 24,
        },
    )
    assert mute_action.status_code == 201, mute_action.text
    mute_action_id = mute_action.json()["action"]["id"]

    use_cookies(client, author_cookies)
    denied_message = await client.post(
        f"/api/v1/community/rooms/{room_id}/messages",
        headers=H(client),
        json={"body": "This write is blocked by the active room sanction."},
    )
    assert denied_message.status_code == 403
    mute_appeal = await client.post(
        f"/api/v1/community/moderation/actions/{mute_action_id}/appeals",
        headers=H(client),
        json={"body": "The pause can be lifted; the duplicate posting has stopped."},
    )
    assert mute_appeal.status_code == 201, mute_appeal.text

    use_cookies(client, owner_cookies)
    lifted = await client.post(
        f"/api/v1/community/rooms/{room_id}/moderation/appeals/"
        f"{mute_appeal.json()['id']}/review",
        headers=H(client),
        json={"outcome": "OVERTURNED", "rationale": "Restore bounded contribution access."},
    )
    assert lifted.status_code == 200, lifted.text

    use_cookies(client, author_cookies)
    allowed_message = await client.post(
        f"/api/v1/community/rooms/{room_id}/messages",
        headers=H(client),
        json={"body": "Contribution access is restored by an audited overturn."},
    )
    assert allowed_message.status_code == 201, allowed_message.text
    events = await client.get(f"/api/v1/community/rooms/{room_id}/moderation/events")
    assert events.status_code == 200, events.text
    assert {row["event_type"] for row in events.json()} >= {
        "REPORT_CREATED",
        "ACTION_TAKEN",
        "APPEAL_CREATED",
        "APPEAL_REVIEWED",
    }

    use_cookies(client, outsider_cookies)
    assert (await client.get("/api/v1/community/moderation/reports")).json() == []
    assert (await client.get("/api/v1/community/moderation/appeals")).json() == []

    tables = [
        "community_content_revisions",
        "community_saves",
        "community_relationships",
        "community_reports",
        "community_moderation_actions",
        "community_appeals",
        "community_room_sanctions",
        "community_moderation_events",
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
        for table_name in tables:
            count = (await connection.execute(
                text(f"SELECT count(*) FROM {table_name}")
            )).scalar_one()
            assert count == 0, f"Outsider could see rows in {table_name}"

    assert owner_id not in {moderator_id, author_id, reporter_id, outsider_id}
