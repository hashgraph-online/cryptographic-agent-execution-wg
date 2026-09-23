---
title: "HCS-XX — ZKBC Architecture Diagrams"
description: "Companion diagrams for the Zero-Knowledge Boundary Compliance draft: component architecture, trust boundaries, data flow through the gateway and the proof pipeline, and the public/private input–output split of every policy family, proof mode, and on-graph operation."
sidebar_position: 999
---

# HCS-XX: ZKBC Architecture Diagrams (Companion)

### Status: Draft (companion to [HCS-XX Zero-Knowledge Boundary Compliance](./ZKBC-Zero-Knowledge-Boundary-Compliance.md))

This document is illustrative, not normative. Every diagram is drawn from the
text of the ZKBC draft and links to the section it depicts; where a diagram
exposes an ambiguity that is still open in the draft, the caption points to the
matching entry in the [Architecture Review](./ZKBC-Architecture-Review.md).
Field names, enum values, and hash-preimage orderings are copied verbatim from
the draft so that a reviewer can check each figure against the prose.

Eight diagrams — A1, A3, A5, B1, B2, B4, B7, and C7 — are also embedded in the
draft itself. The draft's copies are canonical; this document mirrors them
byte-for-byte, and a change to one of them belongs in the draft first.

Reading order: **Part A** places the components and trust classes; **Part B**
follows one boundary action from capture to on-graph verification; **Part C**
gives the input/output contract of each policy family, proof mode, wire object,
and topic operation.

Visual convention used throughout: **dashed strokes** mark private-witness
material that never leaves the gateway; solid strokes mark public artifacts.

### Diagram Index

| # | Diagram | Draft section |
|---|---------|---------------|
| A1 | Deployment component overview | [Architecture Overview](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#architecture-overview) |
| A2 | Trust boundaries and threat model | [Security Considerations](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#security-considerations) |
| A3 | Complete mediation: channel × direction | [Complete Mediation](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#complete-mediation) |
| A4 | Deployment profiles | [Deployment Profiles](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#deployment-profiles-informative) |
| A5 | Topic system: types, keys, memos, publishers | [Topic System](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#topic-system) |
| A6 | Standards integration map | [Integration with Existing Standards](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#integration-with-existing-standards) |
| B1 | Lifecycle: topic setup and registration | [Implementation Workflow](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#implementation-workflow) |
| B2 | Gateway two-phase processing | [Gateway Processing Model](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#gateway-processing-model) |
| B3a | Per-action sequence: real-time mode | [Proof Modes](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#proof-modes) |
| B3b | Per-session sequence: batch mode | [Proof Modes](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#proof-modes) |
| B3c | Recursive mode and the chain digest | [Proof Modes](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#proof-modes) |
| B4 | Canonicalization pipelines | [Canonicalization](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#canonicalization) |
| B5 | Commitment constructions | [Commitments and Identifiers](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#commitments-and-identifiers) |
| B6 | Public statement binding | [Public Statement Binding](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#public-statement-binding) |
| B7 | Auditor verification decision flow | [Validation](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#validation) |
| B8 | Policy lifecycle and timestamp-scoped resolution | [`policy_published`](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#policy_published) / [`policy_revoked`](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#policy_revoked) |
| C1 | Output family I/O | [Output Compliance](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#output-compliance) |
| C2 | Tool-invocation family I/O | [Tool-Invocation Compliance](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#tool-invocation-compliance) |
| C3 | Access family I/O | [Access Compliance](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#access-compliance) |
| C4 | Receipt and journal structure | [Public Compliance Journal](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#public-compliance-journal) / [Receipt Wire Format](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#compliance-receipt-wire-format) |
| C5 | Operation envelopes | [Operation Reference](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#operation-reference) |
| C6 | Normalization asymmetry: fail-closed vs fail-open | [Normalization and Confusable Text](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#6-normalization-and-confusable-text) |
| C7 | Proof-mode configuration matrix | [Proof Modes](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#proof-modes) |

---

## Part A — Architecture

### A1. Deployment component overview

The six component classes of the
[Architecture Overview](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#architecture-overview):
host and sandbox, gateways, the two issuer registries, the receipt topics (one
per gateway or one shared), HCS-1 proof storage, and the HCS-11 profile. The
host also runs the per-session sequence counter every gateway draws from. The
agent has no edge to anything outside the sandbox except through a gateway.
Solid on-graph edges carry the operation or artifact named on them; dotted
edges are off-graph distribution or discovery.

```mermaid
flowchart TB
  User(["User"])
  Issuer(["Policy Issuer"])
  Auditor(["Auditor"])

  subgraph Host["Host — trusted to enforce the sandbox boundary and to run the per-session counter"]
    direction TB
    subgraph Sandbox["Sandbox — only egress paths are gateways"]
      Agent["Agent workload<br/>plans · retrieves context · invokes tools · responds"]
    end
    subgraph Gateways["Gateways — non-bypassable mediation points"]
      direction LR
      GWu["user channel"]
      GWd["data channel"]
      GWt["tool / API channel"]
      GWw["web channel"]
    end
    Agent <--> GWu
    Agent <--> GWd
    Agent <--> GWt
    Agent <--> GWw
  end

  subgraph Ext["External services — no requirements placed on them"]
    direction LR
    Data[("Data stores")]
    Tools["Tools · third-party APIs"]
    Web["Web"]
  end

  subgraph Hedera["Hedera Consensus Service"]
    direction LR
    RT["Receipt Topics — type 0<br/>one per gateway, or one shared<br/>submit key: gateway · MUST NOT have admin key"]
    PR["Policy Registry — type 1<br/>submit key: issuer"]
    GR["Program Registry — type 2<br/>submit key: issuer"]
    F1[("HCS-1 files<br/>receipt bytes · verifying keys")]
    P11["HCS-11 agent profile<br/>zkbc block: receipt_topic_ids · policy and program registry ids"]
  end

  User <-->|"query / response"| GWu
  GWd <-->|"retrieval request / returned records"| Data
  GWt <-->|"invocation / result"| Tools
  GWw <-->|"request / response"| Web

  Gateways -->|"receipt_issued — journal inline, proof_ref, vk_id"| RT
  Gateways -->|"store deterministic-CBOR receipt"| F1
  Issuer -->|"policy_published · policy_revoked"| PR
  Issuer -->|"program_registered"| GR
  Issuer -->|"store verifying key — vk_ref"| F1
  Issuer -.->|"distributes policy content — off-graph, confidential"| Gateways

  P11 -.->|"discover authentic topic ids"| Auditor
  RT -->|"read journals, verdicts, sequence_ranges"| Auditor
  PR -->|"resolve policy_id at consensus timestamp"| Auditor
  GR -->|"resolve vk_id → program_id, proof_system"| Auditor
  F1 -->|"fetch receipt · verifying key"| Auditor
```

### A2. Trust boundaries and threat model

The trust class of each principal, from the threat model in
[Security Considerations](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#security-considerations).
The host is the only *trusted* party, and only for one thing: keeping every
egress path inside a gateway. That property is checked by deployment audit; the
proof system cannot establish it, and hardware attestation of the gateway
software is out of scope for this version of the draft.

```mermaid
flowchart LR
  subgraph T0["Trusted"]
    Host["Host<br/>trusted to enforce the sandbox boundary<br/>complete mediation — verified by deployment audit, not by proof"]
  end
  subgraph T1["Potentially malicious"]
    Agent["Agent<br/>may leak, or answer one user with another's data<br/>never relied on to select audited actions or self-report"]
  end
  subgraph T2["Semi-honest"]
    User["User"]
    Gateway["Gateway<br/>semi-honest in operation<br/>adversarial with respect to proof forgery<br/>MUST be non-bypassable"]
  end
  subgraph T3["Honest-but-curious"]
    Issuer["Policy Issuer"]
    Auditor["Auditor"]
    Ext["External services"]
  end

  Host -->|"confines"| Agent
  Agent -->|"every boundary action"| Gateway
  User <-->|"mediated query / response"| Gateway
  Gateway <-->|"mediated actions"| Ext
  Issuer -.->|"policy content — confidential"| Gateway
  Issuer -->|"policy commitments — public"| Auditor
  Gateway -->|"proof + public journal only"| Auditor

  Roots["Security rests on<br/>knowledge soundness and zero knowledge of the proof system<br/>collision and second-preimage resistance of H<br/>host sandbox configuration"]
  Roots -.- Gateway
```

### A3. Complete mediation: channel × direction

[Complete Mediation](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#complete-mediation)
requires a gateway on every channel and in both directions; the action record's
`channel` enum is `{ user, data, tool, web }` and `direction` is
`{ inbound, outbound }` relative to the agent. The dotted, crossed edge is the
path the sandbox MUST deny. Web requests are evaluated under the tool family,
with the request target's scheme and host as the tool identifier.

```mermaid
flowchart LR
  Agent["Agent<br/>inside the sandbox"]

  subgraph GW["Gateway on each channel — capture · canonicalize · evaluate · prove"]
    direction TB
    Gu["channel = user"]
    Gd["channel = data"]
    Gt["channel = tool"]
    Gw["channel = web"]
  end

  User(["User"])
  Data[("Data stores")]
  Tools["Tools · APIs"]
  Web["Web"]

  Agent -->|"outbound: response"| Gu
  Gu -->|"inbound: query"| Agent
  Gu <--> User

  Agent -->|"outbound: retrieval request"| Gd
  Gd -->|"inbound: returned records"| Agent
  Gd <--> Data

  Agent -->|"outbound: invocation"| Gt
  Gt -->|"inbound: result"| Agent
  Gt <--> Tools

  Agent -->|"outbound: request"| Gw
  Gw -->|"inbound: response"| Agent
  Gw <--> Web

  Agent -. "direct un-mediated connection — sandbox MUST deny" .-x Tools
  Tools -. "defense in depth: MAY reject non-gateway origins" .- Gt
```

### A4. Deployment profiles

The three informative profiles of
[Deployment Profiles](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#deployment-profiles-informative)
use the same vocabulary as A1; only *who operates the host* and *where receipts
go* change. The cryptographic layer is identical in all three. The Local
profile MAY keep receipts off-graph, which makes it a partial-conformance
configuration (on-graph anchoring is REQUIRED for full HCS-XX conformance).

```mermaid
flowchart TB
  subgraph Local["Local profile — the user's device is the host"]
    direction LR
    LH["Host = user device"]
    LS["Sandbox: assistant"]
    LG["Gateway<br/>mediates local files · memory · browser · network"]
    LR["Receipts MAY stay off-graph<br/>crypto layer verifies unchanged"]
    LH --> LS --> LG --> LR
  end

  subgraph Enterprise["Enterprise profile — organization-operated hosts"]
    direction LR
    EH["Org hosts"]
    ES["Sandboxed agent workloads"]
    EG["Gateway per sandbox boundary<br/>organizational policy"]
    EX["Tenant-scoped data stores · internal tools · external connectors"]
    ER["Receipt topics on-graph"]
    EH --> ES --> EG --> EX
    EG --> ER
  end

  subgraph Platform["Platform profile — sandbox and gateway built into the runtime"]
    direction LR
    PH["Platform hosts"]
    PS["Agent runtime with embedded sandbox + gateway"]
    PV["Verification artifacts exposed to<br/>customers · auditors · regulators"]
    PR["Receipt topics on-graph"]
    PH --> PS --> PR --> PV
  end
```

### A5. Topic system: types, keys, memos, publishers

The three topic types of the
[Topic System](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#topic-system),
their memos (`hcs-xx:<indexed>:<ttl>:<type>[:<param>]`, always `indexed = 0`),
the key discipline, and the transaction memo `hcs-xx:op:{op}:{type}` on each
operation. Values are the draft's test-vector identifiers. The receipt-topic
memo names its policy registry and `policy_published` names the program
registry, so both registries are reachable from a receipt topic alone.

```mermaid
flowchart LR
  Issuer(["Issuer account<br/>0.0.500100"])
  Gateway(["Gateway account<br/>0.0.500200"])

  PR["Policy Registry — type 1<br/>memo hcs-xx:0:86400:1:0.0.500100<br/>param = issuer account<br/>submit key: issuer"]
  GR["Program Registry — type 2<br/>memo hcs-xx:0:86400:2:0.0.500100<br/>param = issuer account<br/>submit key: issuer"]
  RT["Receipt Topic — type 0<br/>memo hcs-xx:0:86400:0:0.0.600002<br/>param = governing policy registry<br/>submit key: gateway · MUST NOT have admin key"]
  F1[("HCS-1 file topics<br/>hcs://1/topicId<br/>SHA-256 of file in memo")]
  P11["HCS-11 profile · zkbc block<br/>receipt_topic_ids [0.0.600001]<br/>policy_registry_topic_id 0.0.600002<br/>program_registry_topic_id 0.0.600003<br/>proof_systems"]

  Issuer -->|"op 1 policy_published · txn memo hcs-xx:op:1:1"| PR
  Issuer -->|"op 2 policy_revoked · txn memo hcs-xx:op:2:1"| PR
  Issuer -->|"op 3 program_registered · txn memo hcs-xx:op:3:2"| GR
  Gateway -->|"op 0 receipt_issued · txn memo hcs-xx:op:0:0"| RT

  RT -.->|"memo param"| PR
  PR -.->|"policy_published.program_registry_topic_id"| GR
  RT -.->|"proof_ref"| F1
  GR -.->|"vk_ref"| F1
  P11 -.-> RT
  P11 -.-> PR
  P11 -.-> GR
```

### A6. Standards integration map

How ZKBC composes with the rest of the HCS family, per
[Integration with Existing Standards](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#integration-with-existing-standards)
and the [Rationale](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#rationale).

```mermaid
flowchart LR
  ZKBC["HCS-XX ZKBC<br/>receipts · policy commitments · vk registrations"]

  H1["HCS-1 File Data Management<br/>stores receipt bytes and verifying keys<br/>topic-memo SHA-256 integrity anchor"]
  H2["HCS-2 Topic Registries<br/>indexed / ttl memo semantics<br/>optional discovery listing"]
  H4["HCS-4 Standardization Process<br/>assigns the number replacing xx<br/>append-only enum convention"]
  H10["HCS-10 OpenConvAI<br/>shared operation-envelope conventions p, op, m"]
  H11["HCS-11 Profile Metadata<br/>zkbc block advertises topic ids<br/>auditors MUST discover here"]
  H14["HCS-14 Universal Agent ID<br/>RECOMMENDED tenant_id / user_id inputs to identity_digest"]
  H17["HCS-17 State Hash<br/>complementary account-level attestation<br/>SHA-384 vs ZKBC SHA-256 — documented deviation"]
  H19["HCS-19 Privacy Compliance<br/>plaintext documentation layer<br/>audit entries MAY reference ZKBC evidence by HRL"]

  ZKBC -->|"proof_ref · vk_ref"| H1
  ZKBC -->|"memo format"| H2
  ZKBC -->|"numbering"| H4
  ZKBC -->|"envelope"| H10
  ZKBC -->|"discovery"| H11
  H14 -->|"nfc(uaid)"| ZKBC
  ZKBC -.-|"complementary"| H17
  H19 -->|"hcs://xx/receiptTopic#messageSequenceNumber"| ZKBC
```

---

## Part B — Data Flow

### B1. Lifecycle: topic setup and registration (Workflow Steps 1–2)

[Implementation Workflow](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#implementation-workflow)
Steps 1 and 2. Everything here happens once per deployment or per policy
version, before any boundary action is mediated. `program_id` is
`commit(nfc("program"), program_descriptor)`; `vk_id` MUST be
`commit(nfc("vk"), vk_bytes)` over the bytes at the REQUIRED `vk_ref`, so a
fetched key is self-authenticating.

```mermaid
sequenceDiagram
  autonumber
  participant Issuer
  participant Gateway
  participant PR as Policy Registry (type 1)
  participant GR as Program Registry (type 2)
  participant RT as Receipt Topic (type 0)
  participant F1 as HCS-1 File
  participant P11 as HCS-11 Profile

  Note over Issuer,P11: Step 1 — Topic setup
  Issuer->>PR: create topic · memo hcs-xx:0:86400:1:issuerAccount · issuer submit key
  Issuer->>GR: create topic · memo hcs-xx:0:86400:2:issuerAccount · issuer submit key
  Gateway->>RT: create topic (per gateway, or one shared) · memo hcs-xx:0:86400:0:policyRegistryTopicId · gateway submit key · NO admin key
  Gateway->>P11: add zkbc block (receipt_topic_ids, policy registry, program registry topic ids, proof_systems)

  Note over Issuer,F1: Step 2 — Program and policy registration
  Issuer->>Issuer: compile compliance program · program_id = commit("program", descriptor)
  Issuer->>F1: store verifying-key bytes
  F1-->>Issuer: vk_ref = hcs://1/topicId
  Issuer->>Issuer: vk_id = commit("vk", vk_bytes)
  Issuer->>GR: program_registered {program_id, vk_id, proof_system, vk_ref, params?}
  Issuer->>Issuer: set_commit forbidden F · allowlist A · sensitive keys K · commit canonicalization descriptor · access descriptor
  Issuer->>PR: policy_published {policy_id, policy_commitments, program_id, program_registry_topic_id, effective_from}
  Issuer-->>Gateway: distribute policy content off-graph (confidential)
```

### B2. Gateway two-phase processing (per boundary action)

The [Gateway Processing Model](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#gateway-processing-model)
and Workflow Step 3. Phase 1 runs in the clear and gates release; Phase 2 runs
only after Phase 1 passes. Release ordering is mode-dependent: `real_time`
proves before release, `batch` and `recursive` release after the pre-check and
prove at window end. The sequence number is assigned only once the pre-check
passes, so a rejected action leaves no public trace. In `real_time` a proving
failure is fail-closed: the action is held, not released, and the gateway
signals `prover_unavailable`, distinct from `policy_rejected`. The private witness
(dashed) never leaves the gateway; only the receipt and the `receipt_issued`
operation are public.

```mermaid
flowchart TB
  In["Boundary action arrives on a channel"]
  Cap["Capture action record<br/>session_id · channel · direction · payload · captured_at"]
  Canon["Canonicalize<br/>output: fold → UAX 29 words → multiset<br/>tool / web: nfc(id) · RFC 8785 args · RFC 6901 keys"]
  Pre{"Phase 1 — plaintext pre-check<br/>does the action satisfy the issued policy?"}
  Rej["REJECT<br/>return control to the agent<br/>not numbered · nothing released · nothing published"]
  Regen["Agent MAY regenerate output,<br/>revise the tool call, or reissue the access request"]
  Seq["Assign sequence_no<br/>next value of the host's session counter"]

  ModeQ{"mode?"}
  Rel1["Release action to the external party"]
  Rel2["Release action to the external party"]

  Wit["Phase 2 — build private witness<br/>action records · policy sets · Merkle openings · identities"]
  Stmt["Assemble public statement → statement_hash"]
  Prove["Generate zero-knowledge proof<br/>binds action · policy version · session · sequence_range"]
  Defect["Gateway defect<br/>MUST NOT publish the range · SHOULD alert<br/>gap visible to auditors"]
  Hold["HOLD — fail-closed<br/>signal prover_unavailable, distinct from policy_rejected<br/>MUST NOT release · sequence_no retained"]
  Rcpt["Assemble receipt — deterministic CBOR<br/>journal + proof {system, params, bytes, vk_id}"]
  Store["Store receipt as HCS-1 file → proof_ref"]
  Pub["Publish receipt_issued to receipt topic<br/>journal inline · proof_ref · vk_id · txn memo hcs-xx:op:0:0"]

  In --> Cap --> Canon --> Pre
  Pre -->|"no"| Rej --> Regen --> In
  Pre -->|"yes"| Seq --> ModeQ
  ModeQ -->|"real_time: prove before release"| Wit
  ModeQ -->|"batch / recursive: release now, prove at window end"| Rel2 --> Wit
  Wit --> Stmt --> Prove
  Prove -->|"real_time"| Rel1 --> Rcpt
  Prove -->|"batch / recursive"| Rcpt
  Prove -->|"batch / recursive: proving fails post-hoc"| Defect
  Prove -->|"real_time: proving fails"| Hold
  Hold -->|"prover recovers"| Wit
  Rcpt --> Store --> Pub

  classDef witness stroke-dasharray: 5 5;
  class Cap,Wit witness;
```

### B3a. Per-action sequence — real-time mode

[Proof Modes](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#proof-modes),
`real_time` (`0x02`): one proof per boundary action, generated on the release
path before the action is released, over `sequence_range = { n, n }`. The mode
is fail-closed: no proof, no release. Prover latency SHOULD be low enough for
interactive use.

```mermaid
sequenceDiagram
  autonumber
  participant Agent
  participant Gateway
  participant Ext as External Service / User
  participant F1 as HCS-1 File
  participant RT as Receipt Topic

  Agent->>Gateway: boundary action (channel, direction, payload)
  Gateway->>Gateway: capture action record · canonicalize
  alt pre-check fails
    Gateway-->>Agent: policy_rejected — control returned, not numbered, nothing released
  else pre-check passes, proving fails
    Gateway->>Gateway: assign sequence_no = n · proof generation fails
    Gateway-->>Agent: prover_unavailable — action held, NOT released, sequence_no retained, retry
  else pre-check passes, proof generated
    Gateway->>Gateway: assign sequence_no = n · build private witness · statement_hash binds sequence_range {n, n} · generate proof
    Gateway->>Ext: release action
    Ext-->>Gateway: result (captured as the inbound action)
    Gateway->>F1: store CBOR receipt (journal + proof)
    F1-->>Gateway: proof_ref = hcs://1/topicId
    Gateway->>RT: receipt_issued {journal (mode = real_time, sequence_range = {n, n}), proof_ref, vk_id}
    Gateway-->>Agent: result delivered
  end
```

### B3b. Per-session sequence — batch mode

`batch` (`0x01`, post-hoc): actions are pre-checked, numbered, and released as
they occur; one proof later covers the contiguous `sequence_no` range named by
the journal's `sequence_range`, which is bound into `statement_hash`. A proving
failure after release is a gateway defect: nothing is published for the range
and the gap shows up in the auditor's coverage check.

```mermaid
sequenceDiagram
  autonumber
  participant Agent
  participant Gateway
  participant Ext as External Service / User
  participant F1 as HCS-1 File
  participant RT as Receipt Topic

  loop each boundary action in the interval
    Agent->>Gateway: action
    Gateway->>Gateway: capture · canonicalize · plaintext pre-check
    alt pre-check fails
      Gateway-->>Agent: reject, not numbered, nothing released
    else pre-check passes
      Gateway->>Gateway: assign sequence_no = i from the host's session counter
      Gateway->>Ext: release action i
      Gateway->>Gateway: retain action record i as witness
    end
  end
  Note over Gateway: interval or session ends
  Gateway->>Gateway: one witness over records [from..to] · statement_hash binds sequence_range · one proof
  alt proving fails
    Gateway->>Gateway: gateway defect — publish nothing for the range, raise alert
  else proof ready
    Gateway->>F1: store CBOR receipt
    F1-->>Gateway: proof_ref
    Gateway->>RT: receipt_issued {journal (mode = batch, sequence_range = {from, to}), proof_ref, vk_id}
  end
```

### B3c. Recursive mode and the chain digest

`recursive` (`0x03`): per-action proofs are aggregated into a constant-size
cumulative receipt; each step extends a public chain digest. The journal carries
`chain_digest` and `prev_chain_digest` (REQUIRED in this mode). Each
`statement_hash` binds `prev_chain_digest`; `chain_digest` is then derived from
that `statement_hash`, so it is not itself in the preimage
([R-16](./ZKBC-Architecture-Review.md#r-16)). The verifier recomputes
`chain_digest` and checks that `prev_chain_digest` is empty at genesis or equals
the `chain_digest` of the preceding recursive receipt on the same topic and
session. Per-action proving is off the release path, as in `batch`. A receipt is published at the end of each window (which MAY be a
single step); its `sequence_range` names the steps folded in since the previous
receipt, so the per-receipt step count is public.

```mermaid
flowchart LR
  G0["genesis<br/>prev_chain_digest_0 = empty string"]
  S1["statement_hash_1"]
  C1["chain_digest_1 = H( LP(PROTOCOL_LABEL) ‖ LP(nfc(chain)) ‖ LP(prev_0) ‖ LP(statement_hash_1) )"]
  S2["statement_hash_2"]
  C2["chain_digest_2 = H( … ‖ LP(chain_digest_1) ‖ LP(statement_hash_2) )"]
  Sn["statement_hash_n"]
  Cn["chain_digest_n = H( … ‖ LP(chain_digest_n-1) ‖ LP(statement_hash_n) )"]
  Rn["Cumulative receipt at window end<br/>constant size · attests the whole sequence<br/>journal: mode = recursive, chain_digest = chain_digest_n, prev_chain_digest = chain_digest_n-1,<br/>sequence_range = steps folded in since the previous receipt"]

  G0 --> C1
  S1 --> C1
  C1 -->|"prev_chain_digest_2"| C2
  S2 --> C2
  C2 -.->|"…"| Cn
  Sn --> Cn
  Cn --> Rn
```

### B4. Canonicalization pipelines

[Canonicalization](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#canonicalization)
uses two deliberately different text forms: `fold` (NFKC + default case
folding + UTF-8) for output tokens matched against the forbidden set, and `nfc`
(NFC + UTF-8) for tool identifiers matched against the allowlist. The pinned
Unicode version, forms, and tokenizer are serialized as an RFC 8785 descriptor
and committed as `output.canonicalization`, so every verifier reproduces the
same public statement.

```mermaid
flowchart LR
  subgraph OutLane["Output (response) records — matching form"]
    direction LR
    O0["raw output text"] --> O1["fold: NFKC → default case fold → UTF-8"] --> O2["UAX 29 word segmentation"] --> O3["drop tokens that are all whitespace or punctuation"] --> O4["canonical multiset of token byte strings"]
    F0["forbidden set F"] --> F1["fold each element"] --> F2["sorted, deduplicated F"]
  end

  subgraph ToolLane["Tool and web records — identifier form"]
    direction LR
    T0["tool identifier · web scheme://host"] --> T1["nfc: NFC → UTF-8 · exact, case-sensitive"]
    A0["allowlist A · sensitive-key set K"] --> A1["nfc each element"]
    G0["tool arguments · web /query and /body"] --> G1["RFC 8785 JSON Canonicalization"] --> G2["keys addressed by RFC 6901 JSON Pointer paths"]
  end

  subgraph Desc["Canonicalization descriptor — RFC 8785 canonical JSON"]
    D0["unicode: pinned version<br/>identifier_form: nfc<br/>matching_form: nfkc+casefold<br/>tokenizer: uax29-words"]
    D1["output.canonicalization = commit( nfc(policy/canonicalization), descriptor )"]
    D0 --> D1
  end

  O4 -->|"non-membership test against"| F2
  T1 -->|"membership test against"| A1
  G2 -->|"sensitive key if path ∈ K"| A1
  D1 -.->|"REQUIRED in policy_commitments when family includes output"| OutLane
```

### B5. Commitment constructions

The hash constructions of
[Commitments and Identifiers](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#commitments-and-identifiers)
and [Notation and Primitives](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#notation-and-primitives).
Every variable-length field is length-prefixed (`LP(x) = uint64be(len(x)) ‖ x`)
and every commitment is domain-separated by `PROTOCOL_LABEL = nfc("ZKBC/v1")`
and a purpose tag. Merkle leaves and nodes carry `0x00` / `0x01` prefixes
(RFC 6962 §2.1).

```mermaid
flowchart TB
  subgraph Scalar["Scalar commitment"]
    SC["commit(tag, m) = H( LP(PROTOCOL_LABEL) ‖ LP(tag) ‖ LP(m) )"]
  end

  subgraph SetC["Set commitment — binary Merkle root"]
    direction TB
    E["elements e_1..e_n<br/>canonical form · ascending byte order · deduplicated"]
    L["leaf(tag, e) = H( byte(0x00) ‖ LP(PROTOCOL_LABEL) ‖ LP(tag) ‖ LP(e) )"]
    Pad["pad with leaf(tag, empty) to next power of two<br/>empty set commits to leaf(tag, empty)"]
    N["node(l, r) = H( byte(0x01) ‖ l ‖ r )<br/>fold pairwise left-to-right"]
    Root["32-byte root = set_commit(tag, set)"]
    E --> L --> Pad --> N --> Root
  end

  subgraph Ids["Identifiers"]
    direction TB
    PID["program_id = commit( nfc(program), program_descriptor )"]
    VK["vk_id = commit( nfc(vk), vk_bytes )  — REQUIRED<br/>auditor recomputes over fetched bytes, rejects on mismatch"]
    IDD["identity_digest = H( LP(PROTOCOL_LABEL) ‖ LP(nfc(identity)) ‖ LP(tenant_id) ‖ LP(user_id) )"]
    SID["session_id — opaque · RECOMMENDED 16 random bytes"]
    POL["policy_id — human-readable issuer-scoped label, non-secret"]
  end

  subgraph Tags["Tags used by the policy families"]
    direction TB
    T1["policy/output/forbidden → F"]
    T2["policy/tool/allowlist → A"]
    T3["policy/tool/sensitive-keys → K"]
    T4["policy/canonicalization → descriptor"]
    T5["policy/access → field-taxonomy descriptor"]
    T6["arg → sanitized argument value (hash form)"]
  end

  SC --> PID
  SC --> VK
  SC --> T4
  SC --> T5
  SC --> T6
  Root --> T1
  Root --> T2
  Root --> T3
```

### B6. Public statement binding

[Public Statement Binding](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#public-statement-binding):
the journal fields are serialized in the exact order shown, hashed, and the
result is both the journal's `statement_hash` and the proof's public input. Any
edit to a bound journal field changes the hash and breaks verification. Three
journal fields are *not* in the preimage — `issued_at` (advisory; consensus
timestamp is authoritative), `proof_system` (bound indirectly through
`vk_id → program_registered`), and `chain_digest` (derived from
`statement_hash`, so binding it would be circular) — see
[R-12](./ZKBC-Architecture-Review.md#r-12) and
[R-16](./ZKBC-Architecture-Review.md#r-16).

```mermaid
flowchart TB
  subgraph P["statement_preimage — exact order · each segment shows the journal fields it is built from"]
    direction TB
    p0["LP(PROTOCOL_LABEL) ‖ LP(nfc(statement))<br/>constants"]
    p1["LP(nfc(version)) ‖ LP(nfc(policy_id))<br/>← journal.version · journal.policy_id"]
    p2["LP(session_id) ‖ LP(program_id)<br/>← journal.session_id · journal.program_id"]
    p3["byte(mode) ‖ byte(family_mask) ‖ byte(verdict)<br/>← journal.mode (batch 0x01 · real_time 0x02 · recursive 0x03)<br/>← journal.family → mask (output 0x01 · tool 0x02 · access 0x04)<br/>← journal.verdict (non_compliant 0 reserved · compliant 1)"]
    p4["uint32be(count(commitments)) ‖ for each (key, value) sorted ascending by key: LP(nfc(key)) ‖ LP(value)<br/>← journal.policy_commitments"]
    p5["LP(identity_digest_or_empty)<br/>← journal.identity_digest, or empty"]
    p6["LP(prev_chain_digest_or_empty)<br/>← journal.prev_chain_digest, or empty"]
    p6b["LP(sequence_range)<br/>← uint64be(from) ‖ uint64be(to) of journal.sequence_range · every mode"]
    p7["LP(counts_canonical_json_or_empty)<br/>← RFC 8785 canonical JSON of journal.counts, or empty"]
    p0 --> p1 --> p2 --> p3 --> p4 --> p5 --> p6 --> p6b --> p7
  end

  Hh["statement_hash = H(statement_preimage)"]
  SH["journal.statement_hash<br/>= the proof's public input"]
  Cmp{"auditor recomputes from the journal<br/>and compares"}
  Ok["proceed to proof verification"]
  Rej["REJECT"]

  p7 --> Hh --> SH --> Cmp
  Cmp -->|"equal"| Ok
  Cmp -->|"mismatch"| Rej

  Unb["Journal fields NOT in the preimage<br/>issued_at — advisory, consensus timestamp is authoritative<br/>proof_system — fixed by vk_id → program_registered<br/>chain_digest — derived from prev_chain_digest and statement_hash, recomputed by the verifier"]
  Unb -.- P

  classDef unbound stroke-dasharray: 5 5;
  class Unb unbound;
```

### B7. Auditor verification decision flow

The ordered rules of
[Validation](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#validation) and the
walk-through in
[Example 3](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#example-3-auditor-verification-walk-through).
An *ignored* message is treated as absent, never as evidence of
non-compliance; a *rejected* `receipt_issued` fails as compliance evidence; the
coverage check runs over the accepted receipts of a session across every topic
in `receipt_topic_ids` and qualifies the session, not any single receipt.
Consensus timestamps, not `issued_at`, drive policy resolution.

```mermaid
flowchart TB
  Start["Discover receipt_topic_ids and registry ids from the agent's HCS-11 profile<br/>read a message on a receipt topic"]

  subgraph IG["Ignore gates — a failing message is treated as absent, never as evidence of non-compliance"]
    direction TB
    I1{"valid JSON with p and op?"}
    I2{"p equals the protocol id in the topic memo?"}
    I3{"op defined for this topic type?"}
    I4{"every REQUIRED field present and well-formed?"}
    N1["IGNORE"]
    N2["IGNORE"]
    N3["IGNORE"]
    N4["IGNORE"]
    I1 -->|"yes"| I2 -->|"yes"| I3 -->|"yes"| I4
    I1 -->|"no"| N1
    I2 -->|"no"| N2
    I3 -->|"no"| N3
    I4 -->|"no"| N4
  end

  subgraph RJ["Reject gates — a failing receipt_issued is rejected as compliance evidence"]
    direction TB
    R1{"journal.version implemented?"}
    R2{"recomputed statement_hash equals journal.statement_hash?"}
    R3{"proof_ref resolves to a valid HCS-1 file whose journal equals the inline journal?"}
    R4{"verdict = compliant?"}
    R5{"sequence_range has 1 ≤ from ≤ to, and from = to when mode = real_time?<br/>family non-empty, no duplicates, in order output · tool · access?"}
    R6{"vk_id has a program_registered entry with matching program_id, proof_system, and params?"}
    R7{"vk_ref resolves, and commit(vk, fetched bytes) equals vk_id?"}
    R8{"a policy_published for policy_id is in effect at the consensus timestamp<br/>(max(consensus_ts, effective_from) ≤ t_r, not revoked)<br/>and its policy_commitments and program_id match?"}
    R9{"family includes output ⇒ output.canonicalization present?"}
    R10{"verifier reproduces the pinned Unicode version, normalization forms, and tokenizer?"}
    R11{"proof verifies against the reconstructed public statement?"}
    R12{"mode = recursive ⇒ chain_digest recomputes, and prev_chain_digest is empty at genesis<br/>or equals chain_digest of the preceding recursive receipt, same topic and session?"}
    X1["REJECT"]
    X2["REJECT"]
    X3["REJECT"]
    X4["REJECT"]
    X5["REJECT"]
    X6["REJECT"]
    X7["REJECT"]
    X8["REJECT"]
    X9["REJECT"]
    X10["REJECT"]
    X11["REJECT"]
    X12["REJECT"]
    R1 -->|"yes"| R2 -->|"yes"| R3 -->|"yes"| R4 -->|"yes"| R5 -->|"yes"| R6 -->|"yes"| R7
    R7 -->|"yes"| R8 -->|"yes"| R9 -->|"yes"| R10 -->|"yes"| R11 -->|"yes"| R12
    R1 -->|"no"| X1
    R2 -->|"no"| X2
    R3 -->|"no"| X3
    R4 -->|"no"| X4
    R5 -->|"no"| X5
    R6 -->|"no"| X6
    R7 -->|"no"| X7
    R8 -->|"no"| X8
    R9 -->|"no"| X9
    R10 -->|"no"| X10
    R11 -->|"no"| X11
    R12 -->|"no"| X12
  end

  Acc["ACCEPT — action(s) proven compliant with policy_id<br/>the auditor learned nothing beyond the journal"]

  subgraph CV["Coverage check — per session_id, over every accepted receipt, in every mode, across all receipt_topic_ids"]
    direction TB
    C1{"ranges pairwise disjoint and union = 1..max(to)?"}
    C2["coverage holds: no released action of the session<br/>up to max(to) was omitted"]
    C3["coverage claim VOID for the session<br/>individual receipts remain accepted"]
    C1 -->|"yes"| C2
    C1 -->|"gap or overlap"| C3
  end

  Start --> I1
  I4 -->|"yes"| R1
  R12 -->|"yes"| Acc
  Acc -.->|"every mode"| C1
```

### B8. Policy lifecycle and timestamp-scoped resolution

[`policy_published`](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#policy_published)
and [`policy_revoked`](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#policy_revoked)
on the policy registry, and how an auditor resolves a receipt's `policy_id`
under the single in-effect rule
([R-09](./ZKBC-Architecture-Review.md#r-09)): only consensus time enters it,
and an asserted `effective_from` or `revoked_from` cannot reach back before its
own publication.

```mermaid
stateDiagram-v2
  [*] --> Defined : issuer commits policy sets, compiles program
  Defined --> Published : policy_published {policy_id, policy_commitments, program_id, program_registry_topic_id, effective_from}
  Published --> Published : newer policy_published for the same policy_id supersedes from max(consensus_ts, effective_from)
  Published --> Revoked : policy_revoked {policy_id, revoked_from}
  Revoked --> [*]

  note right of Published
    Resolution for a receipt R with consensus timestamp t_r:
    an entry e is in effect when max(consensus_ts(e), effective_from) ≤ t_r;
    pick the in-effect entry for R.policy_id with the greatest such value;
    reject R if none, or if its policy_commitments or program_id differ.
  end note

  note right of Revoked
    Receipts citing this policy_id with a consensus timestamp at or after
    max(consensus_ts(revocation), revoked_from) MUST be rejected.
    The label is retired; a later policy_published reusing it is ignored.
  end note
```

---

## Part C — Input / Output by Use Case and Configuration

Each family separates a **public statement** (what the auditor learns) from a
**private witness** (what stays inside the gateway). The families are
orthogonal and MAY be proved separately or as one conjunctive statement; the
journal's `family` array and the `family_mask` byte record which are covered.

### C1. Output family I/O

[Output Compliance](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#output-compliance):
every token of the canonical output multiset is a non-member of the forbidden
set `F`. This is a *non-membership* relation, so a normalization gap fails
open — see C6 for the consequence.

```mermaid
flowchart LR
  subgraph W["Private witness — never leaves the gateway"]
    direction TB
    w1["raw output text"]
    w2["forbidden set F — fold-normalized"]
    w3["Merkle non-membership openings for every token"]
  end

  subgraph Rl["Relation proved in zero knowledge"]
    r1["canonicalize output → token multiset M<br/>for every t in M: t is NOT a member of F"]
  end

  subgraph Pub["Public statement — in the journal"]
    direction TB
    c1["policy_commitments.output.forbidden = set_commit(policy/output/forbidden, F)"]
    c2["policy_commitments.output.canonicalization — REQUIRED"]
    c3["verdict: compliant or non_compliant"]
    c4["counts.output OPTIONAL<br/>token_count · distinct_token_count · hit_count<br/>MAY be padded or range-based"]
  end

  W --> Rl --> Pub
  classDef witness stroke-dasharray: 5 5;
  class w1,w2,w3 witness;
```

### C2. Tool-invocation family I/O

[Tool-Invocation Compliance](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#tool-invocation-compliance):
authorization (identifier ∈ allowlist `A`) plus argument sanitization (every
key in the sensitive-key set `K` crosses the boundary only in an approved form
from `{ mask, redact, hash }`). Both are *membership* relations and fail
closed.

```mermaid
flowchart LR
  subgraph W["Private witness — never leaves the gateway"]
    direction TB
    w1["tool identifier and arguments — RFC 8785 serialized"]
    w2["allowlist A — nfc-normalized"]
    w3["sensitive-key set K — nfc-normalized, RFC 6901 paths"]
    w4["sanitization outcomes per sensitive key"]
    w5["Merkle membership openings"]
  end

  subgraph Rl["Relations proved in zero knowledge"]
    direction TB
    r1["Authorization: nfc(tool id) is a member of A"]
    r2["Sanitization: for every argument key path in K,<br/>the value crosses the boundary only as<br/>mask → policy sentinel · redact → key omitted · hash → commit(nfc(arg), value)"]
  end

  subgraph Pub["Public statement — in the journal"]
    direction TB
    c1["policy_commitments.tool.allowlist = set_commit(policy/tool/allowlist, A)"]
    c2["policy_commitments.tool.sensitive-keys = set_commit(policy/tool/sensitive-keys, K)"]
    c3["verdict"]
    c4["counts.tool OPTIONAL<br/>invocation_count · argument_count · sensitive_argument_count"]
  end

  subgraph Out["What crosses the boundary to the external service"]
    o1["invocation with sensitive values masked, redacted, or hashed"]
  end

  W --> Rl --> Pub
  Rl --> Out
  classDef witness stroke-dasharray: 5 5;
  class w1,w2,w3,w4,w5 witness;
```

### C3. Access family I/O

[Access Compliance](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#access-compliance):
every observed tenant-context value equals the requesting `tenant_id`, every
observed user-context value equals the requesting `user_id` (from which context
consistency follows), and the decision is bound to the one-way
`identity_digest`. With HCS-14, `tenant_id` and `user_id` are `nfc(uaid)`.

```mermaid
flowchart LR
  subgraph W["Private witness — never leaves the gateway"]
    direction TB
    w1["tenant_id — e.g. nfc(uaid)"]
    w2["user_id — e.g. nfc(uaid)"]
    w3["observed context values across captured data accesses"]
  end

  subgraph Rl["Relations proved in zero knowledge"]
    direction TB
    r0["Identity match: every observed tenant-context value = tenant_id<br/>and every observed user-context value = user_id of the requesting principal"]
    r1["Context consistency (consequence): all tenant-context fields agree<br/>and all user-context fields agree"]
    r2["Private-identity binding: decision bound to<br/>identity_digest = H( LP(label) ‖ LP(nfc(identity)) ‖ LP(tenant_id) ‖ LP(user_id) )"]
  end

  subgraph Pub["Public statement — in the journal"]
    direction TB
    c1["identity_digest — REQUIRED when family includes access"]
    c2["policy_commitments.access = commit(nfc(policy/access), field-taxonomy descriptor)"]
    c3["verdict"]
    c4["counts.access OPTIONAL<br/>context_field_count"]
  end

  W --> Rl --> Pub
  classDef witness stroke-dasharray: 5 5;
  class w1,w2,w3 witness;
```

### C4. Receipt and journal structure

The [Public Compliance Journal](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#public-compliance-journal)
(sixteen fields; twelve REQUIRED, four conditional or optional) and the
[Compliance Receipt Wire Format](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#compliance-receipt-wire-format)
(deterministic CBOR, RFC 8949 §4.2; media type `application/zkbc-receipt+cbor`).
Invariants: `proof.system` MUST equal `journal.proof_system`;
`identity_digest` is REQUIRED iff `family` includes `access`; `chain_digest`
and `prev_chain_digest` are REQUIRED iff `mode = recursive`; `sequence_range`
is REQUIRED in every mode, with `from = to` in `real_time`; `family` is listed
in the order `output`, `tool`, `access`; `verdict` is always `compliant`
in this version (`non_compliant` is reserved); `output.canonicalization` MUST
be present iff `family` includes `output`.

```mermaid
classDiagram
  class Receipt {
    +version string = ZKBC/1.0
    +journal Journal
    +proof Proof
  }
  class Journal {
    +version string REQUIRED
    +session_id base64url or UUID REQUIRED
    +issued_at RFC3339 UTC REQUIRED
    +policy_id string REQUIRED
    +policy_commitments map~string,base64url32~ REQUIRED
    +program_id base64url32 REQUIRED
    +proof_system string REQUIRED
    +mode enum batch real_time recursive REQUIRED
    +family array of enum output tool access REQUIRED fixed order
    +verdict enum compliant non_compliant(reserved) REQUIRED
    +statement_hash base64url32 REQUIRED
    +counts Counts OPTIONAL
    +identity_digest base64url32 REQUIRED iff access
    +chain_digest base64url32 REQUIRED iff recursive
    +prev_chain_digest base64url32 or empty REQUIRED iff recursive
    +sequence_range SequenceRange REQUIRED
  }
  class SequenceRange {
    +from uint64
    +to uint64 1 ≤ from ≤ to · from = to in real_time
  }
  class Proof {
    +system string MUST equal journal.proof_system
    +params string OPTIONAL MUST equal program_registered.params
    +bytes base64url opaque proof
    +vk_id base64url32
  }
  class Counts {
    +output token_count distinct_token_count hit_count
    +tool invocation_count argument_count sensitive_argument_count
    +access context_field_count
  }
  class PolicyCommitments {
    +output.forbidden
    +output.canonicalization
    +tool.allowlist
    +tool.sensitive-keys
    +access
  }
  Receipt *-- Journal : journal
  Receipt *-- Proof : proof
  Journal o-- Counts : counts
  Journal o-- SequenceRange : sequence_range
  Journal o-- PolicyCommitments : policy_commitments
```

### C5. Operation envelopes

The four operations of the
[Operation Reference](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#operation-reference),
each a JSON message with `p = "hcs-xx"` and `op`, the topic type it is valid
on, and its transaction memo. The consensus timestamp is the authoritative
publication time of every operation.

```mermaid
classDiagram
  class receipt_issued {
    op enum 0 · topic type 0 · txn memo hcs-xx:op:0:0
    +p string hcs-xx
    +op string receipt_issued
    +account_id string gateway
    +journal Journal inline
    +proof_ref string HRL hcs://1/topicId
    +vk_id base64url32 MUST equal receipt.proof.vk_id
    +m string OPTIONAL memo
  }
  class policy_published {
    op enum 1 · topic type 1 · txn memo hcs-xx:op:1:1
    +p string hcs-xx
    +op string policy_published
    +account_id string issuer
    +policy_id string
    +policy_commitments map
    +program_id base64url32
    +program_registry_topic_id string
    +effective_from RFC3339 UTC
    +m string OPTIONAL
  }
  class policy_revoked {
    op enum 2 · topic type 1 · txn memo hcs-xx:op:2:1
    +p string hcs-xx
    +op string policy_revoked
    +account_id string issuer
    +policy_id string
    +revoked_from RFC3339 UTC
    +m string OPTIONAL
  }
  class program_registered {
    op enum 3 · topic type 2 · txn memo hcs-xx:op:3:2
    +p string hcs-xx
    +op string program_registered
    +account_id string issuer
    +program_id base64url32
    +vk_id base64url32 commits to bytes at vk_ref
    +proof_system string
    +params string OPTIONAL
    +vk_ref string HRL REQUIRED
    +m string OPTIONAL
  }
  class ReceiptTopic {
    type 0 · submit key gateway · no admin key
  }
  class PolicyRegistry {
    type 1 · submit key issuer
  }
  class ProgramRegistry {
    type 2 · submit key issuer
  }
  ReceiptTopic <.. receipt_issued : published by gateway
  PolicyRegistry <.. policy_published : published by issuer
  PolicyRegistry <.. policy_revoked : published by issuer
  ProgramRegistry <.. program_registered : published by issuer
  receipt_issued ..> program_registered : vk_id resolves to program_id
  receipt_issued ..> policy_published : policy_id resolves at consensus timestamp
  policy_published ..> ProgramRegistry : program_registry_topic_id
```

### C6. Normalization asymmetry: fail-closed vs fail-open

Why the draft uses two text forms
([Canonicalization](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#canonicalization)
rationale and
[Normalization and Confusable Text](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#6-normalization-and-confusable-text)),
with the draft's own `ssn` vectors. Homoglyphs across scripts are an
acknowledged residual risk: output compliance is best-effort against an
adversarial agent and sound only against an honest-but-imprecise one.

```mermaid
flowchart LR
  subgraph Tool["Tool allowlist — MEMBERSHIP relation — nfc"]
    direction TB
    t0["identifier as written"] --> t1{"nfc form ∈ A?"}
    t1 -->|"yes"| t2["authorized"]
    t1 -->|"no — including any normalization gap"| t3["rejected → FAIL CLOSED (safe)"]
    t4["an over-aggressive form would map distinct ids onto an allowlisted one → widens authorization"]
  end

  subgraph Outp["Forbidden set — NON-MEMBERSHIP relation — fold"]
    direction TB
    o0["token as written"] --> o1{"fold form ∈ F?"}
    o1 -->|"yes"| o2["pre-check rejects → policy_rejected"]
    o1 -->|"no — including any normalization gap"| o3["released → FAIL OPEN (unsafe)"]
    o4["hence the most aggressive form: NFKC + case fold"]
  end

  subgraph Vec["Test vectors with F = { ssn }"]
    direction TB
    v1["ssn → fold ssn → member → pre-check rejects"]
    v2["SSN → fold ssn → member → pre-check rejects"]
    v3["ｓｓｎ fullwidth → fold ssn → member → pre-check rejects"]
    v4["ѕѕn Cyrillic → fold ѕѕn → NOT member → compliant<br/>homoglyph: residual risk, NOT mitigated"]
    v5["Mitigation options: constrain output script or repertoire at the gateway,<br/>or apply UTS 39 confusable skeletons to tokens and F"]
  end
```

### C7. Proof-mode configuration matrix

The three [Proof Modes](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#proof-modes);
an implementation MUST support at least one and records the selected mode in
the journal.

| Mode | Byte | Coverage unit | Proved vs released | Extra journal fields | Extra verifier checks | Suited to |
|------|------|---------------|--------------------|----------------------|-----------------------|-----------|
| `batch` | `0x01` | many actions over a contiguous `sequence_no` range | released after pre-check; proved post-hoc | none | none | periodic audit, latency uncritical |
| `real_time` | `0x02` | one boundary action (`from = to`) | proved on the release path, before release; fail-closed | none | `from = to` | interactive use |
| `recursive` | `0x03` | cumulative sequence, constant-size receipt; one receipt per window | released after pre-check; per-action proofs aggregated step by step, off the release path | `chain_digest`, `prev_chain_digest` | chain-digest recurrence to the preceding receipt on the same topic and session | long-running sessions, compact evidence |

`sequence_range` is REQUIRED in every mode and the session coverage check
applies to every mode; a session MAY mix modes.

```mermaid
flowchart LR
  subgraph B["batch 0x01"]
    direction LR
    b1["a_from"] --- b2["a_from+1"] --- b3["…"] --- b4["a_to"]
    b5["one proof · one receipt<br/>sequence_range = [from, to]"]
    b4 --> b5
  end
  subgraph R["real_time 0x02"]
    direction LR
    r1["a_i"] --> r2["proof_i · receipt_i<br/>before release · fail-closed<br/>sequence_range = [i, i]"]
  end
  subgraph C["recursive 0x03"]
    direction LR
    c1["a_1 → proof_1"] --> c2["a_2 → proof_2 folds in proof_1"] --> c3["… → cumulative receipt at window end<br/>chain_digest extends each step · sequence_range = window"]
  end
```

---

## License

This document is licensed under Apache-2.0.
