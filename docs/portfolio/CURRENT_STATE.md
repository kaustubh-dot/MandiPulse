# MandiPulse Current State

This is the canonical portfolio snapshot used to orient future work. It records the verified
non-frontend release state and the separately deferred frontend package.

## Snapshot

| Field | Value |
|---|---|
| Snapshot date | August 20, 2026 |
| Audited baseline | `main` at `39f47b2`, followed by the current non-frontend finish pass |
| Data snapshot date | October 30, 2025 |
| Active phase | Phase 3 complete; frontend packaging intentionally deferred |
| Next action | Review and commit the `web/` package, then rerun its parity/build/browser gates |
| Last approved checkpoint | CP-003 |

## Verified strengths

- 206 Python tests pass.
- 74.90% Python coverage.
- Ruff and Black pass.
- The prior local frontend pass recorded 52 assertions and a successful production build; those
  results must be refreshed with the separate frontend commit.
- All 8 web JSON artifacts pass strict JSON/schema/finite validation with manifest hashes.
- Phase 3 technical evidence is reproducible: 3 rolling origins, an untouched 90-day final holdout,
  9 transport scenarios, strict JSON provenance, and numerical regression tests.
- CP-003 is Approved and Complete; the frozen rescue plan has reached its resume-grade point.

The locally updated Next.js product is recommendation-first on `/`, with labeled location,
quantity, transport-rate, and maximum-radius inputs and top-three explanations. Its source and
generated data are intentionally held for a separate commit. Vercel remains optional; no public URL
is claimed.

## Frozen data scope

The committed demo and modeling story are scoped to Onion in Maharashtra, 15 mandis, and a 7-day
forecast horizon. The data snapshot ends on October 30, 2025. The snapshot is intentionally recorded
because the public surfaces are offline/demo artifacts rather than a live market feed.

## Product decision

- Next.js is the planned flagship after its separate release pass.
- Streamlit is secondary.
- FastAPI is a local snapshot API unless connected to a real consumer.

## Confirmed residual risks

- The offline snapshot ends on October 30, 2025; the UI intentionally labels it as frozen and stale.
- The public v1 bundle reports 86.71% all-row interval coverage; the Phase 3 observed-target
  holdout reports 86.87% conditional-residual coverage and 90.91% split-conformal coverage.
  Neither interval is a guarantee.
- Vercel deployment is still an optional external operational step.
- A few historical documentation files retain mojibake encoding.
- Phase 3 is approved and complete for the frozen local scope; public web/API v1 schemas remain
  unchanged by the internal observed-target evaluation.

## Governance note

Update this file only after a phase passes its documented acceptance gate. Implementation evidence
and handoff notes belong in the checkpoint ledger until the review is complete. See the
[rescue plan](RESCUE_PLAN.md) and [checkpoint ledger](CHECKPOINTS.md) for the phase contract.
