# Point Inspector Component (`frontend/src/inspector.js`)

## Purpose
Allows users to hover or click anywhere on the 3D terrain to query exact metric elevation ($Z$), slope angle ($^\circ$), and spatial coordinates.

## Key Functions & Methods
* `inspectPoint(event, camera, terrainMesh)`: Casts a Raycaster vector from camera through screen coordinates to intersect terrain.
* `calculateSlope(faceNormal)`: Computes slope angle in degrees from the intersected mesh face normal ($\arccos(N_z)$).
* `updateHUD(x, y, elevation, slope)`: Updates floating HUD card with precise metrics.

## Inputs & Outputs
* **Inputs:** Mouse Click/Hover screen coordinates $(x, y)$.
* **Outputs:** Elevation in meters, Slope in degrees, Spatial $(X, Y)$ position.
