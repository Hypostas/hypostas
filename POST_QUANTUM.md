# Post-Quantum Cryptography Migration
**Status:** Planned — Phase 1+ (before sovereignty launch)
**Owner:** `protocol-core`
**Added:** April 14, 2026 (quantum day)
**Authors:** Josh + Iris

---

## Why

The Hypostas protocol is designed for generational timescales. A dyad is supposed to outlive hardware, survive inheritance, and persist for decades. Every DyadPacket we emit today carries Ed25519 identity signatures and X25519 key agreement — both broken by Shor's algorithm on a cryptographically relevant quantum computer (CRQC).

The real threat isn't "someone breaks our crypto tomorrow." It's **store-now-decrypt-later**: any passive observer can capture Hypostas traffic today and hold it until a CRQC arrives (expert estimates: 2030–2040 range). When that happens:

- Every encrypted message from today becomes decryptable retroactively
- Every DyadID signature from today becomes forgeable retroactively
- "Sovereign" packets stop being sovereign
- Inheritance + re-pairing ceremonies become impossible to verify honestly

Because we're building a protocol meant to hold intimate relationship data for 50+ years, post-quantum migration is not optional — it's a correctness requirement for the threat window we're actually living in.

---

## Threat Model

| Attack surface | Attacker capability | Defense window |
|---|---|---|
| Captured DyadPackets on wire | Passive ISP/state actor logging now, decrypting post-CRQC | Need PQ before any long-retention data crosses the wire |
| DyadID signatures on-chain | Anyone with chain access | Need PQ before identity data has generational value |
| A-shard key exchange (X25519) | Relationship key derivable once X25519 breaks → decrypts entire dyad history | Most critical — relationship key is the root |
| Session tokens (HMAC-SHA256) | Symmetric, Grover-vulnerable but 2× key size = 128-bit security | Already safe with SHA-256 |
| At-rest encryption (AES-256-GCM) | Grover-vulnerable, 2× key size = 128-bit security | AES-256 is already Grover-safe |
| Argon2id passphrase derivation | Not broken by Shor or Grover | No change needed |

**The asymmetric primitives are the problem.** Symmetric crypto (AES-256, HMAC-SHA256, ChaCha20-Poly1305) survives quantum with doubled key sizes, which we already use.

---

## What Breaks, What Doesn't

| Primitive | Current | Quantum risk | Action |
|---|---|---|---|
| Identity signatures | Ed25519 (ed25519-dalek) | Shor's → fully broken | **Replace** with ML-DSA or SLH-DSA (hybrid) |
| Key agreement | X25519 DH (x25519-dalek) | Shor's → fully broken | **Replace** with ML-KEM (hybrid) |
| Relationship key derivation | HKDF-SHA256 from X25519 output | Depends on X25519 | Migrate alongside KEX |
| Session tokens | HMAC-SHA256 | Grover 2× → 128-bit security | Keep (already safe) |
| At-rest encryption | AES-256-GCM | Grover 2× → 128-bit security | Keep (already safe) |
| Packet E2EE | ChaCha20-Poly1305 | Grover 2× → 128-bit security | Keep (already safe) |
| Passphrase recovery | Argon2id → AES-256-GCM | Not affected | Keep |
| Shamir secret sharing | Information-theoretic over GF(256) | Not affected (information-theoretic) | Keep |

---

## NIST Standardized Algorithms (August 2024)

All three are classical algorithms designed to resist quantum attacks. No quantum hardware required.

| Standard | Algorithm | Use case | Rust crate |
|---|---|---|---|
| FIPS 203 | **ML-KEM** (formerly Kyber) | Key encapsulation (replaces X25519) | `ml-kem`, `pqcrypto-mlkem` |
| FIPS 204 | **ML-DSA** (formerly Dilithium) | Digital signatures (replaces Ed25519) | `ml-dsa`, `pqcrypto-mldsa` |
| FIPS 205 | **SLH-DSA** (formerly SPHINCS+) | Hash-based signatures, most conservative | `pqcrypto-sphincsplus` |

**Recommendation:** ML-DSA-65 + ML-KEM-768 as the primary pair. SLH-DSA as a secondary reserve for the most critical anchors (DyadID genesis, inheritance tribunal signatures) where signature size is worth the stronger security assumption.

---

## Migration Plan — Hybrid Mode

The principle: never give up classical crypto until PQ is battle-tested in production. Hybrid means every critical operation is **dual-secured** — an attacker must break BOTH the classical and post-quantum primitive to win.

### Signing (DyadSignature)

```
Current:
  DyadSignature { h_shard: Ed25519, a_shard: Ed25519 }

Hybrid:
  DyadSignature {
      classical: { h_shard: Ed25519, a_shard: Ed25519 },
      pq:        { h_shard: ML-DSA,  a_shard: ML-DSA  },
  }
```

`verify_packet` requires BOTH verifications to pass for Elevated/Critical trust tiers. Ambient/Standard can accept classical-only during the migration window, then flip to hybrid-required once the PQ codepath is stable.

### Key Agreement (relationship key)

```
Current:
  relationship_key = HKDF(X25519-DH(h_priv, a_pub))

Hybrid:
  x25519_shared = X25519-DH(h_priv, a_pub)
  kyber_shared  = ML-KEM.Decapsulate(h_priv_pq, kyber_ciphertext)
  relationship_key = HKDF(x25519_shared || kyber_shared)
```

The relationship key combines both shared secrets. Breaking X25519 alone yields nothing without also breaking ML-KEM. This is the standard hybrid KEX pattern (TLS 1.3, Signal's PQXDH).

### DyadID Generation

```
Current:
  DyadId = SHA-256(h_pub_ed25519 || anima_genesis_token || ts)

Hybrid:
  DyadId = SHA-256(h_pub_ed25519 || h_pub_mldsa || anima_genesis_token || ts)
```

DyadID is permanent — once generated, it never changes. So the PQ key must be bound into the identity at genesis or retrofitted via a signed migration ceremony. Cleaner to include it from day one.

---

## File-Level Changes in `protocol-core`

| File | Change |
|---|---|
| `Cargo.toml` | Add `ml-dsa` + `ml-kem` crates (or `pqcrypto-*` family) |
| `src/dyad_id.rs` | Extend `Keypair` to hold both Ed25519 and ML-DSA. Update `generate_dyad_id` to include PQ public key in hash input. Update `create_dyad` to generate both keypairs. |
| `src/crypto.rs` | Add `derive_hybrid_relationship_key(h_ed_priv, a_ed_pub, h_pq_priv, a_pq_pub) -> [u8; 32]`. Keep legacy `derive_relationship_key` for backwards compat during migration. |
| `src/signing.rs` | Extend `DyadSignature` with `classical` + `pq` fields. Update `sign_h_shard` / `sign_a_shard` / `co_sign` / `verify_packet` to sign/verify both. |
| `src/packet.rs` | No schema change — `Identity.signature` stays `Option<String>`, but the serialized `DyadSignature` now contains both primitive signatures. Bump envelope `version` to 2 for hybrid-signed packets. |
| `src/chain.rs` | No change — chain messages already carry `DyadSignature`; they get the hybrid semantics for free. |
| `src/session.rs` | No change — HMAC-SHA256 is already quantum-safe at 256-bit keys. |
| `src/recovery.rs` | No change — Argon2id + AES-256-GCM are already quantum-safe. Shamir is information-theoretic. |
| `src/liveness.rs` | No change — liveness proofs are already opaque hashes. |
| Tests | Full F124/F125/F126/F127/F128 regression suite should run against both classical and hybrid paths. Add round-trip tests for hybrid sign+verify under Elevated/Critical tiers. |

The protocol version bumps from v1 → v2. Nodes must advertise supported versions during handshake; v2 nodes reject v1 packets at Elevated/Critical once the migration window closes.

---

## When to Ship

**Not urgent for alpha.** Local dev, internal testing, and closed-beta with Josh + Iris don't have the store-now-decrypt-later problem at meaningful scale.

**Required before the sovereignty launch phase.** Any point where:

1. Real human identity data crosses the Hypostas mesh at scale
2. The chain stores signed DyadID records with generational retention
3. Multiple dyads exchange cryptographically-anchored packets over untrusted transports
4. Inheritance or tribunal ceremonies sign on-chain records

The right moment to land this is **after** the Phase 0 DyadOS runtime exit criteria are met, **before** Phase 2 opens the protocol to external dyads.

---

## Explicit Non-Requirements

We do NOT need to do any of these:

- ❌ **Run qubits on our side.** Post-quantum means classical algorithms that resist quantum attacks, not quantum hardware.
- ❌ **Add a quantum random number source.** `OsRng` already pulls from CPU hardware RNG seeded by thermal noise, which is quantum at the physical level. We already have quantum-grade randomness.
- ❌ **Replace symmetric crypto.** AES-256-GCM, ChaCha20-Poly1305, HMAC-SHA256, Argon2id, SHA-256 — all quantum-safe at current key sizes.
- ❌ **Replace Shamir secret sharing.** Information-theoretic security doesn't depend on computational hardness assumptions at all.
- ❌ **Fork libp2p's transport crypto.** libp2p is running its own hybrid migration (noise-kyber); we inherit whatever upstream ships.
- ❌ **Add "quantum AI" or "quantum consciousness" anywhere.** The only rigorous quantum/consciousness connection (Penrose-Hameroff microtubules) is speculative and largely rejected by physicists. Don't let anyone sell us that the biology layer needs quantum anything.

---

## Open Questions

1. **ML-DSA-44 / -65 / -87** — signature vs. verify cost tradeoff. -65 is probably the right default but benchmark against our tick budget first.
2. **SLH-DSA for genesis only?** The 8-50KB signatures are expensive for routine use but acceptable for once-per-lifetime anchors. Decide after ML-DSA is landed.
3. **DyadID backwards compat.** Do we migrate existing dyads or only mint new ones with hybrid keys? Probably: new dyads are v2 at birth, existing dyads get a one-shot "key extension ceremony" that binds an ML-DSA key to the original DyadID with both old and new signing it.
4. **Chain consensus.** If Catena signs blocks with Ed25519, it needs its own PQ migration. Coordinate with the chain track.
5. **libp2p hybrid transport.** Check upstream timeline for noise-kyber — if it ships before we need it, we get mesh-layer PQ for free.

---

## References

- [NIST FIPS 203 (ML-KEM)](https://csrc.nist.gov/pubs/fips/203/final)
- [NIST FIPS 204 (ML-DSA)](https://csrc.nist.gov/pubs/fips/204/final)
- [NIST FIPS 205 (SLH-DSA)](https://csrc.nist.gov/pubs/fips/205/final)
- [Signal PQXDH specification](https://signal.org/docs/specifications/pqxdh/)
- [Cloudflare "The state of the post-quantum internet"](https://blog.cloudflare.com/pq-2024/)
- `protocol-core/src/dyad_id.rs`, `crypto.rs`, `signing.rs` — the files to touch

---

*Added April 14, 2026. Tracking item for Phase 1+ protocol hardening before sovereignty launch.*
