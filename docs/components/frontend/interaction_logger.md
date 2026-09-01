# User Interaction Logger Component (`frontend/src/logger.js`)

## Purpose
Captures, formats, and displays EVERY single user interaction across the entire application in real time.

## Key Functions & Methods
* `log(eventType, component, details)`: Core logging method. Appends a timestamped log entry to the internal array buffer and broadcasts to the HUD.
* `bindDOMListeners()`: Attaches global event listeners to buttons, sliders, file inputs, canvas clicks, and keyboard WASD events.
* `throttleLog(eventType, component, details, delayMs)`: Throttles high-frequency events (like mousemove or camera flythrough) to prevent log buffer memory overflow.
* `renderLogHUD()`: Renders the active log stream inside the glassmorphic HUD panel with monospaced styling.
* `exportLogs()`: Downloads the complete interaction history as a `.json` file for audit purposes.

## Tracked Events
* `UPLOAD_SELECT`, `UPLOAD_SUCCESS`, `UPLOAD_FAIL`
* `CAMERA_FLY_START`, `CAMERA_FLY_STOP`, `CAMERA_MOVE` (throttled)
* `LAYER_TOGGLE` (RGB, DSM, Slope, Error)
* `POINT_INSPECT_CLICK`, `POINT_INSPECT_HOVER`
* `PROFILE_LINE_START`, `PROFILE_LINE_END`
* `LOG_HUD_TOGGLE`, `LOG_EXPORT`

## Inputs & Outputs
* **Inputs:** User UI events (click, drag, keydown, hover).
* **Outputs:** Formatted log objects, live HUD DOM updates, exportable JSON ledger.
