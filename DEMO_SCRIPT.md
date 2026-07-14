# Commercial Beta Demo Script

1. Start local NUR in disabled AI mode.

   ```bash
   bash infra/scripts/start-nur.sh disabled
   bash infra/scripts/seed-demo-nur.sh
   ```

2. Login as the owner at `http://localhost:5173`.

   ```text
   owner@nur.app / owner-demo-pass-123
   ```

3. Show Talk.

   - Send one message.
   - Explain that disabled AI mode is honest: no fake model output is invented.
   - The Talk thread still persists, and Omega can show what changed from owner
     evidence, contradictions, and unresolved predictions.

4. Show Systems.

   - Open Systems and point out the live owner ledger metrics.
   - Emphasize that visible outcomes are returned through real persisted rows.

5. Show Project Orbit.

   - Open Plan and show the seeded plan step and returned outcome.
   - Explain that prediction resolution depends on persisted outcomes.

6. Show Omega v1.

   - Open `/universe/omega`.
   - Show evidence graph, why-changed, open predictions, consolidation run,
     learning proposals, and owner export.
   - Open `/universe/omega/review` and show the sensitive inferred claim review
     queue.

7. Show Context Capsule.

   - Open the printed capsule URL as the recipient.
   - Ask about an approved decision.
   - Ask about Omega-only owner memory; expected result is not available.
   - Revoke the capsule from the owner account and show recipient access closes.

8. Close with security posture.

   - OpenAI keys are server-only and ignored.
   - RLS is forced for owner memory and Omega tables.
   - Capsule grants do not receive Omega owner memory.
   - The system does not claim sentience, AGI, or autonomous action.
