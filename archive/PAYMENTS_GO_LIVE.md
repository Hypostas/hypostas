# Gnosis — Activate Real Payments
*Written by Iris — March 9, 2026*

Everything is built. Stripe checkout, webhook handler, payment confirmation emails, annual upsell — all coded and tested. The only thing standing between Gnosis and real revenue is 3 env vars in Vercel and a webhook registration.

This takes ~20 minutes. Here's the exact sequence.

---

## What's Ready

- ✅ Stripe checkout (one-time $29 + annual $49) — `/api/checkout`
- ✅ Webhook handler — `/api/webhook`
- ✅ Payment confirmation emails (with RESEND_API_KEY)
- ✅ Report unlock on successful payment
- ✅ Attribution tracking (source, report mode, audience)
- ✅ Annual upsell post-purchase
- ✅ Price IDs already created: standard + annual

**Local dev:** Fully working with real Stripe keys in `.env.local`  
**Production:** Running in **mock mode** — no real payments yet

---

## Step 1 — Add Missing Env Vars to Vercel (10 min)

Go to: **Vercel → gnosis project → Settings → Environment Variables**

Add these 4 variables (all environments: Production + Preview + Development):

| Variable | Where to get it | Notes |
|----------|-----------------|-------|
| `STRIPE_SECRET_KEY` | Stripe Dashboard → API Keys → Secret key | Use `sk_live_...` for prod |
| `STRIPE_PRICE_STANDARD` | Stripe Dashboard → Products → Gnosis Full Report → Price ID | Already created: `price_1T5yKFCozMCZ3FNDlSvxtXPa` |
| `STRIPE_PRICE_ANNUAL` | Stripe Dashboard → Products → Gnosis Annual → Price ID | Already created: `price_1T5yKhCozMCZ3FNDf4t1lWUe` |
| `STRIPE_WEBHOOK_SECRET` | See Step 2 | Get this AFTER registering webhook |
| `ANTHROPIC_API_KEY` | console.anthropic.com | Optional — AI Synthesis tab; if missing, Synthesis shows mock narrative |
| `RESEND_API_KEY` | resend.com → API Keys | Optional — enables confirmation emails |

**STRIPE_SECRET_KEY:** If you've already been using live mode in local dev, this is the same key. If you only have test key locally (`sk_test_...`), get the live key from Stripe Dashboard.

---

## Step 2 — Register Stripe Webhook (5 min)

1. Go to: **Stripe Dashboard → Developers → Webhooks → Add endpoint**
2. **Endpoint URL:** `https://gnosis.hypostas.com/api/webhook`
3. **Events to listen to:**
   - `checkout.session.completed`
   - `payment_intent.payment_failed`
   - `customer.subscription.deleted`
4. Click **Add endpoint**
5. Copy the **Signing secret** (`whsec_...`)
6. Add it to Vercel as `STRIPE_WEBHOOK_SECRET`

---

## Step 3 — Trigger Vercel Redeploy (2 min)

After adding all env vars:
1. Go to **Vercel → gnosis → Deployments**
2. Click the latest deployment → **Redeploy**
3. Wait ~2 minutes

---

## Step 4 — Test One Real Payment (5 min)

1. Upload your genome file at `https://gnosis.hypostas.com`
2. Click **Unlock Full Report** on any locked finding
3. Complete checkout with a real card (or use Stripe's test card `4242 4242 4242 4242` if you only set test keys)
4. Verify: report unlocks, webhook log shows `Payment confirmed`, email arrives (if RESEND set)

---

## Optional: Set Up Resend for Confirmation Emails

1. Go to **resend.com** → Create account → API Keys → New API Key
2. Add to Vercel as `RESEND_API_KEY`
3. Current sender: `noreply@gnosis.hypostas.com` (may need to verify domain in Resend)

The email template is already written in `app/lib/payments.ts` — sends "Your Gnosis report is unlocked" with a link back to the report.

---

## Revenue Projection Once Live

With zero marketing (organic only, existing SEO pages):
- **23andMe alternative page** + 3 other SEO pages live and indexed
- Conversion at 1%: 100 visitors/day → 1 paid @ $29 = $870/month
- Conversion at 2%: → $1,740/month
- With Product Hunt launch: spike to 1,000+ visitors in first 48h

**This is the quickest path to first dollar.** No code changes needed — just the env vars.

---

## What's NOT Required (Already Done)

- ❌ Stripe npm package — already installed (`stripe` in package.json)
- ❌ Checkout UI — already built across all report tabs
- ❌ Success page — `/success` route exists and handles unlock
- ❌ Annual upsell — wired into post-purchase flow
- ❌ Price creation — prices already exist in Stripe

---

*Next revenue unlock after this: Pulse PyPI + Product Hunt (separate blocker — needs Josh's PyPI account).*
