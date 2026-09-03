# Drone Flythrough: Faults & Solutions Architecture

This document serves as the comprehensive threat model for the drone flight simulator. It isolates every potential vector where the physics, rendering, or user input systems could fail, and establishes the strict architectural solutions required to mitigate them.

## 1. Physics & Collision Faults

### Fault 1.1: The Raycasting Performance Collapse
*   **The Flaw:** Raycasting against a massive, highly detailed displaced `PlaneGeometry` (e.g., $1024 \times 1024$ vertices) on every frame is $O(N)$ or $O(\log N)$ with a BVH. At 60 FPS, this will severely bottleneck the browser's main thread and cause catastrophic framerate drops.
*   **The Solution (Bilinear Interpolation):** We already have the raw height matrix (`meshData.height_data`) in RAM. We will replace the raycaster entirely. We take the drone's `(X, Z)` coordinates, map them to the 2D height array indices, and use Bilinear Interpolation to calculate the exact terrain height at that point in $O(1)$ time. 

### Fault 1.2: Framerate-Dependent Physics
*   **The Flaw:** Calculating gravity and momentum in the `animate()` loop using simple `deltaTime` causes non-deterministic physics. A user at 144Hz will have different thrust capabilities than a user at 60Hz. A severe lag spike will cause `deltaTime` to skyrocket, teleporting the drone through a mountain.
*   **The Solution (Fixed Physics Timestep):** Decouple the rendering loop from the physics loop. The physics engine will update at a strict interval (e.g., `1/60` seconds). During a lag spike, the engine will run a `while` loop to process multiple small physics steps to "catch up", ensuring perfectly deterministic flight.

### Fault 1.3: High-Speed Tunneling (Continuous Collision Detection)
*   **The Flaw:** If the drone is moving at 100 m/s horizontally and the terrain features a thin, jagged ridge, the drone's position in Frame 1 might be in front of the ridge, and in Frame 2 it might be behind it. The collision engine never detects the hit.
*   **The Solution (Ray-Marched Collision):** If the velocity vector length exceeds the drone's bounding box size, we must step through the velocity vector in smaller increments during the physics tick, verifying the height at intermediate points to ensure no terrain was passed through.

### Fault 1.4: Map Boundary Escapes (Out-of-Bounds)
*   **The Flaw:** The terrain is a finite 150x150 plane. If the user flies off the edge of the map, the Bilinear Interpolation function will throw an Array Out of Bounds exception, crashing the entire WebGL viewer.
*   **The Solution (Hard Clamping & Repulsion):** The physics engine must evaluate the `(X, Z)` position *before* passing it to the lookup function. If the drone nears the boundary, an artificial "wind" or repulsive force must push it back, and hard-clamp its coordinates to `max_bounds - 1`.

---

## 2. Rendering & Input Faults

### Fault 2.1: Camera Gimbal Lock & Terrain Clipping
*   **The Flaw:** A basic 3rd-person chase camera blindly uses `lookAt()` and follows the drone. If the drone flies straight up, the camera might flip upside down (Gimbal Lock). If the drone flies up a steep slope, the camera will drag through the dirt.
*   **The Solution (Independent Camera Collision & Quaternions):** 
    1.  Use Quaternions for all camera rotations to completely eliminate Gimbal Lock.
    2.  The camera must run its *own* Bilinear Height Lookup. The camera's `Y` coordinate is strictly clamped to `Math.max(desired_y, terrain_height + 2.0)` so it always slides over the mountain peaks.

### Fault 2.2: Input Latency & Key Ghosting
*   **The Flaw:** Standard Javascript `keydown` and `keyup` events suffer from OS-level key repeat delays. If relying directly on events to apply thrust, the controls will feel sluggish.
*   **The Solution (Input Polling Array):** We will maintain a `keys = { W: false, A: false, ... }` state object. Events only toggle the booleans. The Fixed Physics Timestep polls this object 60 times a second and applies smooth acceleration vectors, ensuring razor-sharp, zero-latency input handling.

### Fault 2.3: WebGL Context Loss
*   **The Flaw:** If the user minimizes the browser tab or their GPU runs out of memory, the WebGL context is lost. When they return, the screen is black and the drone physics continue to run in the void.
*   **The Solution (Context Recovery & Pausing):** Implement the `webglcontextlost` and `webglcontextrestored` event listeners. If lost, the `DroneController` immediately pauses physics and mutes audio. Upon restoration, textures are re-uploaded and the physics engine is unpaused.
