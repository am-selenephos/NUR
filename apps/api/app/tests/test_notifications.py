from sqlalchemy import text

from app.tests.conftest import register_user


def H(client) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("nur_csrf")}


async def test_owner_notification_preferences_reminders_and_rls(client, app_engine):
    owner, _, _ = await register_user(client, chosen_name="Reminder Owner")
    owner_id = owner.json()["id"]
    initial = await client.get("/api/v1/notifications/preferences")
    assert initial.status_code == 200
    assert initial.json()["delivery_status"] == "IN_APP_ONLY"
    saved = await client.patch(
        "/api/v1/notifications/preferences", headers=H(client),
        json={
            "category_settings": {"PROJECT": True, "SOCIAL": False},
            "frequency": "QUIET",
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00",
            "push_enabled": False,
            "email_enabled": False,
        },
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["frequency"] == "QUIET"
    reminder = await client.post(
        "/api/v1/notifications/reminders", headers=H(client),
        json={
            "category": "PROJECT",
            "title": "Return to evidence",
            "body": "Review the passed test before closing the milestone.",
            "route": "/projects",
        },
    )
    assert reminder.status_code == 201, reminder.text
    notification_id = reminder.json()["id"]
    listed = await client.get("/api/v1/notifications?unread_only=true")
    assert [row["id"] for row in listed.json()] == [notification_id]
    read = await client.post(f"/api/v1/notifications/{notification_id}/read", headers=H(client))
    assert read.status_code == 200
    assert read.json()["read_at"] is not None

    client.cookies.clear()
    recipient, _, _ = await register_user(client, chosen_name="Reminder Recipient")
    recipient_id = recipient.json()["id"]
    assert (await client.get("/api/v1/notifications")).json() == []

    async with app_engine.connect() as connection:
        await connection.execute(text("SELECT set_config('app.current_user_id', :uid, false)"), {"uid": recipient_id})
        assert (await connection.execute(text("SELECT count(*) FROM notifications"))).scalar_one() == 0
        assert (await connection.execute(text("SELECT count(*) FROM notification_preferences"))).scalar_one() == 0
        flags = (await connection.execute(text("""
            SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class
            WHERE relname IN ('notifications', 'notification_preferences') ORDER BY relname
        """))).all()
        assert len(flags) == 2
        assert all(row.relrowsecurity and row.relforcerowsecurity for row in flags)

    async with app_engine.connect() as connection:
        await connection.execute(text("SELECT set_config('app.current_user_id', :uid, false)"), {"uid": owner_id})
        assert (await connection.execute(text("SELECT count(*) FROM notifications"))).scalar_one() == 1
