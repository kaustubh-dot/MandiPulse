# MandiPulse TODO

The detailed history lives in `docs/TRACKER.md`. This file is the short working checklist.

## Portfolio Finish

- [x] Python MVP pipeline implemented.
- [x] Streamlit dashboard clone-runnable from `data/sample/`.
- [x] FastAPI additive surface implemented and tested.
- [x] Next.js static frontend implemented.
- [x] TS/Python recommendation parity test added.
- [x] GitHub Actions CI added for Python and web gates.
- [ ] Deploy Next.js frontend on Vercel and add the URL to README.
- [ ] Optionally deploy FastAPI on Render and add the URL to README.
- [ ] Confirm GitHub Actions is green on `main`.

## Current Quality Gates

- [x] `pytest -q` passes locally.
- [x] `npm test` passes locally.
- [x] `npm run build` passes locally.
- [ ] CI passes after push.

## Optional Stretch Work

- [ ] Milestone O: offline calendar/exogenous features, with arrivals documented as gated.
- [ ] Milestone P: conformal intervals compared against residual intervals.
- [ ] Revisit 14/30-day horizons only after the 7-day demo is stable.
- [ ] Revisit additional crops/states only after Onion/Maharashtra is stable.
