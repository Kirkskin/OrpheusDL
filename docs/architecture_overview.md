# Orpheus Next-Gen Architecture

This document captures the target architecture required to deliver the
AI-driven, modular downloader platform described in the project vision.
The goal is to keep individual service modules autonomous while providing
a shared intelligence layer that manages networking, authentication,
telemetry, and user guidance.

## Core Pillars

### 1. Orpheus Brain

* Central orchestrator responsible for:
  * Collecting telemetry events (network issues, login failures, CLI input).
  * Running remediation strategies and suggesting next actions.
  * Publishing insights to the CLI “watchdog” and extension ecosystem.
* Implemented as a singleton service (`OrpheusBrain`) with:
  * Event bus (`brain.events`) for modules/services to emit structured events.
  * Strategy registry for automated responses (retry, credential refresh, etc.).
  * Advisory API returning human-readable hints and machine-readable actions.

### 2. Service Registry & API Vault

* Maintains metadata for each module (capabilities, rate limits, login modes).
* Stores API credentials and tokens securely (initially sourced from env/config,
  later supporting encrypted storage).
* Exposes typed clients to modules:
  * `credential_manager.get("qobuz", "auth_token")`
  * `api_registry.get_service("deezer").supports("albums")`

### 3. Login & Session Manager

* Standardises login flows: ARL, OAuth, username/password, auth tokens.
* Tracks session lifetimes, refresh schedules, and failure telemetry.
* Provides hooks for the brain to trigger automated re-authentication.

### 4. Network Fabric

* `utils.network.NetworkManager` remains the single HTTP entry point.
* Emits telemetry events for the brain to consume (DNS failure, 401, etc.).
* Supports policy injection (e.g., throttling, VPN detection warnings).

### 5. Delivery Pipeline

* Encapsulates download orchestration (queueing, tagging, packaging).
* Integrates with the brain for adaptive behaviour (pause queue on errors,
  change conversion strategy, notify user).
* Produces the final artefacts: albums, tracks, EPs, anthologies.

### 6. Enhanced CLI & Watchdog

* CLI becomes the primary user-facing interface for AI guidance.
* Features:
  * Dynamic status updates (“watchdog”) fed by brain advisories.
  * Contextual help, multi-language support, menu-based navigation.
  * Whisper mode for non-intrusive hints.

### 7. Extension Ecosystem

* Extensions subscribe to brain events and publish their own advisories.
* The new `assistant` extension is the first concrete example;
  more specialised extensions (analytics, logging, third-party integrations)
  will plug into the same bus.

## Implementation Roadmap

1. **Service Infrastructure**
   * Introduce `orpheus/services` package with:
     * `brain.py` – orchestrator skeleton.
     * `registry.py` – service metadata & credential vault.
     * `sessions.py` – login manager.
     * `events.py` – typed event definitions.
   * Emit telemetry from `utils.network` and module loaders.

2. **CLI Modernisation**
   * Wrap argument parsing with a watchdog that subscribes to brain advisories.
   * Add interactive menus for common flows (search, download, diagnostics).
   * Implement whisper/help commands leveraging the advisory API.

3. **Delivery Pipeline**
   * Abstract downloader orchestration into a pipeline manager.
   * Expose hooks for the brain to influence retries, conversion flags, etc.

4. **AI Strategy Layer**
   * Start with rule-based strategies fed by telemetry.
   * Plan for ML integration (e.g., preference learning, failure prediction).

5. **Testing & Tooling**
   * Expand test suite to cover the new services and event flows.
   * Provide developer utilities for simulating network/auth scenarios.

## Key Design Principles

* **Autonomy:** Modules continue to own their service-specific logic.
* **Observability:** Everything significant emits structured telemetry.
* **Extensibility:** Brain strategies, advisors, and CLI features are pluggable.
* **Resilience:** Failures trigger actionable guidance, never silent crashes.
* **User Experience:** The CLI should feel like a knowledgeable assistant,
  not just an argument parser.

---

# Expansion Tracks

The sections below break the architecture into concrete build streams so
teams can work independently while keeping alignment with the shared vision.

## 1. Orpheus Brain & Telemetry

### Current State
* `OrpheusBrain` ingests events from the network manager, login flow, delivery
  pipeline, and CLI watchdog.
* Advisors provide static hints (network + login).

### Next Milestones
1. **Event Taxonomy**
   * Define canonical schemas for module, delivery, authentication, CLI, and
     system events (severity, context, remediation hints).
   * Add event correlation IDs to follow a job end-to-end.

2. **Strategy Engine**
   * Implement rule-based strategies that react to patterns (e.g. three DNS
     failures → prompt networking instructions, fallback to alternative endpoints).
   * Expose an action API that delivery/CLI can call to request decisions
     (“should we retry?”, “should we switch login strategy?”).

3. **Persistence & Analytics**
   * Optional logging of events for offline analysis (JSONL/SQLite backend).
   * Hooks for future ML models (e.g. failure prediction, quality selection).

## 2. Service Registry & API Vault

### Current State
* Registry captures service entries from `config/settings.json` folds in
  environment variables.

### Next Milestones
1. **Capability Metadata**
   * Track supported download types (track, album, playlist, artist) and
     advanced features (lyrics, covers, credits).
   * Expose API for modules/CLI to interrogate capabilities.

2. **Credential Management**
   * Enforce a consistent schema for secrets (ARL, OAuth tokens, API keys).
   * Introduce encrypted storage (optional) with pluggable backends.
   * Provide mutation APIs so the brain/CLI can refresh tokens and persist them.

3. **Rate-limit & Policy Attachments**
   * Allow modules to register rate-limit info; create throttle guards in
     the network manager.

## 3. Login & Session Manager

### Current State
* Tracks session status (authenticated/failed).
* Provides credentials seeded from registry/environment.

### Next Milestones
1. **Strategy Catalog**
   * Implement pluggable login strategies (ARL, token refresh, username/password).
   * Store last-used strategy per service; allow fallback ordering.

2. **Auto-refresh**
   * Brain monitors expiry hints; triggers session refresh proactively.

3. **Security Hardening**
   * Mask sensitive info in logs/events.
   * Support password-less workflows (OTP prompts surfaced via CLI).

## 4. Network Fabric

### Current State
* Central `NetworkManager` with retry policy and error classification.
* Emits telemetry to the brain.

### Next Milestones
1. **Policy Layers**
   * Add per-service headers, timeouts, and proxy configuration.
   * Implement circuit breakers to halt repeated failures gracefully.

2. **Connectivity Diagnostics**
   * Add CLI command `network diagnose` to test endpoints and summarise hints.

3. **Offline Simulation**
   * Provide utilities to replay network traces for testing modules without
     hitting live services.

## 5. Delivery Pipeline

### Current State
* Basic job lifecycle events (`started`, `success`, `failed`).

### Next Milestones
1. **Job Graph**
   * Represent multi-step workflows (download → convert → tag → package) and
     emit telemetry at each stage.
   * Enable AI-driven adjustments (skip conversion when repeated failures occur).

2. **Queue Management**
   * Support prioritisation, parallelism limits, pause/resume.

3. **Output Packaging**
   * Standardise final artefact manifest (metadata, logs, checksums).

## 6. Enhanced CLI & Watchdog

### Current State
* Watchdog records commands and displays AI hints post-operation.

### Next Milestones
1. **Interactive Menu**
   * Build subcommands for guided flows (setup, diagnostics, download queue).
   * Provide multi-language prompts via extension/localisation files.

2. **Real-time Updates**
   * Render hints during long-running operations (progress bar integration).

3. **Contextual Help / Whisper Mode**
   * Use brain advisories to suggest next commands or point to docs automatically.

## 7. Extension Ecosystem

### Current State
* `assistant` extension subscribes to network/login events.

### Next Milestones
1. **Extension SDK**
   * Provide utilities for extensions to register advisors, subscribe to events,
     and publish CLI messages.

2. **Specialised Extensions**
   * Logging extension for structured emission (to file/ELK).
   * Analytics extension aggregating download stats.
   * Notification extension (e.g., webhook or desktop alert).

## 8. Testing & Tooling

### Next Milestones
1. **Test Suites**
   * Expand unit tests around new services.
   * Add integration tests covering a full download flow with mocked network.

2. **Developer CLI**
   * Provide commands to simulate events, inspect registry/session states,
     and run end-to-end dry runs.

3. **Migration Stories**
   * Document steps for existing users to move from legacy config to the
     new architecture (env variables, new settings, disabled modules).

---

This blueprint ensures each subsystem evolves cohesively while teams can
focus on specific tracks (Brain, Networking, CLI, Delivery, Extensions).
The next development cycles should prioritise fleshing out the brain’s
strategy engine and delivering an interactive CLI experience that embodies
the AI assistant vision.
This architecture sets the stage for the AI-enhanced Orpheus where service
modules are amplified by a smart, user-centric core. Subsequent tasks will
implement the concrete services and plumbing outlined here.
