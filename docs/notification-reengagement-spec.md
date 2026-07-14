# Notification and Re-engagement Specification

Date: 2026-07-11

## Current state

No push/email/SMS notification delivery is live in Track A and no permission prompt is shown. Quiet sound preference exists separately and must not be represented as notification consent.

## Track B triggers

- unfinished owner Plan move at a chosen return time;
- Outcome requested after a completed step;
- streak rescue before the owner's local-day boundary;
- Group NUR mention or approved consultation return;
- Capsule view/question/revoke audit event;
- Project approval/blocker requiring owner action;
- Omega review item requiring confirmation.

## Delivery law

Consent is per channel and purpose. Store timezone, locale, quiet hours, frequency cap, last-delivered state, dedupe key, and unsubscribe. Default copy reveals no private content on a lock screen. Sensitive events use generic wording and deep-link only after authentication.

## Re-engagement ranking

Prioritize unfinished owner-chosen commitments, actionable returns, social obligations, and expiring grants. Apply fatigue penalty, recent-dismissal penalty, quiet hours, channel cap, and harm/opt-out signals. Variable timing may be tested only inside bounded windows and never fabricate urgency.

## Languages

Templates support the 35 locale registry; draft translations are labelled in internal review. Korean uses Hangul-first copy and speech-style preference. Roman Urdu is `ur + roman`, not a locale. Mixed API/product names use bidi isolation in RTL.

## Acceptance

Consent, revoke, quiet-hours, timezone/DST, dedupe, cap, localization, lock-screen redaction, deep-link auth, delivery failure/retry, unsubscribe, analytics-without-content, and mobile PWA proof must pass before any channel is enabled.
