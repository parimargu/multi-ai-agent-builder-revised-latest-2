/**
 * AgentForge API Client
 * Fetch-based client with JWT auth, error handling, and base URL config.
 */
const API = {
    baseUrl: '',
    token: null,

    init() {
        this.token = localStorage.getItem('agentforge_token');
    },

    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('agentforge_token', token);
        } else {
            localStorage.removeItem('agentforge_token');
        }
    },

    getHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    },

    async request(method, path, body = null) {
        const options = {
            method,
            headers: this.getHeaders(),
        };
        if (body && method !== 'GET') {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(`${this.baseUrl}${path}`, options);
            
            if (response.status === 401) {
                this.setToken(null);
                window.location.reload();
                return null;
            }

            if (response.status === 204) return null;

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || `Request failed: ${response.status}`);
            }

            return data;
        } catch (error) {
            if (error.message === 'Failed to fetch') {
                throw new Error('Network error. Please check your connection.');
            }
            throw error;
        }
    },

    // Auth
    async login(email, password) {
        return this.request('POST', '/api/auth/login', { email, password });
    },

    async register(data) {
        return this.request('POST', '/api/auth/register', data);
    },

    async getMe() {
        return this.request('GET', '/api/auth/me');
    },

    // Agents
    async listAgents() {
        return this.request('GET', '/api/agents');
    },

    async getAgent(id) {
        return this.request('GET', `/api/agents/${id}`);
    },

    async createAgent(data) {
        return this.request('POST', '/api/agents', data);
    },

    async updateAgent(id, data) {
        return this.request('PUT', `/api/agents/${id}`, data);
    },

    async deleteAgent(id) {
        return this.request('DELETE', `/api/agents/${id}`);
    },

    // Nodes & Edges
    async addNode(agentId, data) {
        return this.request('POST', `/api/agents/${agentId}/nodes`, data);
    },

    async updateNode(agentId, nodeId, data) {
        return this.request('PUT', `/api/agents/${agentId}/nodes/${nodeId}`, data);
    },

    async deleteNode(agentId, nodeId) {
        return this.request('DELETE', `/api/agents/${agentId}/nodes/${nodeId}`);
    },

    async addEdge(agentId, data) {
        return this.request('POST', `/api/agents/${agentId}/edges`, data);
    },

    async deleteEdge(agentId, edgeId) {
        return this.request('DELETE', `/api/agents/${agentId}/edges/${edgeId}`);
    },

    async saveWorkflow(agentId, data) {
        return this.request('PUT', `/api/agents/${agentId}/workflow`, data);
    },

    // Executions
    async executeAgent(agentId, inputData = {}) {
        return this.request('POST', `/api/agents/${agentId}/execute`, { input_data: inputData });
    },

    async listExecutions(agentId = null) {
        const query = agentId ? `?agent_id=${agentId}` : '';
        return this.request('GET', `/api/executions${query}`);
    },

    async getExecution(id) {
        return this.request('GET', `/api/executions/${id}`);
    },

    // Providers
    async getNodeTypes() {
        return this.request('GET', '/api/providers/node-types');
    },

    // Health
    async healthCheck() {
        return this.request('GET', '/api/health');
    },
};

API.init();
