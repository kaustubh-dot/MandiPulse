# MandiPulse TODO

The detailed historical record remains in [docs/TRACKER.md](docs/TRACKER.md). The active execution
contract is [RESCUE_PLAN.md](docs/portfolio/RESCUE_PLAN.md), the state snapshot is
[CURRENT_STATE.md](docs/portfolio/CURRENT_STATE.md), and review evidence belongs in
[CHECKPOINTS.md](docs/portfolio/CHECKPOINTS.md).

## Active portfolio execution

**Active phase:** Frontend packaging intentionally deferred. Phase 3 Defensible ML Engineering is
**complete and suitable for a resume with the documented limitations**.

- [x] **P1-01 through P1-08:** Phase 1 strict bundle, policy/API hardening, provenance, docs, and
  browser gate (CP-001 Approved and Complete).
- [ ] **Frontend release package:** The recommendation-first product flow, decision inputs,
  explanations, accessibility work, generated data, and browser gate exist locally but must be
  reviewed and committed together in the separate Next.js release.
- [x] **P3-01:** Point-in-time-safe imputation.
- [x] **P3-02:** Observed-target metrics as the primary evaluation population.
- [x] **P3-03:** Rolling-origin evaluation with an untouched final holdout.
- [x] **P3-04:** Robust recommendation metrics and matched denominators.
- [x] **P3-05:** Multi-origin and transport-cost backtesting.
- [x] **P3-06:** Coordinate, data, and transport-assumption provenance.
- [x] **P3-07:** Conditional/conformal interval comparison and adoption rule.
- [x] **P3-08:** Numerical miniature end-to-end tests.
- [x] **P3-09:** Phase 3 verification and finish gate (CP-003 Approved and Complete).

The latest ML checkpoint is CP-003. P3-01 through P3-09 are evidenced in
`reports/modeling/phase3_evaluation.md` and `.json`. The remaining release task is the intentionally
separate Next.js package; unrelated scope expansion requires a new approved material plan.
