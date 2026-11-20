# Portfolio coverage review: central GPU management and K3s iptables

**Review date:** 2026-11-20

## Why the additional review was necessary

The published portfolio contained GPU time-slicing and MIG comparison notes, but did not mention **KAI Scheduler** or **JupyterHub** anywhere in the project articles. This omitted a major implemented outcome: the author **introduced and operated KAI Scheduler in an offline K3s environment and built and operated JupyterHub**, making GPU capacity available through a centrally managed platform.

The K3s CNI/iptables article also concentrated on open DNS/ClusterIP hypotheses while underemphasizing the separate **completed iptables rules-bootstrap recovery**. The retained operational evidence includes xtables lock contention, subsequent rule regeneration, and a successful `bootstrap done` checkpoint.

## Changes made

| Area | Editorial repair |
| --- | --- |
| New main engineering record | `rokaf-central-gpu-platform-kai-jupyterhub`: a technical first-person account of central GPU management, offline KAI introduction and deployment, JupyterHub service operation, and complementary NVIDIA GPU integration |
| Independent Korean edition | Natural Korean prose with a central-resource-management narrative; exposed manually at `/kr/` and excluded from indexing |
| Figure | Bilingual, conceptual KAI/JupyterHub/K3s resource ownership map, without host identities, internal topology or invented policy deployment |
| Existing GPU sharing article | Linked the implemented central platform; kept time-slicing, whole-GPU allocation and MIG technical comparisons as a separate layer |
| K3s platform overview | Promoted central GPU operations to the opening and project index; added iptables bootstrap outcome to the appropriate investigation row |
| Networking cases | Rewrote CNI/iptables section to state the completed K3s rules-bootstrap recovery, keeping a separate Pod-to-ClusterIP DNS root cause open; cross-linked in the broader networking record |
| Portfolio presentation | Updated Home, About, CV and Projects listing with central GPU platform responsibility and a direct technical link |
| Localization and editorial inventory | Synced the Korean source hashes, added metadata/SVG translations, and updated the publishing roadmap |

## Boundaries kept precise

**Confirmed by the author's account:** KAI Scheduler was brought into the isolated environment, deployed and operated; JupyterHub was built and operated; GPU resources were offered through a centrally managed K3s platform. GPU time-slicing was configured.

**Not inferred:** that every JupyterHub notebook Pod automatically used KAI, or that all of KAI's queue/fairness, gang-scheduling and preemption policies were enabled and benchmarked. Detailed per-workload scheduler selection and quantitative utilization improvements require configuration or test evidence and are not fabricated.

**iptables recovery:** During K3s startup, iptables-restore initially failed due to xtables lock contention; after troubleshooting and restart attempts the network rules were regenerated and `bootstrap done` was observed. The rule-bootstrap failure was recovered. The specific process holding the lock and the causally decisive intervention are not proven by retained logs. **A different Pod→ClusterIP DNS failure is not declared fixed** merely because the startup rule application recovered.

**Security:** No internal nodes, actual addresses, auth secrets, storage paths, organizational resource policy, queue topology, reproduction commands or private deployment details are published.

## Validation

- 28 published English and 28 reviewed Korean project editions.
- Astro check: zero errors, zero warnings, zero hints; subject-led titles accepted.
- 145 static pages, 144 opt-in Korean HTML pages, 90 localized SVGs.
- Korean-localization catalog: zero uncatalogued strings and zero edition errors.
- Rendered HTML checks cover the new EN/KO article, figure, cross-links, Home, CV, platform overview and iptables recovery language; all passed.
- Existing public URLs and unpublished local drafts preserved.

## Follow-up evidence to capture if available

A separate deep operational case study could add the deployed KAI queue policy, representative AI job placement, JupyterHub Single-user Pod resource and scheduler configuration, and sanitized scheduler/workload checks. For iptables, capture a before/after ruleset and responsible process where safe, if a precise root-cause narrative is needed. Those additions would enrich this already completed platform experience, not change the fact that it was deployed and operated.
