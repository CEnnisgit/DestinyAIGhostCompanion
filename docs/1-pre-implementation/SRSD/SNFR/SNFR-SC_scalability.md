# Non-Functional Requirements: Scalability (SNFR-SC)

## Hardware Footprint (SNFR-SCH)
- **`SNFR-SCH-01`**: The local Python API and React Web servers must operate smoothly on consumer hardware alongside Destiny 2 without aggressively stealing CPU cycles from the game.
- **`SNFR-SCH-02`**: Ollama integration must attempt to bind to the most optimized runtime (e.g., Metal, CUDA) available on the host machine to minimize VRAM starvation for the background video game. 
- **`SNFR-SCH-03`**: As a strictly single-tenant application, horizontal user scaling is completely out of scope. Scaling implies supporting larger manifests and expanded persona datasets locally.
