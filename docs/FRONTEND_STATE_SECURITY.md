# Frontend State, Security & Logging Architecture

## State Architecture
* **Ephemeral Memory:** WebGL textures, geometries, and height arrays are held in RAM during the active session.
* **Logger Ledger:** All logged events are stored in a JavaScript `Array` (`window.DepthWizardLogs`).
* **Session Persistence:** Active layer choice and camera preferences are stored in `localStorage`.

## Security Architecture
* **XSS Prevention:** All log details rendered into the HUD console are sanitized using `textContent` / strict string escaping rather than raw `innerHTML`.
* **Client-Side File Validation:** Checks file extensions (`.tif`, `.geotiff`, `.png`, `.jpg`) and file sizes (< 20MB) before triggering backend API POST.

## Logging Enforcement Strategy
Every single module (Viewer, Controls, Inspector, Exporter, Layer Switcher) is injected with a reference to `InteractionLogger`. No action is executed silently without triggering `logger.log()`.
