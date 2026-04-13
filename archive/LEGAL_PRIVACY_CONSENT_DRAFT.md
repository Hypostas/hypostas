# Gnosis — Legal/Privacy/Consent Draft (Launch v1)

**Date:** 2026-03-07  
**Status:** Draft for founder review (not legal advice)

---

## 1) Core Data Principle (Public Positioning)

**Canonical claim:**

> Your raw DNA file stays on your device by default.  
> If you enable cloud features, we only process and store the minimum interpreted data needed to provide those features.

### Language we should avoid
- “Your DNA never leaves your device” (too broad once cloud AI/sync exists)

### Language we should use
- “Your raw DNA file never leaves your device by default.”
- “Optional cloud features process derived interpretation data, not your full raw file.”

---

## 2) Data Ownership + License Model (Terms)

**Recommended model:**
- User owns their personal data.
- User grants Gnosis a limited license to process/store data for service delivery.

**Draft Terms clause:**

> You retain ownership of your personal data. By using the Service, you grant Gnosis a worldwide, non-exclusive, revocable license to process your submitted and derived data solely to operate, maintain, secure, and improve the Service, subject to your privacy settings and applicable law.

**Critical addition:**

> If you revoke consent or delete your account, we will delete or de-identify your personal data as described in our Privacy Policy. We may retain anonymized, aggregated insights that cannot reasonably identify you.

---

## 3) Opt-Out / Deletion Policy (Moat-safe + compliant)

When user opts out or deletes account:

### Must delete / disable
- Account-linked interpreted profile
- Any identifiable report payloads
- Sync links between Gnosis and Anima identity
- Any training data examples tied to user identity

### May retain
- Irreversibly anonymized aggregate stats
- Population-level feature distributions
- Model weights and learned parameters not reasonably re-identifiable
- System logs needed for security/compliance retention windows

**Draft policy line:**

> We may retain anonymized, aggregated, and non-identifiable statistical information and model-level learnings after account deletion or consent withdrawal, provided such information cannot reasonably be linked back to you.

---

## 4) Consent Tiers (Product UX)

### Tier A — Local Only (default)
- Raw DNA local processing only
- No cloud AI synthesis
- No Anima sync

### Tier B — Cloud Features
- Enables cloud synthesis/chat features
- Uses minimized interpreted payloads
- Clear explanation of what is transmitted

### Tier C — Model Improvement (optional, separate toggle)
- Explicit opt-in only
- De-identified contribution for quality improvement
- Revocable at any time

---

## 5) “What is Shared” Transparency Panel

Before user enables cloud features, show exact fields:
- Archetype + confidence
- Derived trait flags
- Protocol recommendations + confidence
- Blood confirmations (if added)
- Excludes full raw DNA file

**CTA copy:**
- `Enable Cloud Features`
- `Keep Local-Only`

---

## 6) Suggested Privacy Policy Copy (Ready to Adapt)

### Data We Process

> We process two categories of information:
> 1) **Raw genomic input** (your uploaded DNA file), which is processed locally by default.
> 2) **Derived interpretation data** (e.g., trait/protocol outputs), which may be processed in cloud services only when you enable cloud features.

### Data Control

> You can use Gnosis in local-only mode. You can also enable or disable cloud features at any time in settings. Disabling cloud features stops new cloud processing.

### Deletion and Retention

> When you request deletion, we delete account-linked personal data and disable your profile. We may retain anonymized, aggregated, and non-identifiable statistics for analytics, safety, and model quality.

---

## 7) Suggested In-App Consent Copy

### Cloud Features Modal

**Title:** Enable Cloud Features?

**Body:**
> Your raw DNA file remains local by default. To enable AI synthesis and Anima sync, Gnosis will process a minimized interpreted profile in cloud services.

**What we send:**
- Derived trait and protocol outputs
- Confidence scores
- Optional blood marker confirmations

**What we do not send:**
- Your full raw DNA file by default

Buttons:
- `Enable Cloud Features`
- `Keep Local-Only`

Checkbox (optional):
- `I also consent to de-identified model improvement` (off by default)

---

## 8) Immediate Implementation Checklist

1. Update `app/privacy/page.tsx` copy to new claim language.
2. Add `/terms` page with ownership/license + retention sections above.
3. Add consent toggles in settings:
   - local-only / cloud features / model-improvement
4. Add a data-sharing preview panel before enabling cloud features.
5. Add delete workflow:
   - delete personal profile data
   - keep only non-identifiable aggregate data
6. Add audit events:
   - consent_granted, consent_revoked, deletion_requested, deletion_completed

---

## 9) Why This Preserves Competitive Moat

- You keep the strongest trust claim (raw file local by default).
- You preserve Gnosis→Anima pipeline via explicit consented derived sync.
- You legally preserve durable value through anonymized aggregates/model learnings even after churn.
- You avoid “data ownership” language that invites regulatory and reputational risk.

---

If approved, next step is to patch `app/privacy/page.tsx` + scaffold `/terms` + add consent schema in code.