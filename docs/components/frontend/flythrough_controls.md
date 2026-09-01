# Flythrough Controls Component (`frontend/src/controls.js`)

## Purpose
Provides dual navigation modes: First-Person Drone Flythrough (WASD + Mouse Look via PointerLock) and Orbit Inspection Controls (`OrbitControls`).

## Key Functions & Methods
* `enableFlyMode()`: Activates PointerLock and WASD flythrough controls.
* `enableOrbitMode()`: Activates 360-degree orbital camera controls around the terrain center.
* `update(deltaTime)`: Updates camera position based on WASD velocity vector and pitch/yaw angles.
* `setFlySpeed(multiplier)`: Adjusts flight speed boost.

## Inputs & Outputs
* **Inputs:** Keyboard `W, A, S, D, Space, Shift`, Mouse Movement.
* **Outputs:** Updated Camera Position & Rotation matrix in Three.js scene.
