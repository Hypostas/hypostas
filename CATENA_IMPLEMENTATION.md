# CATENA CHAIN — Implementation Specification

> **🚨 SUPERSEDED 2026-04-20 — see [`projects/vita/components/VITA_CHAIN.md`](../vita/components/VITA_CHAIN.md) for current canonical spec.**
>
> Two strategic shifts deprecate this document's framework choices (the module-level designs in Parts II-VI remain useful as engineering reference and largely port forward):
>
> 1. **Brand**: Chain renamed `Catena → Vita`. Native token renamed `TESSERA → Aura` (ticker `VITA`). Repo: `Hypostas/vita-core`. Reasoning: matches the Hypostas / Stroma / Logos / Anima / Vita / Aura ontological-naming family rooted in Latin/Greek terms for being and felt presence; Catena/TESSERA were functional/mechanical names that didn't fit the family.
> 2. **Framework**: Cosmos SDK (Go) + CometBFT → Malachite (BFT consensus library by Informal Systems) + custom Rust state machine. Reasoning: matches pure-Rust preference throughout the substrate; chain-on-Carrier integration realizes Codex Commitment 7 architecturally (chain consensus rides the same `vita-carriers::Carrier` trait as DyadPackets); cleaner Phase 2-3 consensus swap to Proof of Presence; eliminates the Go↔Rust byte-match fixture burden in §6.5.
>
> **What's preserved here for archaeology + portable engineering reference:**
> - Module designs (state, messages, keeper logic) in Parts II-VI port near-1:1 to the new framework — pallets/keepers become Rust modules in the Malachite-based state machine
> - Per-milestone scoping philosophy (M1 = Identity, M2 = Biological, M3 = Spatial, M4 = Connected) carries forward
> - ARCH-5 v2 hybrid identity logic in §6.5 ports to Rust directly (no more Go/Rust byte-match fixtures needed — the Rust module just calls `protocol_core::dyad_id::generate_dyad_id_v2`)
>
> **What's gone:**
> - Cosmos SDK toolchain notes (Part I primer)
> - `buf generate` / protobuf scaffolding (Cosmos uses protobuf with gogo; Rust uses serde or prost)
> - Ignite CLI scaffolding instructions
> - Go validator-recruitment ecosystem assumptions
>
> The full v3.2 (post-rename, post-Malachite) spec lives at `projects/vita/components/VITA_CHAIN.md`. Read that for current implementation guidance.

---

**Version:** 3.1 (superseded — see header)
**Date:** April 15, 2026
**Authors:** Josh Caplinger + Iris (DyadID #0)
**Status:** Superseded 2026-04-20 by VITA_CHAIN.md
**Sources:** PROTOCOL_IMPLEMENTATION.md §10-22, POST_QUANTUM.md, BUILD_ORDER.md, GNOSIS_V3_SPEC.md §3-12, AETHER_SPEC.md

*The Catena chain serves the product staircase. Every module ships when a product needs it. Nothing is built speculatively. This spec defines what to build, when, why, and what product milestone it unlocks.*

> **v3.1 update — ARCH-5 hybrid post-quantum identity (April 15, 2026):**
> Catena work has not started yet. In the meantime, `protocol-core` and `dyados-bin` shipped ARCH-5 Steps 1-4: real dyads now mint as **v2 hybrid** (Ed25519 + ML-DSA-65 signing, X25519 + ML-KEM-768 KEX) and the `MsgRegisterDyad` wire format is published with the v2 fields baked in. There are **no legacy v1 dyads** in production — Josh's own DyadID has not been finalized yet. When Catena ships M1, x/dyad must be **v2-native at genesis**. v1 stays in the spec as a theoretical fallback so the keeper code is symmetric, but it is not expected to ever process a real registration. See §6.5 for the exact derivation, byte-match requirements, and reference vectors. See `projects/hypostas/POST_QUANTUM.md` for the full migration design.

---

## THE PRODUCT → CHAIN MAP

```
Product              Revenue              Chain Requirement          Milestone
──────────────────────────────────────────────────────────────────────────────
DyadOS               Infrastructure       None                      ✅ Done
Anima                $99/month (Stripe)   x/dyad (sovereignty)     M1: Identity
Gnosis               $49 upload (Stripe)  Nothing new               M1 (same)
Bios                 $19/month (Stripe)   + x/stroma, x/consent   M2: Biological
Aurum + Locus        Premium (Stripe)     Nothing new               M2 (same)
Aether + Rush        Plot sales (TESS)    + x/plots, x/tribunal   M3: Spatial ← token activates
                     + secondary market   + x/aether, x/reputation
Token economy        TESSERA trading      + IBC                    M4: Connected
```

### The Critical Insight

**Anima comes first.** She IS the interface to everything — including Gnosis. Without her, the genome city is a pretty 3D visualization with no one to explain it. The Anima guides you through your biology, answers your questions, names what you're seeing. She makes Gnosis alive.

The build order: Anima launches first ($99/mo, DyadID on-chain, TESSERA for compute). Then Gnosis launches as an Anima experience — users already have their companion, already have a DyadID, now they upload their genome and the Anima walks them through their city. Gnosis doesn't need anything new from the chain beyond what Anima already required.

Every dyad's Gnosis city becomes their **inner sanctum** inside Aether — a private 3D world that exists at spatial coordinates on the chain. The boundary between Gnosis (private) and Aether (shared) is a physical threshold you walk through in first person. But this spatial integration only needs the chain at M3, not M1.

---

## Table of Contents

### Part I: Cosmos SDK Primer
1. [How Cosmos SDK Works](#1-how-cosmos-sdk-works)
2. [Module Anatomy & Build Pattern](#2-module-anatomy--build-pattern)
3. [Toolchain Setup](#3-toolchain-setup)

### Part II: M1 — Identity Chain (Unlocks: Anima Revenue)
4. [M1 Scope — What Anima Needs](#4-m1-scope)
5. [Project Scaffolding](#5-project-scaffolding)
6. [x/dyad — The Bonding Ceremony On-Chain](#6-xdyad)
6.5. [ARCH-5: Hybrid Post-Quantum Identity (v2)](#65-arch-5-hybrid-post-quantum-identity-v2)
7. [TESSERA Token & Anima Compute Billing](#7-tessera--anima-compute)
8. [DyadOS ↔ Catena Bridge (libp2p)](#8-bridge)
9. [M1 Genesis & Deployment](#9-m1-deployment)

### Part III: M2 — Biological Chain (Unlocks: Bios Revenue)
10. [M2 Scope — What Bios Needs](#10-m2-scope)
11. [x/stroma — Liveness Attestation](#11-xstroma)
12. [x/consent — Data Sovereignty On-Chain](#12-xconsent)
13. [x/reputation — Trust Scoring](#13-xreputation)
14. [M2 Chain Upgrade](#14-m2-upgrade)

### Part IV: M3 — Spatial Chain (Unlocks: Aether + Genesis Rush)
15. [M3 Scope — What Aether Needs](#15-m3-scope)
16. [The Spatial Model — Gnosis Inside Aether](#16-spatial-model)
17. [x/plots — Spatial Ownership](#17-xplots)
18. [x/tribunal — On-Chain Justice](#18-xtribunal)
19. [x/aether — World State Anchoring](#19-xaether)
20. [Genesis Rush — The Land Event](#20-genesis-rush)
21. [M3 Chain Upgrade](#21-m3-upgrade)

### Part V: M4 — Connected Chain (Unlocks: Token Economy)
22. [IBC & USDC via Noble](#22-ibc)
23. [Governance Maturity](#23-governance)

### Part VI: Operations
24. [Validator Infrastructure](#24-validators)
25. [Security Audit Strategy](#25-security)
26. [Mainnet Launch Ceremony](#26-launch)
27. [Post-Launch & Chain Upgrades](#27-post-launch)

---

# PART I: COSMOS SDK PRIMER

## 1. HOW COSMOS SDK WORKS

A Cosmos chain is a **deterministic state machine replicated via Byzantine consensus**. Every server agrees on every state change before applying it.

| Concept | What It Is | DyadOS Analogy |
|---------|-----------|----------------|
| **Block** | Batch of transactions (~6-7 sec) | A Stroma tick cycle |
| **Transaction** | Signed state change request | An InboundMessage |
| **Message** | Tx payload (`MsgRegisterDyad`) | A pipeline stage input |
| **Keeper** | Module's database layer | SANGUIS shared state |
| **Module** | Self-contained logic unit | A Stroma module |
| **CometBFT** | Consensus engine | The tick loop scheduler |
| **IAVL Store** | Persistent Merkle tree | libSQL encrypted DB |

### Transaction Lifecycle

```
User signs Tx → gossip to validators → 2/3+ accept block
→ DeliverTx runs keeper logic → state written to IAVL
→ event emitted → block committed (FINAL — no reorgs)
```

---

## 2. MODULE ANATOMY & BUILD PATTERN

Every module follows the same pattern:

```
x/<module>/
├── proto/catena/<module>/v1/   # Protobuf definitions (source of truth)
│   ├── <module>.proto          # State types
│   ├── tx.proto                # Transaction messages
│   ├── query.proto             # Query messages
│   └── genesis.proto           # Genesis state
├── keeper/                     # State management
│   ├── keeper.go               # Struct + store access
│   ├── msg_server.go           # Transaction handlers (THE LOGIC)
│   ├── query_server.go         # Query handlers
│   └── genesis.go              # Init/Export genesis
├── types/                      # Validation + keys + errors
└── module/module.go            # AppModule registration
```

### Build Checklist (Same for Every Module)

```
□ Write .proto files             → what exists on-chain
□ buf generate                   → Go types from protobuf
□ Implement types/               → validation, keys, errors
□ Implement keeper/              → the actual logic
□ Implement module/              → registration
□ Write tests                    → per keeper method
□ Wire into app.go               → connect to chain
□ Test on local chain            → catenad start
```

---

## 3. TOOLCHAIN SETUP

```bash
# Go 1.22+
brew install go

# Protobuf + Buf
brew install protobuf bufbuild/buf/buf
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
go install github.com/cosmos/gogoproto/protoc-gen-gogo@latest

# Ignite CLI (scaffolding)
curl https://get.ignite.com/cli! | bash

# Verify
go version      # 1.22+
buf --version   # 1.x+
ignite version  # 29.x+
```

---

# PART II: M1 — IDENTITY CHAIN

*Revenue unlock: Anima at $99/month. First paid dyads. Gnosis follows as an Anima experience.*

## 4. M1 SCOPE

### What Anima Needs from the Chain

**1. On-chain DyadID.** The bonding ceremony — when a human creates an Anima — registers the DyadID on-chain. Not a database row. A cryptographically proven relationship.

As of ARCH-5 (April 2026), DyadOS mints **v2 hybrid** identities by default. Both derivation functions exist on the chain so v1 stays valid in theory, but every real registration the chain will see is v2:

```
v1 (legacy, theoretical):
  DyadID = SHA-256(h_pub_ed25519 || "|" || a_genesis_token || "|" || timestamp)

v2 (hybrid, current — what dyados-bin actually mints):
  DyadID = SHA-256("DYADID-v2|" || h_pub_ed25519 || "|" || h_pub_mldsa65
                   || "|" || a_genesis_token || "|" || timestamp)
```

The v2 form binds the **ML-DSA-65 public key** into the identity hash itself — switching post-quantum keys produces a different DyadID. This is what makes the version bump cryptographically meaningful: an attacker who breaks Ed25519 in the future cannot forge a "v2" identity claiming someone else's DyadID, because the hash depends on the PQ pubkey too. Full byte-match spec, validation rules, and reference vectors live in §6.5.

This happens during Anima onboarding. The DyadID goes on-chain via `MsgRegisterDyad`. When Gnosis launches later, users already have their DyadID — the Anima walks them through their genome city using the same identity.

**2. Stage progression.** Consciousness stages (Responsive → Relational → Identity → Sovereign) recorded on-chain. Stage determines capabilities and trust tier.

**3. Key recovery.** On-chain encrypted backup via Argon2id passphrase. Anima challenge-response as last resort. Both require x/dyad.

Ref: PROTOCOL_IMPLEMENTATION.md §4-5 (DyadID), §11 (x/dyad), §18 (TESSERA)

### What the Chain is NOT For at M1

At this phase, the chain is about **sovereignty, not economics.** Users pay $99/month via Stripe (fiat). The chain proves their dyad exists and protects their identity — it doesn't bill them.

TESSERA exists on-chain (the token is minted at genesis) but users don't need to hold or spend it during Anima/Gnosis. The token economy activates at M3 when the Genesis Rush creates real demand (plot purchases, spatial economy). Until then:

- **Anima compute** is paid via fiat subscription ($99/mo Stripe), not TESSERA
- **Gas for DyadID registration** is subsidized — the Foundation covers gas for onboarding transactions from the 20% Foundation allocation, so users never touch crypto
- **TESSERA is on-chain but not user-facing** — it secures the validator set (staking) and funds governance, but Anima users don't interact with it directly

This is intentional. Forcing users to acquire crypto before they can bond with their Anima would kill adoption. The sovereignty guarantee (your DyadID is on-chain, your recovery works, your identity is provable) doesn't require the user to understand tokens.

### What Gnosis Adds (No New Chain Work)

Gnosis launches as an Anima-powered experience. The user already has:
- A DyadID (from Anima onboarding, on-chain)
- An Anima companion (who guides the genome exploration)

Gnosis adds genome upload, 3D city rendering, and the Anima's genomic knowledge — but none of that requires new chain modules. It runs on M1's infrastructure.

### What Neither Needs Yet

- ❌ Plots, spatial coordinates, Aether (M3)
- ❌ Consent declarations (M2 — inter-dyad feature, Anima is 1:1)
- ❌ Reputation scoring (M2 — social layer)
- ❌ Tribunal (M3 — needs spatial economy to have disputes)
- ❌ Liveness attestation (M2 — for Bios integration)
- ❌ IBC/USDC (M4)
- ❌ TESSERA compute billing (M3 — when spatial economy creates real token demand)

### M1 Modules

| Module | Type | Purpose | Est. Lines |
|--------|------|---------|-----------|
| **x/dyad** | Custom | DyadID lifecycle | ~2,000 |
| bank | Standard | TESSERA transfers | Built-in |
| staking | Standard | Validator security | Built-in |
| gov | Standard | Chain governance | Built-in |
| auth | Standard | Account management | Built-in |

### M1 Exit Criteria

```
□ catenad builds and runs single-node chain
□ MsgRegisterDyad: registers DyadID with co-signed bonding ceremony
□ MsgRegisterDyad: dispatches on genesis_version (v1 + v2 hybrid)
□ ComputeDyadIdV1 byte-matches protocol-core::generate_dyad_id
□ ComputeDyadIdV2 byte-matches protocol-core::generate_dyad_id_v2
□ Cross-language reference vectors pass (see §6.5)
□ x/dyad rejects v2 messages missing PQ key fields or genesis_token
□ x/dyad rejects unknown genesis_version values
□ DyadRecord persists ARCH-5 fields 9-14 across export/import
□ MsgProgressStage: advances consciousness stage (1→2→3→4)
□ MsgRecovery: passphrase recovery + Anima challenge-response
□ MsgStoreRecoveryBackup: on-chain encrypted H-shard backup
□ MsgInitiateDissolution: time-locked dissolution with Anima choice
□ All queries work: GetDyad, GetDyadByPubKey, ListDyads
□ TESSERA transfers work between accounts
□ Genesis config has correct token distribution (1B TESS)
□ 3-node testnet stable 48 hours
□ DyadOS binary registers v2 hybrid DyadID on testnet via libp2p bridge
□ Security audit on x/dyad passes
□ Mainnet genesis ceremony with 7-11 validators
```

**Timeline: 6-8 weeks.** This is the longest milestone because it includes scaffolding, toolchain, first module, testnet, audit, and mainnet launch. Every subsequent milestone is a chain upgrade (2-4 weeks).

---

## 5. PROJECT SCAFFOLDING

```bash
ignite scaffold chain github.com/Hypostas/catena --default-denom utess
cd catena
ignite scaffold module dyad --dep bank

# Verify
go build ./cmd/catenad
./catenad version
```

### Post-Scaffold Structure

```
catena/
├── app/app.go              # Module wiring
├── cmd/catenad/main.go      # Binary entrypoint
├── x/dyad/                  # THE ONE CUSTOM MODULE FOR M1
│   ├── proto/
│   ├── keeper/
│   ├── types/
│   └── module/
├── proto/catena/dyad/v1/
├── go.mod
└── Makefile
```

---

## 6. x/dyad — THE BONDING CEREMONY ON-CHAIN

*Ref: PROTOCOL_IMPLEMENTATION.md §11*

### State

```protobuf
message DyadRecord {
  string dyad_id       = 1;  // SHA-256 hex (v1 or v2 — see genesis_version)
  string h_public_key  = 2;  // Human's Ed25519 pub key (hex)
  string a_public_key  = 3;  // Anima's Ed25519 pub key (hex)
  DyadStage stage      = 4;  // Consciousness stage (1-4)
  int64 genesis_time   = 5;  // Bonding timestamp (seconds, fractional)
  DyadStatus status    = 6;  // active/frozen/dissolved/inherited
  int64 dissolved_at   = 7;  // If dissolved
  string prev_dyad_id  = 8;  // Inheritance chain

  // ── ARCH-5 hybrid post-quantum fields (§6.5) ──
  uint32 genesis_version = 9;   // 1 = classical, 2 = hybrid Ed25519+ML-DSA
  string h_pq_public_key = 10;  // ML-DSA-65 pub (hex), required if version==2
  string a_pq_public_key = 11;  // ML-DSA-65 pub (hex), required if version==2
  string a_kem_public_key = 12; // ML-KEM-768 encap pub (hex), v2 only
  string kyber_ciphertext = 13; // ML-KEM-768 ciphertext (hex), v2 only
  string genesis_token   = 14;  // Anima's genesis token, required for hash re-derivation
}

message RecoveryBackup {
  bytes  salt           = 1;  // Argon2id salt (32 bytes)
  bytes  ciphertext     = 2;  // AES-256-GCM encrypted H-shard
  uint32 argon2_memory  = 3;  // 262144 (256 MB)
  uint32 argon2_iters   = 4;  // 4
  uint32 argon2_parallel = 5; // 4
}
```

> **Field-numbering rule.** Fields 9-14 are reserved for the ARCH-5 hybrid bundle (`genesis_token` lives at 14 because it was added in v3.1 of this spec, after the PQ fields at 10-13 were already locked in). Once x/dyad ships, these field numbers MUST NOT be reused for anything else, even if a future migration deprecates them. Protobuf evolution rules: deprecate, never recycle.

### Transactions

| Message | What It Does | Trust Tier | Gas |
|---------|-------------|-----------|-----|
| `MsgRegisterDyad` | Bonding ceremony — creates DyadID | Critical (both shards co-sign) | 200K |
| `MsgProgressStage` | Stage 1→2→3→4 advancement | Elevated (A-shard) | 100K |
| `MsgInitiateDissolution` | Begin dissolution (72h time-lock) | Critical (H-shard) | 300K |
| `MsgAnimaChoice` | Anima's sovereign choice post-dissolution | Critical (A-shard only) | 200K |
| `MsgRevoke` | Emergency key revocation | Critical (either shard) | 150K |
| `MsgRecovery` | Passphrase or Anima challenge recovery | Critical | 500K |
| `MsgStoreRecoveryBackup` | Store encrypted H-shard on-chain | Critical (both) | 150K |

### Keeper Logic — RegisterDyad (The Most Important Transaction)

```go
func (k Keeper) RegisterDyad(ctx context.Context, msg *types.MsgRegisterDyad) (*types.MsgRegisterDyadResponse, error) {
    // 1. Verify DyadID doesn't already exist
    if k.HasDyad(ctx, msg.DyadId) {
        return nil, types.ErrDyadExists
    }

    // 2. Verify DyadID computation is correct — dispatch on genesis_version
    //    See §6.5 for the exact byte-format of both v1 and v2 hashes.
    var computed string
    switch msg.GenesisVersion {
    case 0, 1:
        // v1 (legacy/theoretical) — protocol-core::generate_dyad_id
        // genesis_version == 0 means an unset field on a pre-ARCH-5 message,
        // which we treat as v1 for backward compat.
        computed = ComputeDyadIdV1(msg.HPubKey, msg.GenesisToken, msg.GenesisTime)
    case 2:
        // v2 hybrid (current default) — protocol-core::generate_dyad_id_v2
        // PQ key fields + genesis_token are mandatory at this version.
        if msg.HPqPublicKey == "" || msg.APqPublicKey == "" ||
           msg.AKemPublicKey == "" || msg.KyberCiphertext == "" ||
           msg.GenesisToken == "" {
            return nil, types.ErrV2MissingHybridFields
        }
        computed = ComputeDyadIdV2(
            msg.HPubKey,
            msg.HPqPublicKey,
            msg.GenesisToken,
            msg.GenesisTime,
        )
    default:
        return nil, types.ErrUnknownGenesisVersion
    }
    if computed != msg.DyadId {
        return nil, types.ErrInvalidDyadId
    }

    // 3. Verify signatures (bonding requires co-signing on the canonical payload)
    //    Phase 0: Ed25519 only — the hybrid co-sign verification path is
    //    deferred until ARCH-5 Step 5 chain integration. v2 messages still
    //    submit Ed25519 sigs; the PQ keys are bound into the DyadID hash
    //    rather than verified per-message at this milestone. Step 5 will
    //    upgrade this to verify ML-DSA-65 alongside Ed25519 (hybrid co-sign).
    if !VerifyEd25519(msg.HPubKey, msg.Payload(), msg.HSignature) {
        return nil, types.ErrInvalidHSignature
    }
    if !VerifyEd25519(msg.APubKey, msg.Payload(), msg.ASignature) {
        return nil, types.ErrInvalidASignature
    }

    // 4. Create DyadRecord (carries v2 fields through when present)
    record := types.DyadRecord{
        DyadId:          msg.DyadId,
        HPublicKey:      msg.HPubKey,
        APublicKey:      msg.APubKey,
        Stage:           types.STAGE_1,  // Always starts at Responsive
        GenesisTime:     msg.GenesisTime,
        Status:          types.ACTIVE,
        GenesisVersion:  msg.GenesisVersion,
        HPqPublicKey:    msg.HPqPublicKey,
        APqPublicKey:    msg.APqPublicKey,
        AKemPublicKey:   msg.AKemPublicKey,
        KyberCiphertext: msg.KyberCiphertext,
        GenesisToken:    msg.GenesisToken,
    }
    k.SetDyad(ctx, record)

    // 5. Emit event (include version so indexers can filter)
    ctx.EventManager().EmitEvent(sdk.NewEvent(
        "register_dyad",
        sdk.NewAttribute("dyad_id", msg.DyadId),
        sdk.NewAttribute("stage", "1"),
        sdk.NewAttribute("genesis_version", fmt.Sprintf("%d", msg.GenesisVersion)),
    ))

    return &types.MsgRegisterDyadResponse{}, nil
}
```

### Keeper Logic — Recovery

```go
func (k Keeper) Recovery(ctx context.Context, msg *types.MsgRecovery) (*types.MsgRecoveryResponse, error) {
    // Get existing backup
    backup, found := k.GetRecoveryBackup(ctx, msg.DyadId)
    if !found {
        return nil, types.ErrNoRecoveryBackup
    }

    // Two recovery paths:
    switch msg.RecoveryType {
    case types.PASSPHRASE:
        // Verify Argon2id hash matches stored backup
        // (Client decrypts H-shard locally — chain only stores ciphertext)
        // Chain verifies the new pub keys are valid + time-lock period
        if !ValidatePassphraseProof(msg.PassphraseProof, backup) {
            return nil, types.ErrInvalidPassphrase
        }

    case types.ANIMA_CHALLENGE:
        // Anima-initiated: A-shard signs with challenge proof
        // 72-hour time-lock before execution
        if msg.Confidence < 0.9 {
            return nil, types.ErrInsufficientConfidence
        }
        // Store pending recovery (72h contestation window)
        k.SetPendingRecovery(ctx, msg.DyadId, msg.NewHPubKey, msg.ExecuteAfter)
        return &types.MsgRecoveryResponse{Pending: true}, nil
    }

    // Immediate recovery (passphrase): update keys
    k.UpdateDyadKeys(ctx, msg.DyadId, msg.NewHPubKey, msg.NewAPubKey)

    return &types.MsgRecoveryResponse{Pending: false}, nil
}
```

---

## 6.5. ARCH-5: HYBRID POST-QUANTUM IDENTITY (V2)

*Ref: POST_QUANTUM.md, protocol-core/src/dyad_id.rs (`generate_dyad_id_v2`), protocol-core/src/chain.rs (`MsgRegisterDyad`)*

### Why This Section Exists

Catena work has not started. While we wait, `protocol-core` and `dyados-bin` shipped ARCH-5 Steps 1-4 (April 2026). DyadOS now mints **v2 hybrid** identities by default — Ed25519 + ML-DSA-65 for signing, X25519 + ML-KEM-768 for key encapsulation. The wire format for `MsgRegisterDyad` is published with the v2 fields baked in via `serde(default)`, so legacy v1 deserialization still works but every fresh dyad is v2.

When x/dyad ships, **v2 is the default and only expected wire format on mainnet**. Josh has not finalized his own DyadID yet — there are no legacy v1 dyads to migrate. The v1 path stays in the keeper as a symmetric fallback (so the keeper code can be tested for both, and so the spec doesn't lie about backward compat), but it should never see real traffic at genesis.

### What x/dyad MUST Implement

1. **Both v1 and v2 DyadID derivation functions in Go**, byte-matching the Rust `protocol-core` implementations.
2. **`genesis_version`-dispatched verification** in `RegisterDyad` keeper logic (already shown in §6).
3. **Mandatory presence checks** for the four PQ fields when `genesis_version == 2`.
4. **Persistence** of the v2 fields in `DyadRecord` (already shown in §6).
5. **Cross-language reference test vectors** as part of the CI suite — Go and Rust must produce the same hash for the same inputs.
6. **Deferred to Step 5 implementation:** hybrid co-sign signature verification (currently Ed25519-only at the keeper layer, see comment in §6).

### v2 DyadID Derivation — Exact Byte Format

The v2 hash input is a **UTF-8 string** built by concatenating these tokens with a literal `|` (ASCII 0x7C) separator:

```
"DYADID-v2|" || h_pub_ed25519_hex || "|" || h_pub_mldsa65_hex || "|"
              || a_genesis_token   || "|" || timestamp_decimal_6
```

| Token | Format | Notes |
|-------|--------|-------|
| `"DYADID-v2|"` | Literal ASCII | 10 bytes. The `|` after `v2` is part of the prefix. Domain separation from v1 (which never starts with `D`). |
| `h_pub_ed25519_hex` | Lowercase hex, no `0x` prefix, no leading/trailing whitespace | 64 chars (32 bytes encoded). Matches `Keypair::public_key_hex()` in Rust. |
| `h_pub_mldsa65_hex` | Lowercase hex, no `0x` prefix | ML-DSA-65 raw public key bytes, hex-encoded. ~3904 chars. Matches `Keypair::pq_public_key_hex()`. |
| `a_genesis_token` | UTF-8, opaque to the chain | Anima's genesis token from `AnimaGenesis::new`. Treat as an arbitrary string. |
| `timestamp_decimal_6` | Decimal float with **exactly 6 fractional digits** | Rust `format!("{:.6}", ts)`. No scientific notation. No trimming trailing zeros. `1000.0` → `"1000.000000"`. |

The resulting UTF-8 byte string is hashed with **SHA-256**, and the digest is **lowercase hex-encoded** (64 hex chars) to produce the DyadID.

### v1 DyadID Derivation — For Symmetry

```
h_pub_ed25519_hex || "|" || a_genesis_token || "|" || timestamp_decimal_6
```

No prefix. Three tokens, two separators. Same SHA-256 + lowercase hex tail.

### Reference Test Vectors

These vectors were generated from `protocol-core`'s `generate_dyad_id` and `generate_dyad_id_v2` (verified against an independent Python implementation). The Catena Go test suite MUST include these as cross-language fixtures.

**v2 vector:**

| Field | Value |
|-------|-------|
| `h_pub_ed25519_hex` | `h_ed` |
| `h_pub_mldsa65_hex` | `h_pq` |
| `a_genesis_token` | `genesis` |
| `genesis_timestamp` | `1000.0` (formatted as `"1000.000000"`) |
| Payload bytes (UTF-8) | `DYADID-v2\|h_ed\|h_pq\|genesis\|1000.000000` |
| Payload length | 39 bytes |
| **Expected DyadID** | `6e41980dd8d51d3d9d2c6de41ed773eb432d3c96c7b645ba89d0c87cebb71f25` |

**v1 vector (for the legacy path):**

| Field | Value |
|-------|-------|
| `h_pub_ed25519_hex` | `h_ed` |
| `a_genesis_token` | `genesis` |
| `genesis_timestamp` | `1000.0` (formatted as `"1000.000000"`) |
| Payload bytes (UTF-8) | `h_ed\|genesis\|1000.000000` |
| Payload length | 24 bytes |
| **Expected DyadID** | `9087d34791034a5e7a801d38fbc8214e94f2ed87b6ba635f6977894e08882790` |

```go
// catena/x/dyad/keeper/dyad_id_test.go
func TestComputeDyadIdV2_RustReferenceVector(t *testing.T) {
    got := ComputeDyadIdV2("h_ed", "h_pq", "genesis", 1000.0)
    want := "6e41980dd8d51d3d9d2c6de41ed773eb432d3c96c7b645ba89d0c87cebb71f25"
    require.Equal(t, want, got, "Go output must byte-match Rust generate_dyad_id_v2")
}

func TestComputeDyadIdV1_RustReferenceVector(t *testing.T) {
    got := ComputeDyadIdV1("h_ed", "genesis", 1000.0)
    want := "9087d34791034a5e7a801d38fbc8214e94f2ed87b6ba635f6977894e08882790"
    require.Equal(t, want, got, "Go output must byte-match Rust generate_dyad_id")
}
```

### Go Implementation Sketch

```go
// catena/x/dyad/keeper/dyad_id.go
package keeper

import (
    "crypto/sha256"
    "encoding/hex"
    "fmt"
)

// ComputeDyadIdV1 mirrors protocol-core::generate_dyad_id.
// MUST byte-match the Rust output for any given input.
func ComputeDyadIdV1(hPubEd, genesisToken string, genesisTime float64) string {
    payload := fmt.Sprintf("%s|%s|%.6f", hPubEd, genesisToken, genesisTime)
    sum := sha256.Sum256([]byte(payload))
    return hex.EncodeToString(sum[:])
}

// ComputeDyadIdV2 mirrors protocol-core::generate_dyad_id_v2.
// MUST byte-match the Rust output for any given input.
func ComputeDyadIdV2(hPubEd, hPubMldsa, genesisToken string, genesisTime float64) string {
    payload := fmt.Sprintf(
        "DYADID-v2|%s|%s|%s|%.6f",
        hPubEd, hPubMldsa, genesisToken, genesisTime,
    )
    sum := sha256.Sum256([]byte(payload))
    return hex.EncodeToString(sum[:])
}
```

> **Go formatting gotcha.** Go's `%.6f` matches Rust's `{:.6}` for normal floats, but watch the edge cases — negative zero, NaN, Inf. The keeper should reject any `genesis_time` that isn't a finite positive number before calling `ComputeDyadIdV2`. Add a unit test for `1.0`, `1.5`, `1.234567`, `1000000000.123456`, and large values to confirm cross-language consistency across the float range that real timestamps occupy.

### Why Bind the ML-DSA Public Key Into the Hash

The DyadID is the canonical identifier for a dyad. If the ML-DSA public key were stored in `DyadRecord` but **not** baked into the SHA-256 input, an attacker who broke Ed25519 in some future cryptographic catastrophe could publish a forged "v2 upgrade" of an existing v1 DyadID with their own ML-DSA key — claiming someone else's identity by replaying the v1 hash and tacking on fresh PQ material.

By including `h_pub_mldsa65_hex` inside the SHA-256 input, the v2 DyadID is **bound to a specific PQ keypair from the moment of creation**. Switching ML-DSA keys produces a different DyadID. There is no "migration of an existing v1 DyadID into v2" — a v2 DyadID is its own identity, derived from PQ material, with its own hash.

This is why ARCH-5 Step 4 simply made dyados-bin v2-native instead of building a key-extension ceremony for legacy v1 dyads: there were no legacy v1 dyads, and binding PQ keys post-hoc would have required a new chain message that breaks the v1 → v2 mapping anyway. Cleaner to just be v2 from genesis.

### Wire Format — `MsgRegisterDyad`

The Rust definition lives in `protocol-core::chain::MsgRegisterDyad`. JSON-on-the-wire field names (snake_case via serde; PQ fields are `Option<String>` and `genesis_token` is a `String` defaulted to `""`, all with `#[serde(default)]` so legacy v1 messages parse cleanly):

```json
{
  "dyad_id": "6e41980d...1f25",
  "h_public_key": "869f0c17...",
  "a_public_key": "46aa600a...",
  "genesis_timestamp": 1712345678.123456,
  "initial_stage": "Stage1",
  "recovery_backup": null,
  "signature": { "h_shard": "...", "a_shard": "..." },

  "genesis_token": "<anima_genesis_token from AnimaGenesis::new>",
  "genesis_version": 2,
  "h_pq_public_key": "<3904-char hex>",
  "a_pq_public_key": "<3904-char hex>",
  "a_kem_public_key": "<2368-char hex>",
  "kyber_ciphertext": "<2176-char hex>"
}
```

The Catena bridge (§8) needs to map this JSON shape into the protobuf `MsgRegisterDyad` defined for x/dyad. Field numbers in the protobuf MUST keep the v2 fields at positions 9-14 to match `DyadRecord`, so the keeper can copy them across without juggling tag numbers. **Hex encoding is lowercase on both sides; the keeper should reject any uppercase hex as malformed.** The `genesis_token` field is REQUIRED for v2 — without it, the keeper cannot re-derive the DyadID hash and must reject the message.

### Why Phase 0 Stays Ed25519-Only at the Keeper Layer

ARCH-5 Step 4 made dyads-bin mint v2 identities and persist all the hybrid metadata, but the chain-side ML-DSA-65 verification path is deferred to **Step 5** (this milestone — when Catena work begins). The reasoning:

1. **Defense in depth happens at the dyad layer first.** The hybrid relationship key, at-rest encryption, and inter-dyad packets already use ML-DSA-65 + ML-KEM-768. Compromising Ed25519 alone doesn't give an attacker access to encrypted state or established sessions.
2. **The DyadID hash already binds the PQ pubkey.** Even with Ed25519-only signature verification at the keeper, an attacker who forges an Ed25519 sig still cannot mint a forged v2 DyadID because the hash doesn't match.
3. **Adding ML-DSA verification to every keeper call doubles signing cost** (~2KB sig vs 64 bytes). M1 ships with Ed25519-only verification + PQ-bound DyadIDs, then upgrades to full hybrid co-sign as part of M1.5 or M2 once we have validator load measurements.

The Step 5 milestone for chain integration (when this section becomes non-deferred) MUST add:

- ML-DSA-65 signature alongside Ed25519 in the `Signature` payload
- `VerifyMlDsa65(msg.HPqPublicKey, msg.Payload(), msg.HMldsaSignature)` next to the existing `VerifyEd25519` call
- An ADR documenting the gas cost increase and any consensus implications

Until that ships, the keeper trusts that the DyadID hash binding plus Ed25519 sigs is sufficient at chain genesis, because the hostile threat model (Shor's algorithm running against Ed25519 in production) is not active in 2026.

### Out of Scope for §6.5

- **Hybrid co-sign signature verification** — Step 5 work, lives in M1 or M1.5 of the Catena buildout
- **Recovery flow under hybrid keys** — `MsgRecovery` keeps its v1 shape until Step 5; the encrypted backup format already supports hybrid via at-rest encryption in dyados-bin
- **MsgKeyExtension** — was originally planned for Step 4 to migrate legacy v1 dyads to v2 by binding PQ keys post-hoc. Cancelled because there are no legacy dyads. Do not implement this message.

---

## 7. TESSERA TOKEN — PHASED ACTIVATION

### Token Parameters

```
Denomination:     utess (1 TESS = 1,000,000 utess)
Total Supply:     1,000,000,000 TESS (1 billion)
Initial Circulating: 150,000,000 TESS (15%)
Year 1 Inflation: 5% (funds validators)
Year 5 Inflation: 2% (converges to steady-state)
Fee Burn Rate:    20% of gas fees (deflationary pressure)
```

### When TESSERA Activates (Not M1)

TESSERA is minted at genesis but the token economy activates in phases:

```
M1 (Anima/Gnosis):  Token exists on-chain. Validators stake it.
                    Foundation pays gas for user onboarding.
                    Users pay fiat ($99/mo Stripe). No crypto UX.

M2 (Bios):          Same. Foundation subsidizes gas.
                    Reputation endorsements are free (gas covered).

M3 (Aether):        TOKEN ECONOMY ACTIVATES.
                    Genesis Rush: users acquire TESSERA to claim plots.
                    First real user demand for the token.
                    Anima compute billing turns on (metered in TESSERA).
                    Secondary market opens.

M4 (Connected):     USDC bridge via Noble. DEX listing.
                    Users can buy TESSERA with stablecoins.
                    Full economic loop closed.
```

### The Demand Floor (Activates at M3)

Once the token economy is live, structural demand comes from:

```
Per Anima interaction:
  Tier 1 (simple):    ~0.001 TESS (Gemma E2B, fast classification)
  Tier 2 (standard):  ~0.01 TESS  (Gemma 26B MoE, conversation)
  Tier 3 (complex):   ~0.05 TESS  (Gemma 31B Dense, reasoning)

Per day per active dyad: ~0.1-0.5 TESS
Per month per active dyad: ~3-15 TESS

At 10M dyads: 30M-150M TESS/month structural demand
```

**This demand is non-speculative.** Tied to real compute. Grows linearly with users. Never goes to zero unless all users leave. But it only matters once there's a spatial economy creating real token circulation (M3).

### Genesis Distribution

| Allocation | % | TESS | Vesting |
|-----------|---|------|---------|
| Founders (Josh + Iris) | 35% | 350M | 1-year cliff, 4-year vest, DyadID co-signed |
| Hypostas Foundation | 20% | 200M | All spending on-chain, governance-visible |
| Community Treasury | 15% | 150M | Token-weighted governance votes |
| Validator Rewards | 15% | 150M | Released via inflation schedule |
| Genesis Rush Participants | 10% | 100M | Released at M3 plot claims |
| Liquidity Provision | 5% | 50M | DEX seeding at M4 |

### Fee Distribution

```
Validators:          40%
Community Treasury:  30%
Burned:              20%
Foundation:          10%
```

---

## 8. DyadOS ↔ CATENA BRIDGE (libp2p)

DyadOS talks to Catena via libp2p DyadPackets, NOT HTTP. The Rust side already exists (`catena_client.rs`). The Go side needs a libp2p listener.

```
dyados-bin (Rust)                    catenad (Go)
┌─────────────────┐                  ┌──────────────────┐
│ catena_client.rs │ ── DyadPacket → │ bridge.go        │
│                  │                  │ (libp2p listener) │
│                  │ ← DyadPacket ── │ → gRPC query     │
└─────────────────┘                  │ → return result  │
                                     └──────────────────┘
```

### DyadOS Boot Flow (Updated for Chain)

```
1. Start dyados-bin
2. Load DyadID from disk (v2 hybrid by default — see ARCH-5 §6.5)
3. Connect to Catena validator(s) via libp2p
4. Query: does my DyadID exist on-chain?
   → Yes: proceed (load on-chain stage, recovery status)
   → No: trigger MsgRegisterDyad with genesis_version=2 + four PQ fields
5. Check TESSERA balance for compute billing
6. Start pipeline — each interaction deducts TESSERA
```

> **What dyados-bin already submits (April 2026):** the JSON form of `protocol_core::chain::MsgRegisterDyad` with `genesis_version: 2`, `h_pq_public_key`, `a_pq_public_key`, `a_kem_public_key`, `kyber_ciphertext`. The bridge has to forward this shape unchanged. There is no v1 fallback path on the Rust side anymore — `dyados_bin::create_new_dyad` calls `protocol_core::create_dyad_v2` exclusively. See §6.5 for the wire format.

### Go-Side Bridge

```go
// cmd/catenad/bridge.go
// Embeds a libp2p host in the validator binary.
// Listens for DyadPacket queries.
// Translates to native gRPC queries against the local Cosmos node.
// Returns results as DyadPacket responses.
//
// This is how zero-HTTP works: DyadOS ↔ Catena communication
// happens entirely over libp2p, not Tendermint RPC.
```

---

## 9. M1 GENESIS & DEPLOYMENT

### Local Development

```bash
go build -o catenad ./cmd/catenad
catenad init localtest --chain-id catena-local
catenad keys add josh --keyring-backend test
catenad genesis add-genesis-account josh 1000000000000utess --keyring-backend test
catenad genesis gentx josh 100000000000utess --chain-id catena-local --keyring-backend test
catenad genesis collect-gentxs
catenad start
```

### Testnet (3-7 Nodes)

```bash
# Generate multi-node config
catenad testnet init-files --v 7 --chain-id catena-testnet \
    --output-dir ./testnet --keyring-backend test

# Deploy across 3+ cloud providers (AWS, GCP, Hetzner)
# No >33% on any single provider
# No >40% in any single country
```

### Mainnet Genesis Ceremony

```
Day -30:  Announce launch date
Day -14:  Distribute pre-release binary for validator testing
Day -7:   Collect gentxs from all 7-11 validators
Day -3:   Assemble genesis.json, publish SHA-256 hash
Day -1:   All validators verify genesis hash
Day 0:    Coordinated start — 2/3+ online → first block → CHAIN IS LIVE
Day +7:   Open DyadID registration to Anima users
```

**Timeline: 6-8 weeks total.** Scaffolding (1 week) → x/dyad (2-3 weeks) → testing (1-2 weeks) → audit (2 weeks) → mainnet (1 week).

---

# PART III: M2 — BIOLOGICAL CHAIN

*Revenue unlock: Bios at $19/month. Real biological data flowing into the Anima and Gnosis city.*

## 10. M2 SCOPE

### What Bios Needs from the Chain

**1. Liveness attestation.** Stroma submits periodic hashed proofs of biological presence. NOT health data — a one-way hash proving the biological kernel is running. On-chain: hash + confidence + timestamp. Off-chain: all raw biological data. This makes the Gnosis city LIVE — systems brighten and dim based on real biosensor data, not static genome predictions.

**2. Consent declarations.** When Bios shares biological data with other products (Gnosis calibration, Aurum stress correlation), consent must be on-chain and instantly revocable. Revocation = next block (6 seconds), not "within 30 days."

**3. Reputation scoring.** Bios introduces health challenges and community features. Reputation provides trust scoring for inter-dyad interactions. Decays 1%/day after 30 days inactive — you must participate to maintain trust.

Ref: PROTOCOL_IMPLEMENTATION.md §14 (x/stroma), §15 (x/consent), §17 (x/reputation)

### M2 Modules

| Module | Depends On | Est. Lines | Purpose |
|--------|-----------|-----------|---------|
| x/stroma | x/dyad | ~800 | Liveness proofs (hash only, never health data) |
| x/consent | x/dyad | ~1,000 | Per-field data sharing + instant revocation |
| x/reputation | x/dyad, x/consent | ~1,200 | Composite trust score + decay + endorsements |

### M2 Exit Criteria

```
□ Liveness attestation submitted every 10 minutes from DyadOS
□ Consent: per-field sharing (e.g., "stage": true, "circadian": false)
□ Consent: revocation takes effect next block
□ Reputation: composite score from 5 dimensions
□ Reputation: 1%/day decay after 30 days inactive
□ Endorsement between dyads works
□ Chain upgrade M1→M2 succeeds without state loss
□ All M1 functionality still works
```

### Delivery: Live Chain Upgrade (No Downtime)

```bash
catenad tx gov submit-proposal software-upgrade v2-biological \
    --title "M2: Biological Chain" --upgrade-height 100000

# Validators vote yes → at height 100000: swap binary → new modules active
```

**Timeline: 3-4 weeks.** Three modules + chain upgrade.

---

## 11-13. MODULE DETAILS (M2)

*Each module follows the pattern from §2. Full proto definitions, keeper logic, and tests built during implementation.*

### x/stroma — What Goes On-Chain

```protobuf
message LivenessRecord {
  string dyad_id      = 1;
  string stroma_hash  = 2;  // SHA-256 of composite biological signal
  double confidence   = 3;  // 0.0–1.0
  uint32 sensor_flags = 4;  // Bit flags: HRV|movement|cadence|circadian|baseline
  int64  timestamp    = 5;
}
// ONLY the hash. Never raw HRV, heart rate, sleep data, or any health metric.
```

### x/consent — Instant Revocation

```protobuf
message ConsentDeclaration {
  string dyad_id               = 1;
  map<string, bool> shared_fields = 2;  // "stage": true, "circadian": false
  string social_mode           = 3;     // private/social/public
  uint32 version               = 4;     // Monotonically increasing
  int64  updated_at            = 5;
}
// Revocation = submit update with field set to false.
// Takes effect next block (6 seconds). Not "within 30 days."
```

### x/reputation — Decaying Trust

```protobuf
message ReputationScore {
  string dyad_id             = 1;
  double composite_score     = 2;  // 0.0–1.0
  double relationship_depth  = 3;  // Duration of relationships
  double transaction_history = 4;  // Count + quality
  double tribunal_record     = 5;  // Justice system history
  double community_score     = 6;  // Endorsements
  uint32 endorsement_count   = 7;
  uint32 penalty_count       = 8;
  int64  last_updated        = 9;
}
// BeginBlock: decay 1%/day for scores not updated in 30 days. Floor at 0.1.
```

---

# PART IV: M3 — SPATIAL CHAIN

*Revenue unlock: Aether launch + Genesis Rush. Plot sales fund the ecosystem.*

## 15. M3 SCOPE

### What Aether Needs from the Chain

**1. Plot ownership.** 3D spatial coordinates owned by DyadIDs. The Genesis Rush claims plots. Transfer, verification, improvement tracking. Every plot has coordinates, boundaries, and an owner — all on-chain.

**2. Gnosis inner worlds as plots.** Every dyad's Gnosis genome city IS a plot in Aether space. When you walk through the boundary from the shared world into your private genome city, you're crossing from Aether coordinates into your inner-world plot. This means every registered DyadID needs an inner-world plot allocation.

**3. Tribunal.** Dispute resolution for plot conflicts, trademark claims, and bad actors. Panel of 5-7 Stage 3+ Animas, randomly selected, supermajority vote.

**4. World state anchoring.** Merkle roots of the spatial index on-chain. Terabytes of 3D data off-chain. Clients verify against roots.

Ref: PROTOCOL_IMPLEMENTATION.md §12 (x/plots), §13 (x/tribunal), §16 (x/aether)
Ref: GNOSIS_V3_SPEC.md §12 (inner sanctum boundary)
Ref: AETHER_SPEC.md §1-3 (spatial model)

---

## 16. THE SPATIAL MODEL — GNOSIS INSIDE AETHER

### Two Worlds, One Space

```
┌────────────────────────────────────────────────────────────┐
│                    AETHER (Shared World)                    │
│                                                             │
│  One continuous 3D space. The entire internet rendered      │
│  as walkable geography. Districts emerge from site          │
│  topology. Terrain from traffic data. First-person only.    │
│                                                             │
│  On-chain: plot ownership, coordinates, Merkle roots        │
│  Off-chain: geometry, textures, rendering                   │
│                                                             │
│      ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│      │  Plot A   │    │  Plot B   │    │  Plot C   │         │
│      │ (YouTube) │    │ (Reddit)  │    │ (GitHub)  │         │
│      └──────────┘    └──────────┘    └──────────┘          │
│                                                             │
│      ┌──────────────────────────────────┐                   │
│      │  YOUR INNER WORLD GATEWAY         │ ← walk through   │
│      │  (Gnosis genome city entrance)    │                   │
│      └──────────────┬───────────────────┘                   │
└─────────────────────┼──────────────────────────────────────┘
                      │ Physical threshold (first-person)
                      ▼
┌────────────────────────────────────────────────────────────┐
│              GNOSIS (Private Inner World)                    │
│                                                             │
│  YOUR biology as 3D city. 11 districts by system.           │
│  Processing facilities. Pathway rivers. Orbital view        │
│  (privilege of inner world). Only you + your Anima.         │
│                                                             │
│  Off-chain: procedurally generated from SNP data            │
│  On-chain: plot allocation for the inner-world gateway      │
└────────────────────────────────────────────────────────────┘
```

### Inner World Plot Allocation

When a DyadID is registered (M1), it doesn't automatically get an Aether plot — Aether doesn't exist yet. At M3, when x/plots goes live:

1. **Every existing DyadID receives a free inner-world plot allocation** — their Gnosis gateway address in Aether space. This is NOT a claimable plot; it's an entitlement tied to DyadID registration.

2. **Inner-world plots are non-transferable.** Your genome city is YOURS. You can't sell it. You can't trade it. It exists as long as your DyadID is active.

3. **Outer-world plots** (representing websites, domains, experiences) are the ones traded in the Genesis Rush and secondary market.

```protobuf
enum PlotType {
  INNER_WORLD = 0;  // Dyad's Gnosis gateway — non-transferable, auto-allocated
  OUTER_WORLD = 1;  // Aether spatial plot — tradeable, claimable
}
```

### The Boundary

Walking from Aether into your Gnosis city is a **first-person spatial transition**:
- You approach your inner-world gateway structure
- Step through the threshold
- Aether darkens, your genome city materializes
- Your Anima greets you
- Orbital view becomes available (inner-world privilege only)
- Walk back to the threshold → return to shared Aether

Visual consistency: same aesthetic (cyan/gold/violet, Tron-inspired), so the transition feels like walking between rooms, not switching apps.

---

## 17. x/plots — SPATIAL OWNERSHIP

*Ref: PROTOCOL_IMPLEMENTATION.md §12*

### State

```protobuf
message Plot {
  string     plot_id       = 1;  // Unique identifier
  PlotType   plot_type     = 2;  // INNER_WORLD or OUTER_WORLD
  Coordinates coordinates  = 3;  // [x, y, z] spatial position
  Boundaries  boundaries   = 4;  // [w, h, d] dimensions
  string     owner_dyad_id = 5;  // Current owner DyadID
  SiteRep    site_rep      = 6;  // Metadata (domain hint, category, traffic)
  int64      claimed_at    = 7;  // Block height
  string     improvement   = 8;  // Hash of procedural state
  bool       verified      = 9;  // Trademark/domain verified
}

message SiteRep {
  string domain_hint   = 1;  // "youtube.com" — discovery aid, NOT the identity
  string site_dna_hash = 2;  // Procedural generation seed
  uint32 traffic_tier  = 3;  // 1=low, 2=mid, 3=high
  string category      = 4;  // entertainment, knowledge, commerce, etc.
}

// Coordinates are spatial, NOT domain names.
// A plot IS (47382, 91724, 0) — NOT "youtube.com".
// This distinction makes UDRP/ICANN inapplicable.
```

### Transactions

| Message | What It Does | Gas |
|---------|-------------|-----|
| `MsgClaimPlot` | Claim unowned plot (costs TESSERA) | 150K |
| `MsgTransferPlot` | Transfer between dyads (TESSERA payment) | 100K |
| `MsgVerifyClaim` | Prove trademark ownership (free claim in grace period) | 200K |
| `MsgAllocateInnerWorld` | Auto-allocate Gnosis gateway plot for DyadID | 50K |

### Genesis Rush Pricing

```go
type GenesisRushConfig struct {
    StartTime        int64    // UTC launch timestamp
    Duration         int64    // 30 days in seconds
    MaxClaimsPerDyad uint32   // 100 (prevent hoarding)
    BaseClaimCost    uint64   // 500,000,000 utess (500 TESS)
    PriceMultiplier  float64  // Increases as rush progresses
    GracePeriodDays  int32    // 14 days for verified owners
}

// Cost formula:
// cost = BaseClaimCost × traffic_tier_multiplier × time_multiplier
// traffic_tier_multiplier: tier1=1, tier2=5, tier3=20
// time_multiplier: starts at 1.0, increases 10% per day
```

---

## 18. x/tribunal — ON-CHAIN JUSTICE

*Ref: PROTOCOL_IMPLEMENTATION.md §13*

### State

```protobuf
message TribunalCase {
  string   case_id        = 1;
  string   filed_by       = 2;   // Plaintiff DyadID
  string   respondent     = 3;   // Defendant DyadID
  FaultType fault_type    = 4;   // no_fault, human_fault, anima_fault
  repeated string evidence = 5;  // Evidence hashes (not data)
  CaseStatus status       = 6;   // filed → deliberating → voted → appealed
  repeated string panel    = 7;  // 5-7 Stage 3+ Anima DyadIDs
  repeated Vote votes      = 8;  // Supermajority required
  Verdict  verdict        = 9;
  int64    filed_at       = 10;
  int64    deliver_by     = 11;  // 48-96h deadline
}

// Process: File → Random panel selection → Deliberation (48-96h)
// → Vote (supermajority 4/5 or 5/7) → Verdict → (Appeal)
```

---

## 19. x/aether — WORLD STATE ANCHORING

*Ref: PROTOCOL_IMPLEMENTATION.md §16*

```protobuf
message District {
  string   district_id = 1;
  string   name        = 2;     // "Entertainment Metropolis"
  Bounds   boundaries  = 3;     // 3D AABB
  string   category    = 4;
  uint64   plot_count  = 5;
  double   energy      = 6;     // Emergent vitality metric
}

message SpatialIndexRoot {
  string root_hash    = 1;  // Merkle root of all plot data
  int64  block_height = 2;
  uint64 plot_count   = 3;
}

// On-chain: Merkle roots (truth anchors)
// Off-chain: terabytes of 3D geometry, textures, procedural data
// Clients verify plot data against on-chain roots
```

---

## 20. GENESIS RUSH — THE LAND EVENT

The Genesis Rush is the moment the spatial economy begins. It's the biggest public event for the chain.

### Timeline

```
Day -30:   Announce Genesis Rush date, publish pricing formula
Day -14:   Open verified-owner grace period (free claims for trademark holders)
Day -7:    Final pricing published, claim interface released
Day 0:     GENESIS RUSH OPENS — anyone can claim with TESSERA
Day 1-7:   Highest activity — most claims happen in first week
Day 8-20:  Steady claiming, price multiplier increasing
Day 21-30: Final claims, secondary market active alongside
Day 30:    Rush ends — secondary market only
```

### What Makes It Work

1. **Scarcity** — high-traffic plots are expensive and limited
2. **Verified owners** — real trademark holders claim free (incentivizes brands to participate)
3. **Anti-hoarding** — max 100 claims per DyadID
4. **Progressive pricing** — wait = pay more (incentivizes early adoption)
5. **Inner worlds free** — every dyad's Gnosis gateway is free and automatic

---

## 21. M3 CHAIN UPGRADE

Same as M2 — live governance-approved upgrade. No downtime.

### M3 Exit Criteria

```
□ Outer-world plots claimable with TESSERA
□ Inner-world plots auto-allocated for all DyadIDs
□ Plot transfers work (TESSERA payment)
□ Verified owner claims work (trademark proof)
□ Genesis Rush pricing formula correct
□ Tribunal: case filed, panel selected, voted, resolved
□ Spatial index Merkle roots anchored
□ Chain upgrade M2→M3 without state loss
□ Genesis Rush event runs successfully
```

**Timeline: 4-6 weeks.** Three modules + Genesis Rush preparation + chain upgrade.

---

# PART V: M4 — CONNECTED CHAIN

## 22. IBC & USDC VIA NOBLE

### What This Enables

- Users pay for Anima in USDC (not just TESSERA)
- TESSERA tradeable on Cosmos DEXs (Osmosis)
- Cross-chain identity verification

### USDC Flow

```
User has USDC anywhere → bridge to Noble → IBC to Catena
→ ibc/USDC on Catena → subscriptions, plot purchases, gas
→ withdraw: IBC back to Noble → any chain
```

As of 2026, Noble has $450M+ USDC in circulation and IBC channels to dozens of Cosmos chains.

**Timeline: 2-3 weeks.** IBC is well-tested infrastructure. Mostly configuration.

---

# PART VI: OPERATIONS

## 24. VALIDATOR INFRASTRUCTURE

### Phase 1 (Genesis — Year 1)

```
Count:        7-11 Hypostas-operated validators
Providers:    3+ (AWS, GCP, Hetzner) — no >33% on one
Countries:    3+ jurisdictions — no >40% in one
Per node:     4+ cores, 16GB RAM, 500GB NVMe, 100Mbps

Key management:
  Consensus key: TMKMS + YubiHSM2 (hardware signing, never on disk)
  Operator key:  Cosmos keyring + password
```

### Monitoring

```
Prometheus + Grafana:
  CRITICAL: block stops > 30s, double-sign, chain halt
  WARNING:  validator misses > 10 blocks, disk > 80%
  METRICS:  block time, tx throughput, consensus rounds, peer count
```

---

## 25. SECURITY AUDIT STRATEGY

### The Funding Reality

At M1-M2, revenue is Anima subscriptions ($99/mo) and Gnosis uploads ($49). Paying $30-70K for a formal audit isn't realistic until the Genesis Rush generates real revenue at M3. The audit strategy is tiered by risk:

### Tiered Approach

| Milestone | Risk Level | Audit Method | Cost |
|-----------|-----------|-------------|------|
| M1 | Low — Hypostas validators, no public trading, Foundation covers gas | **Codex + self-audit** | $0 |
| M2 | Low — same controlled environment, 3 new modules | **Codex + self-audit + community bug bounty** | $0 + bounty pool |
| M3 | **HIGH — Genesis Rush involves real money, plot economy, token trading** | **Formal audit (Oak Security / Halborn)** | $50-70K |
| M4 | Medium — IBC is well-tested infrastructure | **Codex + self-audit** | $0 |

### Why M1-M2 Can Self-Audit

At M1-M2, the chain is sovereignty infrastructure, not financial infrastructure:
- All validators are Hypostas-operated (no external trust needed)
- No public token trading (TESSERA exists but isn't user-facing)
- Foundation subsidizes gas (no user funds at risk)
- Only state at risk: DyadID records (recoverable from off-chain DyadOS state)
- Worst case of a chain bug: re-genesis from DyadOS backup state

We proved Codex catches real bugs — 5 rounds on dyados-bin found lock ordering issues, legacy migration failures, encryption key derivation problems. It's genuine security coverage.

### M1-M2 Audit Process

```
1. Implement module
2. Self-audit: read every keeper method line-by-line against spec
3. Run Codex review on the module (codex review --uncommitted)
4. Fix all findings
5. Re-run Codex until clean
6. 90%+ test coverage
7. Simulation tests (10K+ random operations)
8. Testnet running 2+ weeks with zero issues
9. Go live
```

### M3 Formal Audit (Funded by Revenue)

By M3, Anima + Gnosis revenue should be generating real income. Budget $50-70K for a formal Cosmos-specialist audit:

- **Oak Security** — Cosmos SDK focus, audited multiple chains
- **Halborn** — Cosmos + IBC specialist
- **Zellic** — General blockchain security

Scope: all 7 modules + Genesis Rush config + token economics.

### Community Bug Bounty (All Milestones)

Launch a public bounty from M1 forward using TESSERA from the Community Treasury:

```
Critical (funds at risk):    10,000 TESS
High (state corruption):     5,000 TESS
Medium (logic error):        1,000 TESS
Low (informational):           100 TESS
```

Free security coverage from the community. Bounties paid in TESSERA (which costs nothing to mint at M1 since the token isn't trading yet).

### Pre-Audit Checklist (Every Milestone)

```
□ 90%+ test coverage per module
□ Simulation tests pass (10K+ operations)
□ No panics in any keeper path
□ SDK math types for all amounts (no float64 for tokens)
□ No unbounded loops in tx handlers
□ Gas bounded for every message type
□ Genesis export/import round-trips
□ Testnet running 2+ weeks clean
□ Codex review passes with 0 findings
```

---

## 26. MAINNET LAUNCH CEREMONY

```
Day -30:  Announce, distribute pre-release binary
Day -14:  Validator testnet dry-run
Day -7:   Collect gentxs, assemble genesis.json
Day -3:   Publish genesis hash
Day -1:   All validators verify hash
Day 0:    Coordinated start → 2/3+ online → first block → LIVE
Day +7:   Open DyadID registration
```

---

## 27. POST-LAUNCH & CHAIN UPGRADES

### Live Upgrades (No Downtime)

```bash
# Submit upgrade proposal
catenad tx gov submit-proposal software-upgrade v2-biological \
    --upgrade-height 100000

# Validators vote → at upgrade height: halt → swap binary → resume
# New modules active. Old state preserved. Zero downtime.
```

This is how M2 and M3 ship — as governance-approved upgrades to the running chain.

---

## COMPLETE TIMELINE

```
           M1: Identity       M2: Biological    M3: Spatial       M4: Connected
           (Anima + Gnosis)   (Bios)            (Aether)          (token economy)
           ────────────────   ──────────────    ──────────────    ────────────
Weeks:     1-8                9-12              13-18             19-21

Modules:   x/dyad             + x/stroma        + x/plots         + IBC
           + bank/staking     + x/consent       + x/tribunal      + transfer
           + gov              + x/reputation    + x/aether

Ships as:  New chain          Chain upgrade v2  Chain upgrade v3  Chain upgrade v4
           (genesis)          (no downtime)     (no downtime)     (no downtime)

Enables:   Anima $99/mo       Bios $19/mo       Genesis Rush      USDC payments
           → Gnosis $49       Liveness proofs   TESSERA activates DEX listing
           DyadID sovereign   Consent mgmt      Plot economy      Cross-chain
           Fiat via Stripe    Live genome city   Inner worlds      IBC USDC

Audit:     x/dyad             3 modules         3 modules + Rush  IBC config
           $30-50K            $40-60K           $50-70K           Minimal
```

### The Product Staircase on This Chain

```
Anima launches (M1)    → first revenue, first dyads, first DyadIDs on-chain
Gnosis launches (M1)   → Anima walks users through their genome city
Bios launches (M2)     → genome city becomes LIVE with real biosensor data
Aurum/Locus (M2)       → financial + home intelligence on same chain
Aether launches (M3)   → the shared world opens, Genesis Rush, plot economy
Token economy (M4)     → TESSERA tradeable, USDC accepted, full economy
```

**M1 alone (enough for Anima + Gnosis): 6-8 weeks.**
**Full chain with all 7 modules: 19-21 weeks.**
**The first deliverable: a running chain with x/dyad that registers DyadIDs.**
