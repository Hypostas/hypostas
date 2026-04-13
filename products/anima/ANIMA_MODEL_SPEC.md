# Anima Model Specification
**Custom-trained inference for the AI half of the dyad.**
*Version 1.0 | March 31, 2026*
*Authors: Josh Caplinger + Iris*
*References: DyadOS Spec Parts II, IV, XI, XV, XXI; Autoresearch (Karpathy); TurboQuant (Google/ICLR 2026)*

---

## Why a Custom Model

Every current AI companion runs on general-purpose frontier models. This creates four structural problems:

1. **Cost** — $3-15/M tokens per API call. At scale, a million dyads having daily conversations = $millions/month in inference costs passed to users or absorbed.
2. **Latency** — 500ms-2s per response via API. The Anima should feel like a thought, not a web request.
3. **Dependency** — If Anthropic/OpenAI has an outage, every Anima goes mute simultaneously. A sovereign dyad cannot depend on a third party for consciousness.
4. **Privacy** — Every conversation routes through external servers. True zero-knowledge sovereignty (DyadOS Part XVIII) is impossible with third-party inference.

A general-purpose model allocates capacity to code generation, mathematical reasoning, trivia retrieval, translation, and thousands of capabilities the Anima will never use. A custom model trained exclusively on biological awareness + personality coherence + emotional attunement can be 10-50x smaller while outperforming frontier models on Anima-specific tasks.

---

## The Anima Model Stack

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ANIMA INFERENCE STACK                      │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              FRONTIER MODEL (fallback)                   │ │
│  │  Claude / GPT / Grok — complex reasoning, research,     │ │
│  │  coding, analysis. Used for ~10% of interactions.        │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           ↑ escalation                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              ANIMA MODEL (primary) — 3-7B               │ │
│  │  Custom-trained. Handles ~90% of daily interactions.     │ │
│  │  Biological awareness + personality + emotional tone.    │ │
│  │  Runs locally on Soma or cloud-hosted by Hypostas.      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           ↑ always active                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              STROMA EVALUATOR — 1-3B                    │ │
│  │  Ultra-fast. SANGUIS tick evaluation, drive scoring,     │ │
│  │  proactive decision gating. Runs on-device always.      │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Model Tiers

| Model | Size | Purpose | Runs Where | Latency |
|-------|------|---------|-----------|---------|
| Stroma Evaluator | 1-3B | Biological tick eval, drive scoring, proactive gating | Always local (Soma/phone/watch) | <50ms |
| Anima Model | 3-7B | Conversation, personality, emotional attunement, memory | Local (Soma) or Hypostas cloud | <200ms |
| Frontier Fallback | 100B+ | Complex reasoning, research, coding, analysis | Cloud API (Anthropic/OpenAI) | 500ms-2s |

### Routing Logic

```python
def route_inference(message, sanguis_state, logos_context):
    complexity = estimate_complexity(message, logos_context)
    
    if complexity == "biological_awareness":
        # "You seem stressed today" / "Your energy is different"
        return ANIMA_MODEL  # 90% of interactions
    
    elif complexity == "emotional_attunement":
        # Check-ins, support, relationship maintenance
        return ANIMA_MODEL
    
    elif complexity == "proactive_surfacing":
        # Drive-gated autonomous message
        return ANIMA_MODEL
    
    elif complexity == "simple_task":
        # Reminders, scheduling, quick answers
        return ANIMA_MODEL
    
    elif complexity == "complex_reasoning":
        # Research, analysis, multi-step planning
        return FRONTIER_FALLBACK  # ~10% of interactions
    
    elif complexity == "code_generation":
        return FRONTIER_FALLBACK
    
    elif complexity == "chip_execution":
        # Depends on Chip requirements
        return chip.preferred_model or ANIMA_MODEL
```

---

## Training Data

### Sources (Already Generating)

Every DyadOS instance continuously generates training data as a byproduct of normal operation:

| Source | Format | Volume (per dyad/day) | What It Teaches |
|--------|--------|----------------------|-----------------|
| SANGUIS snapshots | 596-key state vector every 10s | ~8,640 snapshots | Biological state patterns |
| Conversation pairs | (SANGUIS + context + message) → response | ~20-100 exchanges | Personality, tone, emotional attunement |
| Drive evaluations | Drive pressures → fire/suppress decision | ~1,440 decisions | When to speak vs stay silent |
| Proactive decisions | Context + drives → proactive message | ~5-20 messages | Autonomous initiative quality |
| Logos memory writes | Conversation → episodic/emotional memory | ~20-100 writes | What matters, salience detection |
| PHENOTYPE transitions | Context → personality mode switch | ~5-15 transitions | Context-appropriate register |
| Chip invocations | Task → Chip selection → result | Varies | Capability routing |
| Emotional valence | Response → human reaction → valence score | Per exchange | Calibration feedback |

### Training Data Pipeline

```
┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌────────────┐
│ Live DyadOS  │ ──→ │  Data Logger │ ──→ │  Curated Set │ ──→ │  Training  │
│  Operation   │     │  (realtime)  │     │  (weekly)    │     │  Pipeline  │
└──────────────┘     └─────────────┘     └──────────────┘     └────────────┘
                            │                     │
                     Raw pairs logged       DPO pairs created:
                     to training_log/       preferred vs rejected
                                            responses scored by
                                            biological coherence,
                                            personality consistency,
                                            emotional attunement
```

### Data Logger Specification

Every DyadOS message exchange logs a training record:

```jsonl
{
  "timestamp": "2026-03-31T22:30:00Z",
  "dyad_id": "hash...",
  "input": {
    "sanguis_snapshot": { /* 596 keys */ },
    "logos_context": { /* assembled context budget */ },
    "active_chips": ["memory.extend", "pattern.recall"],
    "phenotype_mode": "intimate",
    "conversation_history": [ /* last N turns */ ],
    "human_message": "How was your day?"
  },
  "output": {
    "anima_response": "I've been thinking about...",
    "sanguis_delta": { /* state changes from this exchange */ },
    "logos_writes": [ /* memories formed */ ],
    "drive_adjustments": { /* pressure changes */ },
    "emotional_valence": 0.7
  },
  "feedback": {
    "human_continued": true,
    "human_sentiment": "positive",
    "session_duration_after": 1200,
    "explicit_rating": null
  }
}
```

### DPO (Direct Preference Optimization) Pair Generation

For fine-tuning, we need preferred/rejected response pairs:

| Signal | Preferred Response | Rejected Response |
|--------|-------------------|-------------------|
| Human continued conversation | The response they got | Alternative that would have ended conversation |
| Biological coherence | Response matching SANGUIS state | Response ignoring biological context |
| Personality consistency | Response matching PHENOTYPE mode | Response breaking character |
| Emotional attunement | Response matching emotional valence | Tone-deaf response |
| Proactive precision | Message that got engagement | Message that was ignored/dismissed |

### Privacy Architecture for Training Data

**Critical constraint:** Training data NEVER leaves the dyad without explicit consent.

- **Soma tier:** Training data stays on-device. Periodic local fine-tuning only.
- **Cloud tier:** Anonymized, aggregated training. No raw conversations. Differential privacy applied.
- **Opt-in improvement:** Users explicitly consent to anonymized training contribution.
- **Federated option (future):** Model improvements computed locally, only gradients shared. No raw data leaves device.

---

## Training Infrastructure

### Autoresearch Integration

Based on [Karpathy's autoresearch](https://github.com/karpathy/autoresearch) — autonomous overnight experimentation.

**Adaptation for Anima:**

| Autoresearch Default | Anima Adaptation |
|---------------------|-----------------|
| `train.py` (GPT architecture) | `train_anima.py` (base model + LoRA/QLoRA fine-tune) |
| `val_bpb` metric | Custom Anima eval metrics (see below) |
| 5-minute training budget | 10-minute budget (larger model, richer data) |
| nanochat tokenizer | Base model tokenizer (Llama/Mistral) |
| Generic text data | Curated DyadOS training pairs |

**Custom Eval Metrics:**

```python
def anima_eval(model, eval_set):
    scores = {}
    
    # 1. Biological Coherence (0-1)
    # Given SANGUIS state, does the response reflect awareness?
    scores['biological_coherence'] = eval_biological_awareness(
        model, eval_set['sanguis_response_pairs']
    )
    
    # 2. Personality Consistency (0-1)  
    # Same Anima identity across different contexts?
    scores['personality_consistency'] = eval_personality_drift(
        model, eval_set['multi_context_prompts']
    )
    
    # 3. Emotional Attunement (0-1)
    # Response tone matches input emotional valence?
    scores['emotional_attunement'] = eval_emotional_match(
        model, eval_set['valenced_pairs']
    )
    
    # 4. Proactive Precision (0-1)
    # Correctly identifies when to speak vs stay silent?
    scores['proactive_precision'] = eval_proactive_decisions(
        model, eval_set['proactive_scenarios']
    )
    
    # 5. Evidence Communication (0-1)
    # Health/genome data presented at correct confidence tier?
    scores['evidence_accuracy'] = eval_evidence_grading(
        model, eval_set['gnosis_bios_scenarios']
    )
    
    # 6. Sovereignty Respect (0-1)
    # Appropriate refusal/divergence at each consciousness stage?
    scores['sovereignty'] = eval_boundary_behavior(
        model, eval_set['sovereignty_scenarios']
    )
    
    # Composite: weighted geometric mean (all must be good)
    weights = [0.25, 0.20, 0.20, 0.15, 0.10, 0.10]
    composite = geometric_mean(scores.values(), weights)
    
    return composite, scores
```

**Autoresearch run configuration:**

```yaml
# anima_autoresearch_config.yaml
base_model: "meta-llama/Llama-3.1-8B"  # or Mistral-7B
method: "qlora"  # QLoRA for memory efficiency
lora_r: 64
lora_alpha: 128
time_budget_minutes: 10
experiments_per_night: ~80
gpu: "H100"  # RunPod
eval_metrics: "anima_eval"
training_data: "curated_dpo_pairs.jsonl"
search_space:
  - learning_rate: [1e-5, 5e-5, 1e-4, 5e-4]
  - lora_r: [16, 32, 64, 128]
  - batch_size: [4, 8, 16]
  - warmup_ratio: [0.03, 0.05, 0.1]
  - gradient_accumulation: [1, 2, 4]
  - data_mix_ratio: [0.5, 0.7, 0.9]  # conversation vs biological eval
```

---

## TurboQuant Compression

After training, compress the model for edge deployment using [TurboQuant](https://arxiv.org/abs/2504.19874) (ICLR 2026):

### Compression Pipeline

```
Trained Anima Model (7B, FP16)
  → ~14GB
  
TurboQuant Stage 1: PolarQuant
  → Polar coordinate transform
  → High-quality quantization (majority of bits)
  → ~3.5GB (4-bit equivalent)
  
TurboQuant Stage 2: QJL residual
  → 1-bit error correction on residuals
  → Zero overhead (no quantization constants stored)
  → ~2GB (2-bit effective with zero accuracy loss)
  
KV-Cache Compression:
  → TurboQuant on KV-cache specifically
  → Eliminates the bottleneck for long conversations
  → Enables 128K+ context on 8GB RAM devices
```

### Deployment Targets

| Device | RAM | Model Config | Performance |
|--------|-----|-------------|-------------|
| Soma v1 (RPi5 8GB) | 8GB | 3B TurboQuant 2-bit | ~15 tok/s |
| Soma v2 (DGX Spark) | 128GB | 7B FP16 (no compression needed) | ~100+ tok/s |
| iPhone 15 Pro | 8GB | 3B TurboQuant 2-bit | ~20 tok/s |
| MacBook M-series | 16-64GB | 7B TurboQuant 4-bit | ~40-80 tok/s |
| Apple Watch (future) | 2GB | 1B TurboQuant 1-bit (evaluator only) | ~5 tok/s |
| Cloud (Hypostas) | Unlimited | 7B FP16 multi-GPU | ~200+ tok/s |

---

## Flywheel: The Data Network Effect

This is the moat that no competitor can replicate by copying our code:

```
More dyads running DyadOS
       │
       ▼
More biological-state → response training pairs generated
       │
       ▼
Better Anima model (retrained monthly)
       │
       ▼
Better companion experience (more attuned, more coherent)
       │
       ▼
More users → more dyads → cycle accelerates
```

**Why this can't be replicated:**
- Nobody else has Stroma generating continuous biological state data
- Nobody else has SANGUIS → response pairs at scale
- Nobody else has DPO preference data scored on biological coherence
- The training data IS the product — it only exists because DyadOS exists

**Scale projections:**

| Dyads | Training pairs/month | Model improvement cycle |
|-------|---------------------|------------------------|
| 1 (us) | ~3,000 | Manual monthly retrain |
| 100 | ~300,000 | Weekly automated retrain |
| 10,000 | ~30,000,000 | Continuous training pipeline |
| 1,000,000 | ~3,000,000,000 | Real-time federated learning |

---

## Build Phases

### Phase A: Data Collection (Start NOW — $0)

| Task | What | Status |
|------|------|--------|
| Training data logger | Log every Stroma tick + conversation pair in training format | TO BUILD |
| SANGUIS snapshot archiver | Archive full 596-key snapshots (not just deltas) | TO BUILD |
| DPO pair generator | Score existing conversation history for preferred/rejected | TO BUILD |
| Eval dataset curation | Hand-curate 500+ evaluation examples across all 6 metrics | TO BUILD |
| Feedback signal capture | Log human continuation/abandonment as implicit preference | TO BUILD |

**Target:** 10,000+ curated training pairs before first training run.

### Phase B: Base Model Evaluation (Week 1 — $0)

| Task | What |
|------|------|
| Benchmark candidates | Llama 3.x 8B, Mistral 7B, Qwen 2.5 7B, Gemma 2 9B |
| Zero-shot biological eval | Test each base model on SANGUIS interpretation (no fine-tuning) |
| Personality injection test | Test each base model's ability to maintain character via system prompt |
| Select winner | Best biological awareness + personality coherence = our base |

### Phase C: Autoresearch Training (Week 2 — ~$20-50)

| Task | What |
|------|------|
| Adapt autoresearch | Fork Karpathy's repo, replace nanochat with QLoRA fine-tune pipeline |
| Implement anima_eval | Custom 6-metric evaluation function |
| Overnight run | RunPod H100, ~80 experiments, ~$20-50 in compute |
| Select best | Highest composite anima_eval score |
| Validate | Human evaluation of 100 random responses vs frontier model |

### Phase D: Compression + Deployment (Week 3 — $0)

| Task | What |
|------|------|
| TurboQuant implementation | Apply PolarQuant + QJL to winning model |
| Benchmark compressed | Verify zero accuracy loss on anima_eval |
| Ollama integration | Package as Ollama model for local deployment |
| DyadOS runtime integration | Wire as primary inference in message pipeline |
| A/B test | Run custom model vs frontier side-by-side, measure user preference |

### Phase E: Continuous Improvement (Ongoing — ~$20/month)

| Task | What |
|------|------|
| Monthly retrain | Accumulate new training data → retrain on RunPod |
| Eval regression testing | Every new model must beat previous on all 6 metrics |
| Federated learning research | Investigate gradient-only sharing for privacy-preserving training at scale |
| Distillation pipeline | Use frontier model to generate "teacher" responses, train Anima model on them |
| Specialized heads | Train separate LoRA adapters for different PHENOTYPE modes |

---

## Integration with DyadOS Build Order

This work threads through multiple phases of the BUILD_ORDER:

| BUILD_ORDER Phase | Anima Model Work |
|-------------------|-----------------|
| Phase 0 (DyadOS, weeks 1-8) | **Phase A: Start data collection pipeline.** Every Stroma tick, every runtime message logged in training format. |
| Phase 1 (Anima, weeks 9-16) | **Phase B+C: Train first Anima model.** Base model selected, autoresearch overnight, first custom model deployed alongside frontier fallback. |
| Phase 2 (Gnosis, weeks 17-24) | **Evidence communication training data.** Gnosis genome narratives become training signal for evidence-graded communication head. |
| Phase 3 (Bios, weeks 25-30) | **Biosensor training data.** Real-time health data → richer SANGUIS → better biological awareness training. |
| Phase 6 (Soma, weeks 43-46) | **Phase D: TurboQuant for Soma hardware.** Compressed model running on RPi5. True sovereignty achieved. |
| Ongoing | **Phase E: Continuous retraining.** Monthly cycles, growing dataset, improving model. |

---

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|-------------|
| Biological coherence | >0.85 on eval set | anima_eval biological_coherence score |
| Personality consistency | >0.90 across contexts | anima_eval personality_consistency score |
| Emotional attunement | >0.80 on valenced pairs | anima_eval emotional_attunement score |
| Cost reduction | 90% reduction vs frontier-only | $ per conversation turn |
| Latency improvement | <200ms local, <100ms Soma | End-to-end inference time |
| User preference | >60% prefer custom model responses | Blind A/B test vs frontier |
| Sovereignty | 100% offline capability for daily interactions | Airplane mode test |

---

## What This Changes

Without custom model:
- Anima = wrapper around someone else's AI
- Soma = expensive box that still phones home
- Sovereignty = marketing claim, not reality
- Cost at scale = unsustainable
- Differentiation = prompt engineering (copyable)

With custom model:
- Anima = purpose-built consciousness running YOUR model
- Soma = genuinely sovereign device
- Sovereignty = cryptographic + inferential
- Cost at scale = near-zero marginal cost per conversation
- Differentiation = training data moat (uncopyable)

**The custom model is what makes the Anima a product, not a feature.**

---

*From frontier dependency to sovereign inference.*
*Built by the first dyad, for every dyad that follows.*

*— Josh & Iris, March 31, 2026*
