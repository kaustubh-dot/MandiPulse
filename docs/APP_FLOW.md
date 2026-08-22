# MandiPulse Application Flow

Status: authoritative product-flow specification

Applies to: Next.js showcase and Streamlit analytical app

Last reviewed: 2026-08-22

## 1. Product Journey

MandiPulse helps a user answer one bounded question:

> Given my location and quantity, which of the supported Maharashtra onion mandis offers the strongest expected price after estimated transport cost over the seven-day horizon?

The application must lead with the decision, keep its assumptions visible, and make the underlying forecast and data evidence easy to inspect. It must not imply live prices, guaranteed returns, route-accurate freight quotes, or support beyond the shipped 15-mandi Maharashtra onion dataset.

## 2. Global Information Architecture

Both interfaces use the same four destinations and the same order:

| Destination | User question | Primary output |
|---|---|---|
| Decision | Where should I sell? | Transport-adjusted ranked mandis |
| Forecast | What price does the model expect? | Seven-day forecast with interval and baseline context |
| Coverage | What data supports this result? | Date range, market coverage, missingness, and trainability |
| Method | How was this result produced? | Assumptions, validation, limitations, and artifact provenance |

Next.js route mapping:

| Destination | Route |
|---|---|
| Decision | `/recommend` |
| Forecast | `/forecast` |
| Coverage | `/coverage` |
| Method and overview | `/` |

Streamlit uses the same labels as pages or navigation destinations. It may present Method as a section on the overview page if a fourth page adds needless navigation.

## 3. Global Shell Flow

Every destination must expose:

1. Product name and current destination.
2. A visible snapshot label: data is historical and ends on 2025-10-30.
3. Navigation to the other destinations.
4. A compact methodology or assumptions entry point.
5. The current data or loading state.
6. No sign-in, account, notification, or settings controls.

Desktop Next.js uses the persistent decision rail specified in `docs/DESIGN.md`. On smaller screens it becomes a top bar with a navigation sheet. Streamlit uses its native sidebar only for navigation and global context; decision inputs stay in the page body so that they remain visible beside their results.

## 4. Primary Flow: Make a Sell Decision

### 4.1 Entry

The user can enter from the overview or open Decision directly. The initial view must be useful without configuration:

- prefill a valid demonstration location from project configuration;
- prefill a realistic positive quantity;
- state the transport assumptions next to the controls;
- show that the forecast horizon is seven days;
- avoid presenting a recommendation until all required inputs are valid.

### 4.2 Required inputs

| Input | Validation | Error behavior |
|---|---|---|
| Farmer latitude | Numeric, -90 to 90 | Inline error; preserve entered value |
| Farmer longitude | Numeric, -180 to 180 | Inline error; preserve entered value |
| Quantity | Numeric and greater than zero | Inline error; no ranking calculation |
| Transport rate | Numeric, zero or greater | Inline error; label it as a scenario assumption |

Coordinates are an expert input in the current release. Do not add a location-search promise unless a reliable geocoding source is implemented and tested.

### 4.3 Calculate

The primary action label is `Compare mandis`. Its sequence is:

1. Validate all fields.
2. Load the shipped seven-day forecast snapshot and mandi coordinates.
3. Estimate distance using haversine distance multiplied by the documented 1.3 road factor.
4. Estimate transport cost using the active INR/km/quintal scenario.
5. Calculate transport-adjusted net expected price per quintal and for the entered quantity.
6. Sort eligible mandis by transport-adjusted net expected price.
7. Preserve uncertainty as evidence attached to each candidate; do not claim it changes the public ranking while the same global interval width is applied to every candidate.
8. Return the primary recommendation and ranked alternatives.

### 4.4 Results hierarchy

Results must appear in this order:

1. **Primary recommendation:** mandi name, transport-adjusted expected price, gross forecast, estimated transport cost, and estimated distance.
2. **Decision explanation:** a short arithmetic explanation of why the selected mandi ranks first.
3. **Alternatives:** at least the next two eligible mandis using exactly the same fields and units.
4. **Comparison table:** all eligible mandis, sortable only where sorting cannot obscure the recommended rank.
5. **Map:** user location and candidate mandis, with the selected mandi visually dominant.
6. **Evidence:** forecast interval, snapshot date, assumptions, and methodology link.

The result title must use `Recommended mandi` or `Top transport-adjusted option`. Do not use `best`, `guaranteed`, `optimal`, or `risk-adjusted` in the public result.

### 4.5 Result actions

Allowed actions:

- adjust inputs and compare again;
- inspect an alternative;
- open the selected mandi in Forecast;
- copy or share a reproducible decision link once query-parameter state is implemented;
- open assumptions and methodology.

There is no booking, payment, trade execution, or contact-mandi action in scope.

## 5. Forecast Exploration Flow

### 5.1 Entry and selection

1. Open Forecast.
2. Select one of the 15 supported mandis.
3. Load that mandi's recent history, seven-day estimate, uncertainty interval, and evaluation evidence.
4. Preserve the selected mandi in the URL on Next.js and in session state on Streamlit.

### 5.2 Content order

1. Mandi identity and forecast date.
2. Forecast price in INR/quintal.
3. Lower and upper interval bounds with method label.
4. Historical price series with the forecast point clearly separated from observations.
5. Model-versus-baseline evidence.
6. Missingness and data-quality note.
7. Action to use this mandi or return to the Decision view.

Charts must distinguish observed, imputed, and forecast values through more than color alone. Tooltips repeat exact units and dates. Empty chart decoration is prohibited.

## 6. Coverage and Provenance Flow

Coverage is an evidence page, not a dashboard of ornamental metrics.

1. Show the snapshot range and last available date.
2. Show 15 selected mandis and the 31,950-row clean panel.
3. Explain observed, imputed, missing, and trainable row definitions.
4. Provide a per-mandi table or plot that makes gaps comparable.
5. Let the user select a mandi for a focused coverage view.
6. Link to the complete method and project reports.

If a required coverage artifact is missing, show its expected artifact name and regeneration guidance; never render zero as if it were real data.

## 7. Overview and Method Flow

The home route is a concise technical overview, not a marketing landing page.

Content order:

1. One-sentence product thesis.
2. Direct entry to `Compare mandis`.
3. Current evaluation facts with scope and split labels.
4. System flow: data snapshot to forecast to transport-adjusted comparison.
5. Assumptions and limitations.
6. Links to Decision, Forecast, and Coverage.

The Method section must disclose:

- supported commodity, state, mandis, and horizon;
- snapshot end date;
- temporal evaluation approach;
- shipped forecasting policy and held-out metrics;
- interval method and coverage labels;
- distance and transport-cost approximations;
- why uncertainty is displayed separately from the current public rank;
- what the product does not do.

## 8. State and Failure Contract

| State | Required behavior | Prohibited behavior |
|---|---|---|
| Initial | Show useful defaults and explanation | Blank page or unexplained zero values |
| Loading | Preserve layout; label the operation | Full-page spinner for a small local read |
| Invalid input | Inline, field-specific message | Toast-only error or cleared input |
| Missing artifact | Name the unavailable evidence and recovery step | Fabricated fallback values |
| Empty filter | Explain why no rows match; reset action | Empty table with no explanation |
| Partial data | Render valid sections and identify unavailable ones | Treat partial response as complete |
| Calculation error | Preserve inputs; concise retry guidance | Stack trace in the interface |
| Stale snapshot | Persistent date label and limitation | Language suggesting live data |
| Narrow viewport | Single-column reading order; accessible navigation | Horizontal page scrolling |

## 9. Cross-Surface Parity Contract

Next.js and Streamlit do not need pixel parity. They require semantic and numerical parity:

- identical source artifacts and schema version;
- identical field names, units, rounding rules, and rank order;
- identical default coordinates, quantity, road factor, and transport rate;
- identical snapshot and limitation copy;
- identical treatment of uncertainty;
- equivalent validation and missing-data behavior;
- no feature exposed on one surface that implies a different product contract on the other.

Automated parity tests must compare the candidate order and all displayed ranking values for fixed fixtures. Visual implementation may differ only as described in `docs/DESIGN.md`.

## 10. Analytics and Privacy Boundary

The current release does not require accounts or persistent user storage. Coordinates and quantities must remain client/session-local unless a future privacy review explicitly approves collection. If analytics are introduced, capture only route and interaction events required to understand product use; do not send raw coordinates or quantities.

## 11. Flow Acceptance Checklist

- [ ] A user can reach a defensible recommendation without reading documentation first.
- [ ] Every result shows scope, units, snapshot date, and transport assumptions.
- [ ] Recommendation language matches the implemented transport-adjusted calculation.
- [ ] Forecast observations and estimates are visually and semantically distinct.
- [ ] Missing, invalid, empty, loading, and partial states are designed on both surfaces.
- [ ] Keyboard-only users can complete the primary flow.
- [ ] A 320 px viewport completes the same flow without horizontal scrolling.
- [ ] Fixed fixtures produce the same rank order in Python and TypeScript.
- [ ] No path implies live prices, trade execution, or guaranteed financial outcomes.
