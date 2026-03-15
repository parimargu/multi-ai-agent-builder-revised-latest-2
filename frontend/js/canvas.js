/**
 * AgentForge Canvas Engine
 * SVG-based visual workflow editor: drag-drop nodes, connect edges, pan/zoom.
 */

const Canvas = {
    nodes: [],
    edges: [],
    agentId: null,
    agentData: null,
    scale: 1,
    offsetX: 0,
    offsetY: 0,
    isPanning: false,
    panStartX: 0,
    panStartY: 0,
    dragNode: null,
    dragOffset: { x: 0, y: 0 },
    connectingFrom: null,
    selectedNodeId: null,
    nextNodeId: 1,
    svgEl: null,
    nodesLayer: null,
    canvasArea: null,
    initialized: false,

    init() {
        if (this.initialized) return;
        this.initialized = true;

        this.svgEl = document.getElementById('canvas-svg');
        this.nodesLayer = document.getElementById('canvas-nodes-layer');
        this.canvasArea = document.getElementById('canvas-area');

        // Pan
        this.canvasArea.addEventListener('mousedown', (e) => {
            const isBg = e.target === this.canvasArea || 
                         e.target === this.svgEl || 
                         e.target === this.nodesLayer ||
                         e.target.classList.contains('canvas-area');
            
            if (isBg) {
                this.isPanning = true;
                this.panStartX = e.clientX - this.offsetX;
                this.panStartY = e.clientY - this.offsetY;
                this.deselectAll();
            }
        });

        document.addEventListener('mousemove', (e) => {
            if (this.isPanning) {
                this.offsetX = e.clientX - this.panStartX;
                this.offsetY = e.clientY - this.panStartY;
                this.updateTransform();
            }
            if (this.dragNode) {
                const rect = this.canvasArea.getBoundingClientRect();
                const x = (e.clientX - rect.left - this.offsetX) / this.scale - this.dragOffset.x;
                const y = (e.clientY - rect.top - this.offsetY) / this.scale - this.dragOffset.y;
                this.dragNode.x = Math.round(x / 10) * 10;
                this.dragNode.y = Math.round(y / 10) * 10;
                this.renderNode(this.dragNode);
                this.renderEdges();
            }
            if (this.connectingFrom) {
                this.renderTempEdge(e);
            }
        });

        document.addEventListener('mouseup', () => {
            this.isPanning = false;
            this.dragNode = null;
            if (this.connectingFrom) {
                this.connectingFrom = null;
                this.clearTempEdge();
            }
        });

        // Zoom
        this.canvasArea.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            const newScale = Math.max(0.2, Math.min(3, this.scale * delta));
            
            const rect = this.canvasArea.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            this.offsetX = mouseX - (mouseX - this.offsetX) * (newScale / this.scale);
            this.offsetY = mouseY - (mouseY - this.offsetY) * (newScale / this.scale);
            this.scale = newScale;
            this.updateTransform();
        }, { passive: false });

        this.buildPalette();
    },

    updateTransform() {
        this.nodesLayer.style.transform = `translate(${this.offsetX}px, ${this.offsetY}px) scale(${this.scale})`;
        // Sync SVG
        const svg = this.svgEl;
        svg.style.transform = `translate(${this.offsetX}px, ${this.offsetY}px) scale(${this.scale})`;
        svg.style.transformOrigin = '0 0';
    },

    reset() {
        this.nodes = [];
        this.edges = [];
        this.agentId = null;
        this.agentData = null;
        this.selectedNodeId = null;
        this.nextNodeId = 1;
        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        this.updateTransform();
        this.render();
    },

    async loadAgent(agentId) {
        this.reset();
        this.agentId = agentId;

        try {
            const agent = await API.getAgent(agentId);
            this.agentData = agent;
            document.getElementById('canvas-agent-name').value = agent.name;
            document.getElementById('canvas-agent-status').textContent = agent.status;
            document.getElementById('canvas-agent-status').className = `badge badge-${agent.status}`;

            // Convert nodes
            this.nodes = (agent.nodes || []).map((n, i) => ({
                id: n.id,
                subType: n.sub_type,
                type: n.node_type,
                label: n.label,
                x: n.position_x || (150 + i * 250),
                y: n.position_y || 200,
                config: n.config || {},
                parentNodeId: n.parent_node_id,
            }));

            // Convert edges
            this.edges = (agent.edges || []).map(e => ({
                id: e.id,
                sourceId: e.source_node_id,
                targetId: e.target_node_id,
                sourcePort: e.source_port,
                targetPort: e.target_port,
                edgeType: e.edge_type,
            }));

            this.nextNodeId = this.nodes.length + 1;
            this.render();
            // Delay fitView slightly to ensure container dimensions are computed correctly
            setTimeout(() => this.fitView(), 100);
        } catch (err) {
            showToast('Failed to load agent: ' + err.message, 'error');
        }
    },

    addNode(subType, x, y) {
        const def = NODE_TYPES[subType];
        if (!def) return;

        const nodeId = 'temp-' + (this.nextNodeId++);
        const node = {
            id: nodeId,
            subType,
            type: def.type,
            label: def.label,
            x: x || 200 + Math.random() * 300,
            y: y || 150 + Math.random() * 200,
            config: {},
        };

        // Set defaults
        for (const field of def.configFields || []) {
            node.config[field.key] = field.default;
        }

        this.nodes.push(node);
        this.render();
        this.selectNode(nodeId);
        return node;
    },

    removeNode(nodeId) {
        this.nodes = this.nodes.filter(n => n.id !== nodeId);
        this.edges = this.edges.filter(e => e.sourceId !== nodeId && e.targetId !== nodeId);
        if (this.selectedNodeId === nodeId) {
            this.selectedNodeId = null;
            closeConfigPanel();
        }
        this.render();
    },

    addEdge(sourceId, targetId, sourcePort, targetPort, edgeType) {
        // Prevent duplicates
        const exists = this.edges.find(e =>
            e.sourceId === sourceId && e.targetId === targetId &&
            e.sourcePort === sourcePort && e.targetPort === targetPort
        );
        if (exists) return;

        this.edges.push({
            id: 'edge-' + Date.now(),
            sourceId,
            targetId,
            sourcePort: sourcePort || 'output',
            targetPort: targetPort || 'input',
            edgeType: edgeType || 'default',
        });
        this.render();
    },

    removeEdge(edgeId) {
        this.edges = this.edges.filter(e => e.id !== edgeId);
        this.render();
    },

    selectNode(nodeId) {
        this.selectedNodeId = nodeId;
        this.render();
        const node = this.nodes.find(n => n.id === nodeId);
        if (node) openConfigPanel(node);
    },

    deselectAll() {
        this.selectedNodeId = null;
        closeConfigPanel();
        this.render();
    },

    // ---- Rendering ----
    render() {
        this.renderNodes();
        this.renderEdges();
    },

    renderNodes() {
        this.nodesLayer.innerHTML = '';
        for (const node of this.nodes) {
            this.renderNode(node);
        }
    },

    renderNode(node) {
        const def = NODE_TYPES[node.subType] || {};
        let el = document.getElementById(`node-${node.id}`);
        const isNew = !el;

        if (isNew) {
            el = document.createElement('div');
            el.id = `node-${node.id}`;
            el.className = 'wf-node';
            this.nodesLayer.appendChild(el);
        }

        el.style.left = node.x + 'px';
        el.style.top = node.y + 'px';
        el.className = `wf-node${this.selectedNodeId === node.id ? ' selected' : ''}`;

        const subPorts = (def.ports?.sub_input || []);
        const hasSubPorts = subPorts.length > 0;
        const hasInput = (def.ports?.input || []).length > 0;
        const hasOutput = (def.ports?.output || []).length > 0;

        let portsHtml = '';
        if (hasInput) {
            portsHtml += `<div class="wf-node-port port-input" data-node="${node.id}" data-port="input" data-dir="input"></div>`;
        }
        
        const outputs = def.ports?.output || [];
        if (outputs.length === 1) {
            portsHtml += `<div class="wf-node-port port-output" data-node="${node.id}" data-port="${outputs[0]}" data-dir="output"></div>`;
        } else if (outputs.length > 1) {
            outputs.forEach((port, i) => {
                const top = 30 + (i * 28);
                portsHtml += `<div class="wf-node-port port-output" data-node="${node.id}" data-port="${port}" data-dir="output" style="top:${top}px;right:-7px;transform:none;" title="${port}"></div>`;
            });
        }

        let subPortsHtml = '';
        if (hasSubPorts) {
            subPortsHtml = `<div class="wf-node-sub-ports">
                ${subPorts.map(p => `
                    <div class="wf-node-sub-port" data-node="${node.id}" data-port="${p}" data-dir="sub_input">
                        <div class="port-dot" data-node="${node.id}" data-port="${p}" data-dir="sub_input"></div>
                        <span class="port-label">${p.charAt(0).toUpperCase() + p.slice(1)}</span>
                    </div>
                `).join('')}
            </div>`;
        }

        el.innerHTML = `
            ${portsHtml}
            <div class="wf-node-header">
                <div class="wf-node-icon ${def.type || ''}">${def.icon || '📦'}</div>
                <div class="wf-node-info">
                    <div class="wf-node-label">${node.label || def.label}</div>
                    <div class="wf-node-type">${def.description || def.type}</div>
                </div>
            </div>
            ${subPortsHtml}
        `;

        // Drag
        const header = el.querySelector('.wf-node-header');
        header.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            const rect = this.canvasArea.getBoundingClientRect();
            this.dragNode = node;
            this.dragOffset = {
                x: (e.clientX - rect.left - this.offsetX) / this.scale - node.x,
                y: (e.clientY - rect.top - this.offsetY) / this.scale - node.y,
            };
            this.selectNode(node.id);
        });

        // Port interactions
        el.querySelectorAll('.wf-node-port, .port-dot').forEach(portEl => {
            portEl.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                const dir = portEl.dataset.dir;
                const port = portEl.dataset.port;
                const nodeId = portEl.dataset.node;

                if (dir === 'output' || dir === 'sub_input') {
                    // This is an invalid connection start for sub_input
                    // Only output ports can start connections
                }
                if (dir === 'output') {
                    this.connectingFrom = { nodeId, port, dir };
                }
            });

            portEl.addEventListener('mouseup', (e) => {
                e.stopPropagation();
                if (this.connectingFrom) {
                    const dir = portEl.dataset.dir;
                    const port = portEl.dataset.port;
                    const nodeId = portEl.dataset.node;

                    if (nodeId !== this.connectingFrom.nodeId) {
                        if (dir === 'input' || dir === 'sub_input') {
                            const edgeType = dir === 'sub_input' ? 'sub_node' : 'default';
                            this.addEdge(
                                this.connectingFrom.nodeId, nodeId,
                                this.connectingFrom.port, port, edgeType
                            );
                        }
                    }
                    this.connectingFrom = null;
                    this.clearTempEdge();
                }
            });
        });

        // Also allow output-port-to-sub-port connections the other way
        el.querySelectorAll('.port-dot').forEach(portEl => {
            portEl.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                // Sub-input ports: we start a "reverse" connection search
                // The idea is: you drag FROM a sub_input port to look for the appropriate output node 
                // For simplicity, skip and rely on output→sub_input direction
            });
        });
    },

    renderEdges() {
        this.svgEl.innerHTML = '';
        for (const edge of this.edges) {
            this.renderEdge(edge);
        }
    },

    renderEdge(edge) {
        const sourceNode = this.nodes.find(n => n.id === edge.sourceId);
        const targetNode = this.nodes.find(n => n.id === edge.targetId);
        if (!sourceNode || !targetNode) return;

        const sourceEl = document.getElementById(`node-${edge.sourceId}`);
        const targetEl = document.getElementById(`node-${edge.targetId}`);
        if (!sourceEl || !targetEl) return;

        // Calculate port positions
        let sx, sy, tx, ty;
        const sourceDef = NODE_TYPES[sourceNode.subType] || {};
        const targetDef = NODE_TYPES[targetNode.subType] || {};

        // Source position (right side)
        sx = sourceNode.x + sourceEl.offsetWidth;
        const sourceOutputs = sourceDef.ports?.output || [];
        if (sourceOutputs.length > 1) {
            const idx = sourceOutputs.indexOf(edge.sourcePort);
            sy = sourceNode.y + 30 + (idx * 28) + 7;
        } else {
            sy = sourceNode.y + sourceEl.offsetHeight / 2;
        }

        // Target position
        if (edge.edgeType === 'sub_node') {
            // Connect to bottom sub-port
            const subPorts = targetDef.ports?.sub_input || [];
            const portIdx = subPorts.indexOf(edge.targetPort);
            const portCount = subPorts.length;
            const nodeWidth = targetEl.offsetWidth;
            const spacing = nodeWidth / (portCount + 1);
            tx = targetNode.x + spacing * (portIdx + 1);
            ty = targetNode.y + targetEl.offsetHeight;
        } else {
            // Connect to left side input
            tx = targetNode.x;
            ty = targetNode.y + targetEl.offsetHeight / 2;
        }

        // Draw bezier curve
        const isSubNode = edge.edgeType === 'sub_node';
        let path;
        if (isSubNode) {
            // Draw curve from output side down to sub-port
            const mx = (sx + tx) / 2;
            const my = Math.max(sy, ty) + 60;
            path = `M ${sx} ${sy} C ${sx + 80} ${sy}, ${tx} ${my}, ${tx} ${ty}`;
        } else {
            const dx = Math.abs(tx - sx) * 0.5;
            path = `M ${sx} ${sy} C ${sx + dx} ${sy}, ${tx - dx} ${ty}, ${tx} ${ty}`;
        }

        const pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        pathEl.setAttribute('d', path);
        pathEl.setAttribute('fill', 'none');
        pathEl.setAttribute('stroke', isSubNode ? '#7c3aed' : '#00d4aa');
        pathEl.setAttribute('stroke-width', '2');
        pathEl.setAttribute('stroke-dasharray', isSubNode ? '6 4' : 'none');
        pathEl.style.pointerEvents = 'stroke';
        pathEl.style.cursor = 'pointer';
        pathEl.addEventListener('click', () => {
            if (confirm('Remove this connection?')) {
                this.removeEdge(edge.id);
            }
        });

        this.svgEl.appendChild(pathEl);
    },

    renderTempEdge(e) {
        this.clearTempEdge();
        if (!this.connectingFrom) return;

        const sourceNode = this.nodes.find(n => n.id === this.connectingFrom.nodeId);
        if (!sourceNode) return;

        const sourceEl = document.getElementById(`node-${sourceNode.id}`);
        if (!sourceEl) return;

        const rect = this.canvasArea.getBoundingClientRect();
        const sx = sourceNode.x + sourceEl.offsetWidth;
        const sy = sourceNode.y + sourceEl.offsetHeight / 2;
        const tx = (e.clientX - rect.left - this.offsetX) / this.scale;
        const ty = (e.clientY - rect.top - this.offsetY) / this.scale;

        const dx = Math.abs(tx - sx) * 0.5;
        const path = `M ${sx} ${sy} C ${sx + dx} ${sy}, ${tx - dx} ${ty}, ${tx} ${ty}`;

        const pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        pathEl.setAttribute('d', path);
        pathEl.setAttribute('fill', 'none');
        pathEl.setAttribute('stroke', '#00d4aa');
        pathEl.setAttribute('stroke-width', '2');
        pathEl.setAttribute('stroke-opacity', '0.5');
        pathEl.setAttribute('stroke-dasharray', '6 4');
        pathEl.id = 'temp-edge';

        this.svgEl.appendChild(pathEl);
    },

    clearTempEdge() {
        const el = document.getElementById('temp-edge');
        if (el) el.remove();
    },

    fitView() {
        if (this.nodes.length === 0) return;

        const rect = this.canvasArea.getBoundingClientRect();
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

        for (const node of this.nodes) {
            minX = Math.min(minX, node.x);
            minY = Math.min(minY, node.y);
            maxX = Math.max(maxX, node.x + 200);
            maxY = Math.max(maxY, node.y + 100);
        }

        const padding = 100;
        const contentWidth = maxX - minX + padding * 2;
        const contentHeight = maxY - minY + padding * 2;

        this.scale = Math.min(
            rect.width / contentWidth,
            rect.height / contentHeight,
            1.5
        );
        this.scale = Math.max(0.3, this.scale);
        this.offsetX = (rect.width - contentWidth * this.scale) / 2 - minX * this.scale + padding * this.scale;
        this.offsetY = (rect.height - contentHeight * this.scale) / 2 - minY * this.scale + padding * this.scale;
        this.updateTransform();
    },

    // ---- Palette ----
    buildPalette() {
        const list = document.getElementById('palette-list');
        const categories = getNodeCategories();

        list.innerHTML = categories.map(cat => `
            <div class="palette-category" data-category="${cat.key}">
                <div class="palette-category-title">${cat.label}</div>
                ${cat.items.map(item => `
                    <div class="palette-node"
                         data-sub-type="${item.subType}">
                        <div class="palette-node-icon" style="background:${item.color}22; color:${item.color};">
                            ${item.icon}
                        </div>
                        <div class="palette-node-info">
                            <div class="palette-node-name">${item.label}</div>
                            <div class="palette-node-desc">${item.description}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `).join('');

        // Use event delegation for palette nodes
        list.querySelectorAll('.palette-node').forEach(el => {
            el.addEventListener('click', () => {
                this.onPaletteNodeClick(el.dataset.subType);
            });
        });
    },

    onPaletteNodeClick(subType) {
        const rect = this.canvasArea.getBoundingClientRect();
        const x = (rect.width / 2 - this.offsetX) / this.scale;
        const y = (rect.height / 2 - this.offsetY) / this.scale;
        this.addNode(subType, x, y);
    },

    getWorkflowData() {
        return {
            nodes: this.nodes.map(n => ({
                id: n.id,
                node_type: n.type,
                sub_type: n.subType,
                label: n.label,
                position_x: n.x,
                position_y: n.y,
                config: n.config || {},
                parent_node_id: n.parentNodeId || null,
            })),
            edges: this.edges.map(e => ({
                source_node_id: e.sourceId,
                target_node_id: e.targetId,
                source_port: e.sourcePort,
                target_port: e.targetPort,
                edge_type: e.edgeType || 'default',
            })),
        };
    },
    // ---- Config Panel ----
    openConfigPanel(node) {
        const panel = document.getElementById('config-panel');
        const title = document.getElementById('config-panel-title');
        const body = document.getElementById('config-panel-body');
        const def = NODE_TYPES[node.subType] || {};

        title.textContent = node.label || def.label;
        panel.classList.add('open');

        let html = `
            <div class="form-group">
                <label class="form-label">Label</label>
                <input class="form-input" type="text" id="config-label" value="${node.label || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Type</label>
                <input class="form-input" type="text" value="${def.label} (${def.type})" disabled>
            </div>
        `;

        for (const field of (def.configFields || [])) {
            const value = node.config?.[field.key] ?? field.default ?? '';
            if (field.type === 'textarea') {
                html += `
                    <div class="form-group">
                        <label class="form-label">${field.label}</label>
                        <textarea class="form-input" id="config-${field.key}" rows="4">${value}</textarea>
                    </div>
                `;
            } else if (field.type === 'select') {
                html += `
                    <div class="form-group">
                        <label class="form-label">${field.label}</label>
                        <select class="form-input" id="config-${field.key}">
                            ${(field.options || []).map(opt =>
                                `<option value="${opt}" ${opt === value ? 'selected' : ''}>${opt}</option>`
                            ).join('')}
                        </select>
                    </div>
                `;
            } else {
                html += `
                    <div class="form-group">
                        <label class="form-label">${field.label}</label>
                        <input class="form-input" type="${field.type}" id="config-${field.key}" value="${value}">
                    </div>
                `;
            }
        }

        body.innerHTML = html;
    },

    closeConfigPanel() {
        document.getElementById('config-panel').classList.remove('open');
    },

    applyNodeConfig() {
        const node = this.nodes.find(n => n.id === this.selectedNodeId);
        if (!node) return;

        const def = NODE_TYPES[node.subType] || {};
        const label = document.getElementById('config-label')?.value;
        if (label) node.label = label;

        for (const field of (def.configFields || [])) {
            const el = document.getElementById(`config-${field.key}`);
            if (el) {
                node.config[field.key] = field.type === 'number' ? parseFloat(el.value) : el.value;
            }
        }

        this.render();
        showToast('Node config updated', 'success');
    },

    toggleNodePalette() {
        document.getElementById('node-palette').classList.toggle('open');
    },

    filterPaletteNodes(query) {
        const q = query.toLowerCase();
        document.querySelectorAll('.palette-node').forEach(el => {
            const name = el.querySelector('.palette-node-name').textContent.toLowerCase();
            const desc = el.querySelector('.palette-node-desc').textContent.toLowerCase();
            el.style.display = (name.includes(q) || desc.includes(q)) ? '' : 'none';
        });
    },

    zoomReset() {
        this.fitView();
    },

    async saveWorkflow() {
        if (!this.agentId) return;

        const btn = document.querySelector('button[title="Save"]');
        let oldHtml = '';
        if (btn) {
            btn.disabled = true;
            oldHtml = btn.innerHTML;
            btn.innerHTML = '<span>Saving...</span>';
        }

        try {
            const data = this.getWorkflowData();
            const updatedAgent = await API.saveWorkflow(this.agentId, data);
            
            // Update local agent data
            this.agentData = updatedAgent;
            
            // Refresh canvas with server-side IDs
            await this.loadAgent(this.agentId);
            
            showToast('Workflow saved successfully!', 'success');
        } catch (err) {
            showToast('Save failed: ' + err.message, 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = oldHtml || '💾 Save';
            }
        }
    },

    async executeWorkflow() {
        if (!this.agentId) return;

        try {
            const result = await API.executeAgent(this.agentId, { message: 'Hello, execute this workflow.' });
            showToast(`Execution queued! ID: ${result.id.slice(0, 8)}...`, 'success');
        } catch (err) {
            showToast('Execution failed: ' + err.message, 'error');
        }
    },
    
    deleteSelectedNode() {
        if (this.selectedNodeId) {
            this.removeNode(this.selectedNodeId);
            showToast('Node deleted', 'success');
        }
    },
};
