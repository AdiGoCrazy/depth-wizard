import { logger } from './logger.js';

export class PointInspector {
    constructor(viewer) {
        this.viewer = viewer;
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        
        this.inspectZ = document.getElementById('inspect-z');
        this.inspectSlope = document.getElementById('inspect-slope');
        this.inspectCoords = document.getElementById('inspect-coords');

        this.init();
    }

    init() {
        const canvas = this.viewer.renderer.domElement;
        
        // Listen for click and mousemove on canvas
        canvas.addEventListener('click', (e) => this.onPointerAction(e, 'POINT_INSPECT_CLICK'));
        canvas.addEventListener('mousemove', (e) => this.onPointerAction(e, 'POINT_INSPECT_HOVER', true));
    }

    onPointerAction(event, eventType, isHover = false) {
        if (!this.viewer.terrainMesh) return;

        const rect = this.viewer.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.viewer.camera);
        const intersects = this.raycaster.intersectObject(this.viewer.terrainMesh);

        if (intersects.length > 0) {
            const hit = intersects[0];
            const point = hit.point;
            const face = hit.face;

            // Calculate elevation (Z or Y height depending on plane orientation)
            const elevation = (point.y * 6.66).toFixed(2); // De-scaled for real meters
            
            // Calculate Slope angle from face normal vector
            let slopeDeg = 0;
            if (face) {
                const normal = face.normal;
                // Angle between normal and UP vector (0, 1, 0)
                const dot = Math.abs(normal.y);
                slopeDeg = (Math.acos(dot) * (180 / Math.PI)).toFixed(1);
            }

            // Update UI
            if (this.inspectZ) this.inspectZ.textContent = `${elevation} m`;
            if (this.inspectSlope) this.inspectSlope.textContent = `${slopeDeg}°`;
            if (this.inspectCoords) this.inspectCoords.textContent = `X: ${point.x.toFixed(1)} | Y: ${point.z.toFixed(1)}`;

            // Log user inspection event (throttled on hover, instant on click)
            if (!isHover) {
                logger.log(eventType, 'PointInspector', {
                    elevation_m: elevation,
                    slope_deg: slopeDeg,
                    point: { x: point.x.toFixed(2), y: point.y.toFixed(2), z: point.z.toFixed(2) }
                });
            }
        }
    }
}
