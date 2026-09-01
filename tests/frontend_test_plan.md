# Frontend Test Plan (`tests/frontend_test_plan.md`)

## 1. Interaction Logger Unit Tests
* **Test:** Trigger `logger.log('TEST_EVENT', 'UI', {foo: 'bar'})`. **Expected:** Log count increases by 1, DOM HUD stream updates, payload matches schema.
* **Test:** Fire 100 rapid `CAMERA_MOVE` calls within 10ms. **Expected:** `throttleLog` ensures only 1-2 entries are saved to prevent buffer overflow.

## 2. 3D Viewer & WebGL Memory Tests
* **Test:** Load terrain mesh, then call `updateTerrainMesh()` 5 times consecutively with new data. **Expected:** `dispose()` is called 4 times; GPU memory remains stable without memory leaks.

## 3. Point Inspector Raycasting Tests
* **Test:** Raycast onto flat plane at $Z=150m$. **Expected:** Inspector outputs $Z=150.0m$ and Slope $= 0.0^\circ$.
* **Test:** Raycast onto 45-degree slope plane. **Expected:** Inspector outputs Slope $= 45.0^\circ \pm 0.5^\circ$.
