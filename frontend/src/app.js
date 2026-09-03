import { logger } from './logger.js';
import { TerrainViewer } from './viewer.js';
import { PointInspector } from './inspector.js';

class App {
    constructor() {
        this.viewer = null;
        this.inspector = null;
        this.init();
    }

    init() {
        logger.log('APP_INIT_START', 'MainApp', { version: '1.0.0-prototype' });

        // Initialize 3D WebGL Viewer
        this.viewer = new TerrainViewer('webgl-canvas-container');
        this.inspector = new PointInspector(this.viewer);

        // Wire Up Event Listeners
        this.bindEvents();

        this.dsmUrl = null; // Store active DSM for download
        this.downloadBtn = document.getElementById('btn-download-dsm');

        logger.log('APP_INIT_COMPLETE', 'MainApp', { status: 'Ready for satellite image processing.' });
    }

    bindEvents() {
        // 1. File Upload Event
        const uploadInput = document.getElementById('file-upload');
        if (uploadInput) {
            uploadInput.addEventListener('change', (e) => this.handleFileUpload(e));
        }

        // 2. Layer Buttons
        const layerBtns = document.querySelectorAll('.layer-btn');
        layerBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const layer = e.target.getAttribute('data-layer');
                layerBtns.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                
                this.viewer.setLayerMode(layer);
            });
        });

        // 3. Navigation Controls Toggle
        const btnOrbit = document.getElementById('btn-mode-orbit');
        const btnFly = document.getElementById('btn-mode-fly');
        const flyHint = document.getElementById('fly-instructions');

        if (btnOrbit && btnFly) {
            btnOrbit.addEventListener('click', () => {
                btnOrbit.classList.add('active');
                btnFly.classList.remove('active');
                if (flyHint) flyHint.style.display = 'none';
                this.viewer.setCameraMode('orbit');
                logger.log('CAMERA_MODE_SWITCH', 'NavigationControls', { mode: 'ORBIT' });
            });

            btnFly.addEventListener('click', () => {
                btnFly.classList.add('active');
                btnOrbit.classList.remove('active');
                if (flyHint) flyHint.style.display = 'block';
                this.viewer.setCameraMode('fly');
                logger.log('CAMERA_MODE_SWITCH', 'NavigationControls', { mode: 'FLYTHROUGH_WASD' });
            });
        }

        // 4. Download DSM Event
        if (this.downloadBtn) {
            this.downloadBtn.addEventListener('click', () => this.handleDownload());
        }
    }

    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        logger.log('UPLOAD_INITIATED', 'FileHandler', { 
            name: file.name, 
            sizeBytes: file.size, 
            type: file.type 
        });

        // Client-side File Size Validation (20MB Cap)
        if (file.size > 20 * 1024 * 1024) {
            logger.log('UPLOAD_REJECTED', 'FileHandler', { reason: 'Exceeds 20MB hardware limit.' });
            alert("File size exceeds 20MB limit.");
            return;
        }

        // Hide download button during new upload
        if (this.downloadBtn) {
            this.downloadBtn.style.display = 'none';
            this.dsmUrl = null;
        }

        const formData = new FormData();
        formData.append("file", file);
        
        // Extract Environment toggle state
        const envRadios = document.getElementsByName('environment');
        let selectedEnv = 'urban';
        for (const radio of envRadios) {
            if (radio.checked) {
                selectedEnv = radio.value;
                break;
            }
        }
        formData.append("environment", selectedEnv);
        logger.log('ENVIRONMENT_SELECTED', 'FileHandler', { environment: selectedEnv });

        const statusIndicator = document.getElementById('status-indicator');
        if (statusIndicator) statusIndicator.textContent = "● PROCESSING INFERENCE...";

        try {
            logger.log('API_POST_START', 'HTTPClient', { endpoint: '/api/process' });
            
            const response = await fetch('/api/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errJson = await response.json();
                throw new Error(errJson.detail || "API processing failed.");
            }

            const data = await response.json();
            logger.log('API_POST_SUCCESS', 'HTTPClient', data);

            if (statusIndicator) {
                statusIndicator.textContent = data.is_metric ? "● ABSOLUTE DSM (METRIC)" : "● RELATIVE rDSM";
            }

            const modeIndicator = document.getElementById('mode-indicator');
            if (modeIndicator) {
                modeIndicator.textContent = data.is_metric ? "METRIC (SRTM 30m ALIGNED)" : "RELATIVE (0.0 - 1.0)";
            }

            // Fetch Heightmesh JSON
            const meshRes = await fetch(data.mesh_url);
            const meshData = await meshRes.json();

            // Update 3D Terrain using the JPEG texture returned by the API
            this.viewer.updateTerrain(meshData, data.texture_url);

            // Expose GeoTIFF Download
            if (this.downloadBtn) {
                this.dsmUrl = data.dsm_url;
                this.downloadBtn.style.display = 'flex';
            }

        } catch (error) {
            logger.error ? logger.error(error) : console.error(error);
            logger.log('API_POST_ERROR', 'HTTPClient', { message: error.message });
            alert(`Processing Error: ${error.message}`);
            if (statusIndicator) statusIndicator.textContent = "● ERROR";
        }
    }

    async handleDownload() {
        if (!this.dsmUrl) return;
        
        logger.log('GEOTIFF_EXPORT_INITIATED', 'FileHandler', { url: this.dsmUrl });
        const originalText = this.downloadBtn.innerHTML;
        this.downloadBtn.innerHTML = 'DOWNLOADING...';
        this.downloadBtn.disabled = true;

        try {
            const response = await fetch(this.dsmUrl);
            if (!response.ok) throw new Error("Failed to fetch GeoTIFF blob.");
            
            const blob = await response.blob();
            logger.log('GEOTIFF_BLOB_GENERATED', 'FileHandler', { sizeMB: (blob.size / (1024*1024)).toFixed(2) });
            
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = this.dsmUrl.split('/').pop() || 'dsm_export.tif';
            document.body.appendChild(a);
            
            logger.log('GEOTIFF_EXPORT_SUCCESS', 'FileHandler', { action: 'Triggering local download prompt' });
            a.click();
            
            // Memory Leak Prevention (Fault 4)
            setTimeout(() => {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, 5000);
            
        } catch (error) {
            logger.error ? logger.error(error) : console.error(error);
            logger.log('GEOTIFF_EXPORT_FAILED', 'FileHandler', { error: error.message });
            alert("GeoTIFF Download Failed: " + error.message);
        } finally {
            this.downloadBtn.innerHTML = originalText;
            this.downloadBtn.disabled = false;
        }
    }
}

// Bootstrap
window.addEventListener('DOMContentLoaded', () => {
    new App();
});
