# Fictional assignment test accounts

Run `.\.venv\Scripts\python.exe scripts\seed_test_users.py --create` from the repository root after the local workspace owner has completed setup. The script uses this app's configured local database. It creates four ordinary workspace members and two separate projects; existing projects and accounts are preserved. It never connects sources or calls a model.

| Account | TEST - Orchid | TEST - Cedar | Assigned cases |
|---|---|---|---|
| `test.review.owner` | Project owner | Project owner | Manages both reviews and assignments |
| `test.product.owner` | Decision owner | No access | Orchid pilot date |
| `test.engineer` | Reviewer | Decision owner | Cost, vendor credentials, earlier version and performance; also Cedar pilot date |
| `test.security.owner` | Decision owner | Decision owner | Security approval in both projects |

Passwords are generated locally and saved only to ignored `artifacts/test-users/credentials.json`. Treat that file as private. They are not committed or placed in the application database in plaintext. This is local fictional test access, not production authentication or real team membership. Rerunning the script reuses the fixture and does not reset passwords, findings or decisions. A username collision causes it to stop before changing records.

Both projects contain three fictional documents and a clearly labelled deterministic test review with six assigned, open findings: conflicting pilot dates, missing security approval, assumed service cost, vendor-credential dependency, an earlier-version decision and an unspecified performance target. Every citation points to its project-specific passage. No live AI detection is claimed by these fixtures.

To try the workflow:

1. Open `http://127.0.0.1:8027`. Sign out, then sign in using a test account and its private password. An InPrivate window keeps your normal owner session separate.
2. Open the account's TEST project and its existing review. Inspect the finding and cited source passages.
3. As the assigned account, record an answer. Choose a contextual option or Other and provide your answer. An answer alone leaves the finding open.
4. For Orchid engineering cases, sign in as `test.product.owner`, `test.security.owner` or `test.review.owner` to confirm the answer. The engineer has reviewer rights in Orchid and cannot confirm it. Decision-owner permission is project-wide in the current app; topic mappings suggest assignment and do not restrict confirmation to a particular domain owner.
5. Inspect the updated report and decision history. Unknown answers stay unresolved. The product-owner account cannot access Cedar. Assignments never send messages.

Leave the TEST projects in place while experimenting; no automatic data cleanup is performed. The original workspace owner can inspect both projects.

Verification: all four accounts signed in through the running browser UI and opened their expected findings. Direct HTTP checks verified review access and Cedar denial for the product-owner account. Confirmation authority and response permissions were exercised in isolated automated tests so the twelve local sample findings remain open. The current UI still shows some actions to members who cannot perform them; the server rejects unauthorized assignment, response, confirmation and dismissal requests. Role-aware action visibility remains a UX improvement.
