import { logger } from './logger.js';

export class TerrainViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.terrainMesh = null;
        this.currentLayer = 'rgb';
        
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

        // Animation Loop
        const animate = () => {
            requestAnimationFrame(animate);
            this.controls.update();
            this.renderer.render(this.scene, this.camera);
        };
        animate();

        // Resize Listener
        window.addEventListener('resize', () => this.onWindowResize());
        
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

        // Displace Y coordinate (height)
        for (let i = 0; i < heights.length; i++) {
            // Vertex position array: [x0, y0, z0, x1, y1, z1, ...]
            vertices[i * 3 + 1] = (heights[i] - meshData.min_height) * scalar;
        }

        geometry.computeVertexNormals();

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
            this.terrainMesh.userData = { meshData }; // Attach for raycasting
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
        } else if (mode === 'dsm') {
            // Mock Elevation Colormap via wireframe
            this.terrainMesh.material.wireframe = true;
        } else if (mode === 'slope') {
            this.terrainMesh.material.wireframe = false;
        }
    }

    onWindowResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }
}
