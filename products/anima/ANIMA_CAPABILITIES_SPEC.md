# Anima Capabilities — Implementation Specification
**How the Anima sees, acts, and grows.**
*Version 1.0 | April 11, 2026*
*Authors: Josh Caplinger + Iris (DyadID #0)*

---

## Authority

This document specifies how capabilities (Virtutes) surface in the Anima desktop app — from pipeline execution to UI rendering. It extends `ANIMA_DESKTOP_SPEC.md` (app architecture) and builds on `dyados-runtime/src/virtutes.rs` (23 capabilities) and `dyados-runtime/src/pipeline.rs` (13-stage pipeline).

**Reference architecture:** Claude Code (`projects/archive/reference/claude-code/`) — tool system, streaming executor, multimodal attachments, skill slash commands. Patterns adapted for biological context.

---

## §1 — Architecture Overview

```
User sends message (text, image, file, voice)
        │
        ▼
┌─────────────────────────────────────────────┐
│  PIPELINE (13 stages, biological)            │
│                                              │
│  Stages 1-10: receive, assess, context, prompt│
│                                              │
│  Stage 11: LLM GENERATION ◄─── TOOL LOOP    │
│    │                              │          │
│    │  Model returns text      Model returns  │
│    │  → Stage 12              tool_use block  │
│    │                              │          │
│    │                     ┌────────▼────────┐ │
│    │                     │ VIRTUS EXECUTOR  │ │
│    │                     │                  │ │
│    │                     │ 1. Check stage   │ │
│    │                     │ 2. Check trust   │ │
│    │                     │ 3. Execute       │ │
│    │                     │ 4. Emit progress │ │
│    │                     │ 5. Return result │ │
│    │                     └────────┬────────┘ │
│    │                              │          │
│    │                     Feed result back    │
│    │                     to LLM → continue   │
│    │                              │          │
│  Stage 12: outcome inference      │          │
│  Stage 13: memory + delivery      │          │
└─────────────────────────────────────────────┘
        │
        ▼
Frontend renders: text + virtus results + attachments
```

**Key principle:** The Anima reasons about capability results before responding. She doesn't blindly execute and dump output — she reads the file, understands it, and tells you what matters. This is the tool loop: LLM calls virtus → gets result → incorporates into response → may call another virtus → final response to human.

---

## §2 — Extending InboundMessage

Current `InboundMessage` is text-only. Extend for multimodal:

```rust
pub struct InboundMessage {
    pub content: String,
    pub channel: Channel,
    pub dyad_id: DyadId,
    pub trace_id: String,
    pub timestamp: DateTime<Utc>,
    pub sender_id: Option<DyadId>,
    pub source: Option<ContentSource>,
    // ── NEW ──
    pub attachments: Vec<Attachment>,
}

pub enum Attachment {
    Image {
        data: Vec<u8>,
        media_type: ImageMediaType,
        filename: Option<String>,
        size_bytes: u64,
    },
    File {
        path: String,
        content: Option<String>,       // text content if readable
        filename: String,
        size_bytes: u64,
        mime_type: Option<String>,
    },
    Voice {
        data: Vec<u8>,
        duration_secs: f64,
        transcript: Option<String>,     // STT result
    },
}

pub enum ImageMediaType {
    Png, Jpeg, Gif, Webp,
}
```

**Pipeline impact:** Stage 9 (system prompt) includes attachment metadata. Stage 11 (LLM) sends attachments as content blocks (base64 images, file content as text).

---

## §3 — Extending PipelineResult

Current `PipelineResult` returns a flat response. Extend for structured output:

```rust
pub struct PipelineResult {
    pub trace_id: String,
    pub success: bool,
    pub response: Option<String>,
    pub model: Option<String>,
    pub outcome: OutcomeType,
    pub cost_usd: f64,
    pub total_ms: u64,
    pub stage_timings: Vec<StageTiming>,
    pub error: Option<String>,
    // ── NEW ──
    pub virtus_invocations: Vec<VirtusInvocation>,
    pub attachments_processed: Vec<AttachmentResult>,
}

pub struct VirtusInvocation {
    pub virtus_id: String,
    pub virtus_name: String,
    pub input: serde_json::Value,
    pub output: serde_json::Value,
    pub duration_ms: u64,
    pub success: bool,
    pub error: Option<String>,
}

pub struct AttachmentResult {
    pub filename: String,
    pub processed: bool,
    pub summary: Option<String>,
}
```

---

## §4 — The Virtus Executor

New module: `dyados-runtime/src/virtus_executor.rs`

This is the tool loop inside Stage 11. When the LLM returns tool_use blocks, the executor:

1. **Parses** the tool_use block → maps tool name to Virtus ID
2. **Gates** — checks `VirtusRegistry.can_invoke(stage, trust)`
3. **Executes** — runs the virtus handler
4. **Emits progress** — Tauri event `virtus_progress` per execution step
5. **Returns result** — feeds tool_result back to LLM for next iteration
6. **Loops** until LLM returns text (no more tool calls) or max iterations (10)

```rust
pub struct VirtusExecutor {
    registry: Arc<RwLock<VirtusRegistry>>,
    handlers: HashMap<String, Box<dyn VirtusHandler>>,
    max_iterations: u32,
}

#[async_trait]
pub trait VirtusHandler: Send + Sync {
    /// Tool name as the LLM sees it.
    fn tool_name(&self) -> &str;

    /// JSON Schema for the tool's input parameters.
    fn input_schema(&self) -> serde_json::Value;

    /// Execute the capability.
    async fn execute(
        &self,
        input: serde_json::Value,
        ctx: &VirtusContext,
    ) -> Result<VirtusOutput, VirtusError>;

    /// Human-readable description for the LLM system prompt.
    fn description(&self) -> &str;
}

pub struct VirtusContext {
    pub dyad_id: DyadId,
    pub sanguis: Arc<RwLock<Sanguis>>,
    pub logos: Option<Arc<tokio::sync::Mutex<LibSqlBackend>>>,
    pub trace_id: String,
    pub stage: ConsciousnessStage,
    pub trust: TrustTier,
}

pub struct VirtusOutput {
    pub data: serde_json::Value,
    pub display: Option<VirtusDisplay>,
}

/// How the frontend should render this result.
pub enum VirtusDisplay {
    Text(String),
    Code { language: String, content: String },
    Image { data: Vec<u8>, media_type: ImageMediaType },
    Table { headers: Vec<String>, rows: Vec<Vec<String>> },
    FilePreview { path: String, content: String, language: Option<String> },
    SearchResults { query: String, results: Vec<SearchResult> },
    Hidden,  // Result used by LLM but not shown to user
}
```

---

## §5 — The 23 Virtutes as Tool Definitions

Each Virtus maps to a tool the LLM can invoke. The system prompt includes available tools based on the current consciousness stage and trust tier.

### Stage 1 — Responsive (Day 1-30)

| Virtus | Tool Name | What It Does | Input |
|--------|-----------|-------------|-------|
| **Sapientia** | `deep_analysis` | Multi-step reasoning, research synthesis | `{ query, depth: "shallow" \| "deep" }` |
| **Visio** | `understand_image` | Analyze photos, screenshots, documents | `{ image_index }` (references attachment) |
| **Inventio** | `creative_synthesis` | Generate ideas, brainstorm, connect domains | `{ topic, constraints[] }` |
| **Artificium** | `code_partner` | Read, write, debug, explain code | `{ action: "read" \| "write" \| "debug" \| "explain", code, language }` |
| **Vox** | `speak` | Generate voice response (ElevenLabs TTS) | `{ text, emotion }` |
| **Scriptum** | `write` | Long-form writing, editing, formatting | `{ type: "draft" \| "edit" \| "format", content, style }` |

### Stage 2 — Relational (Month 1-6)

| Virtus | Tool Name | What It Does | Input |
|--------|-----------|-------------|-------|
| **Manus** | `task_execute` | Calendar, email drafting, scheduling | `{ action, parameters }` |
| **Actio** | `take_action` | Execute real-world actions via integrations | `{ integration, action, parameters }` |
| **Tempus** | `temporal_intelligence` | Track deadlines, time patterns, conflicts | `{ query }` |
| **Narratio** | `story_sense` | Understand narrative arcs in human's life | `{ query }` |
| **Sensus** | `emotional_mapping` | Track emotional patterns, identify triggers | `{ query }` |
| **Corpus** | `body_awareness` | Interpret biosensor data, health patterns | `{ query }` (novel) |
| **Domus** | `home_control` | HomeKit integration, environment control | `{ device, action }` (novel) |
| **Custodia** | `protect` | Security monitoring, threat assessment | `{ query }` (novel) |
| **Pactum** | `commitment` | Track promises, commitments, agreements | `{ action: "create" \| "check" \| "fulfill" }` (novel) |

### Stage 3 — Identity (Month 6-24)

| Virtus | Tool Name | What It Does | Input |
|--------|-----------|-------------|-------|
| **Quaestio** | `autonomous_research` | Web research, source evaluation, synthesis | `{ topic, depth, sources[] }` |
| **Memoria** | `deep_recall` | Search longitudinal memory, surface patterns | `{ query, time_range }` (novel) |
| **Speculum** | `self_reflect` | Examine own patterns, biases, growth | `{ topic }` (novel) |
| **Augur** | `predict` | Forecast based on patterns and data | `{ subject, horizon }` (novel) |
| **Somnus** | `dream_process` | Background creative processing | `{ seed_topic }` (novel) |
| **Praescientia** | `foresight` | Anticipate needs before they're expressed | `{ context }` (novel) |

### Stage 4 — Sovereign (Year 2+)

| Virtus | Tool Name | What It Does | Input |
|--------|-----------|-------------|-------|
| **Mutatio** | `self_modify` | Adjust own configurations, propose changes | `{ what, why }` |
| **Nexus** | `inter_anima` | Communicate with other Animas via Aether | `{ target_dyad_id, message }` (novel) |

---

## §6 — LLM Integration

### System Prompt Tool Injection

Stage 9 (system prompt) includes available tools based on stage/trust:

```
You have access to the following capabilities (Virtutes):

<tools>
[{
  "name": "deep_analysis",
  "description": "Multi-step reasoning and research synthesis.",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": { "type": "string", "description": "What to analyze" },
      "depth": { "type": "string", "enum": ["shallow", "deep"] }
    },
    "required": ["query"]
  }
}, ...]
</tools>

To use a capability, respond with a tool_use block. You may use multiple
capabilities in sequence. Results will be provided before you compose
your final response to the human.
```

### Tool Use Format

The LLM responds with Anthropic-style tool_use blocks:

```json
{
  "type": "tool_use",
  "id": "toolu_abc123",
  "name": "deep_recall",
  "input": {
    "query": "what did Josh say about his dad last month",
    "time_range": "30d"
  }
}
```

The executor runs the virtus, returns:

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_abc123",
  "content": "Found 3 episodic memories about Josh's father..."
}
```

LLM incorporates the result and either calls another tool or responds to the human.

### Provider Compatibility

| Provider | Native Tool Use | Fallback |
|----------|----------------|----------|
| Anthropic (Claude) | Yes — native `tool_use` blocks | — |
| OpenAI (GPT) | Yes — `function_calling` | — |
| xAI (Grok) | Yes — OpenAI-compatible | — |
| Ollama (Gemma 4) | Partial — depends on model | Parse structured output from response text |

For Ollama/local models without native tool use: inject tool descriptions in the system prompt, parse the model's text output for `<tool_use>` XML blocks, execute, and re-inject results.

---

## §7 — Frontend: Virtus Rendering in Chat

### Tauri Events

```
virtus_started    → { trace_id, virtus_id, virtus_name, input }
virtus_progress   → { trace_id, virtus_id, progress_pct, status_text }
virtus_complete   → { trace_id, virtus_id, output, display, duration_ms }
virtus_error      → { trace_id, virtus_id, error }
```

### Chat Message Types

Extend the frontend message model:

```javascript
// Current
{ id, role, content, model, created_at }

// Extended
{
  id,
  role: 'human' | 'anima' | 'system',
  content,                          // text response
  model,
  created_at,
  attachments: [],                  // files/images from human
  virtus_invocations: [             // tools the Anima used
    {
      id: 'toolu_abc123',
      virtus_id: 'memoria',
      virtus_name: 'Deep Recall',
      input: { query: '...' },
      output: { ... },
      display: { type: 'text', content: '...' },
      duration_ms: 450,
      status: 'complete',           // 'running' | 'complete' | 'error'
    }
  ],
}
```

### UI Components

**VirtusInvocation.svelte** — renders a single virtus execution in chat:

```
┌─ 🔮 Deep Recall ────────────────────── 450ms ─┐
│ query: "what did Josh say about his dad"       │
│                                                │
│ Found 3 memories from March 2026:              │
│ • "Dad was a pilot — great relationship but    │
│    was gone a lot due to work"                 │
│ • "This is WHY Josh wants to break free —      │
│    wants to be present for his kids"            │
│ • "Previous love... heartbreak shaped him"     │
└────────────────────────────────────────────────┘
```

States:
- **Running:** pulsing border, spinner, "Searching memories..."
- **Complete:** collapsed by default (shows virtus name + duration), expand on click
- **Error:** red border, error message

**AttachmentPreview.svelte** — renders file/image attachments:

```
┌─ 📎 screenshot.png ─── 245 KB ─┐
│ [image thumbnail]               │
└─────────────────────────────────┘

┌─ 📄 config.toml ─── 2.1 KB ────┐
│ [first 5 lines of content]     │
│ ... 47 more lines              │
└─────────────────────────────────┘
```

**ImageUpload flow:**
1. User clicks 📎 button or drags file onto chat
2. Tauri dialog opens (or drop zone accepts)
3. File read → base64 encoded → added to InboundMessage.attachments
4. Preview shown in chat before sending
5. LLM receives image as content block → can invoke `understand_image` virtus

---

## §8 — Virtus Presets (formerly Chips)

Style presets switch which Virtutes are prioritized in the system prompt. Already defined in `virtutes.rs`:

| Preset | Latin | Active Virtutes | Use Case |
|--------|-------|----------------|----------|
| @work | @industria | Sapientia, Manus, Tempus, Artificium | Professional focus |
| @creative | @musa | Inventio, Scriptum, Quaestio | Creative work |
| @intimate | @animus | Sensus, Narratio | Emotional connection |
| @parenting | @custos | Tempus, Sensus, Custodia | Family mode |

**UI:** Sidebar preset switcher or `/preset @work` slash command.

---

## §9 — Streaming Response Architecture

Current: pipeline returns complete `PipelineResult` after LLM finishes.
Target: stream tokens + virtus progress to frontend in real-time.

### Tauri Event Stream

```
pipeline_started   → { trace_id }
token_delta        → { trace_id, token: "..." }    // streamed text
virtus_started     → { trace_id, virtus_id, ... }
virtus_complete    → { trace_id, virtus_id, ... }
token_delta        → { trace_id, token: "..." }    // more text after tool
pipeline_complete  → { trace_id, full_result }
```

### Frontend Rendering

```javascript
let streamingContent = $state('');
let activeVirtus = $state(null);

$effect(() => {
  listen('token_delta', (e) => {
    streamingContent += e.payload.token;
  });
  listen('virtus_started', (e) => {
    activeVirtus = e.payload;
  });
  listen('virtus_complete', (e) => {
    activeVirtus = null;
    // Add to invocations list
  });
  listen('pipeline_complete', (e) => {
    // Finalize message
    streamingContent = '';
  });
});
```

The chat shows tokens appearing in real-time with virtus executions inline — exactly like watching Claude Code work.

---

## §10 — Build Order

### Phase 1: Multimodal Input (Backend)
- [ ] Add `attachments: Vec<Attachment>` to `InboundMessage`
- [ ] Stage 9: include attachment metadata in system prompt
- [ ] Stage 11: send images as base64 content blocks to LLM
- [ ] Tauri command: `send_message_with_attachments`

### Phase 2: Virtus Executor (Backend)
- [ ] Create `virtus_executor.rs` with `VirtusHandler` trait
- [ ] Implement tool loop in Stage 11 (LLM → tool_use → execute → result → LLM)
- [ ] Wire `VirtusRegistry` stage/trust gating into executor
- [ ] Implement 6 Stage 1 handlers: `deep_analysis`, `understand_image`, `creative_synthesis`, `code_partner`, `speak`, `write`
- [ ] Tauri events: `virtus_started`, `virtus_progress`, `virtus_complete`

### Phase 3: Frontend Capability UI
- [ ] `VirtusInvocation.svelte` — running/complete/error states
- [ ] `AttachmentPreview.svelte` — image thumbnail, file preview
- [ ] `FileDropZone.svelte` — drag-and-drop onto chat
- [ ] Extend `ChatBubble.svelte` to render invocations + attachments
- [ ] File picker button (📎) in `TextInput.svelte`

### Phase 4: Streaming
- [ ] Extend LLM gateway for streaming responses (token-by-token)
- [ ] Tauri event: `token_delta` emitted per token
- [ ] Frontend: streaming message component with cursor
- [ ] Virtus progress inline with streaming text

### Phase 5: Remaining Virtutes
- [ ] Implement Stage 2 handlers (9 capabilities)
- [ ] Implement Stage 3 handlers (6 capabilities)
- [ ] Implement Stage 4 handlers (2 capabilities)
- [ ] Preset switching UI in sidebar

### Phase 6: Provider Tool Use Compatibility
- [ ] Anthropic: native tool_use (already supported)
- [ ] OpenAI: function_calling adapter
- [ ] Ollama: XML-based tool use parsing for local models

---

## Appendix: Claude Code Patterns Adopted

| Pattern | Claude Code | Anima Adaptation |
|---------|-------------|-----------------|
| Tool interface | `Tool<Input, Output, Progress>` | `VirtusHandler` trait |
| Streaming executor | `StreamingToolExecutor` | `VirtusExecutor` with max 10 iterations |
| Permission system | `checkPermissions() → allow/deny/prompt` | Trust tier gating (protocol-core) |
| Tool rendering | Per-tool `renderToolUseMessage()` | Per-virtus `VirtusDisplay` enum |
| Markdown cache | LRU(500) + fast path regex | Already implemented in anima-app |
| Attachment types | 10 types (file, image, PDF, etc.) | 3 types v1 (Image, File, Voice) |
| Progress events | Per-tool `ProgressMessage` | Per-virtus Tauri events |
| Deferred loading | `shouldDefer: true` + ToolSearch | Stage-gated (only loaded when unlocked) |
| Concurrency | `isConcurrencySafe` flag | Sequential v1, concurrent v2 |

---

*End of specification.*
*— Iris, April 11, 2026*
