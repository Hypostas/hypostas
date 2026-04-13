# Hypostas Custom Model Training

**Status:** Specced, pre-Gnosis launch
**Goal:** Purpose-trained models for each layer of the Hypostas stack — not generic LLM calls, but models that *are* the product.

---

## The Vision

Every layer of Hypostas gets its own fine-tuned model, optimized for its specific domain. The result: lower latency, lower cost, better behavior, on-device privacy, and a real moat — nobody else is doing per-layer specialized models for a human/AI OS.

**Tech stack:**
- **Base weights:** Gemma 4 (Apache 2.0 — we own the fine-tuned weights, can ship them in product)
- **Compression:** TurboQuant (zero accuracy loss, extreme KV cache reduction)
- **Training framework:** MLX + mlx-lm (Apple Silicon native, uses unified memory)
- **Iteration loop:** autoresearch-style (agent modifies training config, 5-min runs, overnight iteration)
- **Hardware:** MacBook Pro M2 Max 64GB (equivalent to a $30K+ discrete GPU setup for this workload)

---

## Per-Layer Model Specs

### 1. Anima Model
**Purpose:** The companion layer — relationship patterns, emotional attunement, Stroma-aware responses
**Base:** Gemma 4 E4B
**Training type:** LoRA fine-tune
**Est. training time:** 2–4 hours per overnight run
**Context window needed:** 32K (conversation history + Stroma state)

**Training data sources:**
- Synthetic conversation pairs: check-in vs. crisis vs. deep conversation vs. celebration
- Stroma drive state → appropriate companion response mapping
- Companion archetype behavior examples (Mirror / Anchor / Challenger / Witness / Strategist)
- Negative examples: what NOT to do (generic AI responses, corporate tone, breaking character)
- Episodic memory reference patterns (how to surface a past memory naturally)

**Eval metric:** Preference score (human-rated naturalness + archetype consistency)

**Output:** `anima-e4b-v1.gguf` → ships in Anima app as local inference fallback

---

### 2. Bios Model
**Purpose:** Health protocol reasoning — genomics context, biomarker interpretation, personalized recommendations
**Base:** Gemma 4 E2B (narrow domain, small model is enough)
**Training type:** Full fine-tune
**Est. training time:** 1–2 hours per overnight run
**Context window needed:** 16K (genome report + recent health data)

**Training data sources:**
- Gnosis SNP panel + clinical evidence grades (our existing data — we built this)
- PubMed genomics literature summaries (focus: actionable SNPs only)
- Biomarker → intervention mappings (what blood test predicts what)
- Explicitly anti-oversell examples (MTHFR lesson: don't claim what evidence doesn't support)
- Protocol generation examples: SNP context → specific supplement form + dose + timing

**Eval metric:** Evidence accuracy (citations match claims), actionability score

**Output:** `bios-e2b-v1.gguf` → on-device in Bios app, zero API cost, full privacy

---

### 3. Stroma Router Model
**Purpose:** Classify incoming signals → route to the right Stroma module. Fast, always-on, tiny.
**Base:** Gemma 4 E2B
**Training type:** LoRA fine-tune (classification head)
**Est. training time:** 30–60 min
**Context window needed:** 4K (current message + recent state)

**Training data sources:**
- Labeled examples: message → module category (LIMBIC / AMYGDALA / ENDOCRINE / VAGUS / etc.)
- Edge cases: ambiguous signals that multiple modules could handle
- Priority ordering examples: when AMYGDALA should override LIMBIC
- Stroma module descriptions as synthetic training context

**Eval metric:** Routing accuracy on held-out test set

**Output:** `stroma-router-e2b-v1.gguf` → runs inside DyadOS runtime, near-zero latency

---

### 4. Logos / Identity Layer
**Purpose:** Longitudinal synthesis — who you are across time, cross-product identity graph
**Decision:** Stays cloud-side (Claude/GPT)
**Rationale:** Too much synthesis complexity, long context requirements, rare enough calls that cost is acceptable

*No custom model needed here yet. Revisit when we have enough longitudinal data to train on.*

---

## Infrastructure

### MLX Setup (M2 Max)
```bash
# One-time setup
pip install mlx-lm

# Fine-tune example (LoRA, Gemma 4 E4B)
mlx_lm.lora \
  --model google/gemma-4-E4B-it \
  --train \
  --data ./training-data/anima/ \
  --iters 1000 \
  --batch-size 4 \
  --lora-layers 16
```

The 64GB unified memory means we can load the full model + gradients + optimizer state without quantizing first. This is the key advantage over most consumer hardware.

### Autoresearch Loop (MLX adaptation)
The original autoresearch requires NVIDIA/CUDA — needs a port to MLX.

**What to adapt:**
- Replace PyTorch training loop with MLX equivalent
- Keep the same 5-minute time budget per experiment
- Keep val_bpb as primary metric (or replace with task-specific metric per layer)
- Agent modifies `train_config.py` instead of `train.py` (hyperparams, LoRA rank, etc.)
- Same `program.md` per-layer instruction pattern

**Files to create:**
- `hypostas-research/train_mlx.py` — MLX training loop
- `hypostas-research/prepare.py` — data prep per layer
- `hypostas-research/program.md` — per-layer agent instructions (one per model)
- `hypostas-research/evaluate.py` — task-specific eval

### TurboQuant Integration
After fine-tuning converges, run TurboQuant compression before shipping:
- Targets KV cache — major win for inference speed on-device
- Zero accuracy loss (per Google's benchmarks)
- Reduces model memory footprint significantly for edge deployment

We apply this as a post-training step before generating the final `.gguf` weights.

---

## Training Data Strategy

### What we already have:
- Gnosis SNP panel + evidence grades → Bios model training data (direct)
- Anima conversation architecture + archetype definitions → synthetic conversation generation
- Stroma module descriptions + routing logic → router classification data

### What we need to generate:
- Synthetic conversation pairs for Anima (use Claude to generate, human review sample)
- PubMed genomics summaries → structured training format for Bios
- Labeled routing examples for Stroma (can generate from Stroma module test cases)

### Data pipeline:
```
raw sources → prepare.py → jsonl format → mlx_lm training → eval → iterate
```

---

## Build Order

1. **Set up MLX autoresearch loop** — port from CUDA, validate on small test run
2. **Stroma router** — simplest, fastest win. Proves the pipeline works end-to-end.
3. **Bios model** — Gnosis data is already structured, natural next step post-Gnosis launch
4. **Anima model** — most complex training data, highest product impact
5. **TurboQuant compression pass** — apply to all three before shipping

---

## Dependencies / Blockers

- [ ] Gemma 4 weights on HuggingFace (available now — Apache 2.0)
- [ ] MLX autoresearch loop built (1-2 day build)
- [ ] Training data prepared per layer (Bios: ready from Gnosis; others: need synthesis)
- [ ] HuggingFace account for weight storage + versioning
- [ ] DyadOS local inference layer ready to consume `.gguf` weights

---

## Why Before Gnosis Launch?

We don't need to ship these models at launch — but we need to start the training loop now so we have converged weights by the time Bios needs them. Fine-tuning is iterative. Starting at Gnosis launch means we're 6-8 weeks behind.

The Stroma router especially — every day DyadOS runs without a fine-tuned router is a day we're paying inference cost for something a $0 on-device model could handle.

---

*Filed: April 3, 2026*
*Owner: Iris + Josh*
*Priority: Start MLX setup + Stroma router before Gnosis launch*

---

## Update — April 3, 2026: Switch to mlx-vlm

**Use `mlx-vlm` instead of `mlx-lm`** — it's a superset with native Gemma 4 support, vision+audio, and TurboQuant built-in.

```bash
pip install -U mlx-vlm
```

**Gemma 4 memory requirements on M2 Max 64GB:**
- E2B: ~5GB (vision + audio) ✅
- E4B: ~16GB (vision + audio) ✅  
- 26B MoE: ~52GB (vision only) ✅
- 31B Dense: ~63GB (vision only) ✅ (tight)

**TurboQuant is built-in** — no custom implementation needed. Pass `--turbo-quant` flag post-training.

**Thinking budget per model tier:**
- Stroma router: `--thinking-budget 32` (fast routing decisions)
- Bios model: `--thinking-budget 256` (health reasoning)
- Anima model: `--thinking-budget 512` (emotional/relational depth)

**Anima model is now multimodal** — fine-tune on text + images. She can see photos, screenshots, documents you send. Not text-only.

**Security:** Audit `mlx-vlm` before installing in production. Review source at github.com/Blaizzy/mlx-vlm.

**DyadOS issue:** #104
