# Idempotent owned local image cleanup

Result: PARTIAL

Date: 2026-10-27. Harness-only change from d1f03cc17853b46ebb73586d02f9916f1656ff22.

- pytest scripts/test_public_launch_e2e.py: PASS41 plus6 subtests,1.89s.
- Real Docker29.9.2 control: original cleanup FAIL for an already removed task tag;
  fixed cleanup PASS after independent image inspect confirms exact tag absent.
  The shared active registry image remains present; no force deletion used.
- Negative controls retain failures for a present tag, inaccessible daemon, image
  in use and an alias embedded in a foreign repository name. No foreign deletion.
- Hermes original complete CLI/SDK/HTTP business tasks PASS, but overall receipt
  FAIL due to this local-tag check. Original receipt retained. Fresh independent
  exact-journal reconciliation confirmed sandbox, template, remote tag and local
  tags absent, with zero new business/model calls. A distinct supplementary receipt
  binds the original SHA256; no original result or cleanup field was overwritten.
- Earlier safe local reclaim only selected this task's exact fully pushed image
  journal entries after actual owned cloud provisioning, excluded active push/build
  arguments, removed exact local tags without force and independently inspected
  absence. Remote resources stayed under normal own-resource cleanup.
- Document links: PASS224/zero failures; diff and configured-secret scans PASS.
  Current-head CI pending. The full50-template task remains incomplete.

[Original Hermes cleanup failure](2026-10-27-idempotent-owned-local-cleanup/hermes-original-failed-cleanup.json)
and [independent supplement](2026-10-27-idempotent-owned-local-cleanup/hermes-independent-cleanup-supplement.json)
are distinct immutable records. The supplement binds both the sanitized public
original bytes and the private operator input digest; no alias/credential is published.
