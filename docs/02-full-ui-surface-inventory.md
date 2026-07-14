# Full UI Surface Inventory

Statuses: `LIVE_REAL`, `LIVE_PARTIAL`, `DISABLED_HONEST`, `NEEDS_V197_ADJUNCT`, `MISSING`.

| Surface | V197 presentation | Backend | Audit state |
|---|---|---|---|
| Entry/Auth | canonical Entry chambers | real Auth/session | LIVE_REAL |
| Today | canonical page | check-in/Talk/Glow, but no total Today model | LIVE_PARTIAL |
| Talk | canonical chamber | persisted server kernel/provider | LIVE_REAL; current runtime disabled |
| Journal | canonical page | private persistence | LIVE_REAL |
| Plan | canonical page | Plan/step/Outcome | LIVE_REAL |
| Systems Universe | canonical map shell | seven Orbits/read summaries | LIVE_PARTIAL |
| Map | canonical map and detail card | real summary; no future-path mutation | LIVE_PARTIAL |
| Orbits | canonical lens | owner Orbits only; no people/group detail | LIVE_PARTIAL |
| Timeline | canonical lens | real history; no future action mutation | LIVE_PARTIAL |
| Insights | canonical lens | Omega summary; no full accept/correct/convert UI | LIVE_PARTIAL |
| Research | canonical card | local persisted questions | LIVE_PARTIAL |
| Web Signals | canonical focus | local staging only | DISABLED_HONEST for live web |
| Community | canonical card | private consultation notes only | DISABLED_HONEST |
| Group NUR/Council | no complete native chamber | missing product backend | MISSING |
| AM Projects | no complete native chamber | missing project backend | MISSING |
| Language | scope chamber native controls | owner preference | LIVE_PARTIAL; top-bar picker missing |
| Glow | Today/right-rail slots | core persisted ledger/streak | LIVE_PARTIAL |
| Settings | contract only | preference/provider APIs exist | NEEDS_V197_ADJUNCT |
| Capsule owner/recipient | contract only | complete bounded backend | NEEDS_V197_ADJUNCT |
| Omega dashboard/review | contract only | complete owner backend | NEEDS_V197_ADJUNCT |
| Feasibility | no native surface | missing | MISSING |

Selector-level current controls remain in `interaction-registry.json`. SOL expansion must register trigger-opened, modal, and mobile controls as they are added.
