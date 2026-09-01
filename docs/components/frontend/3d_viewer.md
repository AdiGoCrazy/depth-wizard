# 3D Viewport Component (`frontend/src/viewer.js`)

## Purpose
Manages the Three.js WebGL scene, terrain displacement mesh, lighting, background atmosphere, and texture rendering.

## Key Functions & Methods
* `initScene(containerEl)`: Initializes WebGLRenderer, PerspectiveCamera, Scene, and Ambient/Directional Lights.
* `updateTerrainMesh(heightData, width, height)`: Creates or updates `PlaneGeometry(width, height, width-1, height-1)` and displaces vertex Z positions based on the DSM height array.
* `applyTexture(imageUri)`: Loads texture via `TextureLoader` and maps it onto the terrain mesh.
* `dispose()`: Disposes old geometry, materials, and textures to prevent WebGL memory leaks.

## Inputs & Outputs
* **Inputs:** Heightmap JSON payload (`width`, `height`, `height_data`), RGB texture URL.
* **Outputs:** Rendered 60 FPS WebGL scene canvas.
