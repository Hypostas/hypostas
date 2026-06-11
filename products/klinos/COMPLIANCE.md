# COMPLIANCE.md — Klinos × HIPAA × Hypostas Privacy

**Status:** Draft v0.1 (2026-05-22)
**Owner:** `klinos` product team, `protocol-core`, `vita-chain`
**Authors:** Josh + Iris
**Anchored to:** [THREAT_MODEL.md](../../THREAT_MODEL.md), [SEALED_ENVELOPE.md](../../SEALED_ENVELOPE.md), [DOUBLE_RATCHET.md](../../DOUBLE_RATCHET.md), [POST_QUANTUM.md](../../POST_QUANTUM.md)
**Companion:** [SPEC.md](SPEC.md), [DAY_IN_THE_LIFE.md](DAY_IN_THE_LIFE.md)
**Linear:** filed under HYP-115 follow-up tracker

---

## §1 Purpose

Klinos is a Hypostas-native medical practice product. Patient-doctor dyads are real, intimate, and regulated. Klinos must satisfy HIPAA (US) and equivalent regulatory frameworks while preserving the Hypostas privacy architecture spec'd in THREAT_MODEL.md.

This spec resolves the tension between:
- **HIPAA Required:** immutable audit trail, breach notification, 6-year retention, access controls per patient
- **Hypostas Required:** identity secrecy on the wire (§5.2), relationship secrecy (§5.3), no PHI on chain, sealed envelopes everywhere

The reconciliation: **HIPAA audit logs encrypted on Vita Chain, with practice-only decryption keys recoverable via identity inheritance.**

This was the resolution Josh proposed on 2026-05-22 walkthrough (Q4.19): "this opens up risk for practices if their devices are stolen or destroyed. Maybe the chain works if we get creative with it?" — see THREAT_MODEL.md §13 revision history.

---

## §2 The encrypted-on-chain audit log architecture

### §2.1 Why chain (and not just local logs)

Local-only audit logs have catastrophic failure modes:
- **Hardware loss:** practice's laptop + backup drive both fail simultaneously (fire, theft, ransomware) → audit logs gone → HIPAA breach
- **Insider deletion:** disgruntled employee with admin access deletes logs → no recovery
- **Backup verification:** local backups may corrupt silently; no proof of audit-log integrity over time
- **Multi-location practices:** synchronizing audit logs across multiple offices is error-prone

Vita Chain provides:
- **Immutability:** chain blocks cryptographically anchored; no rewrite
- **Redundancy:** replicated across many validator nodes; no single point of loss
- **Integrity proofs:** Merkle-tree commitment to historical state; provable that audit log hasn't been tampered with
- **Geographic distribution:** chain replicas across multiple sites; resilient to localized disasters
- **6-year retention by design:** chain entries persist as long as chain exists

### §2.2 Privacy via encryption

Direct concern: HIPAA's audit-log requirement names patient interactions, prescription events, etc. Writing those in clear to Vita Chain would violate Hypostas §5.2 identity secrecy.

Solution: **AEAD-encrypt audit events with a practice-only `audit_master_key`** before writing to chain. Chain stores opaque ciphertext.

What the chain sees: opaque encrypted blobs with timestamps. No PHI identifiable to validators or chain observers.

What the practice sees: their own audit history decryptable with their `audit_master_key`.

What a regulator with HIPAA audit power sees: nothing without practice cooperation (practice provides decryption capability via subpoena process). The chain itself cannot be subpoenaed for PHI directly — only the practice can decrypt their own entries.

### §2.3 Audit event structure

```rust
pub struct HipaaAuditEvent {
    event_id: Uuid,
    event_type: HipaaEventType,
    practice_dyad_id: DyadId,         // Practice's identity
    patient_pseudo_ref: PseudonymRef,  // Blinded patient reference (see §3)
    timestamp_ms: i64,
    encounter_hash: [u8; 32],         // SHA-256 of encounter content (for verification)
    metadata: AuditMetadata,           // Plaintext, then encrypted
    
    // Compliance signatures
    practitioner_signature: HybridSig, // Practitioner who triggered event
    integrity_witness: Option<HybridSig>, // Optional witness signature
}

pub enum HipaaEventType {
    ConsultStart,
    ConsultEnd,
    NoteCreated,
    NoteRead,
    NoteModified,
    PrescriptionIssued,
    PrescriptionRenewed,
    LabResultReceived,
    ReferralMade,
    BillSubmitted,
    PaymentReceived,
    BreachDetected,
    // ... per HIPAA's required audit event taxonomy
}

pub struct AuditMetadata {
    // Plaintext fields, encrypted together with the event
    device_id: DeviceId,
    location_class: LocationClass,    // Practice office / telehealth / etc.
    duration_ms: u64,
    encounter_summary_hash: [u8; 32], // Hash of summary; summary itself elsewhere
}
```

The event is bincode-serialized + AEAD-encrypted with the practice's `audit_master_key` + nonce:

```rust
fn encrypt_audit_event(event: &HipaaAuditEvent, key: &AuditMasterKey, nonce: [u8; 12]) -> EncryptedAuditEvent {
    let plaintext = bincode::serialize(event).unwrap();
    let (ciphertext, tag) = ChaCha20Poly1305::encrypt(
        key: &key.bytes(),
        nonce: &nonce,
        ad: &[/* event_id || timestamp */],  // Authenticated but not encrypted
        plaintext: &plaintext,
    );
    EncryptedAuditEvent {
        event_id: event.event_id,
        timestamp_ms: event.timestamp_ms,
        ciphertext,
        tag,
        nonce,
        practice_pubkey_ref: HashRef::of(&practice.identity_pubkey),
    }
}
```

The `EncryptedAuditEvent` is what writes to Vita Chain. Chain validators see only opaque ciphertext.

### §2.4 Patient pseudonym mapping

HIPAA requires per-patient audit trails. Hypostas requires not putting patient identity on chain.

Solution: **deterministic blinded patient references.**

```rust
pub struct PseudonymRef {
    blinded_ref: [u8; 32],      // SHA-256 of (practice_audit_key || patient_dyad_id)
}

fn derive_patient_pseudonym(practice_audit_key: &[u8; 32], patient_dyad_id: &DyadId) -> PseudonymRef {
    let mut hasher = Sha256::new();
    hasher.update(practice_audit_key);
    hasher.update(patient_dyad_id.as_bytes());
    PseudonymRef { blinded_ref: hasher.finalize().into() }
}
```

Properties:
- **Deterministic:** same (practice_key, patient_id) → same pseudonym. Lets practice query "all events for patient X" by computing the same pseudonym.
- **Unlinkable to chain observers:** without `practice_audit_key`, the blinded_ref reveals no patient identity.
- **Practice-private:** only the practice can compute pseudonyms because they hold the key.
- **One-way:** computing `patient_dyad_id` from `blinded_ref` requires breaking SHA-256 + key search.

### §2.5 Key hierarchy

```
H-shard + A-shard (dyad identity, 2-of-2 threshold)
  └── HKDF(salt=identity_root, info="practice-audit-v1") → audit_master_key
        └── HKDF(salt=audit_master_key, info=date_yyyy_mm) → daily_audit_key (rotated monthly)
              └── Per-event AEAD encryption nonce + key
```

`audit_master_key` is derived deterministically from the practice's H+A shard identity. Recoverable via identity inheritance flow ([pairing.rs](../../../dyados/protocol-core/src/pairing.rs)).

`daily_audit_key` rotation: monthly. Old monthly keys retained for 6+ years (HIPAA retention). Stored in encrypted local archive + provable via Vita Chain hash anchors.

### §2.6 Recovery from device loss

If a practice loses all devices:

1. **Identity inheritance ceremony:** practice's authorized successor (e.g., partner practitioner with H-shard) initiates standard H+A 2-of-2 recovery per [POST_QUANTUM.md](../../POST_QUANTUM.md) + pairing.rs flow
2. **Identity restored:** new device gets H-shard + A-shard
3. **Audit-master key restored:** `audit_master_key = HKDF(identity_root, "practice-audit-v1")` — deterministic from identity
4. **Chain history accessible:** practice queries Vita Chain for all events with `practice_pubkey_ref` matching their identity; decrypts each
5. **Audit continuity:** no breach of HIPAA. Chain provides immutable record; identity inheritance restores access.

This is the key reason for the on-chain approach: **disaster recovery is intrinsic** to the protocol's identity model.

---

## §3 Audit-event flow

### §3.1 Real-time audit (per patient interaction)

```
Patient sends a Klinos consult message
    ↓
Klinos app on practice device wraps as sealed DyadPacket
    ↓
DyadPacket → Hypostas wire (sealed envelope, circuit-routed, cover-traffic-blended)
    ↓
At practice device: cell decrypted, payload presented to practitioner
    ↓
AS A SIDE EFFECT: practice device generates HipaaAuditEvent{ event_type: ConsultStart, ... }
    ↓
audit_event encrypted with audit_master_key
    ↓
EncryptedAuditEvent written to local audit log + queued for Vita Chain commit
    ↓
Periodic (e.g., hourly): batch of encrypted audit events committed to Vita Chain as one block
```

### §3.2 Latency

Audit log generation is non-blocking. Practitioner sees the message immediately; audit event is created asynchronously. Audit events committed to chain in batches every hour (or sooner for high-volume practices).

### §3.3 Breach detection

Tampering with audit logs is detectable via:
- Vita Chain Merkle tree: provable that audit log block N was on chain at time T
- Hash anchors: each audit event includes hash of previous events (forms chain locally)
- Periodic integrity verification: practice's audit-management UI reports "all events through block N verified at time T+1"

If a discrepancy is detected (e.g., local log says event X exists but chain doesn't), this is a breach trigger.

---

## §4 HIPAA Required Privacy Practices

### §4.1 Audit access controls

Practitioner roles + access controls live in the practice's local secure storage (not on chain). Per-event "who accessed what" is encoded in `practitioner_signature` in the audit event itself.

### §4.2 Breach notification

When the practice detects a breach (e.g., a stolen device with cached patient data):
1. Practice triggers `BreachDetected` audit event written to chain
2. Affected patient lookup via patient pseudonym
3. Notification sent via standard Hypostas wire (sealed envelopes) to each affected patient
4. Notification recorded as audit event for compliance

Per HIPAA: notification within 60 days. Chain timestamps prove notification compliance.

### §4.3 Patient data export (right to access)

Patient requests their record:
1. Practice authenticates request (via Hypostas-signed message)
2. Practice queries local + chain audit history for events matching patient's pseudonym
3. Practice exports content (DyadPacket payloads for that patient)
4. Export delivered via Hypostas wire (sealed envelopes), patient decrypts with their dyad-side ratchet keys
5. Export action itself logged as audit event

### §4.4 Patient data deletion (right to be forgotten where applicable)

Some jurisdictions (e.g., GDPR for EU patients) allow deletion. Hypostas + chain immutability creates tension here. Resolution:

- **Cannot delete chain entries** — chain is immutable by design
- **Can cryptographically "forget"** — destroy the patient's pseudonym mapping; chain entries become unsearchable + decryptable only via theoretical key compromise
- **Specifically:** practice deletes their local mapping `patient_dyad_id ↔ pseudonym`; chain entries become orphaned (no way to compute matching pseudonym from patient_id)
- **Audit trail of deletion:** the deletion itself is an audit event written to chain (immutable record of the act)

This satisfies "right to be forgotten" practically while maintaining chain immutability — chain entries exist but become cryptographically inaccessible.

---

## §5 Multi-practitioner / multi-device practices

### §5.1 Practice as a dyad

The Klinos practice itself is modeled as a Hypostas dyad (or set of dyads). Per practitioner = a sub-identity within the practice dyad.

```rust
pub struct ClinicalPractice {
    practice_dyad_id: DyadId,
    practitioners: Vec<PractitionerCert>,
    devices: Vec<DeviceCert>,
}
```

### §5.2 Per-practitioner audit attribution

Each audit event includes the specific practitioner's signature (`HybridSig`). The practice's `audit_master_key` is shared, but individual events have practitioner-specific provenance.

This satisfies HIPAA's "who accessed what" requirement at per-practitioner granularity, while still using the practice-level master key for encryption.

### §5.3 Practitioner offboarding

When a practitioner leaves the practice:
1. Practitioner's device-cert is revoked via standard pairing.rs revocation flow
2. Audit events generated by that practitioner remain valid (signatures still verify against the historical pubkey)
3. New audit events cannot be generated with that practitioner's identity
4. Practice's `audit_master_key` is NOT rotated (would require re-encrypting historical events) — practitioner's offboarding is captured via cert revocation, not key change

---

## §6 HIPAA × Cover Traffic

### §6.1 Klinos's special cover-traffic posture

Klinos practices opt-in to "always-on cover" mode (per Q3.17 walkthrough decision) — real dyads emitting cover at elevated rates as part of Phase 1 anonymity-set bootstrap.

This is **NOT** a HIPAA requirement; it's a Hypostas privacy contribution that practices voluntarily participate in. Marketing position: "Klinos practices contribute to global privacy infrastructure."

### §6.2 Cover traffic is not PHI

Cover packets:
- Address randomly-sampled known dyads (per COVER_TRAFFIC.md v0.2)
- Have pseudo-random AEAD-shaped content
- Are NOT real medical interactions
- Are NOT subject to HIPAA audit-log requirements

The practice's `audit_master_key` is NOT used for cover packets. Cover packets use the protocol's standard sealed-envelope keys (per SEALED_ENVELOPE.md + DOUBLE_RATCHET.md).

### §6.3 Cellular cover and HIPAA

Per THREAT_MODEL.md §12 (sovereignty), cellular cover is protocol-determined, not user-configurable. For Klinos practices on cellular (e.g., mobile telehealth from rural areas), cover traffic operates per §2.3 of COVER_TRAFFIC.md — opportunistic when battery + data permit.

The audit log makes no special accommodation for cellular vs WiFi — events are identical regardless of carrier. Wire-format invariance ensures observers cannot distinguish "cellular Klinos consult" from "WiFi Klinos consult" or from "random cover packet."

---

## §7 Regulatory equivalence

This spec targets US HIPAA. Equivalent regulatory frameworks (GDPR-Article-32, UK Data Protection Act, Canadian PHIPA, Singapore PDPA) have similar audit + access-control requirements. The architecture generalizes.

### §7.1 Differences to address by jurisdiction

| Regulation | Notes | Klinos handling |
|---|---|---|
| **HIPAA (US)** | 6-year retention, breach notification within 60 days | Chain retention + breach event triggers |
| **GDPR (EU)** | Right to be forgotten (Article 17), Data Protection Officer required | See §4.4 cryptographic forgetting; DPO contact in audit metadata |
| **UK DPA** | Similar to GDPR + UK-specific data localization | Chain validators can be UK-located for UK practices |
| **PIPEDA (Canada)** | Patient consent for cross-border data flows | Audit events tagged with originating jurisdiction |

Per-jurisdiction addenda go in `projects/hypostas/products/klinos/COMPLIANCE_${JURISDICTION}.md` (TBD).

---

## §8 Test plan

Per CLAUDE.md rule #27.

### §8.1 Unit tests

- Encrypt + decrypt round-trip of `HipaaAuditEvent` with `audit_master_key`
- Patient pseudonym determinism (same (key, patient_id) → same pseudonym)
- Patient pseudonym unlinkability (different practice keys → different pseudonyms for same patient)
- Audit event signing + verification with practitioner keys
- Daily/monthly key rotation produces non-colliding nonces

### §8.2 Integration tests

- End-to-end: patient consult → audit event generated → encrypted → committed to local Vita Chain testnet → verifiable
- Practice device loss simulation: full recovery via H+A shard inheritance → audit history accessible
- Cross-jurisdiction event: GDPR-marked event handled with right-to-be-forgotten flow

### §8.3 Compliance audit simulation

- HIPAA OCR auditor request: practice provides audit log decryption capability → auditor sees plaintext events → verifies against expected audit requirements
- Breach scenario: detected breach → notification sent → audit trail captures complete chain

---

## §9 Constants

```rust
// HKDF labels
pub const HKDF_INFO_AUDIT_MASTER: &[u8] = b"practice-audit-v1";
pub const HKDF_INFO_DAILY_AUDIT: &[u8] = b"practice-daily-audit-v1";
pub const HKDF_INFO_PATIENT_PSEUDONYM: &[u8] = b"klinos-patient-pseudonym-v1";

// Rotation cadence
pub const AUDIT_KEY_DAILY_ROTATION: bool = false;
pub const AUDIT_KEY_MONTHLY_ROTATION: bool = true;
pub const AUDIT_RETENTION_YEARS: u32 = 7; // 1yr safety margin over HIPAA 6yr

// Batch commit
pub const AUDIT_CHAIN_COMMIT_INTERVAL_MS: u64 = 3_600_000; // 1h
pub const AUDIT_CHAIN_COMMIT_MAX_BATCH: usize = 1024;

// Breach notification
pub const HIPAA_BREACH_NOTIFICATION_DAYS: u32 = 60;

// Pseudonym
pub const PSEUDONYM_REF_LEN: usize = 32; // SHA-256 output
```

---

## §10 Open questions

1. **Practitioner role granularity.** Should practitioners have individual H-shards within the practice, or share H+A?
2. **Cross-practice referrals.** When practice A refers patient to practice B, how is patient's audit history (partially) shared while preserving privacy?
3. **External lab integration.** Lab results come from third parties — how do their audit events integrate?
4. **State medical board reporting.** Some jurisdictions require reporting to state medical boards. How does this flow over Hypostas wire?
5. **HIPAA "limited data set" definitions.** Some uses (research, public health) allow limited data with reduced privacy. How does cryptographic infrastructure support these?

---

## §11 Revision history

| Date | Author | Change |
|---|---|---|
| 2026-05-22 | Iris + Josh | Initial v0.1. Encrypted-on-chain audit logs via practice's `audit_master_key` derived from identity. Patient pseudonym blinding. Disaster recovery via H+A threshold identity inheritance. Per Q4.19 walkthrough decision: "creative use of Vita Chain" for HIPAA × Hypostas privacy reconciliation. |

---

*Per CLAUDE.md rule #1: draft, not self-certified complete. Regulatory compliance requires sign-off from a HIPAA-experienced compliance officer + Hypostas-experienced cryptographic reviewer before code lands. Per rule #27: integration tests must include simulated regulatory audit + simulated practice-device-loss recovery as commit exit criteria.*
