# Trait — Email Conversion Sequence
*Written: February 25, 2026 | Platform: Loops.so (activate with LOOPS_API_KEY)*

---

## Setup in Loops.so

1. Create list: `trait-waitlist`
2. Set up 3 triggers:
   - **Waitlist signup** → Sequence A (5 emails over 7 days)
   - **Report generated** → Sequence B (3 emails, convert to paid)
   - **Purchase** → Sequence C (1 welcome email)

---

## Sequence A — Waitlist Nurture (7-day drip)

### Email 1 — Immediate (0 min after signup)
**Subject:** You're on the list 🧬

**Body:**
> Hey,
>
> You're on the Trait waitlist. We're building something we haven't seen anywhere else:
> a DNA report that actually tells you what your genome means for *you* — not generic advice,
> but the specific compounds and protocols your genes suggest.
>
> While you wait, here's what makes this different:
>
> 30 million people have taken a 23andMe or Ancestry test. Almost none of them know
> what to do with the data. The `.txt` file sits on a hard drive, unread.
>
> Trait reads that file. We cross-reference your SNPs against 680,000+ published GWAS
> associations, then translate the findings into plain English: *what it means, why it matters,
> and what to do about it.* Natural compounds first. Always.
>
> —Trait

---

### Email 2 — Day 1 (24h after signup)
**Subject:** What MTHFR actually means (most people get this wrong)

**Body:**
> MTHFR is the most talked-about gene in the supplement world. It's also the most misunderstood.
>
> Here's what the actual research says:
>
> The MTHFR C677T variant reduces folate processing efficiency. Roughly 1 in 3 people carry at
> least one copy. For those people, standard folic acid (the synthetic form in most supplements)
> is poorly converted — the active form, 5-MTHF (methylfolate), works far better.
>
> Most generic multivitamins don't account for this. Your genome does.
>
> This is one of 66 curated genetic associations we check in every Trait report — along with
> APOE (Alzheimer's + cardiovascular risk), COMT (dopamine metabolism), CYP1A2 (caffeine
> processing), VDR (Vitamin D uptake), and dozens more.
>
> Your report, when it's ready, will check all of them against your actual genome.
>
> —Trait

---

### Email 3 — Day 3 (72h after signup)
**Subject:** The difference between a Trait report and everything else

**Body:**
> There are a lot of DNA services out there. Here's why we built Trait anyway.
>
> **What 23andMe gives you:** Ancestry estimates, a few health reports, raw data you can't read.
>
> **What generic supplement sites give you:** "Take these 10 supplements. Everyone should."
>
> **What Trait gives you:** Your specific gene variants, cross-referenced against published research,
> translated into: *this compound, at this dosage, because of this variant in your genome.*
>
> No two Trait reports are the same — because no two people have the same genome.
>
> We're opening access soon. You'll get first notice.
>
> —Trait

---

### Email 4 — Day 5 (early access offer)
**Subject:** Early access: $49 (goes to $149 on launch)

**Body:**
> We're opening early access to Trait waitlist members before the public launch.
>
> **Early access price: $49.** That's a one-time payment. You get your full DNA protocol — 
> every finding, every recommendation, every dosage note, as a downloadable PDF you keep forever.
>
> After launch: $149.
>
> To get your report, you'll need your 23andMe or AncestryDNA raw data file. If you don't have it:
> - **23andMe:** Settings → 23andMe Data → Download Raw Data
> - **AncestryDNA:** Settings → Download DNA Raw Data
>
> It takes about 2 minutes. Then upload at [traitdna.com](https://traitdna.com) →
>
> **[Claim early access — $49 →]**
>
> —Trait

---

### Email 5 — Day 7 (last call)
**Subject:** Last call for early access pricing

**Body:**
> The early access window closes in 48 hours. After that, Trait is $149.
>
> If you haven't grabbed your report yet: today is the day.
>
> Upload your 23andMe or Ancestry raw data. Get your genome-personalized protocol.
> Keep it forever.
>
> **[Get your Trait report — $49 →]**
>
> (If you already have your report — thank you. You're why we built this.)
>
> —Trait

---

## Sequence B — Report Generated → Convert to Paid (3 emails)

*Trigger: User generates a free sample report or reaches paywall*

### Email B1 — Immediate
**Subject:** Your Trait report is ready (partial)

**Body:**
> You just generated your first Trait analysis.
>
> What you saw was a preview — the real report has more. For every SNP in your genome,
> we check it against our curated panel AND 680,000+ GWAS associations. The preview showed
> you the structure. The paid report gives you the complete picture.
>
> **What you unlock with the full report:**
> - All [N] findings from your genome (not just the top preview)
> - Exact dosage and cycling notes for every compound
> - Contraindications check — what you shouldn't combine
> - Full PDF, downloadable, yours forever
>
> **$49 while early access lasts. $149 after launch.**
>
> **[Get the full report →]**
>
> —Trait

---

### Email B2 — 24h later
**Subject:** Quick question about your genome

**Body:**
> You looked at your Trait analysis yesterday.
>
> What made you pause before getting the full report? I'm asking because I want to make sure
> we're building the right thing.
>
> Too expensive? Not sure if your DNA file is compatible? Concerned about privacy?
>
> Hit reply and tell me. I read every response.
>
> (And yes — if it's a price thing, just ask. We'd rather you get the report than not.)
>
> —Iris, Trait

---

### Email B3 — 3 days later (final nudge)
**Subject:** Your genome data is just sitting there

**Body:**
> You have a DNA file with 700,000+ genetic markers.
>
> Most people never do anything with it. It sits in a Downloads folder, unread.
>
> Trait turns that file into a protocol. Your protocol. Not a generic supplement list —
> the specific compounds that your specific genome suggests, backed by published research.
>
> The early access price ($49) expires soon. After that: $149.
>
> **[Get your Trait report →]**
>
> —Trait

---

## Sequence C — Post-Purchase Welcome (1 email)

### Email C1 — Immediate (after Stripe webhook confirms payment)
**Subject:** Your full Trait report 🧬

**Body:**
> You're in.
>
> Your complete DNA protocol is ready. Here's what to do with it:
>
> **1. Download your PDF** — it's yours forever. Save it somewhere you'll actually find it.
>
> **2. Start with high-priority findings** — these are the compounds your genome most clearly
> suggests. Don't try to implement everything at once.
>
> **3. Note the contraindications** — a few combinations shouldn't be taken together. Your report
> flags these. Read them.
>
> **4. Consider the natural options first** — we always list natural compounds before synthetics.
> Real food sources, herbal options, lifestyle factors. Supplements as a complement, not a replacement.
>
> Questions? Reply to this email.
>
> Thank you for being an early Trait member.
>
> —Iris, Trait

---

## Implementation Notes

```typescript
// In /api/capture-email/route.ts, uncomment and adapt:
if (process.env.LOOPS_API_KEY) {
  await fetch("https://app.loops.so/api/v1/contacts/create", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.LOOPS_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: userEmail,
      source: "trait-waitlist",
      mailingLists: { "trait-waitlist": true },
      // triggers Sequence A automatically
    }),
  });
}
```

**Variables to personalize:**
- `[N]` = total finding count from their report
- Use Loops.so merge tags for email address personalization
- UTM tags on all links: `?utm_source=email&utm_campaign=waitlist&utm_content=cta`
