# Unlisted Korean editions

## URL behavior

The canonical site is English. There is **no language switcher**, no visible Korean link, and no automatic translation or language detection.

To open a Korean edition, explicitly append `/kr/` to a public route, for example:

- `/projects/rokaf-offline-gitops-delivery/kr/`
- `/projects/rokaf-service-lb-hostport-conflict/kr/`
- `/about/kr/`
- `/cv/kr/`

Following internal links **while on a Korean edition** keeps `/kr/` when that page exists. A visitor using a normal English URL does not see or get redirected to a Korean edition. `/kr` is intentionally unlisted in navigation, RSS, and the public sitemap. Korean generated pages use `lang=ko`, `noindex,nofollow` and an English canonical URL.

Korean editions are built static files (suitable for GitHub Pages). No browser-side calls to translation providers are made.

## Translation source of truth

`apps/web/i18n/ko.json` is a checked-in source-English-to-Korean translation memory. `automation/scripts/localize-static-site.py` reads the **generated public HTML**, preserving Markdown/MDX structure, code spans, code fences, scripts, links and figures. It copies all public HTML routes with a `/kr/index.html` suffix and localizes all SVGs used by the pages. English originals are unchanged by localization.

English Projects (including reviewed incident records), site pages, and public article headings/metadata are translated. Notes already written in Korean remain Korean; their SVG labels and site chrome are localized. Private/unpublished drafts are excluded because they do not appear in the English static build.

The Korean SVGs are generated separately under `dist/figures/ko/` from the original artwork. They preserve the shapes, source figures and numerical claims; only descriptive labels and accessibility metadata are translated. Technical names and standards identifiers can remain in English.

## Authoring and updating translations

When creating or changing any public article:

1. Edit the English MDX as usual.
2. Build the English source before updating translations:
   `cd apps/web && npx astro build`
3. On a trusted **local workstation**, install an offline English→Korean Argos model in a dedicated Python environment. Run:
   `path/to/python automation/scripts/localize-static-site.py translate`
   from the repository root, or activate the environment and use `npm run l10n:translate` from `apps/web`.
4. Review new Korean strings in `apps/web/i18n/ko.json`, especially title, lead, technical claims, table headings and diagrams. Preferred human-edited corrections belong in `apps/web/i18n/ko-overrides.json`, which takes priority over the machine-generated catalog. They are retained across syncs.
5. Run `npm run build` from `apps/web`. The `postbuild` hook duplicates and translates all public routes and fails if any newly introduced translatable English text is missing from the catalog.
6. Check a representative English and Korean page, SVG readability, all links, `lang=ko`, `noindex` and correct code blocks. Then commit source changes and translation catalog together.

`npm run l10n:collect` creates an **ignored** local `apps/web/i18n/missing-ko.json` report. `npm run l10n:translate` uses the installed *offline* Argos model; the GitHub Action requires only Python's standard library and the checked-in catalog.

**New Projects articles cannot be published successfully unless their Korean visible strings and SVG labels are included in the catalog.** The same applies to modifications to existing public articles, so Korean copies do not silently become stale.

`automation/scripts/check-korean-editions.py` runs after localization and verifies every /kr page, every localized SVG, code-span equivalence, unlisted SEO behavior and internal image links.

## Quality and disclosure

Machine translation is a first pass, not evidence of technical correctness. Keep code, unit values and numeric results exact; review security-sensitive language and avoid disclosure of material absent from the English public page. Never translate a private draft into public output. Korean versions of investigation notes must preserve uncertainty rather than inventing a resolved incident.

Do not introduce `/kr` links to the English UI, header, sitemap or feed. If this routing model changes, update this document and regression tests together.
