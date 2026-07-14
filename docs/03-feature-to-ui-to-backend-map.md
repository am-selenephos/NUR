# SOL Feature to UI to Backend Map

| Feature | V197-native UI target | Existing reuse | Missing build |
|---|---|---|---|
| Today | `#page-today` cards/composer | current state, plans, Glow, events | aggregate/service, Body/Mind/Life, daily actions |
| Systems | existing seven nodes + detail chamber | Orbit/map summaries | diagnostics, actions, progress, advice, prediction |
| Glow | Today/right rail + adjunct ledger | core ledger/service | daily/weekly/level/achievement/leaderboards/rules |
| Goals/objectives | System detail and Today | Plan/Orbit primitives | records, progress, timeline hooks |
| Schedule | Today/Timeline future lane | Plan steps | scheduled actions, complete/miss/reschedule |
| Map | existing map/detail panel | `/universe/map-summary` | graph edges, future path, action from node |
| Timeline | lens/detail lane | `/universe/timeline` | future action controls and prediction lifecycle |
| Insights | lens/detail panel | Omega claims/evidence | product insight actions/convert flow |
| Feasibility | V197-native modal/adjunct | provider/kernel patterns | persisted assessment service/API |
| Research | existing card/detail | research tables/routes | live connector/citation verifier UI |
| Community | existing card + native chamber | consultation note foundation | room/post/comment/reaction/moderation |
| Group/Council | native adjunct chamber | Capsule grants/Omega evidence | groups/membership/messages/councils |
| AM Projects | native project cockpit | Orbit/Plan/evidence/worker | project/task/evidence/run/review/package |
| Language | top-bar popover + scope chamber | preference/translation | locale/catalog endpoints and full keys |
| OpenAI | Talk/provider status | server provider/model runs | fresh real smoke and Settings adjunct |

All owner records require owner RLS. Shared domains require explicit membership/grant checks before any UI is enabled.
