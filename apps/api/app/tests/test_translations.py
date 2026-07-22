from app.ai.errors import AIProviderError
from app.i18n.provider import TranslationProviderResult, get_translation_provider
from app.tests.conftest import register_user


def H(client) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("nur_csrf")}


class FakeTranslationProvider:
    name = "test-provider"
    version = "test-provider:v1"

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def translate(self, **kwargs) -> TranslationProviderResult:
        self.calls.append(kwargs)
        target = kwargs["target_locale"]
        translated = (
            "یہ اصل مفہوم اور ماڈریشن کا سیاق محفوظ رکھتا ہے۔"
            if target == "ur"
            else "Traduction test conservee."
        )
        return TranslationProviderResult(
            available=True,
            provider=self.name,
            model="test-model",
            provider_version=self.version,
            translated_text=translated,
            detected_source_locale=kwargs["source_locale"] or "en",
        )


class FailingTranslationProvider:
    name = "failing-provider"
    version = "failing-provider:v1"

    async def translate(self, **kwargs) -> TranslationProviderResult:  # noqa: ARG002
        raise AIProviderError("Translation provider timed out; request failed closed.")


async def test_locale_catalog_has_35_truthful_slots_and_priority_writing_variants(client):
    response = await client.get("/api/v1/translations/catalog")
    assert response.status_code == 200
    body = response.json()
    assert body["catalog_version"] == "v5-35-locales-1"
    assert body["locale_count"] == 35
    assert body["glossary_version"] == "nur-core-v1"
    assert "NUR" in body["protected_glossary_terms"]
    assert len(body["locales"]) == 35
    assert len({row["locale"] for row in body["locales"]}) == 35
    assert set(body["quality_states"]) == {
        "CORE_POLISHED",
        "BETA_REVIEWED",
        "DRAFT_MACHINE_TRANSLATED",
        "MISSING_REVIEW",
    }

    by_locale = {row["locale"]: row for row in body["locales"]}
    assert by_locale["ur"]["variants"] == [
        {
            "preference": "roman",
            "label": "Roman Urdu",
            "script": "Latn",
            "direction": "ltr",
            "quality_state": "MISSING_REVIEW",
            "priority_for_review": True,
        },
        {
            "preference": "script",
            "label": "Urdu script",
            "script": "Arab",
            "direction": "rtl",
            "quality_state": "MISSING_REVIEW",
            "priority_for_review": True,
        },
    ]
    assert [row["label"] for row in by_locale["hi"]["variants"]] == [
        "Roman Hindi",
        "Hindi",
    ]
    assert all(
        variant["quality_state"] == "MISSING_REVIEW"
        for locale in body["locales"]
        for variant in locale["variants"]
    )
    assert "does not imply human review" in body["quality_claim"]


async def test_dynamic_translation_preserves_original_cache_scope_and_owner_correction(client):
    await register_user(client, chosen_name="Translation Owner A")
    fake = FakeTranslationProvider()
    client.app.dependency_overrides[get_translation_provider] = lambda: fake
    try:
        no_consent = await client.post(
            "/api/v1/translations",
            headers=H(client),
            json={
                "source_text": "Yeh line moderation context ko preserve kare.",
                "source_locale": "ur-PK",
                "source_writing_preference": "roman",
                "target_locale": "ur",
                "target_writing_preference": "script",
                "content_type": "COMMUNITY_MESSAGE",
                "scope": "COMMUNITY_ROOM",
            },
        )
        assert no_consent.status_code == 200
        assert no_consent.json()["status"] == "CONSENT_REQUIRED"
        assert no_consent.json()["translated_text"] is None
        assert fake.calls == []

        translated = await client.post(
            "/api/v1/translations",
            headers=H(client),
            json={
                "source_text": "Yeh line moderation context ko preserve kare.",
                "source_locale": "ur-PK",
                "source_writing_preference": "roman",
                "target_locale": "ur",
                "target_writing_preference": "script",
                "content_type": "COMMUNITY_MESSAGE",
                "scope": "COMMUNITY_ROOM",
                "allow_external_provider": True,
            },
        )
        assert translated.status_code == 200
        body = translated.json()
        translation_id = body["id"]
        assert body["source_text"] == "Yeh line moderation context ko preserve kare."
        assert body["translated_text"].startswith("یہ")
        assert body["source_direction"] == "ltr"
        assert body["target_direction"] == "rtl"
        assert body["source_writing_preference"] == "roman"
        assert body["target_writing_preference"] == "script"
        assert body["scope"] == "COMMUNITY_ROOM"
        assert body["cache_state"] == "MISS"
        assert body["quality_state"] == "DRAFT_MACHINE_TRANSLATED"
        assert body["moderation_context_preserved"] is True
        assert body["can_view_original"] is True
        assert len(fake.calls) == 1
        assert fake.calls[0]["preserve_moderation_context"] is True

        cached = await client.post(
            "/api/v1/translations",
            headers=H(client),
            json={
                "source_text": "Yeh line moderation context ko preserve kare.",
                "source_locale": "ur",
                "source_writing_preference": "roman",
                "target_locale": "ur",
                "target_writing_preference": "script",
                "content_type": "COMMUNITY_MESSAGE",
                "scope": "COMMUNITY_ROOM",
                "allow_external_provider": True,
            },
        )
        assert cached.json()["id"] == translation_id
        assert cached.json()["cache_state"] == "HIT"
        assert len(fake.calls) == 1

        corrected = await client.post(
            f"/api/v1/translations/{translation_id}/feedback",
            headers=H(client),
            json={
                "helpful": False,
                "correction": "یہ درست مالک کی تصحیح ہے۔",
                "note": "Tone ko softer rakho, meaning nahi badlo.",
            },
        )
        assert corrected.status_code == 200
        corrected_body = corrected.json()
        assert corrected_body["source_text"] == body["source_text"]
        assert corrected_body["translated_text"] == "یہ درست مالک کی تصحیح ہے۔"
        assert corrected_body["provider"] == "owner"
        assert corrected_body["quality_state"] == "BETA_REVIEWED"
        assert corrected_body["translation_version"] == 2
        assert corrected_body["feedback_count"] == 1
        assert corrected_body["cache_state"] == "UPDATED"

        fetched = await client.get(f"/api/v1/translations/{translation_id}")
        assert fetched.status_code == 200
        assert fetched.json()["translated_text"] == "یہ درست مالک کی تصحیح ہے۔"

        client.cookies.clear()
        await register_user(client, chosen_name="Translation Owner B")
        assert (await client.get(f"/api/v1/translations/{translation_id}")).status_code == 404
        assert (await client.get("/api/v1/translations")).json() == []
    finally:
        client.app.dependency_overrides.pop(get_translation_provider, None)


async def test_translation_can_load_an_owned_source_object_without_client_text(client):
    await register_user(client, chosen_name="Source Translation Owner")
    journal = await client.post(
        "/api/v1/journal",
        headers=H(client),
        json={"body": "A private source stays linked to its translation."},
    )
    assert journal.status_code == 201

    fake = FakeTranslationProvider()
    client.app.dependency_overrides[get_translation_provider] = lambda: fake
    try:
        translated = await client.post(
            "/api/v1/translations",
            headers=H(client),
            json={
                "source_object_type": "JOURNAL_ENTRY",
                "source_object_id": journal.json()["id"],
                "source_locale": "en",
                "target_locale": "fr",
                "content_type": "JOURNAL_ENTRY",
                "allow_external_provider": True,
            },
        )
        assert translated.status_code == 200
        body = translated.json()
        assert body["source_text"] == "A private source stays linked to its translation."
        assert body["source_link"] == f"JOURNAL_ENTRY:{journal.json()['id']}"
        assert body["scope"] == "PRIVATE_ORBIT"

        client.cookies.clear()
        await register_user(client, chosen_name="Foreign Source Requestor")
        denied = await client.post(
            "/api/v1/translations",
            headers=H(client),
            json={
                "source_object_type": "JOURNAL_ENTRY",
                "source_object_id": journal.json()["id"],
                "target_locale": "fr",
                "content_type": "JOURNAL_ENTRY",
                "allow_external_provider": True,
            },
        )
        assert denied.status_code == 404
    finally:
        client.app.dependency_overrides.pop(get_translation_provider, None)


async def test_translation_provider_failure_is_persisted_without_fake_output(client):
    await register_user(client, chosen_name="Fail Closed Translation Owner")
    client.app.dependency_overrides[get_translation_provider] = FailingTranslationProvider
    try:
        response = await client.post(
            "/api/v1/translations",
            headers=H(client),
            json={
                "source_text": "Do not fabricate a translation when the provider fails.",
                "source_locale": "en",
                "target_locale": "fr",
                "content_type": "JOURNAL_ENTRY",
                "allow_external_provider": True,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "FAILED"
        assert body["translated_text"] is None
        assert body["cache_state"] == "MISS"
        assert body["reason"] == "Translation provider timed out; request failed closed."

        repeated = await client.post(
            "/api/v1/translations",
            headers=H(client),
            json={
                "source_text": "Do not fabricate a translation when the provider fails.",
                "source_locale": "en",
                "target_locale": "fr",
                "content_type": "JOURNAL_ENTRY",
                "allow_external_provider": True,
            },
        )
        assert repeated.status_code == 200
        assert repeated.json()["id"] != body["id"]
        assert repeated.json()["cache_state"] == "MISS"
    finally:
        client.app.dependency_overrides.pop(get_translation_provider, None)
