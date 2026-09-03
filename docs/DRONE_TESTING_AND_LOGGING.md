# Drone Flythrough: Testing Strategy & Logging Architecture

This document defines the stringent Test-Driven Preparation (TDP) and Observability requirements for the drone flight simulator. Because WebGL physics engines are notoriously difficult to debug using standard browser tools, we must build custom testing matrices and an in-engine logging architecture.

---

## 1. Test-Driven Preparation (TDP)

Before writing any physics logic, we must define the behavioral test suite.

### Category A: Physics & Collision Tests
*   **Test A1: Physics Determinism (Framerate Test)**
    *   *Setup:* Initialize the `DroneController` at `(0, 100, 0)` with zero thrust.
    *   *Action:* Simulate 60 frames passing at `0.016s` intervals (60Hz). In parallel, simulate 30 frames passing at `0.033s` intervals (30Hz).
    *   *Verification:* Both simulations must result in the exact same final Y-coordinate. Gravity applies consistently regardless of the simulated framerate.
*   **Test A2: Bilinear Height Lookup Accuracy**
    *   *Setup:* Generate a mock $2 \times 2$ height array where the points are `[0, 10, 10, 20]`. Place the drone at exact intermediate coordinates (e.g., $X=0.5, Z=0.5$).
    *   *Action:* Call `terrainHeightLookup(drone.x, drone.z)`.
    *   *Verification:* The function must return the exact interpolated slope height (e.g., `10.0`). 
*   **Test A3: Terminal Velocity Ground Interaction**
    *   *Setup:* Drone is dropped from `Y = 1000`. Terrain height beneath it is `Y = 10`. 
    *   *Action:* Drone impacts the ground at terminal velocity.
    *   *Verification:* Drone Y perfectly snaps to `10.0`. Velocity Y instantly becomes `0.0`. The drone does not sink, bounce endlessly, or glitch through the floor.

### Category B: Input & Boundary Tests
*   **Test B1: Key Ghosting & Latency**
    *   *Setup:* Trigger a rapid sequence of `keydown` (W) and `keyup` (W) events spaced exactly 5ms apart (faster than typical OS repeat delays).
    *   *Verification:* The internal `keys` state object toggles instantly without dropping events, and the physics acceleration vector remains strictly bound to `0.0` or `MAX_ACCEL`.
*   **Test B2: Map Boundary Repulsion**
    *   *Setup:* Force the drone's position to `X = 149.9` (assuming a 150x150 map) while holding the 'D' (Move Right) key.
    *   *Verification:* The drone is physically unable to cross `X = 150.0`. The repulsion force negates the input thrust, preventing an Out-of-Bounds crash on the heightmap array.

---

## 2. Structured Logging & Observability

To trace state changes without creating a monolithic, unreadable browser console, we will implement a tiered logging architecture and a **visual debug overlay**.

### 2.1 The Visual Debug Overlay (In-Engine HUD)
Instead of relying purely on `console.log`, which lags the browser if spammed, we will render an HTML/CSS HUD overlay on top of the WebGL canvas that updates natively with the animation frame.
*   **Telemetry Data Displayed:**
    *   `FPS`: Current render framerate.
    *   `POS (X,Y,Z)`: Exact drone coordinates.
    *   `VEL (X,Y,Z)`: Current velocity vector.
    *   `ALT (AGL)`: Altitude Above Ground Level (Drone Y - Terrain Y).
    *   `TIMESTEP`: The exact `deltaTime` used in the last physics tick.

### 2.2 Console Log Categorization (Extending `logger.js`)
We will enforce strict categorization for persistent state changes.

| Level | Component | Trigger Condition | Output Example |
| :--- | :--- | :--- | :--- |
| `INFO` | `DroneController` | User toggles the "DRONE FLYTHROUGH" button. | `[INFO] Camera Mode Switched to FLYTHROUGH. Drone activated at (0, 150, 0).` |
| `INFO` | `PhysicsEngine` | Fired when the drone transitions between Airborne and Landed states. | `[INFO] Touchdown detected at elevation 234m. Velocity zeroed.` |
| `WARN` | `PhysicsEngine` | A lag spike forces the engine to process > 3 physics steps in a single frame. | `[WARN] Severe lag detected. DeltaTime = 0.12s. Processed 7 catch-up ticks.` |
| `WARN` | `TerrainCollider` | Drone hits the map boundary and is repulsed. | `[WARN] Boundary collision at X=150. Applying repulsion force.` |
| `ERROR` | `TerrainCollider` | The drone attempts to query a terrain height but the `meshData` array is null or corrupted. | `[ERROR] Height lookup failed (Null Reference). Resetting drone to origin.` |

### 2.3 Local Storage Telemetry Dump
If a catastrophic `ERROR` level event occurs (e.g., WebGL context loss or `meshData` corruption), the logging engine will immediately dump the last 5 seconds of telemetry data into `localStorage`. This allows developers to refresh the page and instantly pull the exact velocity and position vectors that caused the crash.
