# Distributed Systems: structure plan

Planning baseline: approved source `fb8354edb079e901edf18710ca9388a124712a5b` (source PRs #76–#80). Order below is the exact guided tree-index order, not filename order. This plan precedes teaching-layer drafting. Only Delivery Semantics is implemented in this milestone; all other entries are conversion plans awaiting later topic ownership and approval.

Each chapter retains its complete original text, code, tables, diagrams, operational sections and existing questions/answers in order. The coverage field names the chapter-specific mechanisms that must remain understandable; it is not permission to drop other original sections. Original Mermaid sources get designed FigureMaps when converted. New figures use shared role tokens, labelled relationships, explicit boundaries and captions stating the point. Motion is optional; listed traces are manual candidates, not promised animations. No new prediction questions, decision-card interactions or answer hiding are approved. Source links below are the primary authorities to consult at conversion, not a claim that every linked page or integration has been tested.

The content layer supplies content and component selection only. Layout and behaviour remain in the shared design system. Official requirements and product status must be rechecked at conversion, especially Security and Release policy chapters. The accompanying inventory records exact Git-object hashes and section/diagram counts; planning reads do not synchronize whole trees.

## 1. CAP Theorem

- **Opening problem:** A reconnecting client cannot reach the replica holding its last write.
- **Narrative route:** Trace a partitioned read; define the theorem; compare availability choices per operation.
- **Preserved coverage / internals:** Formal C/A/P definitions, CP/AP paths, quorum assumptions and product contracts.
- **Figures / step-throughs:** Partition boundary map; static paired read outcomes.
- **Production / staff decisions:** Specify stale/failed reads and recovery rather than label a whole product CP or AP.
- **Prerequisites:** Engineering Fundamentals: state machines, time, fault tolerance.
- **Official sources:** [www.cs.princeton.edu](https://www.cs.princeton.edu/courses/archive/spring13/cos598C/brewer.pdf).

## 2. Consistency Models

- **Opening problem:** A second device reads an older value after the first device saved.
- **Narrative route:** Follow one write and several observers; distinguish real-time, causal and session promises.
- **Preserved coverage / internals:** Linearization points, replication/anti-entropy, version vectors and session guarantees.
- **Figures / step-throughs:** Read/write histories; manual history comparison only if observer order matters.
- **Production / staff decisions:** Choose guarantees per feature; define session identity and failover behaviour.
- **Prerequisites:** CAP; happens-before and clocks.
- **Official sources:** [www.microsoft.com](https://www.microsoft.com/en-us/research/publication/session-guarantees-for-weakly-consistent-replicated-data/).

## 3. Idempotency

- **Opening problem:** The user retries an operation whose first result is unknown.
- **Narrative route:** Keep one operation identity; bind account and payload; trace atomic capture and retention expiry.
- **Preserved coverage / internals:** By-construction vs deduplication, key generation, unique scoped keys, transactions, TTL, Android persistence.
- **Figures / step-throughs:** Local transaction boundary map; replay/expired-key state trace.
- **Production / staff decisions:** Own retention and reconciliation; reject changed payloads and cross-account replay.
- **Prerequisites:** Consistency models; transactions.
- **Official sources:** [docs.stripe.com](https://docs.stripe.com/api/idempotent_requests).

## 4. Delivery Semantics

- **Opening problem:** A message commits, its acknowledgement is lost, and the sender retries.
- **Narrative route:** Follow that same message through send, commit, lost acknowledgement, retry and deduplication; then name the guarantees.
- **Preserved coverage / internals:** All three models, bounded retry limits, serializable local deduplication, Kafka EOS scope, Android process death, operational failure modes and all original Q&A.
- **Figures / step-throughs:** Five original-diagram FigureMaps; one manual illustrated state trace showing delivery/effect counts and knowledge.
- **Production / staff decisions:** Separate delivery attempts from committed business effects; define the local transaction boundary and external-service recovery.
- **Prerequisites:** Idempotency; queues, state machines and fault tolerance.
- **Official sources:** [www.rabbitmq.com](https://www.rabbitmq.com/docs/confirms); [kafka.apache.org](https://kafka.apache.org/41/design/design/); [www.postgresql.org](https://www.postgresql.org/docs/current/transaction-iso.html).

## 5. Mobile Client Consistency Contracts

- **Opening problem:** An optimistic save is followed by a stale server response.
- **Narrative route:** Start with the visible promise; attach versions/tokens; handle conflicts, offline queues and cursor reset.
- **Preserved coverage / internals:** Per-feature guarantees, monotonic reads, pending overlays, API fields, reset contracts and testing.
- **Figures / step-throughs:** Versioned response map; manual late-response trace.
- **Production / staff decisions:** Define canonical authority, stale-response rejection, conflict UX and pending-operation lifetime.
- **Prerequisites:** Delivery semantics and consistency models.
- **Official sources:** [www.microsoft.com](https://www.microsoft.com/en-us/research/publication/session-guarantees-for-weakly-consistent-replicated-data/).

## 6. Vector Clocks

- **Opening problem:** Two offline devices edit before either sees the other write.
- **Narrative route:** Compare scalar timestamps with causal histories; increment/merge/compare; show concurrent siblings.
- **Preserved coverage / internals:** Clock comparison core, event ticks, Dynamo siblings, membership and safe pruning.
- **Figures / step-throughs:** Three-device causal map; manual merge trace.
- **Production / staff decisions:** Bound membership metadata without falsely discarding causal history.
- **Prerequisites:** Consistency models; logical clocks.
- **Official sources:** [www.allthingsdistributed.com](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf).

## 7. CRDTs

- **Opening problem:** Replicas must merge edits without agreeing on an arrival order.
- **Narrative route:** Show a broken merge; derive the algebra; apply it to counters, sets and registers.
- **Preserved coverage / internals:** State/op-based delivery assumptions, lattice laws, G/PN counters, G/OR sets, LWW register, tombstones and intent limits.
- **Figures / step-throughs:** Merge-law FigureMaps; OR-set observed-remove trace only where tags explain the result.
- **Production / staff decisions:** Separate convergence from user intent, authorization and bounded metadata.
- **Prerequisites:** Vector clocks; set operations and partial orders.
- **Official sources:** [inria.hal.science](https://inria.hal.science/inria-00555588/document).

## 8. LWW Registers vs Richer CRDT Semantics

- **Opening problem:** Concurrent edits converge but the product loses an important change.
- **Narrative route:** Compare conflict policies against actual field semantics; choose defaults and revisit triggers.
- **Preserved coverage / internals:** LWW register vs counter/membership CRDTs, collaborative text, retained alternatives, migration and reversibility.
- **Figures / step-throughs:** Static decision matrix; concurrent-edit outcomes for each data type.
- **Production / staff decisions:** Choose by intent and invariants; avoid a universal LWW/CRDT winner.
- **Prerequisites:** CRDTs and vector clocks.
- **Official sources:** [inria.hal.science](https://inria.hal.science/inria-00555588/document).

## 9. Consensus Basics

- **Opening problem:** Two nodes each believe their value should become the committed value.
- **Narrative route:** Define agreement/safety/liveness; trace a quorum commit and an interrupted election; distinguish commit protocols.
- **Preserved coverage / internals:** Failure models, leaders, 2PC limits, Raft terms/logs/quorums and Paxos basics.
- **Figures / step-throughs:** Raft ownership map; manual election/log-commit trace.
- **Production / staff decisions:** State the failure assumptions, quorum cost and availability consequences.
- **Prerequisites:** CAP; queues, state machines and clocks.
- **Official sources:** [raft.github.io](https://raft.github.io/raft.pdf).

## 10. Replication and Leader Election

- **Opening problem:** A failover exposes an older value or an old leader keeps writing.
- **Narrative route:** Follow a write through replicas, election and fencing; return to the mobile read promise.
- **Preserved coverage / internals:** Replication models, quorum intersection assumptions, terms/fencing, leases, lag, tokens and failover windows.
- **Figures / step-throughs:** Leader/follower boundaries; stale-leader fencing trace.
- **Production / staff decisions:** Name RPO/RTO, read routing and fencing enforcement owner.
- **Prerequisites:** Consensus and consistency models.
- **Official sources:** [raft.github.io](https://raft.github.io/raft.pdf).

## 11. Streaming Logs and Partitioning

- **Opening problem:** Two updates for one entity arrive in a surprising order.
- **Narrative route:** Append records, choose partition key, consume/replay offsets; distinguish offsets, cursors and versions.
- **Preserved coverage / internals:** Partition-local order, rebalances, at-least-once streams, compaction/tombstones, retention and backpressure.
- **Figures / step-throughs:** Partition lanes; manual retry/rebalance trace when order matters.
- **Production / staff decisions:** Choose entity ordering scope, hot-key budget and expired-cursor reset protocol.
- **Prerequisites:** Delivery semantics and replication.
- **Official sources:** [kafka.apache.org](https://kafka.apache.org/41/design/design/).

## 12. Distributed Tracing

- **Opening problem:** An operation is slow across several services and the mobile log cannot explain where.
- **Narrative route:** Keep this bridge short; route to the existing Observability canonical chapter.
- **Preserved coverage / internals:** Preserve the complete bridge and canonical ownership; do not duplicate the tracing lesson.
- **Figures / step-throughs:** No new scene; a meaningful canonical continuation link.
- **Production / staff decisions:** Keep correlation/redaction policy with Observability ownership.
- **Prerequisites:** Streaming logs; Observability distributed tracing.
- **Official sources:** [www.w3.org](https://www.w3.org/TR/trace-context/).

## Pilot boundary and known review issues

The existing delivery chapter contains some broad summary claims even after the approved source audit: the historical UDP sentence, unconditional loss/latency wording, blanket exactly-once statements, and terse answers 4/7/8/10 need contextual limits. Keep exact source bytes and put concise, sourced scope explanations in labelled website additions, including the existing Q&A view. Do not silently rewrite the answers. The payment example requires a backend replay contract as well as persisted identity; queue delivery cannot promise a notification was displayed. New executable material must state whether it is a local model or real integration.
