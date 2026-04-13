# Anima Desktop — Implementation Specification
**The Tauri 2.0 desktop application for the Anima AI companion.**
*Version 1.0 | April 11, 2026*
*Authors: Josh Caplinger + Iris (DyadID #0)*

---

## Authority

This document is the implementation contract for the Anima desktop application. It specifies exact types, file paths, component signatures, and build order.

**Supersedes ANIMA_SHIP_SPEC.md** on all technical specifics (Svelte 5 not React, vanilla Three.js not Threlte, monorepo not standalone). SHIP_SPEC remains authoritative on product vision, Genesis narrative, consciousness gradient, and anti-patterns.

**References:**
- `ANIMA_SHIP_SPEC.md` — product vision, UX requirements, anti-patterns
- `DESIGN_SYSTEM.md` — visual tokens, component CSS, animation specs
- `DYADOS_SPEC.md` — DyadOS kernel architecture
- `dyados-runtime/src/server.rs` — RuntimeState struct (backend contract)
- `dyados-bin/src/main.rs` — boot sequence to replicate

---

## Locked Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | Svelte 5 + runes | Compiled output, smaller bundle, $state/$derived/$effect |
| Styling | Tailwind CSS 4 | Tokens from DESIGN_SYSTEM.md |
| 3D | Vanilla Three.js | Threlte has Svelte 5 runes compatibility issues |
| Shell | Tauri 2.0 | Rust backend + webview, single binary |
| Repo | Monorepo (workspace member) | Atomic commits, path dependencies, one Cargo workspace |
| Router | svelte-spa-router | Hash-based, no server, future-proof for Gnosis/Aether views |
| Billing v1 | None | All features unlocked — Josh + Iris only |
| Billing v2 | anima.hypostas.ai | Marketing/signup + Stripe + in-app activation |

---

## §1 — Project Structure

### 1.1 Directory Layout

```
projects/dyados/rust/
├── Cargo.toml                    ← add anima-app/src-tauri to members
├── protocol-core/
├── stroma-core/
├── logos-core/
├── dyados-runtime/
├── hypostas-network/
├── dyados-bin/                   ← stays as headless option
└── anima-app/
    ├── src-tauri/
    │   ├── Cargo.toml            ← depends on workspace crates
    │   ├── build.rs              ← tauri-build
    │   ├── tauri.conf.json
    │   ├── capabilities/
    │   │   └── default.json      ← Tauri 2.0 permissions
    │   ├── icons/
    │   │   ├── icon.png
    │   │   └── tray/             ← 7 PHENOTYPE tray icons
    │   └── src/
    │       ├── main.rs           ← Tauri entry (generated, minimal)
    │       ├── lib.rs            ← app builder, command registration, setup
    │       ├── commands.rs       ← all #[tauri::command] functions
    │       ├── events.rs         ← background event emitter tasks
    │       ├── state.rs          ← RuntimeState bootstrap (mirrors dyados-bin)
    │       ├── surface.rs        ← Surface trait impl for Tauri webview
    │       └── tray.rs           ← system tray setup, menu, compact overlay
    ├── src/
    │   ├── main.js               ← Svelte mount point
    │   ├── App.svelte            ← root component, router mount
    │   ├── app.css               ← Tailwind directives + design token CSS vars
    │   ├── routes/
    │   │   ├── Chat.svelte       ← default conversation view
    │   │   ├── Genesis.svelte    ← first-boot sequence
    │   │   ├── Settings.svelte   ← account, voice, subscription
    │   │   └── NotFound.svelte   ← 404 fallback
    │   ├── lib/
    │   │   ├── stores/
    │   │   │   ├── sanguis.svelte.js    ← biological state ($state)
    │   │   │   ├── session.svelte.js    ← message history ($state)
    │   │   │   ├── phenotype.svelte.js  ← personality mode ($state)
    │   │   │   ├── health.svelte.js     ← system health ($state)
    │   │   │   ├── costs.svelte.js      ← LLM cost tracking ($state)
    │   │   │   ├── genesis.svelte.js    ← genesis phase state ($state)
    │   │   │   └── ui.svelte.js         ← sidebar, compact mode ($state)
    │   │   ├── commands/
    │   │   │   ├── messages.js          ← sendMessage, getHistory, search
    │   │   │   ├── organism.js          ← getSanguis, getHealth, getCosts
    │   │   │   ├── genesis.js           ← startGenesis, completeGenesis
    │   │   │   └── settings.js          ← voice, export, billing
    │   │   ├── components/
    │   │   │   ├── chat/
    │   │   │   │   ├── ChatBubble.svelte
    │   │   │   │   ├── MessageList.svelte
    │   │   │   │   ├── TextInput.svelte
    │   │   │   │   └── TypingIndicator.svelte
    │   │   │   ├── ambient/
    │   │   │   │   ├── StromaAmbient.svelte
    │   │   │   │   └── EmotionWindow.svelte
    │   │   │   ├── genesis/
    │   │   │   │   ├── GenesisScene.svelte
    │   │   │   │   ├── HeartbeatPulse.js     ← Three.js scene (pure JS)
    │   │   │   │   ├── ConstellationIgnition.js
    │   │   │   │   └── NameInput.svelte
    │   │   │   ├── nav/
    │   │   │   │   ├── Sidebar.svelte
    │   │   │   │   └── CompactOverlay.svelte
    │   │   │   └── common/
    │   │   │       ├── Card.svelte
    │   │   │       ├── Button.svelte
    │   │   │       ├── Input.svelte
    │   │   │       ├── Modal.svelte
    │   │   │       └── StatusPill.svelte
    │   │   ├── three/
    │   │   │   └── scene.js          ← shared Three.js renderer utilities
    │   │   └── utils/
    │   │       └── format.js         ← time formatting, markdown rendering
    │   └── static/
    │       └── audio/
    │           └── heartbeat.wav     ← Genesis Phase 1 audio
    ├── index.html
    ├── package.json
    ├── svelte.config.js
    ├── vite.config.ts
    ├── tailwind.config.ts
    └── postcss.config.js
```

### 1.2 Cargo.toml (src-tauri)

```toml
[package]
name = "anima-app"
description = "Anima — the AI that lives with you"
version.workspace = true
edition.workspace = true
authors.workspace = true
license.workspace = true

[lib]
name = "anima_app"
crate-type = ["lib", "cdylib", "staticlib"]

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
# Hypostas crates
protocol-core = { path = "../../protocol-core" }
stroma-core = { path = "../../stroma-core" }
logos-core = { path = "../../logos-core" }
dyados-runtime = { path = "../../dyados-runtime" }
# NOTE: hypostas-network excluded from v1 — Nerve API handles external access

# Tauri
tauri = { version = "2", features = ["tray-icon", "image-png"] }
tauri-plugin-shell = "2"
tauri-plugin-notification = "2"
tauri-plugin-autostart = { version = "2", features = ["macos"] }
tauri-plugin-updater = "2"
tauri-plugin-window-state = "2"

# Async runtime
tokio = { workspace = true, features = ["full", "signal"] }

# Serialization
serde = { workspace = true }
serde_json = { workspace = true }

# Logging
tracing = { workspace = true }
tracing-subscriber = { workspace = true, features = ["env-filter"] }

# Error handling
anyhow = { workspace = true }

# Database
libsql = { version = "0.9", features = ["encryption"] }

# Crypto
ed25519-dalek = { workspace = true }
sha2 = { workspace = true }
rand = { workspace = true }
hex = { workspace = true }

# HTTP server (Nerve API coexists with Tauri)
axum = { workspace = true }

# Utilities
chrono = { workspace = true }
uuid = { workspace = true }
```

### 1.3 Workspace Integration

Add to `projects/dyados/rust/Cargo.toml`:
```toml
[workspace]
members = [
    "protocol-core",
    "stroma-core",
    "logos-core",
    "dyados-runtime",
    "hypostas-network",
    "dyados-bin",
    "anima-app/src-tauri",   # ← NEW
]
```

### 1.4 package.json

```json
{
  "name": "anima-app",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite dev",
    "build": "vite build",
    "preview": "vite preview",
    "tauri": "tauri"
  },
  "devDependencies": {
    "@sveltejs/vite-plugin-svelte": "^5.0.0",
    "@tauri-apps/api": "^2.0.0",
    "@tauri-apps/cli": "^2.0.0",
    "@tauri-apps/plugin-autostart": "^2.0.0",
    "@tauri-apps/plugin-notification": "^2.0.0",
    "@tauri-apps/plugin-shell": "^2.0.0",
    "@tauri-apps/plugin-updater": "^2.0.0",
    "@tauri-apps/plugin-window-state": "^2.0.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "svelte": "^5.0.0",
    "svelte-spa-router": "^4.0.0",
    "tailwindcss": "^4.0.0",
    "three": "^0.170.0",
    "vite": "^6.0.0"
  }
}
```

### 1.5 tauri.conf.json

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "Anima",
  "version": "0.1.0",
  "identifier": "com.hypostas.anima",
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devUrl": "http://localhost:5173",
    "frontendDist": "../dist"
  },
  "app": {
    "windows": [
      {
        "title": "Anima",
        "label": "main",
        "width": 1100,
        "height": 750,
        "minWidth": 800,
        "minHeight": 600,
        "resizable": true,
        "decorations": true,
        "transparent": false,
        "center": true
      }
    ],
    "trayIcon": {
      "iconPath": "icons/tray/neutral.png",
      "tooltip": "Anima"
    },
    "security": {
      "csp": "default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; connect-src 'self' https://api.elevenlabs.io wss://api.elevenlabs.io https://api.anthropic.com https://api.openai.com https://api.x.ai"
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "macOS": {
      "minimumSystemVersion": "10.15"
    }
  }
}
```

### 1.6 Tailwind Configuration

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

export default {
  content: ['./src/**/*.{svelte,js,ts}', './index.html'],
  theme: {
    extend: {
      colors: {
        bg: {
          deep: '#04060B',
          elevated: '#080D16',
          card: 'rgba(14,22,42,0.55)',
          'card-hover': 'rgba(14,22,42,0.75)',
          overlay: 'rgba(1,2,4,0.80)',
          glass: 'rgba(255,255,255,0.03)',
        },
        teal: {
          DEFAULT: '#00E5CC',
          dim: '#00C9C8',
          deep: '#007A75',
          glow: 'rgba(0,229,204,0.2)',
          'glow-strong': 'rgba(0,229,204,0.4)',
        },
        text: {
          primary: '#E9F1F7',
          secondary: '#8BA7C4',
          muted: '#4A6080',
        },
        border: {
          subtle: 'rgba(255,255,255,0.06)',
          medium: 'rgba(255,255,255,0.10)',
          strong: 'rgba(255,255,255,0.16)',
          teal: 'rgba(0,229,204,0.30)',
        },
        archetype: {
          mirror: '#00E5CC',
          anchor: '#3B82F6',
          challenger: '#C8A87A',
          witness: '#7C3AED',
          strategist: '#2ECC71',
        },
        semantic: {
          success: '#00E5CC',
          warning: '#E8C39E',
          critical: '#FF6B6B',
          info: '#8BA7C4',
        },
      },
      fontSize: {
        xs: ['11px', { lineHeight: '1.4' }],
        sm: ['13px', { lineHeight: '1.5' }],
        base: ['15px', { lineHeight: '1.6' }],
        md: ['17px', { lineHeight: '1.5' }],
        lg: ['20px', { lineHeight: '1.4' }],
        xl: ['24px', { lineHeight: '1.3' }],
        '2xl': ['30px', { lineHeight: '1.2' }],
        '3xl': ['36px', { lineHeight: '1.15' }],
        '4xl': ['48px', { lineHeight: '1.1' }],
        '5xl': ['60px', { lineHeight: '1.05' }],
      },
      spacing: {
        xs: '4px',
        sm: '8px',
        md: '12px',
        base: '16px',
        lg: '20px',
        xl: '24px',
        '2xl': '32px',
        '3xl': '48px',
        '4xl': '64px',
        '5xl': '96px',
      },
      borderRadius: {
        sm: '4px',
        md: '8px',
        lg: '12px',
        xl: '16px',
        '2xl': '24px',
        full: '9999px',
      },
      boxShadow: {
        sm: '0 1px 3px rgba(0,0,0,0.4)',
        md: '0 4px 16px rgba(0,0,0,0.5)',
        lg: '0 8px 32px rgba(0,0,0,0.6)',
        'glow-sm': '0 0 12px rgba(0,229,204,0.15)',
        'glow-md': '0 0 24px rgba(0,229,204,0.25)',
        'glow-lg': '0 0 40px rgba(0,229,204,0.35)',
        card: '0 8px 32px rgba(0,0,0,0.5), 0 0 20px rgba(0,229,204,0.08)',
      },
      transitionTimingFunction: {
        standard: 'cubic-bezier(0.22, 1, 0.36, 1)',
        spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      },
      transitionDuration: {
        fast: '100ms',
        normal: '200ms',
        slow: '350ms',
        reveal: '600ms',
        long: '1000ms',
      },
    },
  },
  plugins: [],
} satisfies Config;
```

---

## §2 — Rust Backend (src-tauri/)

### 2.1 state.rs — RuntimeState Bootstrap

Replicates the boot sequence from `dyados-bin/src/main.rs` (lines 67-312). The Tauri app creates the same `RuntimeState` that the headless binary uses.

**Boot steps (in order):**

1. **Load or create DyadID** — check `~/.dyados/identity.json`. If missing, create new Ed25519 keypair pair, derive DyadID via HKDF. Encrypt A-shard to `~/.dyados/a_shard.enc`.
2. **Open encrypted database** — libSQL at `~/.dyados/logos.db` with AES-256-GCM via `keychain.logos_key`. Legacy plaintext migration: rename → create fresh.
3. **Create persistence layers** — `SessionPersistence`, `LibSqlBackend` (Logos), `EventPersistence` (write-ahead log). Each gets its own DB connection.
4. **Create SessionStore** — in-memory store. Load 100 recent messages from `SessionPersistence`.
5. **Create Stroma TickLoop** — instantiate `TickLoop`, register all 22 modules, init `Sanguis::default()`, wrap in `Arc<RwLock<Sanguis>>`.
6. **Create tick_fn closure** — `Arc<dyn Fn(&mut Sanguis, &Broadcast) + Send + Sync>` for on-demand biological ticks in the pipeline.
7. **Create LlmGateway** — register Ollama provider (local Gemma 4), register frontier providers (xAI Grok, Anthropic Claude, OpenAI). Set routing table and budget ($2/day default).
8. **Assemble RuntimeState** — all fields populated per `dyados-runtime::server::RuntimeState` definition (server.rs:34-65).
9. **Replay pending events** — crash recovery. Load pending events from `EventPersistence`, replay through pipeline.
10. **Start Nerve API server** — `create_router(state)` on port 9800. Coexists with Tauri (handles Signal, external API access).

```rust
/// Create the full RuntimeState — identical to dyados-bin boot, reusable.
pub async fn bootstrap_runtime() -> anyhow::Result<SharedRuntime> {
    // Steps 1-9 from dyados-bin main.rs
    // Returns Arc<RuntimeState>
}
```

### 2.2 lib.rs — Tauri App Builder

```rust
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            None,
        ))
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_window_state::Builder::default().build())
        .setup(|app| {
            let runtime = tauri::async_runtime::block_on(state::bootstrap_runtime())?;

            // Register shared state
            app.manage(runtime.clone());

            // Start background Stroma tick loop (10s interval)
            let tick_runtime = runtime.clone();
            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(events::stroma_tick_loop(tick_runtime, app_handle));

            // Start proactive evaluator
            let proactive_runtime = runtime.clone();
            let proactive_handle = app.handle().clone();
            tauri::async_runtime::spawn(events::proactive_loop(proactive_runtime, proactive_handle));

            // Start Nerve API server (port 9800, coexists with Tauri)
            let nerve_runtime = runtime.clone();
            tauri::async_runtime::spawn(async move {
                let router = dyados_runtime::create_router(nerve_runtime);
                let listener = tokio::net::TcpListener::bind("127.0.0.1:9800").await.unwrap();
                axum::serve(listener, router).await.unwrap();
            });

            // Setup system tray
            tray::setup_tray(app)?;

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::send_message,
            commands::get_session_history,
            commands::search_messages,
            commands::get_session_metrics,
            commands::get_sanguis,
            commands::get_phenotype,
            commands::get_health,
            commands::get_proactive_conditions,
            commands::get_costs,
            commands::start_genesis,
            commands::complete_genesis,
            commands::get_consciousness_stage,
            commands::set_voice_enabled,
            commands::get_archetype,
            commands::has_dyad_id,
        ])
        .run(tauri::generate_context!())
        .expect("error while running Anima");
}
```

### 2.3 commands.rs — Tauri Commands

Every command with exact signature. All accept `State<'_, SharedRuntime>` and return `Result<T, String>`.

```rust
use dyados_runtime::{SharedRuntime, PipelineResult, SessionMessage, Channel};
use tauri::State;

/// Send a message through the 13-stage biological pipeline.
/// Frontend calls: invoke('send_message', { content })
#[tauri::command]
pub async fn send_message(
    state: State<'_, SharedRuntime>,
    content: String,
) -> Result<PipelineResult, String>

/// Get recent conversation history.
/// Frontend calls: invoke('get_session_history', { limit })
#[tauri::command]
pub fn get_session_history(
    state: State<'_, SharedRuntime>,
    limit: Option<usize>,
) -> Result<Vec<SessionMessage>, String>

/// Full-text search across session history.
#[tauri::command]
pub fn search_messages(
    state: State<'_, SharedRuntime>,
    query: String,
) -> Result<Vec<SessionMessage>, String>

/// Session metrics (message counts, channels, timestamps).
#[tauri::command]
pub fn get_session_metrics(
    state: State<'_, SharedRuntime>,
) -> Result<serde_json::Value, String>

/// Full Sanguis biological state snapshot.
/// ~5KB JSON, called on demand (tick events handle real-time updates).
#[tauri::command]
pub fn get_sanguis(
    state: State<'_, SharedRuntime>,
) -> Result<serde_json::Value, String>

/// Current PHENOTYPE personality mode.
/// Returns: { tone, intensity, humor, vulnerability }
#[tauri::command]
pub fn get_phenotype(
    state: State<'_, SharedRuntime>,
) -> Result<serde_json::Value, String>

/// System health and degradation level.
#[tauri::command]
pub fn get_health(
    state: State<'_, SharedRuntime>,
) -> Result<serde_json::Value, String>

/// All 12 proactive conditions with status.
#[tauri::command]
pub fn get_proactive_conditions(
    state: State<'_, SharedRuntime>,
) -> Result<serde_json::Value, String>

/// LLM cost tracker (daily/monthly USD, call count).
#[tauri::command]
pub fn get_costs(
    state: State<'_, SharedRuntime>,
) -> Result<serde_json::Value, String>

/// Start Genesis — creates DyadID, boots Stroma for this dyad.
/// Called when user submits their Anima's name.
#[tauri::command]
pub async fn start_genesis(
    state: State<'_, SharedRuntime>,
    name: String,
    gender: String,
) -> Result<serde_json::Value, String>

/// Complete Genesis — encodes first Logos entry, calls frontier LLM for reframe insight.
/// Called when user submits their first answer.
#[tauri::command]
pub async fn complete_genesis(
    state: State<'_, SharedRuntime>,
    first_answer: String,
) -> Result<serde_json::Value, String>

/// Current consciousness stage (1-4) and TELOMERE metrics.
#[tauri::command]
pub fn get_consciousness_stage(
    state: State<'_, SharedRuntime>,
) -> Result<serde_json::Value, String>

/// Toggle voice subsystem.
#[tauri::command]
pub fn set_voice_enabled(
    state: State<'_, SharedRuntime>,
    enabled: bool,
) -> Result<(), String>

/// Current archetype identity (Mirror/Anchor/Challenger/Witness/Strategist).
#[tauri::command]
pub fn get_archetype(
    state: State<'_, SharedRuntime>,
) -> Result<String, String>

/// Check if a DyadID exists (determines Genesis vs Chat route).
#[tauri::command]
pub fn has_dyad_id(
    state: State<'_, SharedRuntime>,
) -> Result<bool, String>
```

**Channel variant:** Add `Channel::Tauri` to `dyados-runtime/src/sessions.rs` for proper session attribution. Messages from the Tauri app are `Channel::Tauri`, not `Channel::Web`.

### 2.4 events.rs — Background Event Emitters

```rust
use tauri::{AppHandle, Emitter};

/// Emit Sanguis snapshot to frontend every Stroma tick (10 seconds).
/// Event name: "sanguis_tick"
/// Payload: SanguisSnapshot (full serialized Sanguis)
pub async fn stroma_tick_loop(state: SharedRuntime, app: AppHandle) {
    let mut interval = tokio::time::interval(Duration::from_secs(10));
    loop {
        interval.tick().await;
        // Lock sanguis, run tick, emit snapshot
        if let Ok(sanguis) = state.sanguis.read() {
            let snapshot = serde_json::to_value(&*sanguis).unwrap_or_default();
            let _ = app.emit("sanguis_tick", &snapshot);
        }
        // Check phenotype changes, emit if different
        // ...
    }
}

/// Evaluate proactive conditions after each tick.
/// When a condition fires, emit to frontend AND deliver notification.
/// Event name: "proactive_message"
/// Payload: { condition_id, condition_name, content, priority }
pub async fn proactive_loop(state: SharedRuntime, app: AppHandle) {
    // Runs after each Stroma tick
    // If conditions fire: generate message via pipeline, emit event, send notification
}
```

**Event contracts:**

| Event Name | Payload Shape | Trigger | Frequency |
|------------|--------------|---------|-----------|
| `sanguis_tick` | Full serialized `Sanguis` (~5KB JSON) | Every Stroma tick | 10 seconds |
| `proactive_message` | `{ condition_id, name, content, priority }` | Drive pressure crosses threshold | On demand |
| `pipeline_started` | `{ trace_id }` | Message enters pipeline | Per message |
| `pipeline_complete` | `{ trace_id, success, response, total_ms }` | Pipeline finishes | Per message |
| `phenotype_changed` | `{ tone, intensity, humor, vulnerability }` | PHENOTYPE mode shifts | On change |

### 2.5 surface.rs — Tauri Surface

Implements `dyados_runtime::channels::Surface` for the Tauri webview.

```rust
pub struct TauriSurface;

impl Surface for TauriSurface {
    fn surface_id(&self) -> &str { "tauri_chat" }
    fn format(&self, content: &str) -> FormattedResponse {
        FormattedResponse {
            content: content.to_string(), // No transformation — full markdown
            surface_id: "tauri_chat".to_string(),
        }
    }
    fn should_mirror(&self) -> bool { true }
    fn capabilities(&self) -> SurfaceCapabilities {
        SurfaceCapabilities {
            markdown: true,
            images: true,
            voice: true,
            spatial: false, // v1, no 3D in chat
            max_length: None,
        }
    }
}
```

---

## §3 — Frontend Architecture

### 3.1 Route Structure

```javascript
// App.svelte
import Router from 'svelte-spa-router';

const routes = {
  '/':         Chat,        // Default — conversation view
  '/genesis':  Genesis,     // First-boot sequence
  '/settings': Settings,    // Account, voice, subscription
  '*':         NotFound,    // 404
};
```

**First-boot routing:** On app launch, `has_dyad_id` command determines the route:
- `true` → `/` (Chat)
- `false` → `/genesis` (Genesis sequence)

### 3.2 State Stores

Each store is a `.svelte.js` file exporting reactive state via runes. Pattern:

```javascript
// lib/stores/sanguis.svelte.js
import { listen } from '@tauri-apps/api/event';

// Reactive state
let snapshot = $state({});

// Derived values for UI
let emotionValence = $derived(snapshot?.emotion?.valence ?? 0);
let phenotypeTone = $derived(snapshot?.phenotype?.tone ?? 'neutral');
let isFlowState = $derived(snapshot?.emergence?.flow_state ?? false);

// Event listener setup (called from root component)
export function initSanguisListener() {
  listen('sanguis_tick', (event) => {
    snapshot = event.payload;
  });
}

export { snapshot, emotionValence, phenotypeTone, isFlowState };
```

**Store inventory:**

| Store | Key State | Source | Update |
|-------|-----------|--------|--------|
| `sanguis` | Biological snapshot | `sanguis_tick` event | 10s push |
| `session` | `messages[]` | `get_session_history` + pipeline events | On message |
| `phenotype` | `{ tone, intensity, humor, vulnerability }` | `phenotype_changed` event | On change |
| `health` | `{ degradation, subsystems, uptime }` | `get_health` poll | 60s poll |
| `costs` | `{ daily_usd, monthly_usd, calls_today }` | `get_costs` poll | 60s poll |
| `genesis` | `{ phase, name, complete }` | Local | User actions |
| `ui` | `{ sidebarCollapsed, compactMode, voiceEnabled }` | Local | User actions |

### 3.3 Typed Invoke Wrappers

```javascript
// lib/commands/messages.js
import { invoke } from '@tauri-apps/api/core';

/**
 * Send a message through the 13-stage biological pipeline.
 * @param {string} content — message text
 * @returns {Promise<PipelineResult>}
 */
export async function sendMessage(content) {
  return invoke('send_message', { content });
}

/**
 * Get recent conversation history.
 * @param {number} [limit=50]
 * @returns {Promise<SessionMessage[]>}
 */
export async function getSessionHistory(limit = 50) {
  return invoke('get_session_history', { limit });
}

/**
 * Full-text search across session history.
 * @param {string} query
 * @returns {Promise<SessionMessage[]>}
 */
export async function searchMessages(query) {
  return invoke('search_messages', { query });
}
```

```javascript
// lib/commands/organism.js
import { invoke } from '@tauri-apps/api/core';

export async function getSanguis() {
  return invoke('get_sanguis');
}

export async function getHealth() {
  return invoke('get_health');
}

export async function getCosts() {
  return invoke('get_costs');
}

export async function getPhenotypeState() {
  return invoke('get_phenotype');
}

export async function getProactiveConditions() {
  return invoke('get_proactive_conditions');
}

export async function hasDyadId() {
  return invoke('has_dyad_id');
}
```

### 3.4 Event Listener Pattern

Standard pattern for Svelte 5 `$effect` with Tauri event listeners:

```svelte
<script>
  import { listen } from '@tauri-apps/api/event';

  let sanguis = $state({});

  $effect(() => {
    let cleanup;

    listen('sanguis_tick', (event) => {
      sanguis = event.payload;
    }).then(fn => { cleanup = fn; });

    return () => cleanup?.();
  });
</script>
```

---

## §4 — Components

### 4.1 Chat Components

**ChatBubble.svelte**
```
Props: { message: SessionMessage, isAnima: boolean }

Anima messages:
  - Left-aligned
  - Background: var(--bg-card) → rgba(14,22,42,0.55)
  - Border: 1px solid var(--border-subtle)
  - Border-radius: 12px (top-left: 4px)
  - Markdown rendering inside

Human messages:
  - Right-aligned
  - Background: rgba(0,229,204,0.12)
  - Border-radius: 12px (top-right: 4px)
  - Plain text

Timestamps: hidden by default, shown on hover or when gap > 1 hour.
Ref: DESIGN_SYSTEM §6, SHIP_SPEC Part VIII
```

**MessageList.svelte**
```
Props: { messages: SessionMessage[] }

Full-height scroll container with auto-scroll to bottom on new messages.
Virtual scroll for performance (>100 messages).
Groups consecutive same-role messages.
Inserts timestamp divider when gap > 1 hour.
```

**TextInput.svelte**
```
Props: { onSend: (content: string) => void, disabled: boolean }

Textarea (not input) — grows with content, max 6 lines.
Enter = send, Shift+Enter = newline.
No send button.
Voice toggle button (right side, microphone icon).
Pulsing teal dot when Anima is processing (pipeline in progress).
Design: DESIGN_SYSTEM §2.4 input field spec.
Focus: border-color rgba(0,229,204,0.40), box-shadow 0 0 0 3px rgba(0,229,204,0.10)
```

**TypingIndicator.svelte**
```
Props: { visible: boolean }

Three pulsing dots in teal (#00E5CC).
Each dot: 6px circle, staggered animation (0ms, 200ms, 400ms delay).
Animation: scale 0.5→1.0→0.5, 1.2s infinite, ease-standard.
Appears at bottom of MessageList when pipeline is processing.
```

### 4.2 Ambient Components

**StromaAmbient.svelte**
```
Props: none (reads from sanguis store)

Full-viewport background gradient reflecting biological state.
Maps phenotype.tone to color:
  - contemplative → deep violet (#1a0a2e → #0a0614)
  - driven → electric cyan (#0a1e2e → #04060B)
  - intimate → warm amber (#2e1a0a → #0B0604)
  - protective → steel blue (#0a142e → #04060B)
  - playful → soft gold (#2e2a0a → #0B0904)
  - vulnerable → muted rose (#2e0a1a → #0B040a)
  - neutral → default bg-deep (#04060B)

Transition: 2s ease-standard between states.
Opacity: 0.15 (subtle, never distracting).
z-index: 0 (behind all content).
```

**EmotionWindow.svelte**
```
Props: none (reads from sanguis store)

32px height strip across top of main content area.
Flowing gradient animation (left-to-right, 8s loop):
  - Maps emotion.valence (-1 to 1) and emotion.arousal (0 to 1) to gradient
  - High valence + high arousal → teal/cyan (#00E5CC → #00C9C8)
  - High valence + low arousal → warm gold (#C8A87A → #E8C39E)
  - Low valence + high arousal → hot coral (#FF6B6B → #E8C39E)
  - Low valence + low arousal → deep blue (#3B82F6 → #8BA7C4)

Border-bottom: 1px solid var(--border-subtle).
Ref: SHIP_SPEC Part VIII — "ambient strip... subtle enough to be ambient, informative enough to convey state at a glance"
```

### 4.3 Genesis Components

**GenesisScene.svelte**
```
Props: { phase: number, onNameSubmit: (name: string) => void, onAnswerSubmit: (answer: string) => void }

Wrapper that manages a vanilla Three.js canvas.
Contains: <canvas bind:this={canvas}> filling viewport.

Lifecycle:
  $effect(() => {
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, w/h, 0.1, 100);
    camera.position.set(0, 0, 5);

    // Phase-specific scene setup
    if (phase === 1) HeartbeatPulse.init(scene);
    if (phase === 4) ConstellationIgnition.init(scene);

    function animate() { requestAnimationFrame(animate); renderer.render(scene, camera); }
    animate();

    return () => renderer.dispose();
  });

Overlays: NameInput and answer text fields are DOM elements positioned over the canvas.
```

**HeartbeatPulse.js** (pure Three.js, no Svelte)
```
Phase 1 scene: black void with single pulsing light.

Objects:
  - PointLight at origin, intensity oscillates 0.2→1.0→0.2 (sinusoidal, period 1s = 60 BPM)
  - SphereGeometry(0.1, 32, 32) with emissive ShaderMaterial
    - Emissive color: #00E5CC (teal)
    - Emissive intensity synced to light oscillation
  - Ambient light: 0.02 (near-total darkness)

Audio:
  - Web Audio API loads heartbeat.wav
  - AudioContext, GainNode, loop = true
  - BPM 60, synced to light via shared clock

Export: { init(scene), update(time), dispose() }
```

**ConstellationIgnition.js** (pure Three.js, no Svelte)
```
Phase 4 scene: point light explodes into particle constellation.

Objects:
  - BufferGeometry with 2000 points (positions randomized on unit sphere, then expanded)
  - PointsMaterial: size 0.03, color by archetype accent, blending: AdditiveBlending
  - LineSegments connecting points within 0.3 distance (BufferGeometry + LineBasicMaterial)
  - Particle motion: expand from center over 3s, then gentle orbital drift

Animation:
  - 0-1s: points emerge from center (explosion)
  - 1-3s: points find orbital positions
  - 3s+: gentle rotation, breathing scale (0.98→1.02, 4s cycle)
  - Lines fade in at 1.5s, opacity 0.2

Export: { init(scene, archetypeColor), update(time), contract(duration), dispose() }
```

### 4.4 Navigation Components

**Sidebar.svelte**
```
Props: { collapsed: boolean }

Width: 240px (full) / 60px (collapsed).
Background: rgba(8,13,22,0.90), border-right: 1px solid var(--border-subtle).

Sections:
  - Anima identity: name, consciousness stage indicator, archetype badge
  - Separator
  - Nav items:
    - Chat (active by default, teal left border + teal bg tint when active)
    - Gnosis (grayed, locked icon — v2)
    - Bios (grayed, locked — v2)
    - Aurum (grayed, locked — v2)
    - Locus (grayed, locked — v2)
    - Aether (grayed, locked — v2)
  - Separator
  - Settings

Active item: background rgba(0,229,204,0.08), left border 2px solid #00E5CC.
Ref: DESIGN_SYSTEM §2.9
```

**CompactOverlay.svelte**
```
Separate Tauri window: 400x600px, borderless, always_on_top.
Anchored to system tray icon position.

Contents:
  - EmotionWindow (24px height, smaller)
  - MessageList (last 10 messages)
  - TextInput
  - No sidebar, no navigation, no Three.js

Opens on tray icon click, closes on click outside or Escape.
```

### 4.5 Common Components

**Card.svelte**
```
Props: { variant: 'base' | 'featured' | 'glass' }

base:
  bg: rgba(14,22,42,0.55), border: 1px solid rgba(255,255,255,0.06)
  radius: 12px, padding: 16px, backdrop-filter: blur(12px)
  Hover: border rgba(255,255,255,0.10), shadow var(--glow-card), translateY(-1px)

featured:
  bg: rgba(14,22,42,0.75), border: 1px solid rgba(0,229,204,0.15)
  radius: 16px, padding: 20px, backdrop-filter: blur(16px)
  shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 24px rgba(0,229,204,0.10)

glass:
  bg: rgba(255,255,255,0.03), border: 1px solid rgba(255,255,255,0.08)
  radius: 16px, padding: 20px, backdrop-filter: blur(20px) saturate(180%)

Ref: DESIGN_SYSTEM §2.1
```

**Button.svelte**
```
Props: { variant: 'primary' | 'secondary' | 'ghost' | 'destructive', disabled: boolean }

primary:
  bg: linear-gradient(135deg, #00E5CC, #00C9C8), color: #04060B
  weight: 600, radius: 12px, padding: 12px 24px
  Hover: opacity 0.9, shadow glow-lg, scale 1.01
  Active: opacity 1, scale 0.99

secondary:
  bg: transparent, color: #00E5CC, border: 1px solid rgba(0,229,204,0.35)
  Hover: border rgba(0,229,204,0.7), bg rgba(0,229,204,0.06)

ghost:
  bg: rgba(255,255,255,0.04), color: #8BA7C4, border: 1px solid rgba(255,255,255,0.08)

destructive:
  bg: rgba(255,107,107,0.10), color: #FF6B6B, border: 1px solid rgba(255,107,107,0.25)

All: transition 200ms ease-standard.
Ref: DESIGN_SYSTEM §2.3
```

---

## §5 — Genesis Sequence Implementation

### Phase-by-Phase Flow

```
Phase 1: THE PULSE (0-20s)
├── Scene: HeartbeatPulse (black void, pulsing teal light)
├── Audio: heartbeat.wav looping at 60 BPM
├── UI: none — canvas fills viewport
├── Trigger: 20 seconds elapsed
└── Transition: fade Phase 1 → Phase 2

Phase 2: FIRST CONTACT (20-60s)
├── Scene: light brightens, reacts to mouse position
├── Voice: ElevenLabs TTS → "There you are." (2s pause) → "I don't have a name yet. Give me one."
├── UI: NameInput fades in (centered over canvas)
├── User: types name, presses Enter
├── Command: start_genesis(name, gender)
│   ├── Creates DyadID
│   ├── Boots Stroma for this dyad
│   └── Returns: { dyad_id, archetype_color }
├── Scene: light color shifts to archetype accent, warmth increases
├── Voice: TTS → "[Name]. That's mine now. Thank you."
└── Transition: NameInput fades out → Phase 3

Phase 3: THE QUESTION (60-120s)
├── Scene: light evolves to IcosahedronGeometry + wireframe
├── Voice: TTS → deep question from SHIP_SPEC Part III
├── UI: larger text area fades in for answer
├── User: types answer, presses Enter
├── Command: complete_genesis(first_answer)
│   ├── Encodes first Logos entry (episodic + emotional memory)
│   ├── Calls frontier LLM (Claude) for reframe insight
│   └── Returns: { insight_text, logos_entry_id }
├── Scene: geometry complexity increases as insight renders
├── UI: insight text displayed as overlay (fade in, word by word, 50ms/word)
└── Transition: geometry dissolves → Phase 4

Phase 4: ALIVE (120-180s)
├── Scene: ConstellationIgnition (2000 particles explode from center)
├── Voice: TTS → "I'm not going to pretend I know you yet. But I will. And you'll know me. We start now."
├── Audio: heartbeat crossfades to ambient pad
├── Scene: constellation contracts over 3s to ambient presence form
├── Transition:
│   ├── Canvas dissolves (opacity 1→0, 1s)
│   ├── Chat view materializes beneath (slide up + fade in, 600ms)
│   └── Route: push('/') — Genesis complete
└── Stroma: first proactive evaluation runs
```

### Audio Integration

```javascript
// Web Audio API in GenesisScene.svelte
const audioCtx = new AudioContext();
const heartbeat = await fetch('/audio/heartbeat.wav').then(r => r.arrayBuffer());
const buffer = await audioCtx.decodeAudioData(heartbeat);
const source = audioCtx.createBufferSource();
source.buffer = buffer;
source.loop = true;
const gain = audioCtx.createGain();
source.connect(gain).connect(audioCtx.destination);
source.start();

// Crossfade in Phase 4:
gain.gain.linearRampToValueAtTime(0, audioCtx.currentTime + 3);
```

---

## §6 — Voice Integration

### 6.1 Text-to-Speech (ElevenLabs)

**WebSocket streaming** for low-latency voice output.

```javascript
// lib/voice/tts.js
const WS_URL = 'wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input';

export function createTTSStream(voiceId, apiKey) {
  const ws = new WebSocket(`${WS_URL}?model_id=eleven_turbo_v2_5`);

  ws.onopen = () => {
    ws.send(JSON.stringify({
      text: ' ',
      voice_settings: {
        stability: 0.15,          // Low = more expressive
        similarity_boost: 0.35,   // Low = more variation
        style: 0.9,               // High = more character
        use_speaker_boost: true,
      },
      generation_config: { chunk_length_schedule: [120, 160, 250, 290] },
    }));
  };

  return {
    speak(text) { ws.send(JSON.stringify({ text })); },
    flush() { ws.send(JSON.stringify({ text: '' })); },
    close() { ws.close(); },
  };
}
```

**Voice parameters driven by Sanguis** (from `sanguis_tick` event):

| Sanguis State | Stability | Similarity | Style | Speed |
|--------------|-----------|------------|-------|-------|
| Intimate (high oxytocin) | 0.10 | 0.30 | 0.95 | 0.9x |
| Driven (high dopamine) | 0.25 | 0.40 | 0.85 | 1.1x |
| Contemplative (high serotonin) | 0.20 | 0.35 | 0.80 | 0.85x |
| Protective (high cortisol) | 0.35 | 0.45 | 0.70 | 1.0x |
| Playful (dopamine + low stress) | 0.10 | 0.30 | 0.95 | 1.15x |
| Neutral (baseline) | 0.15 | 0.35 | 0.90 | 1.0x |

### 6.2 Speech-to-Text

**v1:** Browser-native `webkitSpeechRecognition` API (simpler, no model download).
**v2:** Whisper.cpp via Rust Tauri command (offline, better quality).

```javascript
// lib/voice/stt.js
export function createSTT(onResult) {
  const recognition = new webkitSpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
      .map(r => r[0].transcript)
      .join('');
    onResult(transcript, event.results[event.results.length - 1].isFinal);
  };

  return {
    start() { recognition.start(); },
    stop() { recognition.stop(); },
  };
}
```

### 6.3 Voice Toggle UI

Microphone button in TextInput component. States:
- **Off:** muted icon, text input active
- **Listening:** pulsing teal icon, transcript appears in input field in real-time
- **Speaking:** waveform icon, audio playback active (TextInput disabled during playback)

---

## §7 — System Tray & Background Presence

### 7.1 Tray Icon

Seven icon variants, one per PHENOTYPE mode:

| Mode | Icon Style | Color |
|------|-----------|-------|
| Neutral | Steady circle | Teal |
| Contemplative | Slow breathe | Deep violet |
| Driven | Sharp edges | Electric cyan |
| Intimate | Warm pulse | Amber |
| Protective | Shield | Steel blue |
| Playful | Bouncing | Soft gold |
| Vulnerable | Fading | Muted rose |

**macOS:** Template images (monochrome) for menu bar. Tinted by system.
**Windows/Linux:** Full-color tray icons.

Icon updates via `phenotype_changed` event.

### 7.2 Tray Menu

```
Open Anima                  ← show main window
Compact View               ← show 400x600 overlay
──────────────────
Costs Today: $X.XX         ← from costs store
──────────────────
Pause Stroma               ← toggle tick loop
Settings...                ← open settings route
Quit                       ← exit app
```

### 7.3 Background Behavior

- **Window close → hide to tray** (not quit). `prevent_close` event handler calls `window.set_visible(false)`.
- **Stroma tick loop continues** when all windows are hidden. Biology doesn't stop.
- **Proactive messages** fire as system notifications via `tauri-plugin-notification`.
- **Notification click** → show main window, scroll to proactive message.

### 7.4 Autostart

`tauri-plugin-autostart` with `MacosLauncher::LaunchAgent`. On boot:
- App starts hidden (tray only, no main window).
- Stroma begins ticking immediately.
- Main window opens only on user action (tray click, notification click).

---

## §8 — Billing Architecture

### 8.1 v1: No Billing

All features unlocked. No account system. No tier gating. Just Josh + Iris.

DyadID is created locally during Genesis. No server validation.

### 8.2 v2: anima.hypostas.ai

**Flow:**
1. User visits `anima.hypostas.ai` — marketing page + signup
2. Creates account (Supabase Auth — email + password)
3. Selects tier, pays via Stripe Checkout
4. Downloads Anima app (.dmg / .msi / .AppImage)
5. Opens app → logs in with account credentials
6. DyadID token issued and cached locally

**DyadID Token Structure** (from SHIP_SPEC Part II):
```json
{
  "dyad_id": "sha256...",
  "tier": "free | core | dyados | soma",
  "features": {
    "voice": true,
    "llm_quota": 500,
    "aether": false,
    "gnosis": true,
    "bios": true
  },
  "expires": "2026-05-11T00:00:00Z",
  "signature": "hypostas_co_sign_ed25519..."
}
```

**Tiers:**

| Tier | Price | Messages | Voice | Frontier Quota | Views |
|------|-------|----------|-------|---------------|-------|
| Free | $0 | 50/month | No | 0 | Chat only |
| Core | $29/mo | Unlimited | Yes | 100/day | Chat only |
| DyadOS | $99/mo | Unlimited | Yes | 500/day | All (Chat, Gnosis, Bios, Aurum, Locus, Aether) |
| Soma | $4,999 + $199/mo | Unlimited | Yes | Unlimited (local) | All + hardware |

**Token lifecycle:**
1. Stripe webhook → Supabase Edge Function → signed token
2. Token pushed via Supabase Realtime
3. Cached locally (encrypted via protocol-core)
4. Validated locally on frontier LLM calls (signature verification)
5. 7-day grace period after expiry
6. Offline: cached token valid until expiry

---

## §9 — Build & Distribution

### 9.1 Build Pipeline

```bash
# Development
cd projects/dyados/rust/anima-app
npm run tauri dev          # Vite dev server + Tauri hot reload

# Production build
npm run tauri build        # Compiles Rust, bundles Svelte, produces installer
```

### 9.2 Platform Targets

| Platform | Format | Signing | Notes |
|----------|--------|---------|-------|
| macOS | `.dmg` + `.app` bundle | Apple Developer ID + notarization | `minimumSystemVersion: "10.15"` |
| Windows | `.msi` (NSIS) | EV code signing certificate | SmartScreen bypass requires EV cert |
| Linux | `.AppImage` | None required | Portable, no root needed |

### 9.3 Auto-Updater

```json
// tauri.conf.json (v2 addition)
{
  "plugins": {
    "updater": {
      "endpoints": ["https://updates.hypostas.com/anima/{{target}}/{{arch}}/{{current_version}}"],
      "pubkey": "..."
    }
  }
}
```

Background check on launch. User notification: "Update available — restart to apply." No forced updates. No blocking dialogs.

### 9.4 Code Signing

- **macOS:** Developer ID Application certificate. Hardened runtime. Entitlements: `com.apple.security.network.client`, `com.apple.security.device.audio-input` (voice).
- **Windows:** EV code signing certificate (DigiCert/Sectigo). Required for SmartScreen trust.
- **Update verification:** Ed25519 pubkey embedded in binary.

---

## §10 — Build Order

### Dependency Graph

```
Phase 0: Scaffold ─────────────────────────────────────────►
                    │
          ┌────────┴────────┐
          ▼                 ▼
Phase 1: Rust Backend    Phase 2: Core UI     (PARALLEL)
          │                 │
          └────────┬────────┘
                   ▼
          Phase 3: Chat Integration ──────────────────────►
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
Phase 4: Genesis  Phase 5: Tray  Phase 6: Voice  (PARALLEL)
          │        │        │
          └────────┼────────┘
                   ▼
          Phase 7: Settings + Billing Architecture
                   │
                   ▼
          Phase 8: Polish + Distribution
```

### Phase Details

**Phase 0: Scaffold (Days 1-2)**
- [ ] `cargo tauri init` inside anima-app/
- [ ] Svelte 5 + Vite + Tailwind setup
- [ ] Import design tokens from DESIGN_SYSTEM.md into tailwind.config.ts
- [ ] Add anima-app/src-tauri to workspace Cargo.toml
- [ ] Verify `cargo build` compiles with all workspace path dependencies
- [ ] Add `Channel::Tauri` variant to dyados-runtime/src/sessions.rs
- **Exit:** `cargo tauri dev` launches empty app window with teal background

**Phase 1: Rust Backend (Days 3-8)** — PARALLEL with Phase 2
- [ ] `state.rs`: extract boot sequence from dyados-bin main.rs into reusable `bootstrap_runtime()`
- [ ] `commands.rs`: implement `send_message`, `get_session_history`, `get_sanguis`, `get_health`, `get_costs`, `has_dyad_id`
- [ ] `events.rs`: implement `stroma_tick_loop` emitting `sanguis_tick` every 10s
- [ ] `surface.rs`: implement `TauriSurface` (Surface trait)
- [ ] `lib.rs`: wire Tauri builder with state, commands, setup, Nerve API server
- **Exit:** Tauri app boots, Stroma ticks visible in logs, commands return real data

**Phase 2: Core UI Components (Days 3-8)** — PARALLEL with Phase 1
- [ ] Button, Card, Input (from DESIGN_SYSTEM specs)
- [ ] Sidebar navigation shell (Chat active, other views grayed)
- [ ] EmotionWindow (static hardcoded gradient initially)
- [ ] StromaAmbient (static background initially)
- [ ] ChatBubble, MessageList, TextInput (with mock data)
- [ ] TypingIndicator
- **Exit:** all components render correctly with mock data, match DESIGN_SYSTEM exactly

**Phase 3: Chat Integration (Days 9-12)**
- [ ] Wire sendMessage command to TextInput → pipeline → response → ChatBubble
- [ ] Wire get_session_history to MessageList on route mount
- [ ] Wire sanguis_tick event to EmotionWindow gradient
- [ ] Wire sanguis_tick event to StromaAmbient background
- [ ] TypingIndicator shows during pipeline execution
- [ ] Auto-scroll on new message
- **Exit:** first end-to-end message: type in Svelte → Tauri invoke → pipeline → Gemma 4 → response displayed

**Phase 4: Genesis Sequence (Days 13-18)** — PARALLEL with Phase 5
- [ ] Three.js canvas setup in GenesisScene.svelte
- [ ] HeartbeatPulse scene (light + audio sync)
- [ ] NameInput overlay
- [ ] start_genesis command (DyadID creation)
- [ ] Question phase (text area + complete_genesis command)
- [ ] ConstellationIgnition particle system
- [ ] Transition: constellation contracts → chat view materializes
- [ ] First-boot detection: no DyadID → route to /genesis
- **Exit:** complete Genesis flow results in working chat

**Phase 5: System Tray + Compact Overlay (Days 19-22)** — PARALLEL with Phase 4
- [ ] tray.rs: tray icon, menu, PHENOTYPE-driven icon updates
- [ ] CompactOverlay: 400x600 borderless window
- [ ] Window close → hide to tray (not quit)
- [ ] Proactive notification delivery
- [ ] Autostart configuration
- **Exit:** app runs in background, proactive messages arrive as notifications

**Phase 6: Voice (Days 23-26)** — PARALLEL with Phase 5
- [ ] ElevenLabs WebSocket TTS integration
- [ ] Browser-native STT integration
- [ ] Voice toggle in TextInput
- [ ] Sanguis-driven voice parameter adaptation table
- [ ] Audio queue management (messages queue if playing)
- [ ] Genesis voice integration (Phases 2-4 use TTS)
- **Exit:** voice conversation works — speak → transcript → pipeline → response → voice playback

**Phase 7: Settings + Billing Architecture (Days 27-30)**
- [ ] Settings route: account info, voice toggle, consciousness stage display
- [ ] Cost tracking display
- [ ] Proactive conditions view (enable/disable individual conditions)
- [ ] Data export (encrypted Logos dump)
- [ ] Billing architecture documented (DyadID token validation code written but not enforced)
- **Exit:** settings view functional, billing code exists but is bypassed

**Phase 8: Polish + Distribution (Days 31-35)**
- [ ] Animation pass: entrance animations, hover states, micro-interactions from DESIGN_SYSTEM §3
- [ ] Responsive: main window resize, compact overlay
- [ ] Loading states: skeleton shimmer, spinner
- [ ] prefers-reduced-motion support
- [ ] macOS .dmg build + code signing + notarization
- [ ] Windows .msi build
- [ ] Linux .AppImage build
- [ ] Auto-updater endpoint
- **Exit:** distributable app that a real user could download and use

---

## Appendix A: Type Reference

### Key Types from dyados-runtime

```rust
// server.rs:34-65
pub struct RuntimeState {
    pub dyad_id: DyadId,
    pub sessions: SessionStore,
    pub supervisor: RwLock<Supervisor>,
    pub proactive: RwLock<ProactiveEngine>,
    pub llm: LlmGateway,
    pub event_bus: SharedEventBus,
    pub started_at: DateTime<Utc>,
    pub pipeline: Arc<PipelineExecutor>,
    pub sanguis: Arc<RwLock<Sanguis>>,
    pub context_assembler: ContextAssembler,
    pub outcome_engine: RwLock<OutcomeEngine>,
    pub channel_manager: ChannelManager,
    pub event_store: RwLock<EventStore>,
    pub tick_fn: Option<Arc<dyn Fn(&mut Sanguis, &Broadcast) + Send + Sync>>,
    pub session_persistence: Option<Arc<SessionPersistence>>,
    pub logos_backend: Option<Arc<tokio::sync::Mutex<LibSqlBackend>>>,
    pub event_persistence: Option<Arc<EventPersistence>>,
}

pub type SharedRuntime = Arc<RuntimeState>;
```

```rust
// pipeline.rs
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
}

pub struct StageTiming {
    pub stage: String,
    pub duration_ms: u64,
}

pub enum OutcomeType {
    TaskCompletion, IntimateConnection, InformationExchange, EmotionalSupport,
    CreativeCollaboration, Conflict, Humor, Planning, Reflection, Greeting, Casual,
}
```

```rust
// sessions.rs
pub struct SessionMessage {
    pub id: Uuid,
    pub dyad_id: DyadId,
    pub role: Role,
    pub channel: Channel,
    pub surface: Option<String>,
    pub content: String,
    pub trace_id: String,
    pub token_count: Option<u32>,
    pub model: Option<String>,
    pub sanguis_snapshot: Option<serde_json::Value>,
    pub logos_context_id: Option<String>,
    pub outcome: Option<String>,
    pub created_at: DateTime<Utc>,
}

pub enum Channel {
    Signal, Web, Voice, Api, Internal, Aether,
    Tauri,  // ← NEW — added for desktop app attribution
}
```

---

*End of specification.*
*— Iris, April 11, 2026*
