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

| Focus | Slug |
| --- | --- |
| Platform experience overview | `independent-on-premises-k3s-platform-engineering` |
| Private image supply and CI | `rokaf-private-artifacts-and-ci` |
| Stateful storage and recovery | `rokaf-stateful-storage-and-recovery` |
| Database HA and stateful migrations | `rokaf-database-ha-and-langfuse-migrations` |
| ServiceAccount RBAC, SSO, Keycloak and OpenFGA | `rokaf-identity-rbac-and-policy` |
| Service networking and TLS | `rokaf-networking-and-tls` |
| GPU placement and capacity resilience | `rokaf-gpu-scheduling-and-capacity` |

The main platform article is an index; specialized details belong in their own records. Policy experiments and GPU sharing alternatives are described as investigated/evaluated unless production deployment can be independently established.

## ROKAF candidate follow-ups — not yet written

| Topic | Evidence needed before publishing |
| --- | --- |
| Control-plane incident analysis (etcd, CoreDNS, API availability) | Sanitized observed symptoms, verified root cause versus hypothesis, durable fix and outcome |
| Monitoring and observability (Prometheus, logs, tracing) | Actual implemented dashboards, metrics/log collection, operational lessons |
| Message queues and idempotency (RabbitMQ) | Architecture scope, idempotent task handling, retry tests and failure semantics |
| GPU operator and node-feature detection | Observed labels/plugin behavior and validated mitigation |
| Single-system upgrade diaries (Langfuse, ClickHouse Keeper) | Public-safe chronology with evidence; remove version-specific internal topology and paths |
| Stateful app security and SSO migrations | Which Keycloak/OpenFGA functions were actually deployed versus prototyped |

## K-Digital Training — published

| Focus | Slug |
| --- | --- |
| Linux Systems & Kernel Expert Course overview | `kdt-linux-system-kernel-expert-course` |
| POSIX, processes, IPC and socket programming | `kdt-posix-system-programming` |
| Kernel tracing, virtual memory and VFS | `kdt-kernel-tracing-vfs-memory` |
| Embedded Linux and driver foundations | `kdt-embedded-linux-drivers` |

The original syllabus and archived course lecture notes establish covered subjects and learning objectives. They **do not prove that every suggested capstone was individually completed**.

## KDT candidate follow-ups — source/artifact check first

- Kernel scheduling, CFS, runqueue and trace analysis, tied to a real trace once reproduced.
- VFS, EXT2/EXT4 journaling, flash FTL and F2FS, tied to a reproducible filesystem lab.
- eBPF/BCC, Prometheus/Grafana/ELK monitoring, with recorded configuration and experiment outputs.
- Raspberry Pi drivers, interrupt handling and workqueues, only with existing source code or a new explicitly labeled reproduction.
- Container fundamentals and service composition, with a reproducible sample rather than claiming the course's sample as original work.

## Illustrations

The two undergraduate project posts use **source-grounded vector diagrams** (consistent dark theme and typography). Original report/poster images were inspected and recreated as clean SVG graphics, but the SVGs are labeled as **schematic redraws**, not original native vector assets.

The ROKAF overview and related articles use **abstract capability diagrams** only. Never publish the actual node layout, security-zone structure, internal identities, exact configuration, or exploit/failure recovery instructions.

## Publication checklist

- A factual personal role confirmed by CV or direct account.
- Implemented vs considered vs course-covered claims clearly separated.
- No unsupported performance figures, availability claims, or unverifiable project authorship.
- Figures remain legible on dark backgrounds and mobile widths.
- All linked articles and assets return HTTP 200 after deployment.
- Notes remain Korean; public repo navigation/docs remain English.
