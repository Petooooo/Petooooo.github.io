# Portfolio project editorial roadmap

Updated: 2026-11-15

This document separates **published engineering records** from **candidate articles requiring source review**. It is not an official military systems inventory. Public entries exclude internal diagrams, hosts, network addresses, identities, credentials and production runbooks.

## Information architecture

| Surface | Responsibility |
| --- | --- |
| About | Research direction and the personal connection among undergraduate projects, operational engineering and incoming graduate study |
| CV | Concise factual timeline, responsibilities, award, technical skills and deep links to focused records |
| Projects | Undergraduate project designs, ROKAF engineering experience and KDT training records |
| systems-notes | Korean study articles with English taxonomy, slugs, directories and README/guidelines |

## ROKAF engineering records — published

The independent K3s platform article is the **overview/index**. Its topic pages are expanded first-person engineering journals, not technology name lists.

| Focus | Slug |
| --- | --- |
| Platform experience overview | `independent-on-premises-k3s-platform-engineering` |
| Private images, Nexus, Kaniko and CI | `rokaf-private-artifacts-and-ci` |
| Longhorn, MinIO and storage recovery | `rokaf-stateful-storage-and-recovery` |
| Database HA and migrations | `rokaf-database-ha-and-langfuse-migrations` |
| ServiceAccount RBAC, OAuth2, Keycloak and OpenFGA | `rokaf-identity-rbac-and-policy` |
| Traefik, MetalLB, DNS and private TLS | `rokaf-networking-and-tls` |
| GPU scheduling and capacity choices | `rokaf-gpu-scheduling-and-capacity` |
| RabbitMQ workers, retries and idempotency | `rokaf-async-workers-and-idempotency` |

## ROKAF open investigations — published as progress records

| Focus | Slug | Recorded boundary |
| --- | --- | --- |
| Langfuse v4 background migrations | `rokaf-langfuse-v4-migration-field-notes` | Step 2 timeout vs persisted completed state; later open stages |
| DNS and VIP reachability | `rokaf-dns-vip-open-investigations` | Intermittent symptom; multiple unconfirmed hypotheses |
| GPU Operator / NFD visibility | `rokaf-gpu-discovery-open-investigation` | Missing/unexpected labels; full root cause not established |
| etcd and host disk incidents | `rokaf-control-plane-incident-log` | Restored service and remaining root-cause questions separated |

These pages explicitly distinguish **observed facts, plausible causes, mitigations and unverified outcomes**. They do not publish internal addresses, replica placement, credentials, military network topology or actual recovery commands.

## Follow-ups still needing stronger evidence

- System observability and dashboards: actual implemented metrics, logs and operational benefit.
- Deeper individual RabbitMQ incident: a sanitized failure/retry case with preserved outcome.
- Longhorn, ClickHouse and Keeper experiments: reproducible lab workloads before publishing numbers.
- Actual Keycloak/OpenFGA rollout details: prototype versus deployment scope when safe to disclose.

## K-Digital Training — published

| Focus | Slug |
| --- | --- |
| Linux Systems & Kernel Expert Course overview | `kdt-linux-system-kernel-expert-course` |
| POSIX, processes, IPC and socket programming | `kdt-posix-system-programming` |
| Kernel tracing, virtual memory and VFS | `kdt-kernel-tracing-vfs-memory` |
| Embedded Linux and driver foundations | `kdt-embedded-linux-drivers` |
| Kernel dump and crash analysis learning progress | `kdt-crash-dump-analysis-progress` |
| eBPF/BCC and monitoring learning progress | `kdt-ebpf-observability-progress` |

The original syllabus and archived course lecture notes establish covered subjects and learning objectives. They **do not prove that every suggested capstone was individually completed**.

## Next KDT / study experiments

The KDT pages now read as **first-person course reflections**, including progress notes for crash analysis and eBPF monitoring. Future experiments should live primarily in `systems-notes` (Korean articles; English categories and README), with source code and measurements there:

- Reproduce scheduler wake-up tracing with ftrace and KernelShark and capture a minimal result.
- Measure page-cache and VFS/writeback behavior in an isolated storage experiment.
- Develop and run a small POSIX IPC/network server with tests for failures and disconnects.
- Revisit interrupt/workqueue concepts in an isolated driver example.
- Study eBPF/BCC and `perf` with a representative workload.

## Design and publishing conventions

- Every focused article includes an original, dark-mode SVG based on the relevant mechanism; illustrations are conceptual, not production diagrams.
- Favor problem → observations → questions → experiments/decisions → verified outcome → open questions.
- For KDT, write in the voice of someone who **attended and learned**, not as a legalistic audit of the syllabus. Never invent a benchmark, personal kernel patch or independently completed final project.
- The main portfolio and project write-ups remain in English; `systems-notes` article titles and bodies remain in Korean.
- On the public site, do not disclose military network identifiers, private credentials, detailed operational procedures, or internal topology.
