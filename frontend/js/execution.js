/**
 * AgentForge Execution Monitor
 * Lists executions with status and shows detailed logs.
 */

async function loadExecutions() {
    const content = document.getElementById('executions-content');
    content.innerHTML = '<div class="text-center mt-4"><div class="loading-spinner" style="margin:auto;"></div></div>';

    try {
        const executions = await API.listExecutions();

        if (executions.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">▶️</div>
                    <h3>No executions yet</h3>
                    <p>Run an agent to see execution history here.</p>
                </div>
            `;
            return;
        }

        content.innerHTML = `
            <div style="margin-bottom:var(--space-6);">
                <h2 style="font-size:var(--font-size-xl);font-weight:600;">Execution History</h2>
                <p class="text-muted mt-2">View and monitor agent workflow executions</p>
            </div>
            <div class="execution-list" id="execution-list">
                ${executions.map(exec => renderExecutionItem(exec)).join('')}
            </div>
            <div id="execution-detail-container" style="margin-top:var(--space-6);"></div>
        `;
    } catch (err) {
        content.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <h3>Error loading executions</h3>
                <p>${err.message}</p>
                <button class="btn btn-secondary" onclick="loadExecutions()">Retry</button>
            </div>
        `;
    }
}

function renderExecutionItem(exec) {
    const created = new Date(exec.created_at).toLocaleString();
    const duration = exec.duration_seconds ? `${exec.duration_seconds.toFixed(2)}s` : '—';
    const agentId = exec.agent_id?.slice(0, 8) || '?';

    return `
        <div class="execution-item" onclick="viewExecution('${exec.id}')">
            <div style="display:flex;align-items:center;gap:var(--space-4);">
                <span class="badge badge-${exec.status}">${exec.status}</span>
                <div>
                    <div style="font-weight:500;">Agent ${agentId}...</div>
                    <div class="text-sm text-muted">${created}</div>
                </div>
            </div>
            <div style="display:flex;align-items:center;gap:var(--space-4);">
                <span class="text-sm text-muted">⏱ ${duration}</span>
                <span class="text-sm text-muted">#${exec.id.slice(0, 8)}</span>
            </div>
        </div>
    `;
}

async function viewExecution(executionId) {
    const container = document.getElementById('execution-detail-container');
    if (!container) return;

    container.innerHTML = '<div class="text-center"><div class="loading-spinner" style="margin:auto;"></div></div>';

    try {
        const exec = await API.getExecution(executionId);

        container.innerHTML = `
            <div class="execution-detail">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-5);">
                    <div>
                        <h3 style="font-size:var(--font-size-lg);font-weight:600;">
                            Execution #${exec.id.slice(0, 8)}
                        </h3>
                        <span class="text-sm text-muted">${new Date(exec.created_at).toLocaleString()}</span>
                    </div>
                    <span class="badge badge-${exec.status}" style="font-size:var(--font-size-sm);">${exec.status}</span>
                </div>

                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:var(--space-4);margin-bottom:var(--space-5);">
                    <div class="stat-card" style="padding:var(--space-4);">
                        <div>
                            <div class="stat-value" style="font-size:var(--font-size-lg);">
                                ${exec.duration_seconds ? exec.duration_seconds.toFixed(2) + 's' : '—'}
                            </div>
                            <div class="stat-label">Duration</div>
                        </div>
                    </div>
                    <div class="stat-card" style="padding:var(--space-4);">
                        <div>
                            <div class="stat-value" style="font-size:var(--font-size-lg);">${exec.logs?.length || 0}</div>
                            <div class="stat-label">Steps</div>
                        </div>
                    </div>
                    <div class="stat-card" style="padding:var(--space-4);">
                        <div>
                            <div class="stat-value" style="font-size:var(--font-size-lg);">
                                ${exec.logs?.filter(l => l.status === 'failed').length || 0}
                            </div>
                            <div class="stat-label">Errors</div>
                        </div>
                    </div>
                </div>

                ${exec.error_message ? `
                    <div style="background:rgba(248,81,73,0.1);border:1px solid rgba(248,81,73,0.3);border-radius:var(--radius-md);padding:var(--space-4);margin-bottom:var(--space-5);">
                        <strong style="color:var(--accent-danger);">Error:</strong>
                        <span class="text-sm">${escapeHtml(exec.error_message)}</span>
                    </div>
                ` : ''}

                ${exec.output_data && Object.keys(exec.output_data).length > 0 ? `
                    <div style="margin-bottom:var(--space-5);">
                        <h4 style="margin-bottom:var(--space-3);font-weight:600;">Output</h4>
                        <pre style="background:var(--bg-tertiary);padding:var(--space-4);border-radius:var(--radius-md);font-family:var(--font-mono);font-size:var(--font-size-sm);overflow-x:auto;white-space:pre-wrap;">${escapeHtml(JSON.stringify(exec.output_data, null, 2))}</pre>
                    </div>
                ` : ''}

                <div class="execution-logs">
                    <h4 style="margin-bottom:var(--space-4);font-weight:600;">Execution Steps</h4>
                    ${(exec.logs || []).map(log => `
                        <div class="log-entry">
                            <div class="log-status-dot ${log.status}"></div>
                            <div style="flex:1;min-width:0;">
                                <div style="display:flex;align-items:center;gap:var(--space-3);margin-bottom:var(--space-1);">
                                    <strong style="font-size:var(--font-size-sm);">${escapeHtml(log.node_label || 'Unknown')}</strong>
                                    <span class="badge badge-${log.status}" style="font-size:10px;">${log.status}</span>
                                    <span class="text-sm text-muted">${log.duration_ms ? log.duration_ms.toFixed(0) + 'ms' : ''}</span>
                                </div>
                                ${log.error_message ? `<div style="color:var(--accent-danger);font-size:var(--font-size-xs);">${escapeHtml(log.error_message)}</div>` : ''}
                                ${log.output_data && Object.keys(log.output_data).length > 0 ? `
                                    <details style="margin-top:var(--space-2);">
                                        <summary class="text-sm text-muted" style="cursor:pointer;">View output</summary>
                                        <pre style="margin-top:var(--space-2);font-family:var(--font-mono);font-size:11px;color:var(--text-secondary);white-space:pre-wrap;">${escapeHtml(JSON.stringify(log.output_data, null, 2))}</pre>
                                    </details>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<p class="text-muted">Error loading execution details: ${err.message}</p>`;
    }
}
