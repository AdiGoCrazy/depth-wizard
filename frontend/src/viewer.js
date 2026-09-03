import { logger } from './logger.js';
import { DroneController } from './drone.js';

export class TerrainViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.terrainMesh = null;
        this.currentLayer = 'rgb';
        
        // Setup clock for physics
        this.clock = new THREE.Clock();
        
        this.init();
    }

    init() {
        logger.log('THREE_INIT_START', '3DViewer', { container: this.container?.id });
        
        const width = this.container.clientWidth || window.innerWidth;
        const height = this.container.clientHeight || window.innerHeight;

        // 1. Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0b0f19);

        // 2. Camera
        this.camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
        this.camera.position.set(0, 150, 200);

        // 3. Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.container.appendChild(this.renderer.domElement);

        // 4. Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
        this.scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(100, 200, 100);
        this.scene.add(dirLight);

        // 5. Controls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;

        // Create initial placeholder grid
        this.createPlaceholderGrid();

        // Initialize Drone
        this.drone = new DroneController(this.camera, this.scene, this.renderer.domElement);
        this.cameraMode = 'orbit';

        this.physicsAccumulator = 0;
        const fixedDt = 1.0 / 60.0;

        // Animation Loop
        const animate = () => {
            requestAnimationFrame(animate);
            
            const dt = Math.min(this.clock.getDelta(), 0.1); // Clamp dt to avoid huge spikes
            
            if (this.cameraMode === 'fly') {
                this.physicsAccumulator += dt;
                let steps = 0;
                while (this.physicsAccumulator >= fixedDt && steps < 10) { // Max 10 steps per frame
                    this.drone.updatePhysics(fixedDt);
                    this.physicsAccumulator -= fixedDt;
                    steps++;
                }
                if (steps >= 5) {
                    logger.log('PHYSICS_WARN', 'PhysicsEngine', { msg: `Processed ${steps} catch-up ticks.` });
                }
            } else {
                this.controls.update();
                this.physicsAccumulator = 0;
            }
            
            this.renderer.render(this.scene, this.camera);
        };
        animate();

        // Resize Listener
        window.addEventListener('resize', () => this.onWindowResize());
        
        // Context Loss & Restoration Listeners
        const canvas = this.renderer.domElement;
        canvas.addEventListener('webglcontextlost', (e) => {
            e.preventDefault();
            logger.log('WEBGL_CONTEXT_LOST', 'TerrainViewer', { msg: 'Context lost. Pausing physics.' });
            if (this.drone) this.drone.disable();
        }, false);
        
        canvas.addEventListener('webglcontextrestored', () => {
            logger.log('WEBGL_CONTEXT_RESTORED', 'TerrainViewer', { msg: 'Context restored. Re-uploading textures.' });
            // The textures will need to be reloaded, but physics can unpause if they switch back to fly mode
            if (this.cameraMode === 'fly' && this.drone) this.drone.enable();
        }, false);
        
        logger.log('THREE_INIT_COMPLETE', '3DViewer', { status: '60 FPS WebGL Ready' });
    }

    createPlaceholderGrid() {
        const size = 200;
        const gridHelper = new THREE.GridHelper(size, 40, 0x00f0ff, 0x1e293b);
        gridHelper.name = "grid_placeholder";
        this.scene.add(gridHelper);
    }

    /**
     * Updates terrain displacement mesh using DSM height data
     */
    updateTerrain(meshData, textureUrl) {
        logger.log('TERRAIN_UPDATE_START', '3DViewer', { 
            width: meshData.width, 
            height: meshData.height,
            minH: meshData.min_height,
            maxH: meshData.max_height
        });

        // Dispose old mesh
        if (this.terrainMesh) {
            this.scene.remove(this.terrainMesh);
            this.terrainMesh.geometry.dispose();
            this.terrainMesh.material.dispose();
            this.terrainMesh = null;
        }

        // Remove placeholder grid
        const oldGrid = this.scene.getObjectByName("grid_placeholder");
        if (oldGrid) this.scene.remove(oldGrid);

        const w = meshData.width;
        const h = meshData.height;
        const heights = meshData.height_data;

        // PlaneGeometry (width, height, widthSegments, heightSegments)
        const geometry = new THREE.PlaneGeometry(150, 150, w - 1, h - 1);
        geometry.rotateX(-Math.PI / 2); // Orient horizontally

        const vertices = geometry.attributes.position.array;
        
        // Dynamically calculate scalar to guarantee prominent 3D features
        // The plane is 150 units wide. We want the max height to be ~30 units (20% of width)
        const heightDiff = meshData.max_height - meshData.min_height;
        const targetMaxVisualHeight = 30.0; 
        const scalar = heightDiff > 0 ? (targetMaxVisualHeight / heightDiff) : 1.0;

        // Displace Y coordinate (height) and set vertex colors
        const colors = new Float32Array(vertices.length);
        
        for (let i = 0; i < heights.length; i++) {
            // Vertex position array: [x0, y0, z0, x1, y1, z1, ...]
            const relativeHeight = heightDiff > 0 ? (heights[i] - meshData.min_height) / heightDiff : 0;
            
            vertices[i * 3 + 1] = (heights[i] - meshData.min_height) * scalar;
            
            // Map height to grayscale (0.0 to 1.0)
            colors[i * 3] = relativeHeight;
            colors[i * 3 + 1] = relativeHeight;
            colors[i * 3 + 2] = relativeHeight;
        }

        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        geometry.computeVertexNormals();

        // Pass exact data to drone for O(1) Bilinear Interpolation collisions
        if (this.drone) {
            this.drone.setTerrainData(meshData, scalar);
        }

        // Load Texture
        const textureLoader = new THREE.TextureLoader();
        textureLoader.load(textureUrl, (texture) => {
            const material = new THREE.MeshStandardMaterial({
                map: texture,
                roughness: 0.8,
                metalness: 0.1,
                side: THREE.DoubleSide
            });

            this.terrainMesh = new THREE.Mesh(geometry, material);
            this.terrainMesh.userData = { meshData, originalTexture: texture }; // Attach for raycasting and texture restore
            this.scene.add(this.terrainMesh);

            logger.log('TERRAIN_UPDATE_COMPLETE', '3DViewer', { status: 'Rendered mesh + optical texture' });
        });
    }

    setLayerMode(mode) {
        if (!this.terrainMesh) return;
        this.currentLayer = mode;
        logger.log('LAYER_SWITCH', '3DViewer', { mode });

        if (mode === 'rgb') {
            this.terrainMesh.material.wireframe = false;
            this.terrainMesh.material.vertexColors = false;
            if (this.terrainMesh.userData.originalTexture) {
                this.terrainMesh.material.map = this.terrainMesh.userData.originalTexture;
            }
            this.terrainMesh.material.color.setHex(0xffffff);
            this.terrainMesh.material.needsUpdate = true;
        } else if (mode === 'dsm') {
            // Grayscale heightmap via vertex colors
            this.terrainMesh.material.wireframe = false;
            this.terrainMesh.material.vertexColors = true;
            this.terrainMesh.material.map = null;
            this.terrainMesh.material.color.setHex(0xffffff);
            this.terrainMesh.material.needsUpdate = true;
        } else if (mode === 'heatmap') {
            // RMSE Error Heatmap Texture
            this.terrainMesh.material.wireframe = false;
            this.terrainMesh.material.vertexColors = false;
            if (this.terrainMesh.userData.heatmapTexture) {
                this.terrainMesh.material.map = this.terrainMesh.userData.heatmapTexture;
            }
            this.terrainMesh.material.color.setHex(0xffffff);
            this.terrainMesh.material.needsUpdate = true;
        }
    }

    setHeatmapTexture(textureUrl) {
        const textureLoader = new THREE.TextureLoader();
        textureLoader.load(textureUrl, (texture) => {
            if (this.terrainMesh) {
                this.terrainMesh.userData.heatmapTexture = texture;
                logger.log('HEATMAP_TEXTURE_LOADED', '3DViewer', { status: 'Success' });
                
                // Automatically activate the heatmap layer button visually
                const heatmapBtn = document.getElementById('btn-layer-heatmap');
                if (heatmapBtn) heatmapBtn.click();
            }
        });
    }

    onWindowResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    setCameraMode(mode) {
        if (mode === this.cameraMode) return;
        
        this.cameraMode = mode;
        if (mode === 'fly') {
            this.controls.enabled = false;
            this.drone.enable();
        } else {
            this.drone.disable();
            this.controls.enabled = true;
            // Reset camera for orbit
            this.camera.position.set(0, 150, 200);
            this.camera.lookAt(0, 0, 0);
        }
    }
}
