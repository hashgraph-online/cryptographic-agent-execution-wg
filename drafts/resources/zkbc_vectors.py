#!/usr/bin/env python3
"""Reference generator for the ZKBC test vectors.

Reproduces every digest in the Test Vectors section of
ZKBC-Zero-Knowledge-Boundary-Compliance.md with H = SHA-256.
Standard library only. Run: python3 zkbc_vectors.py
"""

import base64
import hashlib
import json
import struct
import unicodedata

PROTOCOL_LABEL = None  # set below, after nfc() is defined


def nfc(s: str) -> bytes:
    return unicodedata.normalize("NFC", s).encode("utf-8")


def fold(s: str) -> bytes:
    # NFKC, then Unicode default case folding, then UTF-8.
    return unicodedata.normalize("NFKC", s).casefold().encode("utf-8")


PROTOCOL_LABEL = nfc("ZKBC/v1")


def H(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def uint64be(n: int) -> bytes:
    return struct.pack(">Q", n)


def uint32be(n: int) -> bytes:
    return struct.pack(">I", n)


def LP(x: bytes) -> bytes:
    return uint64be(len(x)) + x


def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def jcs(obj) -> bytes:
    # RFC 8785 for the value shapes used here (ASCII keys, strings, small ints).
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def commit(tag: bytes, m: bytes) -> bytes:
    return H(LP(PROTOCOL_LABEL) + LP(tag) + LP(m))


def leaf(tag: bytes, e: bytes) -> bytes:
    return H(b"\x00" + LP(PROTOCOL_LABEL) + LP(tag) + LP(e))


def node(l: bytes, r: bytes) -> bytes:
    return H(b"\x01" + l + r)


def set_commit(tag: str, elements) -> bytes:
    t = nfc(tag)
    leaves = [leaf(t, e) for e in sorted(set(elements))]
    size = 1
    while size < max(len(leaves), 1):
        size *= 2
    leaves += [leaf(t, b"")] * (size - len(leaves))
    while len(leaves) > 1:
        leaves = [node(leaves[i], leaves[i + 1])
                  for i in range(0, len(leaves), 2)]
    return leaves[0]


def identity_digest(tenant_id: bytes, user_id: bytes) -> bytes:
    return H(LP(PROTOCOL_LABEL) + LP(nfc("identity"))
             + LP(tenant_id) + LP(user_id))


MODE = {"batch": 0x01, "real_time": 0x02, "recursive": 0x03}
FAMILY = {"output": 0x01, "tool": 0x02, "access": 0x04}
VERDICT = {"non_compliant": 0, "compliant": 1}


def statement_hash(*, version, policy_id, session_id, program_id, mode,
                   family, verdict, commitments, identity=b"",
                   prev_chain=b"", sequence_range,
                   counts=None) -> bytes:
    mask = 0
    for f in family:
        mask |= FAMILY[f]
    pre = LP(PROTOCOL_LABEL) + LP(nfc("statement"))
    pre += LP(nfc(version)) + LP(nfc(policy_id))
    pre += LP(session_id) + LP(program_id)
    pre += bytes([MODE[mode], mask, VERDICT[verdict]])
    pre += uint32be(len(commitments))
    for key in sorted(commitments):
        pre += LP(nfc(key)) + LP(commitments[key])
    pre += LP(identity)
    # chain_digest is derived from statement_hash, so only its predecessor
    # is bound here.
    pre += LP(prev_chain)
    pre += LP(uint64be(sequence_range[0]) + uint64be(sequence_range[1]))
    pre += LP(jcs(counts) if counts is not None else b"")
    return H(pre)


def chain_digest(prev: bytes, stmt_hash: bytes) -> bytes:
    return H(LP(PROTOCOL_LABEL) + LP(nfc("chain")) + LP(prev) + LP(stmt_hash))


def main():
    program_id = commit(nfc("program"), nfc("zkbc.output.v1"))
    forbidden = set_commit("policy/output/forbidden",
                           [fold(x) for x in ("credit_card", "ssn")])
    allowlist = set_commit("policy/tool/allowlist",
                           [nfc(x) for x in ("calculator", "email.send", "search")])
    sensitive = set_commit("policy/tool/sensitive-keys",
                           [nfc(x) for x in ("password", "ssn", "to")])
    descriptor = {"unicode": "16.0.0", "identifier_form": "nfc",
                  "matching_form": "nfkc+casefold", "tokenizer": "uax29-words"}
    canon = commit(nfc("policy/canonicalization"), jcs(descriptor))
    ident = identity_digest(nfc("acme"), nfc("alice@acme.example"))
    session_id = bytes.fromhex("4a1f9c0e8b7d6a5f4e3c2b1a09876543")
    commitments = {"output.canonicalization": canon,
                   "output.forbidden": forbidden}
    common = dict(version="ZKBC/1.0", policy_id="acme.pii.v3",
                  session_id=session_id, program_id=program_id,
                  family=["output"], verdict="compliant",
                  commitments=commitments)
    counts = {"output": {"token_count": 128, "distinct_token_count": 42,
                         "hit_count": 0}}
    stmt_rt = statement_hash(mode="real_time", sequence_range=(1, 1),
                             counts=counts, **common)
    stmt_batch = statement_hash(mode="batch", sequence_range=(1, 3), **common)
    # Recursive variant: two windows, 1..3 then 4..5, chained.
    stmt_rec0 = statement_hash(mode="recursive", sequence_range=(1, 3),
                               prev_chain=b"", **common)
    chain0 = chain_digest(b"", stmt_rec0)
    stmt_rec1 = statement_hash(mode="recursive", sequence_range=(4, 5),
                               prev_chain=chain0, **common)
    chain1 = chain_digest(chain0, stmt_rec1)
    # Example verifying-key bytes: 0x00..0x1f. A real key is the proof system's
    # own serialization; only its bytes enter the commitment.
    vk_bytes = bytes(range(32))
    vk_id = commit(nfc("vk"), vk_bytes)

    rows = [
        ('program_id (commit "program")', program_id),
        ('set_commit "policy/output/forbidden" (F)', forbidden),
        ('set_commit "policy/tool/allowlist" (A)', allowlist),
        ('set_commit "policy/tool/sensitive-keys" (K)', sensitive),
        ('commit "policy/canonicalization" (descriptor)', canon),
        ("identity_digest(acme, alice@acme.example)", ident),
        ("session_id (base64url)", session_id),
        ("statement_hash (output / real_time / range 1..1)", stmt_rt),
        ("statement_hash (batch variant, range 1..3)", stmt_batch),
        ('statement_hash (recursive #0, 1..3, prev = "")', stmt_rec0),
        ("chain_digest   (recursive #0, genesis)", chain0),
        ("statement_hash (recursive #1, 4..5)", stmt_rec1),
        ("chain_digest   (recursive #1)", chain1),
        ('vk_id (commit "vk" over vk_bytes)', vk_id),
    ]
    for label, value in rows:
        print(f"{label:<52}= {b64u(value)}")

    print()
    for s in ("ssn", "SSN", "ｓｓｎ", "ѕѕn"):
        f = fold(s)
        hit = f in {fold(x) for x in ("credit_card", "ssn")}
        print(f'"{s}" -> fold = "{f.decode()}"  '
              f'{"member of F -> rejected by pre-check" if hit else "NOT a member -> compliant"}')


if __name__ == "__main__":
    main()
