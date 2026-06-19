# Future Plans / Roadmap

Living document for work that's designed but not yet built. Each item should graduate to
its own dated spec in `docs/superpowers/specs/` when it's picked up.

---

## Data Pipeline v2 — continuous, self-cleaning data (overall vision)

**Goal:** escape the 2020 freeze and make the dataset self-updating and self-cleaning, so
"which city has the worst AQI now?" returns today's reality (Delhi), not 2020 (Ahmedabad).

**Decisions locked during brainstorming (2026-06-19):**
- **Refresh model:** automated ongoing — a GitHub Actions cron updates the data on a
  schedule; Streamlit Cloud + the HF Space auto-redeploy on the resulting push.
- **Source:** **OpenAQ** (free API key). It aggregates India's CPCB CAAQMS stations — the
  same underlying network as the original Kaggle data — with multi-year history, so it can
  backfill 2020→now AND keep updating. It returns pollutant **concentrations**, so we compute
  CPCB AQI ourselves (a feature: one consistent AQI definition, fixes legacy inconsistency).
- **AQI:** recompute across the WHOLE series with one CPCB formula; preserve the original
  CPCB AQI in `AQI_cpcb_original`.
- **Data strategy:** keep the trusted Kaggle 2015→2020-07 base (AQI recomputed); use OpenAQ
  only for 2020-07→now. Both halves use the same AQI formula + cleaner → continuous series.
- **Cleaning:** layered + flag, never delete — physical bounds (null impossible) → recompute
  AQI → statistical flag of isolated, uncorroborated single-day spikes (`quality_flag`).
  Real extreme events (Diwali, stubble burning) are preserved.
- **Utilization:** drive all date text dynamically (kill hardcoded "2015–2020"); add a
  "Data current through <date> · updated weekly" badge; soften the MCP "not real-time"
  wording (the MCP already reports coverage dynamically via `_coverage()`).
- **Posture:** tread lightly — additive schema, preserve originals, validate before
  overwrite, phase the rollout with the risky automation LAST.

### Phase 1 — AQI keystone + cleaner + legacy recompute  ✅ SPEC WRITTEN
See `docs/superpowers/specs/2026-06-19-data-pipeline-phase1-design.md`.
No new data: builds `pipeline/{aqi,clean,build}.py`, recomputes AQI for the existing city +
station parquets, adds `AQI_cpcb_original`/`quality_flag`/`dominant_pollutant`/`source`.
Fixes the station-727 and the AQI/pollutant inconsistency; de-risks all later phases.

### Phase 2 — OpenAQ ingestion + backfill the 2020→now gap  ⏳ NOT STARTED
- `pipeline/sources/openaq.py` — fetch concentrations for the 11 cities + Bangalore stations
  over a date range from OpenAQ v3 (API key from secret/env; pagination; rate-limit handling;
  on-disk cache). Map OpenAQ sensors → our station/city identities.
- **De-risk first:** a throwaway probe confirming OpenAQ coverage/density for our 11 cities
  2020→now BEFORE building the full fetch. If a city is thin, document a fallback
  (e.g. data.gov.in for from-now-on on that city).
- Aggregate sensor → station → city DAILY; run the Phase-1 cleaner + AQI compute; append rows
  for 2020-07-02→now with `source="openaq"`.
- Run manually first; human-review the appended slice before shipping.
- Watch-outs: OpenAQ may lack NO/NOx/Benzene/Toluene/Xylene for some stations (fine — nulls);
  daily aggregation + the CPCB min-3-pollutant rule; timezone/UTC handling; dedupe vs legacy
  at the 2020-07 seam.

### Phase 3 — Automation (GitHub Actions cron + validation gate + auto-deploy)  ⏳ NOT STARTED
- `.github/workflows/update-data.yml`: weekly cron → fetch since last date in the parquet →
  clean → append → **validation gate** → commit (git-lfs) → push → redeploy.
- **Validation gate (the safety core):** before any commit, assert invariants — row count
  only grew, date range only extended, no city dropped, all AQI ∈ [0,500], %flagged below a
  threshold, schema unchanged. Fail → abort, don't ship (optionally open an issue).
- HF redeploy from the workflow via `HfApi().upload_folder` (HF_TOKEN secret) + reuse
  `scripts/verify_hf_deploy.py`. Streamlit Cloud redeploys automatically on the git push.
- Secrets: `OPENAQ_API_KEY`, `HF_TOKEN`.

### Phase 4 — Utilization (dynamic framing + freshness badge)  ⏳ NOT STARTED
- A `data_coverage()` helper (min/max date from the parquet) drives all date text.
- Replace hardcoded "2015–2020" across `app.py`, `pages/*.py`, READMEs with the real range.
- Add a "Data current through <date> · updated weekly" badge (a `utils/style.py` component).
- Soften MCP docstring "historical, not real-time" wording to "through the latest available
  date". Optionally surface `quality_flag`/`dominant_pollutant` in the UI.
