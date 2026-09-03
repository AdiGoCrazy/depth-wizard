# Drone Flythrough Feature Report

The objective is to activate the currently non-functional "DRONE FLYTHROUGH" toggle and implement a realistic 3rd-person flight simulator. Users will be able to fly a drone over their generated 3D satellite terrain and land on it, complete with gravity and collision detection.

## Current State Analysis
*   **The Toggle:** In `frontend/src/app.js`, the `btn-mode-fly` listener only toggles CSS active states and logs the switch. It does not communicate with the 3D viewer.
*   **The Camera:** In `frontend/src/viewer.js`, the scene strictly relies on `THREE.OrbitControls`. There is no logic for switching to a different control scheme.
*   **Collisions:** The terrain is a displaced `PlaneGeometry`. Currently, no physics or collision bounds exist.

## Proposed Changes

---

### Frontend Mechanics

#### [NEW] `frontend/src/drone.js`
We will create a dedicated physics and control engine for the drone.
*   **`DroneController` Class:** Manages keyboard states (`W`, `A`, `S`, `D` for pitch/roll, `Space` for thrust, `Shift` for descend).
*   **Physics Engine:** Implement momentum, drag, gravity, and thrust vectors.
*   **Collision Detection:** Use a downward-pointing `THREE.Raycaster`. On every frame, we cast a ray from the drone's position down to the `terrainMesh`. If the distance between the drone and the terrain is less than the drone's landing gear height, we zero out the downward velocity and snap it to the ground (Landing).
*   **3rd-Person Chase Camera:** Attach a camera target to the drone that lags slightly behind and above it using linear interpolation (Lerp) for a smooth, cinematic flight feel.
*   **Procedural Drone Model:** We will generate a sleek, low-poly quadcopter procedurally using basic `THREE.BoxGeometry` and `THREE.CylinderGeometry` primitives inside the code to avoid loading external `.gltf` assets.

#### [MODIFY] `frontend/src/viewer.js`
*   Import `DroneController`.
*   Add a `setCameraMode(mode)` method. When switching to `fly`, disable `OrbitControls` and enable `DroneController`. When switching to `orbit`, disable the drone and re-enable `OrbitControls`.
*   Update the `animate()` loop to calculate `deltaTime` (using `THREE.Clock`) and call `drone.update(deltaTime, this.terrainMesh)` so the physics engine ticks every frame.

#### [MODIFY] `frontend/src/app.js`
*   Wire the UI buttons (`btn-mode-orbit` and `btn-mode-fly`) to actually trigger `this.viewer.setCameraMode('orbit')` and `this.viewer.setCameraMode('fly')`.

---

## Verification Strategy
1.  Upload a satellite image and wait for the 3D terrain to generate.
2.  Click the "DRONE FLYTHROUGH (WASD)" button.
3.  Verify the camera cuts to a 3rd-person view behind the drone.
4.  Test gravity: Let the drone fall and ensure it perfectly lands on the terrain without clipping through.
5.  Test flight: Use `Space` to lift off and WASD to pitch forward and steer over a mountain.
6.  Verify that if the drone flies directly into the side of a steep mountain, the raycaster prevents it from phasing through the geometry.
