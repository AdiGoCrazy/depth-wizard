import { logger } from './logger.js';

export class DroneController {
    constructor(camera, scene, domElement) {
        this.camera = camera;
        this.scene = scene;
        this.domElement = domElement;
        
        // Drone State
        this.position = new THREE.Vector3(0, 50, 0);
        this.velocity = new THREE.Vector3(0, 0, 0);
        this.rotation = new THREE.Quaternion();
        this.euler = new THREE.Euler(0, 0, 0, 'YXZ');
        
        // Drone Mesh (Procedural)
        this.mesh = this.createDroneMesh();
        this.scene.add(this.mesh);

        // Physics Constants
        this.gravity = -20.0;
        this.thrust = 50.0;
        this.speed = 60.0; // Increased by 1.5x from 40.0
        this.drag = 0.92;
        
        // Input Polling State
        this.keys = {
            KeyW: false, KeyS: false, KeyA: false, KeyD: false,
            Space: false, ShiftLeft: false, ShiftRight: false,
            ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false
        };
        
        this.enabled = false;
        this.meshData = null; // Terrain data for bilinear lookup

        // Bind events
        this.onKeyDown = this.onKeyDown.bind(this);
        this.onKeyUp = this.onKeyUp.bind(this);
        this.onMouseMove = this.onMouseMove.bind(this);
        
        // Setup HUD
        this.setupHUD();
    }

    createDroneMesh() {
        const group = new THREE.Group();
        
        // Main Body
        const bodyGeo = new THREE.BoxGeometry(2, 0.5, 2);
        const bodyMat = new THREE.MeshStandardMaterial({ color: 0x222222, metalness: 0.8, roughness: 0.2 });
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        group.add(body);
        
        // Rotors
        const rotorGeo = new THREE.CylinderGeometry(0.8, 0.8, 0.1, 16);
        const rotorMat = new THREE.MeshStandardMaterial({ color: 0xdddddd, transparent: true, opacity: 0.5 });
        
        const positions = [
            [1.5, 0.3, 1.5], [-1.5, 0.3, 1.5],
            [1.5, 0.3, -1.5], [-1.5, 0.3, -1.5]
        ];
        
        this.rotors = [];
        positions.forEach(pos => {
            const rotor = new THREE.Mesh(rotorGeo, rotorMat);
            rotor.position.set(pos[0], pos[1], pos[2]);
            this.rotors.push(rotor);
            group.add(rotor);
        });

        // Direction indicator (Front)
        const frontGeo = new THREE.BoxGeometry(0.5, 0.5, 0.5);
        const frontMat = new THREE.MeshBasicMaterial({ color: 0xff0000 });
        const front = new THREE.Mesh(frontGeo, frontMat);
        front.position.set(0, 0.25, -1.2);
        group.add(front);
        
        group.scale.set(0.25, 0.25, 0.25); // Scaled down by 4 times

        group.position.copy(this.position);
        group.visible = false;
        return group;
    }

    setupHUD() {
        // Create HUD for telemetry
        this.hud = document.createElement('div');
        this.hud.style.position = 'absolute';
        this.hud.style.top = '10px';
        this.hud.style.left = '50%';
        this.hud.style.transform = 'translateX(-50%)';
        this.hud.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
        this.hud.style.color = '#00ff00';
        this.hud.style.fontFamily = 'monospace';
        this.hud.style.padding = '10px';
        this.hud.style.borderRadius = '5px';
        this.hud.style.pointerEvents = 'none';
        this.hud.style.display = 'none';
        this.hud.style.zIndex = '1000';
        this.domElement.parentElement.appendChild(this.hud);
    }

    enable() {
        this.enabled = true;
        this.mesh.visible = true;
        this.hud.style.display = 'block';
        window.addEventListener('keydown', this.onKeyDown);
        window.addEventListener('keyup', this.onKeyUp);
        this.domElement.addEventListener('mousemove', this.onMouseMove);
        
        // Request pointer lock for mouse look
        this.domElement.addEventListener('click', () => {
            if (this.enabled) this.domElement.requestPointerLock();
        });
        
        logger.log('DRONE_ENABLED', 'DroneController', { msg: 'Flight mode activated.' });
    }

    disable() {
        this.enabled = false;
        this.mesh.visible = false;
        this.hud.style.display = 'none';
        window.removeEventListener('keydown', this.onKeyDown);
        window.removeEventListener('keyup', this.onKeyUp);
        this.domElement.removeEventListener('mousemove', this.onMouseMove);
        document.exitPointerLock?.();
        
        logger.log('DRONE_DISABLED', 'DroneController', { msg: 'Flight mode deactivated.' });
    }

    onKeyDown(event) {
        if (this.keys.hasOwnProperty(event.code)) {
            this.keys[event.code] = true;
        }
    }

    onKeyUp(event) {
        if (this.keys.hasOwnProperty(event.code)) {
            this.keys[event.code] = false;
        }
    }

    onMouseMove(event) {
        if (!this.enabled || document.pointerLockElement !== this.domElement) return;

        const movementX = event.movementX || event.mozMovementX || event.webkitMovementX || 0;
        const movementY = event.movementY || event.mozMovementY || event.webkitMovementY || 0;

        this.euler.y -= movementX * 0.002;
        this.euler.x -= movementY * 0.002;
        
        // Clamp pitch to avoid gimbal lock visually
        this.euler.x = Math.max(-Math.PI/2, Math.min(Math.PI/2, this.euler.x));
        
        this.rotation.setFromEuler(this.euler);
    }

    setTerrainData(meshData, scalar) {
        this.meshData = meshData;
        this.terrainScalar = scalar;
    }

    getTerrainHeight(x, z) {
        if (!this.meshData) return 0;
        
        const w = this.meshData.width;
        const h = this.meshData.height;
        const heights = this.meshData.height_data;
        const minH = this.meshData.min_height;
        
        // Terrain is a 150x150 plane centered at 0,0
        // Map world x,z (-75 to 75) to grid coords (0 to w-1, 0 to h-1)
        const planeSize = 150.0;
        const halfSize = planeSize / 2.0;
        
        let gx = ((x + halfSize) / planeSize) * (w - 1);
        let gz = ((z + halfSize) / planeSize) * (h - 1);
        
        // Clamping to map boundaries to prevent Out of Bounds faults
        if (gx < 0) gx = 0;
        if (gx > w - 1.001) gx = w - 1.001;
        if (gz < 0) gz = 0;
        if (gz > h - 1.001) gz = h - 1.001;
        
        // Bilinear Interpolation
        const x0 = Math.floor(gx);
        const x1 = x0 + 1;
        const z0 = Math.floor(gz);
        const z1 = z0 + 1;
        
        const tx = gx - x0;
        const tz = gz - z0;
        
        const h00 = heights[z0 * w + x0];
        const h10 = heights[z0 * w + x1];
        const h01 = heights[z1 * w + x0];
        const h11 = heights[z1 * w + x1];
        
        const h0 = h00 * (1 - tx) + h10 * tx;
        const h1 = h01 * (1 - tx) + h11 * tx;
        
        const rawHeight = h0 * (1 - tz) + h1 * tz;
        
        // Apply the same scalar applied in viewer.js to match visuals exactly
        return (rawHeight - minH) * this.terrainScalar;
    }

    updatePhysics(dt) {
        if (!this.enabled) return;

        // Input vectors
        const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(this.rotation);
        const right = new THREE.Vector3(1, 0, 0).applyQuaternion(this.rotation);
        
        forward.y = 0; right.y = 0; // Move horizontally
        forward.normalize(); right.normalize();

        const moveDir = new THREE.Vector3(0, 0, 0);
        
        if (this.keys.KeyW || this.keys.ArrowUp) moveDir.add(forward);
        if (this.keys.KeyS || this.keys.ArrowDown) moveDir.sub(forward);
        if (this.keys.KeyD || this.keys.ArrowRight) moveDir.add(right);
        if (this.keys.KeyA || this.keys.ArrowLeft) moveDir.sub(right);
        
        if (moveDir.length() > 0) moveDir.normalize();

        // Apply Forces
        this.velocity.x += moveDir.x * this.speed * dt;
        this.velocity.z += moveDir.z * this.speed * dt;
        
        // Thrust & Gravity (with Auto-Hover Altitude Hold)
        if (this.keys.Space) {
            this.velocity.y += this.thrust * dt;
        } else if (this.keys.ShiftLeft || this.keys.ShiftRight) {
            this.velocity.y -= this.thrust * dt;
        } else {
            // Auto-Hover: Apply exact counter-force to gravity to maintain altitude
            this.velocity.y += Math.abs(this.gravity) * dt;
            // Dampen residual vertical velocity quickly to stabilize hover
            this.velocity.y *= 0.85; 
        }
        
        this.velocity.y += this.gravity * dt;
        
        // Apply Drag
        this.velocity.x *= this.drag;
        this.velocity.z *= this.drag;
        this.velocity.y *= 0.98; // slightly less drag on y

        // Update Position
        this.position.x += this.velocity.x * dt;
        this.position.z += this.velocity.z * dt;
        this.position.y += this.velocity.y * dt;

        // Map Boundary Repulsion
        const boundaryLimit = 74.0;
        if (Math.abs(this.position.x) > boundaryLimit) {
            this.position.x = Math.sign(this.position.x) * boundaryLimit;
            this.velocity.x = 0;
        }
        if (Math.abs(this.position.z) > boundaryLimit) {
            this.position.z = Math.sign(this.position.z) * boundaryLimit;
            this.velocity.z = 0;
        }

        // Terrain Collision (Bilinear Lookup)
        const terrainY = this.getTerrainHeight(this.position.x, this.position.z);
        const droneHeight = 0.25; // Adjusted for 4x smaller scale
        
        if (this.position.y < terrainY + droneHeight) {
            this.position.y = terrainY + droneHeight;
            if (this.velocity.y < 0) {
                if (this.velocity.y < -15) { // Hard landing detection
                    logger.log('DRONE_HARD_LANDING', 'PhysicsEngine', { speed: this.velocity.y.toFixed(2) });
                }
                this.velocity.y = 0;
            }
            
            // Ground friction
            this.velocity.x *= 0.8;
            this.velocity.z *= 0.8;
        }

        // Update mesh transforms
        this.mesh.position.copy(this.position);
        
        // Visual tilt based on local directional velocity
        const localVelocity = this.velocity.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), -this.euler.y);
        
        const pitch = Math.max(-Math.PI/4, Math.min(Math.PI/4, localVelocity.z * 0.02));
        const roll = Math.max(-Math.PI/4, Math.min(Math.PI/4, -localVelocity.x * 0.02));
        
        const tiltEuler = new THREE.Euler(
            pitch,
            this.euler.y,
            roll,
            'YXZ'
        );
        this.mesh.quaternion.setFromEuler(tiltEuler);

        // Spin rotors
        this.rotors.forEach(r => r.rotation.y += 20 * dt);

        // Update Camera (Chase Cam with Collision)
        this.updateCamera(dt, terrainY);
        
        // Update HUD
        this.updateHUD(dt, terrainY);
    }
    
    updateCamera(dt, droneTerrainY) {
        // Calculate desired camera position (behind and above)
        const offset = new THREE.Vector3(0, 4, 10);
        offset.applyQuaternion(this.rotation);
        
        const idealPos = this.position.clone().add(offset);
        
        // Camera Terrain Collision
        const camTerrainY = this.getTerrainHeight(idealPos.x, idealPos.z);
        if (idealPos.y < camTerrainY + 2.0) {
            idealPos.y = camTerrainY + 2.0;
        }

        // Lerp camera position for smoothness
        this.camera.position.lerp(idealPos, 5.0 * dt);
        
        // Look at drone
        this.camera.lookAt(this.position);
    }
    
    updateHUD(dt, terrainY) {
        const fps = Math.round(1.0 / dt);
        const x = this.position.x.toFixed(1);
        const y = this.position.y.toFixed(1);
        const z = this.position.z.toFixed(1);
        const agl = (this.position.y - terrainY).toFixed(1);
        const speed = Math.sqrt(this.velocity.x**2 + this.velocity.z**2).toFixed(1);
        
        this.hud.innerHTML = `
            <div>MODE: FLYTHROUGH</div>
            <div>FPS: ${fps}</div>
            <div>POS: X:${x} Y:${y} Z:${z}</div>
            <div>AGL: ${agl}m | SPD: ${speed}m/s</div>
        `;
    }
}
