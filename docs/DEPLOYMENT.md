# Deployment workflow

MandiPulse has two independent interfaces and no runtime backend:

- `web/` is a static Next.js site.
- `app/streamlit_app.py` is the Streamlit analytical dashboard.

The recommended portfolio setup is Vercel as the main product URL and Streamlit Community Cloud as
the technical dashboard. Hugging Face Static Spaces is an optional mirror of the static site.

## Before deploying

1. Push the exact release commit to GitHub.
2. Confirm the branch is `main`.
3. Run the release checks:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check app src scripts tests
.\.venv\Scripts\black.exe --check app src scripts tests

cd web
npm run lint
npm run typecheck
npm test
npm run test:components
npm run build
```

No environment variable is required for the committed demo bundle.

## Vercel

Use Vercel for the main portfolio URL.

1. Sign in to [Vercel](https://vercel.com/) with the GitHub account that can access the repository.
2. Choose **Add New**, then **Project**, and import `kaustubh-dot/MandiPulse`.
3. Set **Root Directory** to `web`.
4. Keep the detected framework preset as **Next.js**.
5. Keep the install command as `npm install` or set it to `npm ci`.
6. Keep the build command as `npm run build`.
7. Leave environment variables empty.
8. Set the production branch to `main`.
9. Deploy.

The site uses `output: "export"` and `trailingSlash: true` in `web/next.config.mjs`. Vercel should
detect this configuration. If you configure the project as a generic static site instead of using
the Next.js preset, set the output directory to `out`.

After deployment, test these URLs in a signed-out browser:

- `/`
- `/recommend/`
- `/forecast/`
- `/coverage/`

Complete one recommendation, change a forecast mandi, refresh each route directly, and check the
browser console. Vercel documents monorepo root-directory setup in its
[monorepo guide](https://vercel.com/docs/monorepos).

## Streamlit Community Cloud

Use Streamlit Community Cloud for the analytical dashboard.

1. Sign in at [share.streamlit.io](https://share.streamlit.io/).
2. Choose **Create app**, then select the option for an existing app.
3. Select the `kaustubh-dot/MandiPulse` repository.
4. Select the `main` branch.
5. Set the main file path to `app/streamlit_app.py`.
6. Choose a readable subdomain if one is available.
7. Leave secrets empty.
8. In advanced settings, select Python 3.11 if the version control is available.
9. Deploy and wait for the dependency installation to finish.

Community Cloud starts the app from the repository root, so the root `requirements.txt`,
`.streamlit/config.toml`, `data/sample/`, and report paths are already in the expected locations.
The official flow is documented in the
[Streamlit deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

After deployment, open Overview, Coverage, Forecast, and Recommendation. Confirm that the snapshot
date is 2025-10-30, Pune parity values load, and missing-data messages do not appear for committed
artifacts.

## Hugging Face Static Spaces

Hugging Face is optional. Use a Static Space for the exported Next.js site, not for the Python
dashboard.

1. Build the static site locally:

```powershell
cd web
npm ci
npm run build
```

2. Create a new [Hugging Face Space](https://huggingface.co/new-space). Choose **Static HTML** as
   the SDK and start with a blank Space.
3. Clone the Space repository to a separate directory.
4. Copy the contents of `web/out/` into the root of the Space repository. Copy the contents, not the
   `out` directory itself, so `index.html` is at the Space root.
5. Replace the Space repository's `README.md` with:

```yaml
---
title: MandiPulse India
emoji: 🧅
colorFrom: red
colorTo: gray
sdk: static
app_file: index.html
fullWidth: true
---

Static portfolio mirror for MandiPulse India.
```

6. Commit and push the Space repository.
7. Wait for the Space to rebuild, then test the homepage and direct route refreshes.

Static Spaces serve HTML without persistent compute. Their current configuration fields are listed
in the [Hugging Face Static Spaces guide](https://huggingface.co/docs/hub/spaces-sdks-static).

If a nested route does not refresh correctly on the Space host, keep Vercel as the canonical URL.
The Vercel deployment is the primary release target because it natively understands the Next.js
export and trailing-slash routes.

## Portfolio release record

After both primary deployments work:

1. Add the Vercel and Streamlit URLs to `docs/portfolio/RELEASE_GATES.md`.
2. Record the release commit hash and verification date.
3. Check both URLs signed out at desktop and mobile widths.
4. Update the resume only with URLs and metrics that match that exact commit.
5. Keep the Hugging Face URL as an optional mirror rather than presenting three separate products.
