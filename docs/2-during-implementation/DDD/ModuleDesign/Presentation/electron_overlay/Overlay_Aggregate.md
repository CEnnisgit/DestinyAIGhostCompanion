# Aggregate Root: AppOverlay

**Bounded Context:** Presentation
**Feature Slice:** `electron_overlay`

## 1. Description
The `AppOverlay` is the structural window that ensures the Ghost Companion does not interrupt gameplay focus.

## 2. Core Invariants (Rules)
1. **Transparent Pass-Through**: The window must be configured to pass-through mouse clicks unless explicitly summoned.
2. **Microphone Lock**: It must handle Web Speech API instances or OS-level mic streams effectively, ensuring audio flows correctly to the backend port.

## 3. Hexagonal Ports
- **Driver Port (`PushToTalkEvent`)**: Global OS hotkey listener that summons the UI or captures voice.
- **Driven Port (`AxumBackendAdapter`)**: The IPC or REST client that transmits the voice blobs to the Rust backend running in `crates/api`.
