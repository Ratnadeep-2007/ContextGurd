# Single-project demo and team

The local workspace now keeps **synora** as its only project. The five duplicate fictional projects were removed only after confirming they contained test-mode evidence/reviews and no confirmed decisions. A private SQLite backup and the previous credential manifest were saved under ignored artifacts/demo-backup-f90818fdaa884ec3a319d243aad19e3c. Ratnadeep's login, password and workspace-admin role were preserved.

The project contains three clearly fictional Synora documents and one six-finding test review: pilot-date conflict, missing security approval, assumed service cost, vendor-credential dependency, earlier-version decision and an unspecified performance target. No live model inference is claimed. Reopening the sample reuses its project/review instead of adding duplicates.

| Display name | Login | Project role | Assigned work |
|---|---|---|---|
| Ratnadeep | ratnadeep | Admin / project owner | Review ownership, assignments and final decisions |
| Asha Patel | test.review.owner | Reviewer | Cost/requirements assumption |
| Mira Rao | test.product.owner | Decision owner | Pilot date and scope |
| Dev Shah | test.engineer | Reviewer | Credentials, earlier version and performance |
| Leena Nair | test.security.owner | Decision owner | Security approval |

The four mock members are ordinary workspace members, not workspace admins or project owners. Team shows only members, roles and responsibilities. It has no local-account creation, password or configuration forms. Decision-owner permission remains project-wide, rather than restricted to one responsibility topic.

Passwords are unchanged and saved only in ignored **artifacts/test-users/credentials.json**. Never publish that file or the backup. Use an InPrivate window to sign in as a mock member without replacing Ratnadeep's normal session. Reviewers answer their assigned finding; Mira, Leena or Ratnadeep can confirm a known answer. Responses alone do not close a finding.

Manual document/text capture requires Current project and sends only that project's ID. All-project browsing is available only when several projects exist. Team membership never grants access to unrelated projects. New inputs can be shared explicitly with current project members in Review options.

The old two-project seeder is retained for isolated regression tests, not this configured demo. The requested consolidation is implemented by scripts/reset_demo.py; it backs up first, rejects non-demo deletions and preserves an existing single-demo review on rerun.
