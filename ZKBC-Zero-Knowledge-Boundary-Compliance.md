# ZKBC: Zero-Knowledge Boundary Compliance for Autonomous Agents

- **Category:** Open Specification (Standards Track)
- **Version:** 1.0 — Draft
- **Requirement keywords:** as defined in Section 2.1

## Status of This Memo

This document specifies an open, vendor-neutral architecture and conformance
requirements for verifiable, privacy-preserving compliance auditing of the
boundary actions of autonomous software agents. It is offered for review and
adoption by any implementer. It defines interfaces and obligations, not a
particular product; conforming implementations MAY be built on any proof system
that meets the requirements of Section 5. Distribution of this memo is
unlimited.

## Abstract

An autonomous agent is a software principal that plans, retrieves context,
invokes tools, and releases information on behalf of a user. Its privacy posture
is determined by the actions that cross the boundary between the agent and its
environment — released output, tool invocations, and data accesses — not by its
final text alone. This specification defines **Zero-Knowledge Boundary Compliance
(ZKBC)**: a mediation architecture in which a non-bypassable gateway captures and
canonicalizes each boundary action and emits a zero-knowledge proof that the
action satisfies an issuer-defined policy. The proof lets an auditor confirm
compliance without learning the underlying records and without proving full model
inference. This memo defines the roles, the mediation invariant, three policy
families, the proof-system requirements, the journal format, the proof modes, and
the security properties a conforming deployment MUST provide.

## 1. Introduction

Conventional agent audit forces a choice: expose the execution trace to the
auditor, or ask the auditor to trust the enforcement point. Runtime guardrails
enforce policy locally but produce no externally verifiable evidence. Plain logs
provide evidence but expose the very records that policy is meant to protect.

ZKBC resolves this tension by targeting the *boundary*. Compliance is evaluated
over the externally consequential actions an agent produces, and the evidence of
that evaluation is a zero-knowledge proof: verifiable and confidential at once.
The design goals are (a) **verifiability** — any authorized auditor can check
the outcome — and (b) **confidentiality** — checking reveals only the intended
public facts. A conforming implementation binds every proof to an
issuer-authenticated policy version so that auditors verify against a known,
public policy identity rather than the enforcer's word.

## 2. Terminology and Roles

### 2.1 Requirement Keywords

The keywords MUST, MUST NOT, REQUIRED, SHALL, SHOULD, SHOULD NOT, RECOMMENDED,
MAY, and OPTIONAL in this document are to be interpreted as normative
requirement levels in the conventional RFC sense.

### 2.2 Roles

- **User** — submits a request and receives a response. Assumed semi-honest.
- **Agent** — plans, retrieves context, invokes tools, and generates responses.
  It is the source of boundary actions and is treated as potentially malicious.
- **Resource Provider** — exposes external data or capabilities (data stores,
  tools, external services).
- **Policy Issuer** — defines compliance policies, distributes them to gateways,
  and authenticates the public policy identifiers auditors rely on.
- **Gateway** — the mediation component. It captures the action on a channel,
  canonicalizes the relevant records, evaluates the issued policy, and produces
  the compliance proof.
- **Auditor** — receives public compliance evidence and verifies that it
  matches the expected policy version and compliance relation.

## 3. Architecture

### 3.1 Complete Mediation

A conforming deployment MUST place a gateway on **every** channel that carries a
boundary action: the user channel (queries and responses), the data channel
(retrieval requests and returned records), and the tool/API channel (invocations
and results). Resource providers MUST reject direct, un-mediated connections
from the agent, so that an action reaches an external party only through a
gateway. This *complete mediation* invariant is a precondition for the coverage
guarantee of Section 8; it is a deployment property and cannot be established by
the proof system alone.

### 3.2 Gateway Processing Model

Each gateway MUST evaluate the applicable compliance relation in two phases:

1. **Plaintext pre-check.** The gateway canonicalizes the action and evaluates
   the issued policy in the clear. If the action does not satisfy the relation,
   the gateway MUST reject it and return control to the agent (which MAY
   regenerate the output, revise the tool call, or reissue the access request).
   A non-satisfying action MUST NOT be released.
2. **Proof generation.** Only after the pre-check succeeds does the gateway
   construct the private witness and generate the proof that binds the released
   action to the issued policy version and the session identity.

Canonicalization (normalization of records into the representation the policy is
evaluated over) MUST be deterministic: identical actions MUST yield identical
canonical forms, so that the public statement is reproducible by any verifier.

## 4. Compliance Policy Families

A conforming implementation MUST support the three policy families below. The
families are orthogonal: each is defined independently and MAY be proved
separately or combined into a single conjunctive statement. Every family
separates a **public statement** (what the auditor learns) from a **private
witness** (what remains hidden). Policies are referenced publicly by commitment
to a version, so that policy *content* stays confidential while policy *identity*
is verifiable.

### 4.1 Output Compliance

Constrains information released to the user or a downstream consumer. The policy
is a forbidden-content set; the gateway canonicalizes released output into a
normalized token representation and proves that no forbidden item appears. The
public statement MUST include the policy commitment, the verdict, and MAY
include aggregate counts (e.g., number of distinct tokens, number of hits). The
raw output and the forbidden set MUST remain in the private witness.

### 4.2 Tool-Invocation Compliance

Constrains external actions. It combines two relations:

- **Authorization** — every invoked tool identifier MUST be a member of an
  issuer-defined allowlist.
- **Argument sanitization** — every argument whose key is designated sensitive
  MUST cross the boundary only in an issuer-approved masked, redacted, or
  otherwise sanitized form.

The public statement MUST include commitments to the allowlist and the
sensitive-key set, the verdict, and MAY include invocation and argument counts.
Tool arguments, the allowlist, and the sensitive-key set MUST remain private.

### 4.3 Access Compliance

Constrains which data context an agent may use to answer a user. It combines:

- **Context consistency** — all observed tenant-context fields MUST agree and
  all observed user-context fields MUST agree across the captured access
  context (authorization claims, request scope, data filters, retrieved-object
  metadata, response context).
- **Private-identity binding** — the access decision MUST be bound to a public
  identity digest computed by a domain-separated, length-encoded commitment over
  the tenant and user identities.

The public statement MUST include the identity digest and the verdict. Tenant
and user identifiers MUST remain private.

## 5. Proof-System Requirements

The compliance relation MUST be realized by a non-interactive zero-knowledge
argument. A conforming proof system MUST provide:

- **Completeness** — an honestly captured, satisfying action yields an accepting
  proof.
- **Knowledge soundness** — an accepting proof implies knowledge of a private
  witness satisfying the committed compliance relation; a party MUST NOT be able
  to produce an accepting proof for a non-satisfying action, nor to make a
  non-compliant action appear compliant by altering the public journal or
  fabricating proof bytes.
- **Zero knowledge** — verification MUST reveal nothing about the private witness
  beyond the public statement.
- **Succinct verification** — verification cost and evidence size SHOULD be small
  and SHOULD NOT grow with the length of the captured action or session.

The relation binds a public statement (policy commitments, mode, session
identifier, and compliance-program identifier) to a private witness (the captured
records and the confidential policy content). Implementations are RECOMMENDED to
express the relation as an ordinary program compiled to a general-purpose
zero-knowledge virtual machine, so that policies evolve as software rather than as
hand-built circuits. Because compliance evidence may remain relevant long after it
is produced, and because recognized standards bodies have urged migration to
post-quantum cryptography, a conforming proof system SHOULD rest on transparent,
hash-based assumptions that stay sound against quantum-capable adversaries.
Pairing-based succinct proofs MAY be used where their assumptions are acceptable,
but they are OPTIONAL and are NOT post-quantum. Non-interactivity SHOULD be
obtained by transforming a public-coin protocol in the random-oracle model.

## 6. Public Compliance Journal

Every proof MUST be accompanied by a **compliance journal**: a canonical, textual
record that is human-readable, machine-parseable, and carries only the public
statement — nothing more. At minimum:

```
session_id        : opaque session identifier
policy_version     : issuer-authenticated policy identifier / commitment(s)
mode               : batch | real-time | recursive
program_id         : identifier of the compliance program evaluated
verdict            : compliant | non-compliant
counts             : OPTIONAL aggregate metrics (token, invocation, argument)
identity_digest    : OPTIONAL access-compliance identity commitment
chain_digest       : OPTIONAL cumulative digest (recursive mode)
```

Raw records — response text, tool arguments, retrieved data, confidential policy
sets, and tenant or user identifiers — MUST NOT appear in the journal.
Deployments requiring a smaller public footprint MAY replace exact counts with
padded or range-based values without changing the relation.

## 7. Proof Modes

A conforming implementation MUST support at least one of the following modes and
MUST record the selected mode in the journal.

- **Batch (post-hoc).** One proof covers many records accumulated over a session
  or interval. Suited to periodic audit where latency is uncritical.
- **Real-time.** One proof covers a single boundary action and is generated on
  the release path, before the action is released. Prover latency SHOULD be low
  enough for interactive use.
- **Recursive.** Per-action proofs are aggregated into a constant-size cumulative
  receipt that attests to the whole sequence, extending a public chain digest at
  each step. Suited to compact evidence for long-running sessions. To conceal the
  exact number of aggregated steps, deployments MAY pad to a fixed window.

## 8. Security Considerations

**Threat model.** The agent is potentially malicious and MAY attempt to leak
information or to answer one user's request with another user's data; the
framework therefore MUST NOT rely on the agent to select which actions are
audited or to self-report honestly. The user is semi-honest. The gateway is
semi-honest in operation but adversarial with respect to proof forgery, and MUST
be non-bypassable. Resource providers, the policy issuer, and auditors are
honest-but-curious. Security rests on the soundness and zero-knowledge of the
proof system and on the collision resistance of the commitment hash.

A conforming deployment MUST provide:

- **Completeness** — if the gateways capture the relevant actions, canonicalize
  them correctly, and the records satisfy the issued policy, an auditor accepts
  the resulting evidence.
- **Knowledge soundness** — a malicious agent or gateway cannot convince an
  auditor that a non-compliant action was compliant without breaking the proof
  system or finding a hash collision.
- **Boundary-record privacy** — the auditor learns only the intentional public
  outputs of Section 6; raw records are never disclosed.
- **Mediated audit coverage** — because complete mediation (Section 3.1) routes
  every boundary action through a gateway, every privacy-relevant action is
  captured into the audit evidence. This property is supplied by deployment, not
  by the proof alone, and is void if any un-mediated channel exists.

## 9. Deployment Profiles (Informative)

- **Local** — a gateway beside a personal assistant mediates local files,
  memory, browser, and network actions on the user's device.
- **Enterprise** — gateways sit in front of tenant-scoped data stores, internal
  tools, and external connectors, checking actions against organizational policy
  before they reach protected resources.
- **Platform** — gateways are integrated into the agent runtime, exposing
  verification artifacts to customers, auditors, or regulators without revealing
  the underlying records.

## 10. Extensibility

Future versions MAY strengthen commitments with domain separation, per-issuer
salts, and keyed hashing to resist low-entropy guessing of committed values.
The policy language MAY be extended toward nested argument schemas, per-tool
constraints, purpose limitation, and semantic policies proved through committed
auxiliary classifiers. Extensions MUST preserve the public/private split of
Section 4 and the journal minimality of Section 6.

## 11. Conformance

An implementation conforms to this specification if it (1) enforces complete
mediation on all boundary channels; (2) evaluates the gateway processing model
of Section 3.2 with deterministic canonicalization; (3) supports the three
policy families of Section 4 with the mandated public/private split; (4) uses a
proof system meeting Section 5; (5) emits journals conforming to Section 6; (6)
supports at least one proof mode; and (7) provides the four security properties
of Section 8.

## 12. References (Informative)

1. Zero-knowledge proofs and arguments of knowledge.
2. Binding and hiding commitment schemes.
3. General-purpose zero-knowledge virtual machines.
4. Transparent, hash-based succinct non-interactive arguments of knowledge.
5. Post-quantum cryptography migration guidance from recognized standards bodies.
