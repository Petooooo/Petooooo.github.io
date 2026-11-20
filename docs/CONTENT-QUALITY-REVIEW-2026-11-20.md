# Portfolio-wide editorial quality review

**Date:** 2026-11-20
**Scope:** 27 published English Projects, their 27 independently edited Korean editions, 114 source Notes (103 published Notes routes), overview and related-record links, and the generated bilingual static site.

## Executive finding

The most significant recurring problem was **editorial understatement**, not a lack of implementation work. Completed operational actions were often followed by several sentences saying what could not be proven. While the limits were frequently real, the repetition obscured implemented solutions and made some articles read like incomplete proposals. Korean section headings also retained English rhetorical-question patterns or artificial “lesson learned” framing long after project titles had been made technical and subject-led.

The review kept a firm distinction between **a completed implementation/deployment/recovery** and **an unverified root cause, benchmark, data-integrity assertion or rollout scope**. Removing defensive prose does not turn an open investigation into a completed remediation.

## Work performed

| Area | Review and action |
| --- | --- |
| Project articles | Read and compared the headings, openings, endings and cross-links of all 27 published English/Korean pairs; inspected full files for recurring qualifiers and wording mismatches |
| Korean editorial | Revised subject-led headings in **26 of 27** published Korean Projects; A01 had already been rewritten naturally in a previous pass |
| English editorial | Revised headings or evidence-led closing paragraphs in **20** English Projects |
| Heading consistency | **108 section headings** revised across English and Korean articles |
| Evidence-led conclusions | Reduced repeated disclaimers, strengthened explicit implementation and restoration checkpoints, and kept truly unresolved causes open |
| Overview and cross-links | Replaced stale “When/Why…” and rhetorical Korean link labels with topic-led names, without changing destination slugs |
| Study Notes | Scanned all **114 source notes**, including imported study notes; checked title/heading patterns, formulaic phrases and unsupported-implementation indicators; found 103 public note routes after build |
| Editorial prevention | Updated `docs/PROJECT-EDITORIAL-ROADMAP.md` with concrete guidelines about deployment claims, Korean prose and evidence boundaries |

## Selected corrections

### Completed engineering work must be visible

- **Document translation / RabbitMQ:** User-confirmed internal deployment and operation remain explicit. The related RabbitMQ article now connects the implemented Claim/Lease state model to the deployed pipeline rather than stopping at a hypothetical design.
- **K3s ServiceLB:** The observed `svclb-*` host-port collision and service access recovery are stated positively; other DNS/VIP investigations remain separate.
- **Plane CE:** Account and Workspace creation and the later `/live` Pages repair are recorded as two verified corrections, without letting unrelated storage/proxy errors erase them.
- **ClickHouse:** Replicated table conversion, Keeper/read-only investigation, writable status and queue progress lead the conclusion. Full row parity is still an independent check.
- **Longhorn:** `Healthy` after reducing replica count to one is explicitly reduced-redundancy availability, not a fabricated successful two-copy rebuild.
- **MinIO:** Bulk transfer and distributed target deployment are explicit; observed object discrepancies and follow-up reconciliation remain visible.

### Korean translation and narrative

- Replaced long literal question-like headings with focused topics, such as **“API 중단과 etcd 상태 조사”**, **“NFD 비활성화와 노드 라벨”**, **“Plane CE 초기 설정 루프”**, **“Replica 재구축과 데이터 정합성 검증”**.
- Avoided “I cannot claim…”, “만들어 쓸 생각도 없다”, broad moral lessons and multiple repeated paragraphs saying the same test was absent.
- Kept real incidents, component names, actual error codes and the author's first-person operating decisions in the narrative. No invented performance percentage, fully audited data-integrity result, production failover or closed root cause was added.

### Study notes

The Notes collection serves a different purpose from first-person incident journals. The automated scan found no systematic reuse of explicit KDT “what I learned in class” openings or OS Lab-preparation framing. Some notes use teaching questions and an **A versus B** contrast; these were often helpful to a technical explanation, so the review did **not** mechanically rewrite all 114 sources. This was a collection-wide heuristic audit plus targeted contextual sampling, not an independent scientific fact-check of every technical sentence.

## Verification

- Published article source count: **27 English + 27 Korean**; all matched generated EN/`/kr/` pages.
- Astro check: **0 errors, 0 warnings, 0 hints**; 27 published technical titles validated.
- Astro build: **144 pages**.
- Korean localization: **143 opt-in `/kr/` HTML pages**, **89 localized SVGs**, **0 uncatalogued English strings**, **0 Korean-edition check errors**.
- Local checks of article-to-article links, local figure references, preview text, and internal IPv4 literals: **0 issues** across the 27 project pairs.
- Unpublished draft sources and locally untracked review material were left out of the edited set.
- No project slug, existing figure asset or public article URL was renamed.

## Remaining editorial and evidence boundaries

The review deliberately did not invent missing packet traces for DNS/VIP/CNI investigations, full GPU Operator recovery, a root cause for host memory spikes, exhaustive ClickHouse/MinIO parity or a successful broad Keycloak/OpenFGA rollout. Those topics remain credible **open engineering investigations** with concise next checks. A public prose review cannot independently verify internal operational logs unavailable to the repository; it can accurately reflect the author's directly confirmed experience and avoid making up evidence.

The source Notes deserve separate technical-correctness reviews over time, particularly version-sensitive Kubernetes, Cloud, storage and Linux topics. Their longer pedagogical format should not be forced into the style of an incident journal.

**Editorial rule going forward:** Describe **what was designed, implemented, deployed and restored** in direct language; retain a single, precise boundary for what was not measured or diagnosed; write Korean as natural original prose; keep public metadata and overview links aligned with the article.
