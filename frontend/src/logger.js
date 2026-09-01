/**
 * DepthWizard Mandatory Interaction Logger
 * Captures, formats, logs, and displays ALL user interactions across the entire system.
 */
class InteractionLogger {
    constructor() {
        this.logs = [];
        this.streamContainer = document.getElementById('logger-stream-container');
        this.badge = document.getElementById('log-count-badge');
        this.isMinimized = false;
        
        this.initDOMListeners();
        this.log('SYSTEM_INIT', 'LoggerModule', { message: 'Interaction Logger active. All user events tracked.' });
    }

    /**
     * Core logging method
     */
    log(eventType, component, details = {}) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            id: this.logs.length + 1,
            timestamp,
            eventType,
            component,
            details
        };

        this.logs.push(logEntry);
        this.renderLogEntry(logEntry);
        this.updateBadge();
        
        // Also log to browser console for developer auditing
        console.log(`[LOG #${logEntry.id}] [${eventType}] [${component}]`, details);
    }

    /**
     * Appends formatted log entry to HUD stream safely (XSS-proof)
     */
    renderLogEntry(entry) {
        if (!this.streamContainer) return;

        const row = document.createElement('div');
        row.className = 'log-entry';

        const timeSpan = document.createElement('span');
        timeSpan.className = 'timestamp';
        timeSpan.textContent = `[${entry.timestamp.split('T')[1].slice(0, 12)}]`;

        const typeSpan = document.createElement('span');
        typeSpan.className = 'event-type';
        typeSpan.textContent = entry.eventType;

        const compSpan = document.createElement('span');
        compSpan.className = 'component';
        compSpan.textContent = `<${entry.component}>`;

        const detailSpan = document.createElement('span');
        detailSpan.className = 'details';
        detailSpan.textContent = JSON.stringify(entry.details);

        row.appendChild(timeSpan);
        row.appendChild(typeSpan);
        row.appendChild(compSpan);
        row.appendChild(detailSpan);

        this.streamContainer.appendChild(row);

        // Auto scroll to bottom
        this.streamContainer.scrollTop = this.streamContainer.scrollHeight;
    }

    updateBadge() {
        if (this.badge) {
            this.badge.textContent = `${this.logs.length} LOGS`;
        }
    }

    /**
     * Global DOM event listeners for catch-all interaction tracking
     */
    initDOMListeners() {
        // Track all button clicks across the UI
        document.addEventListener('click', (e) => {
            const targetBtn = e.target.closest('button, label, a');
            if (targetBtn) {
                const btnId = targetBtn.id || targetBtn.className || 'unnamed-element';
                this.log('USER_CLICK', 'UI_DOM', {
                    elementId: btnId,
                    tag: targetBtn.tagName,
                    text: targetBtn.innerText?.slice(0, 30) || ''
                });
            }
        });

        // Track Minimize/Maximize toggle
        const toggleBtn = document.getElementById('btn-toggle-logger');
        const loggerPanel = document.getElementById('logger-panel');
        if (toggleBtn && loggerPanel) {
            toggleBtn.addEventListener('click', () => {
                this.isMinimized = !this.isMinimized;
                loggerPanel.classList.toggle('minimized', this.isMinimized);
                toggleBtn.textContent = this.isMinimized ? 'RESTORE' : 'MINIMIZE';
                this.log('LOGGER_HUD_TOGGLE', 'LoggerModule', { isMinimized: this.isMinimized });
            });
        }

        // Track Export Logs button
        const exportBtn = document.getElementById('btn-export-logs');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportLogsJSON();
            });
        }
    }

    /**
     * Downloads interaction history as a structured JSON ledger
     */
    exportLogsJSON() {
        this.log('EXPORT_LOGS', 'LoggerModule', { count: this.logs.length });
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(this.logs, null, 2));
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", `depthwizard_interaction_ledger_${Date.now()}.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
    }
}

export const logger = new InteractionLogger();
