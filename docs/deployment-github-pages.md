# GitHub Pages Deployment

GitHub Pages is the primary public hosting target for this repository. The Astro app lives in `apps/web`, and the workflow builds that app before publishing `apps/web/dist`.

## Production URL

The expected Pages URL is:

```text
https://petooooo.github.io/
```

The GitHub Actions workflow sets:

```bash
SITE_URL=https://petooooo.github.io/
```

Astro builds at the domain root for this user-pages repository, so canonical URLs, Open Graph image URLs, RSS links, sitemap entries, and internal navigation are generated without a project subpath.

## Repository Settings

In GitHub, open `Petooooo/Petooooo.github.io` and configure:

1. Go to **Settings**.
2. Go to **Pages**.
3. Under **Build and deployment**, set **Source** to **GitHub Actions**.
4. Save the setting.
5. Push to `main`, or run the `Deploy GitHub Pages` workflow manually from the **Actions** tab.

## Workflow

The workflow file is `.github/workflows/deploy-pages.yml`.

It does the following:

- Checks out the repository.
- Uses Node 20.
- Runs `npm ci --prefix apps/web`.
- Runs `npm run build --prefix apps/web`.
- Uploads `apps/web/dist` as the Pages artifact.
- Deploys the artifact with GitHub's official Pages action.

## Verification

After the workflow succeeds, verify:

```bash
curl -I https://petooooo.github.io/
curl -I https://petooooo.github.io/rss.xml
curl https://petooooo.github.io/sitemap-index.xml
```

Inspect page source and confirm canonical, Open Graph, RSS, and sitemap URLs use `https://petooooo.github.io/` with no project subpath.

## Optional RP4 Hosting

The Docker, Caddy, and Raspberry Pi 4 deployment files remain available for self-hosting. For RP4 deployment, set `SITE_URL` to the RP4 public URL instead of the GitHub Pages URL, for example:

```bash
SITE_URL=https://your-name.iptime.org
SITE_DOMAIN=your-name.iptime.org
```

Then use the RP4 deployment flow in `docs/deployment-rp4.md`.
