---
title: "HCS-XX — ZKBC Architecture Review"
description: "Review findings against the Zero-Knowledge Boundary Compliance draft v1.0: normative inconsistencies, under-specified relations, and unverifiable guarantees, each with a spec location and a proposed resolution."
sidebar_position: 999
---

# HCS-XX: ZKBC Architecture Review (Companion)

### Status: Review of Draft v1.0 (2026-08-27)

Scope: the full text of
[HCS-XX Zero-Knowledge Boundary Compliance](./ZKBC-Zero-Knowledge-Boundary-Compliance.md)
at commit `c7c397e`. Line references are to that revision. The companion
[Architecture Diagrams](./ZKBC-Architecture-Diagrams.md) were drawn from the
same text; several findings surfaced while drawing them, and each such finding
names the diagram that exposes it.

All findings have since been resolved in the draft (revisions following
`c7c397e`). The **Status** column below and the *Resolution applied* note under
each finding record what changed and where the applied fix departs from the
proposal. R-15 and R-16 were found while applying the earlier resolutions —
R-15 while specifying fail-closed `real_time` proving, R-16 while writing a
recursive-mode test vector — and are recorded here with their fixes. Two
resolutions below are superseded in part by R-15: `sequence_range` is now
REQUIRED in every mode, not only `batch` and `recursive`.

Severity scale:

- **High** — a guarantee the draft states (coverage, soundness, privacy) is not
  achievable or not verifiable as written.
- **Medium** — a normative inconsistency between sections, or a relation whose
  stated form does not enforce what the surrounding prose claims.
- **Low** — clarity, hygiene, or an explicit statement that would prevent
  implementer divergence.

## Summary

| ID | Severity | Status | Area | One-line finding |
|----|----------|--------|------|------------------|
| [R-01](#r-01) | High | Resolved | Proof modes / validation | Batch and recursive coverage require a contiguous `sequence_no` range, but no journal or statement field carries the range bounds. |
| [R-02](#r-02) | High | Resolved | Multi-gateway sessions | `sequence_no` is assigned per gateway; a session spans several gateways and receipt topics, so cross-channel coverage of a session is never attested. |
| [R-03](#r-03) | Medium | Resolved | Real-time mode | Proof Modes says prove-then-release; Workflow Step 3 says release-then-prove. |
| [R-04](#r-04) | Medium | Resolved | Channels | `web` is in the `channel` enum and the Local profile but absent from Complete Mediation, and no family governs it. |
| [R-05](#r-05) | Medium | Resolved | Access family | The relation proves context consistency and binding, not that the observed context matches the requesting identities. |
| [R-06](#r-06) | Medium | Resolved | HCS-19 integration | Referencing a receipt by `#<sequence_no>` would publish private-witness material. |
| [R-07](#r-07) | Medium | Resolved | Threat model | Motivation promises TEE/TPM attestation of the gateway; nothing normative carries or verifies one. |
| [R-08](#r-08) | Low–Medium | Resolved | Discovery | The program registry is discoverable only through an HCS-11 profile, which is SHOULD-level and absent in the Local profile. |
| [R-09](#r-09) | Low | Resolved | Policy time windows | Revocation mixes `issued_at` with consensus time; `effective_from` is published but unused by the resolution rule. |
| [R-10](#r-10) | Low | Resolved | Validation | `params` is not compared between the receipt and the `program_registered` entry. |
| [R-11](#r-11) | Low | Resolved | Journal encoding | `family` array order is unspecified, yet journals are compared byte-for-byte after RFC 8785. |
| [R-12](#r-12) | Low | Resolved | Statement binding | `issued_at` and `proof_system` are unbound journal fields; state this explicitly. |
| [R-13](#r-13) | Medium | Resolved | Verdict semantics | A conforming gateway can never publish `verdict = non_compliant`, leaving the enum and the batch case under-defined. |
| [R-14](#r-14) | Low | Resolved | Recursive mode | Publication cadence (every step vs. window end) is unspecified, yet the chain-link rule assumes preceding receipts exist on-topic. |
| [R-15](#r-15) | High | Resolved | Coverage / real-time mode | `real_time` receipts carry no `sequence_range` but consume numbers from the shared session counter, so mixed-mode sessions can never tile and `real_time` sessions have no coverage claim. |
| [R-16](#r-16) | High | Resolved | Statement binding / recursive mode | `statement_preimage` binds `chain_digest`, but `chain_digest` is computed from `statement_hash`: the definition is circular and recursive mode cannot be implemented as written. |

One item outside the numbered findings was fixed alongside them: the
Validation reject list did not state the `vk_ref` self-authentication check
that Example 3 and diagram B7 both perform. The draft now makes
`vk_id = commit(nfc("vk"), vk_bytes)` and `vk_ref` REQUIRED, rejects on
mismatch, and computes the `vk_id` test vector over example key bytes rather
than over a descriptor string.

---

## Findings

### R-01

**Severity:** High
**Location:** [Validation](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#validation) L827–828;
[Security §2 Omission and Coverage Gaps](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#2-omission-and-coverage-gaps) L1071–1073;
[Public Compliance Journal](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#public-compliance-journal) L502–518;
[Public Statement Binding](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#public-statement-binding) L436–445.
**Diagram:** B3b, B6, C7.

**Problem.** Validation says: "For batch and recursive modes, the attested
`sequence_no` range MUST be contiguous; a gap voids the coverage claim for that
range." Security §2 relies on "`sequence_no` monotonicity plus contiguous-range
attestation." But the journal has no field for the range, `statement_preimage`
binds no range, and `counts` are optional, family-scoped, and may be padded.
The only witness-side quantity is `sequence_no`, which MUST NOT appear in any
journal. A verifier therefore has nothing to check contiguity *against*, and
two batch receipts for the same session cannot be shown to abut.

**Why it matters.** "Mediated audit coverage" is one of the three MUST-level
security properties. As written it is a property of the prover's private
witness with no public handle, so an auditor cannot distinguish "every action
in the interval was attested" from "the gateway chose a convenient subset and
attested that."

**Proposed resolution.**

1. Add to the journal `sequence_range: { "from": uint64, "to": uint64 }`,
   REQUIRED when `mode ∈ { batch, recursive }`, absent otherwise.
2. Bind it into `statement_preimage` after `byte(verdict)`:
   `|| uint64be(from) || uint64be(to)` (fixed width, so no `LP`), or `LP("")`
   equivalent when absent.
3. Require the relation to prove that the witness action records carry
   exactly the sequence numbers `from..to` with no gaps.
4. For recursive mode add the continuity rule `from_{i+1} = to_i + 1` to the
   chain-link check in Validation.
5. Note in Privacy Considerations that the range reveals an action count per
   receipt; deployments MAY pad ranges the same way they MAY pad `counts`.

**Resolution applied.** `sequence_range` added to the journal (REQUIRED for
batch and recursive, MUST be absent otherwise) and bound into
`statement_preimage` — as `LP(sequence_range_or_empty)` with
`uint64be(from) || uint64be(to)`, placed after `prev_chain_digest` alongside
the other conditional fields, rather than as fixed-width bytes after
`byte(verdict)`, so the universal length-prefix discipline holds. The relation
must prove the witness carries exactly `from..to`. Instead of the per-chain
`from_{i+1} = to_i + 1` rule, Validation defines a session-level **coverage
check**: the ranges of all accepted receipts for a `session_id`, across every
topic in `receipt_topic_ids`, must be pairwise disjoint and tile `1..max(to)`;
this handles interleaved topics (R-02) and keeps chain linkage separate from
coverage. Ranges cannot be padded without breaking tiling, so the draft states
the per-receipt count disclosure honestly and drops the "pad to conceal the
step count" claim from Proof Modes and Privacy Considerations. Test vectors
were regenerated (`resources/zkbc_vectors.py`) and a batch vector with range
`1..3` was added.

### R-02

**Severity:** High
**Location:** [Boundary Action Capture](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#boundary-action-capture) L241, L248–250;
[Topic Types](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#topic-types-and-enums) L605;
[Implementation Workflow](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#implementation-workflow) Step 1.2 L892–894;
[HCS-11 Profile Integration](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#hcs-11-profile-integration) L847–852;
[Validation](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#validation) L824–825.
**Diagram:** A1, A3, A5.

**Problem.** `sequence_no` is "a monotonic per-session counter, assigned at
capture," and a deployment MUST have a gateway on each of the user, data, tool
(and web) channels. Each gateway creates *its own* receipt topic with *its own*
submit key. Nothing says the counter is shared across gateways, so a session's
actions on different channels carry overlapping sequence numbers on different
topics. The recursive-mode chain rule links to "the preceding receipt on the
same topic and session," which makes coverage per-topic at best. Separately, the
HCS-11 `zkbc` block advertises a single `receipt_topic_id`, which cannot name
four per-gateway topics.

**Why it matters.** The coverage claim in Security §2 is stated per session
("no silent omission"). With per-gateway counters the strongest verifiable
statement is "no omission on this channel's topic," and an auditor cannot tell
whether a channel's topic was omitted from the profile altogether.

**Proposed resolution.** Choose one and state it normatively:

- **(a) Recommended.** The host (which is already trusted to enforce the
  boundary) supplies a session-scoped monotonic counter shared by every
  gateway; contiguity is checked per session across all receipt topics named in
  the profile. Change `receipt_topic_id` to `receipt_topic_ids` (array) in the
  `zkbc` block, or allow one receipt topic shared by all gateways of a host
  (each gateway holding the submit key).
- **(b)** Keep per-gateway counters, add `channel` to the journal and to
  `statement_preimage`, and define contiguity per `(session_id, channel)`. Then
  soften Security §2 to say per-channel coverage.

**Resolution applied.** Option (a). The host maintains one counter per session
starting at `1`, shared by every gateway; the `zkbc` block carries
`receipt_topic_ids` (array), gateways MAY share one receipt topic or operate
separate ones, and the coverage check of R-01 spans every listed topic.
Security §3 notes that a topic left out of the profile now appears as a
coverage gap.

### R-03

**Severity:** Medium
**Location:** [Proof Modes](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#proof-modes) L574–576 (real-time);
[Gateway Processing Model](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#gateway-processing-model) L261–263;
[Implementation Workflow](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#implementation-workflow) Step 3.3 L909–910.
**Diagram:** B2, B3a.

**Problem.** Real-time mode: "generated on the release path, *before* the
action is released." Step 3.3: "On success, *release the action, generate the
proof*, assemble the receipt…". The Gateway Processing Model orders pre-check
before proof generation but says nothing about release. An implementer
following Step 3 in real-time mode would release before proving, which is the
opposite of what the mode promises.

**Proposed resolution.** Add a sentence to the Gateway Processing Model:
"Release ordering is mode-dependent: in `real_time` the proof MUST be generated
before release; in `batch` and `recursive` the action MAY be released
immediately after the pre-check and proved later." Rewrite Step 3.3 to match,
and note that in every mode the pre-check alone gates release — the proof never
changes the release decision, only the evidence.

**Resolution applied.** As proposed: the Gateway Processing Model states the
mode-dependent ordering and Workflow Step 3.3 is split by mode.

### R-04

**Severity:** Medium
**Location:** action-record `channel` enum L242; [Complete Mediation](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#complete-mediation) L219–222;
`family_mask` L456–457; [Deployment Profiles](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#deployment-profiles-informative) L992–994.
**Diagram:** A3.

**Problem.** The `channel` enum is `{ user, data, tool, web }` and the Local
profile mediates "browser and network actions," but Complete Mediation
enumerates only "the user channel, the data channel, and the tool/API channel."
None of the three policy families names the web channel, so it is unclear
which relation a web request must satisfy, or whether the enum value is
reserved.

**Proposed resolution.** Add the web channel to the Complete Mediation list and
state that web actions are evaluated under the tool family, with the request
target (scheme + host, `nfc`-normalized) as the tool identifier and the
request body/query as arguments — or remove `web` from the enum and fold web
egress into `tool`. Either way, `family_mask` needs no change.

**Resolution applied.** `web` kept. Complete Mediation lists the web channel;
Tool-Invocation Compliance evaluates a web request under the tool family with
`scheme://host` (RFC 3986 case normalization, then `nfc`) as the identifier and
`/query` and `/body` members as the arguments. Inbound web responses are
captured and numbered for coverage but unconstrained in v1.

### R-05

**Severity:** Medium
**Location:** [Access Compliance](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#access-compliance) L413–424.
**Diagram:** C3.

**Problem.** The access relation is (i) all observed tenant-context fields
agree and all observed user-context fields agree, and (ii) the decision is
bound to `identity_digest`. Neither clause says the observed tenant/user
context *equals* the identities from which `identity_digest` was computed. A
gateway that observed a consistent but wrong tenant (every record from tenant
B while serving user A of tenant A) satisfies the relation as written and
receives a `compliant` verdict. The Motivation and threat model make
cross-tenant answering the canonical access failure the family is meant to
catch.

**Proposed resolution.** Add a third clause: "**Identity match** — every
observed tenant-context value MUST equal `tenant_id`, and every observed
user-context value MUST equal `user_id`, where `(tenant_id, user_id)` are the
requesting principal's identifiers bound in `identity_digest`." Clause (i) then
follows and can be kept as a stated consequence.

**Resolution applied.** As proposed; the access-policy descriptor is also
named as the thing that fixes which observed fields are tenant- and
user-context and the form they are compared in.

### R-06

**Severity:** Medium
**Location:** [HCS-19 Privacy Compliance Integration](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#hcs-19-privacy-compliance-integration) L871–873;
[Boundary Action Capture](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#boundary-action-capture) L247–248.
**Diagram:** A6.

**Problem.** An HCS-19 audit entry "MAY reference the ZKBC evidence … by HRL
(`hcs://xx/0.0.600001`, optionally with a `#<sequence_no>` fragment for a
specific receipt)". `sequence_no` is a field of the action record, and "action
records and every field within them are private-witness material and MUST NOT
appear in any journal, receipt, or HCS message." Publishing it in an HCS-19
record contradicts that rule, and the value is not even present in the receipt
to be referenced.

**Proposed resolution.** Reference receipts by the receipt topic's HCS message
sequence number (or consensus timestamp), and rename the fragment to avoid the
collision: `hcs://xx/<receiptTopicId>#<messageSequenceNumber>`. Add a sentence
that the action-record `sequence_no` and the topic message sequence number are
unrelated.

**Resolution applied.** As proposed.

### R-07

**Severity:** Medium
**Location:** [Motivation](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#motivation) L98–99, L107–111;
[Security Considerations](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#security-considerations) threat model L1028–1031.
**Diagram:** A2.

**Problem.** Motivation says non-bypassable enforcement "is achievable through
a trusted hardware environment, attestation of the software version via a TEE
or a TPM," and recommends users run the gateway on their own hardware. The
normative text then simply trusts the host and says mediation "is verified by
deployment audit, not by the proof system." No field anywhere — journal,
receipt, `program_registered`, the HCS-11 `zkbc` block — carries a gateway
software identity or an attestation quote, so an auditor has no way to act on
the Motivation's promise.

**Proposed resolution.** Either (a) add an OPTIONAL `attestation_ref` (HRL to
an HCS-1 file holding a TEE/TPM quote plus the measured gateway software
identity) to the `zkbc` profile block and, optionally, an
`attestation_digest` to `receipt_issued`, with a validation rule that says how
an auditor uses it; or (b) reword Motivation to say hardware attestation of
the gateway is out of scope for v1 and left to deployment audit. Option (b)
is the smaller change and keeps the draft honest; option (a) is the feature
the Motivation is advertising.

**Resolution applied.** Option (b). Motivation now says the invariant is
verified by deployment audit and hardware attestation is out of scope for this
version; Backwards Compatibility anticipates an attestation reference in the
`zkbc` block.

### R-08

**Severity:** Low–Medium
**Location:** receipt-topic memo L626–631; [HCS-11 Profile Integration](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#hcs-11-profile-integration) L836–838, L847–852;
[Deployment Profiles](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#deployment-profiles-informative) L992–995.
**Diagram:** A5.

**Problem.** The receipt-topic memo's `param` names the governing policy
registry, and `policy_published` carries `program_id`, but nothing on-graph
points from a receipt stream (or a policy entry) to the *program registry*
where `vk_id → program_id` is bound. The only path is the HCS-11 profile,
which is SHOULD-level and which a Local deployment may not publish at all. An
auditor holding only a receipt topic id cannot complete Validation.

**Proposed resolution.** Add `program_registry_topic_id` as a REQUIRED field
of `policy_published` (the issuer operates both registries, so it always knows
the id), or extend the receipt-topic memo to
`hcs-xx:0:86400:0:<policyRegistryTopicId>:<programRegistryTopicId>`. The first
option keeps the memo grammar shared with HCS-2/HCS-10 unchanged.

**Resolution applied.** First option: `program_registry_topic_id` is a REQUIRED
field of `policy_published`.

### R-09

**Severity:** Low
**Location:** [`policy_revoked`](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#policy_revoked) L740–742;
[`policy_published`](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#policy_published) L706–709, L719;
[Security §5 Timestamp Trust](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#5-timestamp-trust) L1114–1116.
**Diagram:** B8.

**Problem.** `policy_revoked` rejects receipts "with an `issued_at` (and
consensus timestamp) after `revoked_from`," mixing the prover-asserted and the
authoritative clock that §5 says to prefer. `policy_published` carries
`effective_from`, but the resolution rule selects "the most recent
`policy_published` whose *consensus timestamp* is at or before the receipt's,"
so `effective_from` has no normative effect — an issuer cannot pre-publish a
policy that takes effect later.

**Proposed resolution.** Define one rule: a `policy_published` entry is *in
effect* for a receipt with consensus timestamp `t_r` when
`max(consensus_ts(entry), effective_from) ≤ t_r` and no `policy_revoked` for
the same `policy_id` has `revoked_from ≤ t_r`. Drop the `issued_at` mention
from `policy_revoked`.

**Resolution applied.** As proposed, with one strengthening: revocation uses
`max(consensus_ts(revocation), revoked_from)` as well, so neither operation can
reach back before its own publication. `policy_published` defines the single
in-effect rule; `policy_revoked`, Validation, and Security §4–§5 refer to it.
The resolved entry's `program_id` is now compared along with its commitments, a
revoked `policy_id` is retired for good, and Validation's use of the consensus
timestamp is raised from SHOULD to MUST.

### R-10

**Severity:** Low
**Location:** [Validation](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#validation) L812–814;
receipt `proof.params` L548; [`program_registered`](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#program_registered) L768.
**Diagram:** B7, C5.

**Problem.** Validation compares the registry entry's `program_id` and
`proof_system` with the journal but not `params`. Two `program_registered`
entries for the same `program_id` and `proof_system` with different parameter
sets (say, different security levels) are interchangeable, and a receipt's
`proof.params` is never checked against anything.

**Proposed resolution.** Add to the reject list: "the receipt's `proof.params`
differs from the `program_registered` entry's `params` when either is
present." Since `vk_id` already commits to the verifying key, this is
belt-and-braces, but it closes an obvious question for implementers.

**Resolution applied.** As proposed; one present and the other absent counts
as a difference. `program_registered` also states that a `vk_id` is registered
at most once and consumers use the earliest entry.

### R-11

**Severity:** Low
**Location:** journal `family` L512; [`receipt_issued`](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#receipt_issued) L689–690;
`family_mask` L456–457.
**Diagram:** C4.

**Problem.** The inline journal must equal the stored receipt's journal
"byte-identical after RFC 8785 canonicalization of both." RFC 8785 sorts
object keys but preserves array order, and `family` is an array whose order
is unspecified. Two honest implementations could serialize
`["output","tool"]` and `["tool","output"]` and fail the byte-equality check;
`family_mask` derivation is unaffected but the wire check is.

**Proposed resolution.** "The `family` array MUST list families in ascending
enum order (`output`, `tool`, `access`) without duplicates."

**Resolution applied.** As proposed, in the journal table, with a Validation
reject rule for an empty, duplicated, or mis-ordered array.

### R-12

**Severity:** Low
**Location:** [Public Statement Binding](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#public-statement-binding) L436–445.
**Diagram:** B6.

**Problem.** Of the fifteen journal fields, `issued_at` and `proof_system` are
not in `statement_preimage`. Both omissions are defensible — `issued_at` is
advisory (§5), and `proof_system` is bound through `vk_id → program_registered`
— but the draft does not say so, and a reader auditing the binding list will
flag them.

**Proposed resolution.** Add after the preimage: "`issued_at` and
`proof_system` are deliberately unbound: the consensus timestamp supersedes the
former, and the latter is fixed by the `program_registered` entry that `vk_id`
resolves to."

**Resolution applied.** As proposed. After R-16, `chain_digest` is a third
field outside the preimage, and the draft says why.

### R-13

**Severity:** Medium
**Location:** [Gateway Processing Model](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#gateway-processing-model) L256–260;
[Implementation Workflow](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#implementation-workflow) Step 3.2 L907–908;
journal `verdict` L513; test vector L1282–1283.
**Diagram:** B2, B7.

**Problem.** The pre-check MUST reject a non-satisfying action, "nothing is
released or published," and proof generation happens only after the pre-check
succeeds. A conforming gateway therefore never generates a proof whose verdict
is `non_compliant`, so the enum value is unreachable on the happy path. The
draft never says whether a gateway MAY publish a `non_compliant` receipt (for
example, to attest that it *blocked* something), and in batch mode it is
unclear what happens if the batch relation fails post-hoc for an action that
passed its individual pre-check — the action has already been released.

**Why it matters.** Auditors reading a receipt topic will see only `compliant`
verdicts and cannot distinguish "the gateway blocked N actions" from "N actions
never happened." Batch-mode semantics on post-hoc failure are undefined.

**Proposed resolution.** State explicitly one of: (a) `non_compliant` receipts
are permitted and attest a *blocked* action (the action record is still the
witness; nothing was released), which gives auditors a count of enforcement
events; or (b) `non_compliant` is reserved and MUST NOT be published by a
conforming gateway, in which case say why the enum exists (future extension).
For batch mode, state that the batch relation is the conjunction of the
per-action relations already pre-checked, so post-hoc failure indicates a
gateway defect and the gateway MUST NOT publish the batch.

**Resolution applied.** Option (b). `non_compliant` is reserved; a v1 gateway
MUST NOT publish it and verifiers reject it. To keep ranges free of unreleased
actions, `sequence_no` is now assigned when the pre-check passes (immediately
before release) rather than at capture, so a rejected action leaves no public
trace. Batch post-hoc failure is a gateway defect: publish nothing for the
range, raise an alert; the gap is visible through the coverage check.

### R-14

**Severity:** Low
**Location:** [Proof Modes](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#proof-modes) L577–589;
[Validation](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#validation) L824–825.
**Diagram:** B3c.

**Problem.** Recursive mode "aggregates per-action proofs into a constant-size
cumulative receipt," and the validation rule links `prev_chain_digest` "to the
preceding receipt on the same topic and session." Whether every step's
cumulative receipt is published, or only the one at the end of a padded
window, is not stated. If only the final receipt is published, there is no
"preceding receipt" to link to and the rule cannot be applied; if every step is
published, the constant-size property is per receipt, not per session, and the
on-graph footprint grows linearly like real-time mode.

**Proposed resolution.** State the cadence: "A gateway in recursive mode
publishes a `receipt_issued` at the end of each window (which MAY be a single
step). `prev_chain_digest` of the first receipt in a session is `""`; of every
later receipt, it MUST equal `chain_digest` of the most recent `receipt_issued`
for the same `session_id` on the same topic. Steps folded within a window are
attested by the cumulative proof and are not individually published."

**Resolution applied.** The R-01 resolution states the cadence (one receipt
per window, which MAY be a single step, with `sequence_range` naming the
window). Validation now states the genesis rule — `prev_chain_digest` is `""`
when no earlier accepted `recursive` receipt exists for the session on the
topic, and otherwise equals the `chain_digest` of the most recent one — and
requires `chain_digest` itself to be recomputed. Proof Modes also states that
per-action proving in this mode is off the release path, as in `batch`.

### R-15

**Severity:** High
**Location:** [Public Compliance Journal](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#public-compliance-journal) `sequence_range`;
[Boundary Action Capture](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#boundary-action-capture) *Sequence numbering*;
[Validation](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#validation) coverage check.
**Diagram:** B3a, B7, C7.

**Problem.** After R-01/R-02 the host runs one counter per session, shared by
every gateway, and every released action takes a number. `sequence_range` was
REQUIRED only for `batch` and `recursive` and MUST be absent for `real_time`.
A `real_time` action therefore consumes a position that no receipt ever names:
a session mixing `real_time` with another mode can never tile `1..max(to)`,
and a `real_time`-only session makes no coverage claim, so dropping a
`real_time` receipt is undetectable.

**Why it matters.** Mediated audit coverage is a MUST-level property and
`real_time` is the mode interactive deployments will use.

**Resolution applied.** `sequence_range` is REQUIRED in every mode, with
`from = to` in `real_time`, and is always bound into `statement_preimage`. The
coverage check runs over every accepted receipt regardless of mode, and a
session MAY mix modes. In `real_time` the number is obtained before proving,
since the proof binds it; a proving failure is fail-closed (no release, a
`prover_unavailable` signal distinct from `policy_rejected`), the held action
keeps its number, and the gateway proves it on recovery so the range closes.
Privacy Considerations notes that a `real_time` receipt discloses one position,
which its cadence reveals anyway. Test vectors regenerated.

### R-16

**Severity:** High
**Location:** [Public Statement Binding](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#public-statement-binding) preimage;
[Proof Modes](./ZKBC-Zero-Knowledge-Boundary-Compliance.md#proof-modes) chain-digest construction.
**Diagram:** B3c, B6.

**Problem.** `statement_preimage` included `LP(chain_digest_or_empty)`, and
`chain_digest_i = H(… || LP(prev_chain_digest_i) || LP(statement_hash_i))`.
`statement_hash` depends on `chain_digest`, which depends on `statement_hash`.
No recursive-mode journal can be constructed; the earlier test vector avoided
the cycle only by chaining a `real_time` statement hash whose `chain_digest`
slot was empty.

**Resolution applied.** `chain_digest` is removed from the preimage; only
`prev_chain_digest` is bound. `chain_digest` needs no separate binding because
it is a deterministic function of two bound values, and Validation recomputes
it. Every `statement_hash` vector changes (one fewer `LP("")` segment), and a
two-receipt recursive vector was added to show the order of computation.

---

## Sound as specified

For balance, the design decisions that hold up under review and should be kept
as they are:

- **Two normalization forms.** The `nfc`-for-membership / `fold`-for-
  non-membership split is correctly reasoned from the fail-closed / fail-open
  asymmetry, and the homoglyph residual risk is stated rather than hidden
  (diagram C6).
- **`policy_id` in the statement.** Binding the label as well as the
  commitment set closes a real re-labelling malleability.
- **Universal `LP` + domain separation.** Length-prefixing every variable field
  and tagging every commitment with `PROTOCOL_LABEL` and a purpose tag, plus
  RFC 6962 leaf/node prefixes, is the right discipline for interoperable
  preimages (diagram B5).
- **Receipt topics with no admin key.** Reusing HCS-1's immutability rule
  makes the audit trail undeletable and its memo unrewritable.
- **Consensus timestamp as the clock.** Treating `issued_at` as advisory and
  the network timestamp as authoritative removes prover control over policy
  windows.
- **Journal minimality as the privacy control.** Framing every journal-schema
  extension as a permanent public disclosure decision is the correct posture
  for an append-only public ledger.
- **Transparent, hash-based proof systems as the default.** Keeping
  pairing-based proofs OPTIONAL and non-post-quantum, and putting the
  post-quantum posture on proof-system transparency rather than hash length,
  is coherent with the SHA-256 choice.
- **Self-authenticating verifying keys.** `vk_id = commit("vk", vk_bytes)`
  means a registry entry cannot be substituted without detection.

## License

This document is licensed under Apache-2.0.
