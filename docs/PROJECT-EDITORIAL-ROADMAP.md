# Portfolio project editorial roadmap

Updated: 2026-11-20

This document separates **published engineering records** from **candidate articles requiring source review**. It is not an official military systems inventory. Public entries exclude internal diagrams, hosts, network addresses, identities, credentials and production runbooks.

## Information architecture

| Surface | Responsibility |
| --- | --- |
| About | Research direction and the personal connection among undergraduate projects, operational engineering and incoming graduate study |
| CV | Concise factual timeline, responsibilities, award, technical skills and deep links to focused records |
| Projects | Undergraduate project implementations and ROKAF engineering experience only |
| Notes / systems-notes | Linux system notes, a topic index, and future Korean technical articles (English navigation and metadata) |

## ROKAF engineering records — published

The independent K3s platform article is the **overview/index**. Its topic pages are expanded first-person engineering journals, not technology name lists.

| Focus | Slug |
| --- | --- |
| Platform experience overview | `independent-on-premises-k3s-platform-engineering` |
| Private images, Nexus, Kaniko and CI | `rokaf-private-artifacts-and-ci` |
| Longhorn, MinIO and storage recovery | `rokaf-stateful-storage-and-recovery` |
| Storage placement and failure domains | `rokaf-storage-placement-and-failure-domains` |
| Database HA and migrations | `rokaf-database-ha-and-langfuse-migrations` |
| ServiceAccount RBAC, OAuth2, Keycloak and OpenFGA | `rokaf-identity-rbac-and-policy` |
| Traefik, MetalLB, DNS and private TLS | `rokaf-networking-and-tls` |
| Central GPU infrastructure: KAI Scheduler and JupyterHub deployment and operations | `rokaf-central-gpu-platform-kai-jupyterhub` |
| GPU allocation and time-slicing/MIG comparison | `rokaf-gpu-scheduling-and-capacity` |
| RabbitMQ workers, retries and idempotency | `rokaf-async-workers-and-idempotency` |
| Asynchronous document translation pipeline | `document-translation-pipeline` |

## ROKAF open investigations — published as progress records

| Focus | Slug | Recorded boundary |
| --- | --- | --- |
| Langfuse v4 data migration | `rokaf-langfuse-v4-migration-field-notes` | Step 2 timeout differed from stored progress; Steps 1–5 and historical/new data checks completed November 17, 2026 |
| DNS and VIP reachability | `rokaf-dns-vip-open-investigations` | Intermittent symptom; multiple unconfirmed hypotheses |
| Pod IP vs ClusterIP datapath, with separate iptables bootstrap repair | `rokaf-k3s-cni-service-datapath` | K3s iptables-restore initially hit xtables lock contention; the later rule regeneration and `bootstrap done` establish completed bootstrap recovery. A different Pod-to-ClusterIP DNS failure still lacks packet-level attribution; no Docker/FORWARD/nftables cause was invented |
| GPU Operator / NFD visibility | `rokaf-gpu-discovery-open-investigation` | Missing/unexpected labels; full root cause not established |
| etcd and host disk incidents | `rokaf-control-plane-incident-log` | Restored service and remaining root-cause questions separated |
| Linux memory pressure and earlyoom | `rokaf-memory-pressure-and-service-recovery` | March near-full memory/reboot, service exit 16 and missing stop path, later victim log without attribution of the host-wide spike; no complete recovery or prevention claim |

These pages explicitly distinguish **observed facts, plausible causes, mitigations and unverified outcomes**. They do not publish internal addresses, replica placement, credentials, military network topology or actual recovery commands.

## Follow-ups still needing stronger evidence

- KAI Scheduler's exact configured queue and fairness policies, per-workload placement results, and the scheduler used by individual JupyterHub notebook Pods: do not infer these simply from both components operating in the same GPU cluster.
- A separate Pod-to-ClusterIP network outage's exact drop/translation point: distinguish its unresolved root cause from the **completed K3s iptables bootstrap recovery**.

- System observability and dashboards: actual implemented metrics, logs and operational benefit.
- Deeper individual RabbitMQ incident: a sanitized failure/retry case with preserved outcome.
- Longhorn, ClickHouse and Keeper experiments: reproducible lab workloads before publishing numbers.
- Actual Keycloak/OpenFGA rollout details: prototype versus deployment scope when safe to disclose.

## KDT Linux course — now published as study notes

KDT topics are **course learning materials**, not implementation portfolios. Their canonical source is [systems-notes](https://github.com/Petooooo/systems-notes), and the website publishes them through the **Notes** collection.

| Focus | New public notes route |
| --- | --- |
| Linux systems course overview | `/notes/study-kdt-overview/` |
| POSIX, IPC and networking | `/notes/study-kdt-posix/` |
| Scheduling, memory and VFS | `/notes/study-kdt-kernel-vfs-memory/` |
| Embedded Linux and drivers | `/notes/study-kdt-embedded-linux/` |
| Crash dump analysis | `/notes/study-kdt-crash-dump/` |
| eBPF/BCC and observability | `/notes/study-kdt-ebpf-observability/` |
| Kernel-to-storage reading map | `/notes/study-roadmap/` |

All six original KDT project routes redirect to these Notes routes. The CV keeps the KDT qualification but points readers to the Notes series for technical details.

## Connected topics and future experiments

The source-of-truth connection map is [systems-notes/notes/study-roadmap.mdx](https://github.com/Petooooo/systems-notes/blob/main/notes/study-roadmap.mdx). It covers:

- Nov–Dec 2026: POSIX, scheduler, virtual memory, VFS, tracing
- Jan 2027: ext4/F2FS, cache/writeback, blk-mq, NVMe/ZNS, isolated I/O experiments
- Feb 2027: systems-paper reviews and evaluation methods
- Spring 2027: coursework, baselines, reproducibility and research question selection
- Continuous: algorithms, systems code, research reading and reproducible notes

Experiments should be implemented in `systems-notes/labs/`, and results should be documented in Korean technical notes. Original KDT course source material and private mentor conversations are not published.

## Title and narrative voice

- **Use subject-led titles modeled on the existing `systems-notes` collection.** Prefer `Component: Mechanism / Incident / Migration` or `Component A and B: Specific Problem`. A reader should know the technical topic from the title alone.
- Avoid narrative hooks, rhetorical questions, two-sentence title reveals, and artificial conclusions: `The ...`, `Why ...`, `When ...`, `X was running, but Y ...`. Such material belongs in the body only when the incident actually supports it.
- Keep the English Projects title and the independently edited Korean title **technical and concise**, without translating the English syntax word for word. Examples: `RabbitMQ Redelivery and Worker Idempotency` / `RabbitMQ 메시지 재전달과 Worker 중복 처리`; `Longhorn Replica Failure and Volume Recovery` / `Longhorn Replica 장애와 볼륨 복구`.
- The body may remain a first-person account: begin with the actual observed symptom, show the decisions and evidence, and distinguish recovery, design proposals and unverified hypotheses. Do not manufacture a general moral or a bold aphorism at the end of every article. Close with the concrete checkpoint or outstanding test instead.
- On title/description changes, update the Korean override catalog and acknowledge the English source hashes. Keep slugs stable; verify site cards, HTML `title`, Korean `/kr/` pages and metadata after building.
- `automation/scripts/check-project-titles.py` rejects common narrative-hook titles in published Projects during the site check/build. Editorial judgment is still required for less obvious cases.

## Design and publishing conventions

### Editorial consistency after the November 2026 review

- **State completed work positively.** A successful implementation, internal deployment, service restoration or migration checkpoint belongs near the beginning and in the closing paragraph. Do not downgrade operational experience into a prototype merely because public deployment logs are unavailable; user-confirmed experience is a valid source of scope.
- **Limit uncertainty to its actual object.** A missing packet capture means the root cause remains open, not that the deployment never happened. A missing byte-for-byte reconciliation means data integrity has an unclosed check, not that the entire migration was hypothetical.
- **Avoid defensive repetition.** Do not write several variations of “I cannot claim,” “not a complete success,” “검증했다고 말할 수 없다,” or “만들어 쓸 생각도 없다” in the same article. State the observed result and one concise outstanding check.
- **Edit Korean as original prose.** Use technical subject-led section headings (e.g., “RabbitMQ Ack와 작업 상태”, “Prometheus WAL 저장 공간 장애”) rather than translations of English rhetorical devices. Keep the concrete first-person context in the body without formulaic epiphanies.
- **Keep preview text synchronized.** Project overview link labels and Korean descriptions must reflect the current article title and implementation status, not earlier narrative-hook labels or outdated “prototype only” language.
- **Treat study notes differently from incident journals.** A teaching question or A-versus-B contrast is useful when it explains a concept; do not mechanically remove these from educational notes in the name of style consistency.
- **Preserve the evidence boundary.** Do not fabricate benchmarks, full data-integrity validation, a root cause or an implemented rollout. Maintain internal-host, credential, and deployment-topology exclusions.

- Every focused article includes an original, dark-mode SVG based on the relevant mechanism; illustrations are conceptual, not production diagrams.
- Favor problem → observations → questions → experiments/decisions → verified outcome → open questions.
- KDT learning notes live in the separate study repository; preserve first-person learning context and distinguish illustrative examples from executed labs. Never invent benchmark figures, personal kernel patches or completed course capstones.
- The main portfolio and project write-ups remain in English; `systems-notes` article titles and bodies remain in Korean.
- On the public site, do not disclose military network identifiers, private credentials, detailed operational procedures, or internal topology.
