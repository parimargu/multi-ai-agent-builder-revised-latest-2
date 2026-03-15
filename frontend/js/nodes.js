/**
 * AgentForge Node Type Definitions
 * Defines all available node types with their properties, icons, and configs.
 */
const NODE_TYPES = {
    // ---- Triggers ----
    manual_trigger: {
        type: 'trigger', label: 'Manual Trigger', icon: '▶️', color: '#f97316',
        description: 'Manually start a workflow',
        ports: { input: [], output: ['output'], sub_input: [] },
        configFields: [],
    },
    webhook_trigger: {
        type: 'trigger', label: 'Webhook', icon: '🔗', color: '#f97316',
        description: 'Trigger via HTTP webhook',
        ports: { input: [], output: ['output'], sub_input: [] },
        configFields: [
            { key: 'url_path', label: 'URL Path', type: 'text', default: '/webhook' },
            { key: 'method', label: 'Method', type: 'select', options: ['GET', 'POST'], default: 'POST' },
        ],
    },
    chat_trigger: {
        type: 'trigger', label: 'Chat Message', icon: '💬', color: '#f97316',
        description: 'When chat message received',
        ports: { input: [], output: ['output'], sub_input: [] },
        configFields: [],
    },
    schedule_trigger: {
        type: 'trigger', label: 'Schedule', icon: '⏰', color: '#f97316',
        description: 'Run on a schedule',
        ports: { input: [], output: ['output'], sub_input: [] },
        configFields: [
            { key: 'cron', label: 'Cron Expression', type: 'text', default: '0 * * * *' },
        ],
    },

    // ---- AI Agents ----
    tools_agent: {
        type: 'agent', label: 'AI Agent', icon: '🤖', color: '#00d4aa',
        description: 'Tools Agent',
        ports: { input: ['input'], output: ['output'], sub_input: ['model', 'memory', 'tool'] },
        configFields: [
            { key: 'system_prompt', label: 'System Prompt', type: 'textarea', default: 'You are a helpful AI assistant.' },
            { key: 'max_iterations', label: 'Max Iterations', type: 'number', default: 5 },
        ],
    },
    conversational_agent: {
        type: 'agent', label: 'Conversational Agent', icon: '💭', color: '#00d4aa',
        description: 'Conversational Agent',
        ports: { input: ['input'], output: ['output'], sub_input: ['model', 'memory'] },
        configFields: [
            { key: 'system_prompt', label: 'System Prompt', type: 'textarea', default: 'You are a helpful conversational AI.' },
        ],
    },

    // ---- LLM Models ----
    openai_chat: {
        type: 'llm', label: 'OpenAI Chat Model', icon: '🟢', color: '#8b5cf6',
        description: 'GPT-4o, GPT-4o-mini',
        ports: { input: [], output: ['model'], sub_input: [] },
        configFields: [
            { key: 'model', label: 'Model', type: 'select', options: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'], default: 'gpt-4o-mini' },
            { key: 'temperature', label: 'Temperature', type: 'number', default: 0.7 },
            { key: 'max_tokens', label: 'Max Tokens', type: 'number', default: 4096 },
        ],
    },
    gemini_chat: {
        type: 'llm', label: 'Google Gemini', icon: '🔵', color: '#8b5cf6',
        description: 'Gemini Pro, Flash',
        ports: { input: [], output: ['model'], sub_input: [] },
        configFields: [
            { key: 'model', label: 'Model', type: 'select', options: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash'], default: 'gemini-2.0-flash' },
            { key: 'temperature', label: 'Temperature', type: 'number', default: 0.7 },
        ],
    },
    groq_chat: {
        type: 'llm', label: 'Groq', icon: '🟠', color: '#8b5cf6',
        description: 'Llama, Mixtral on Groq',
        ports: { input: [], output: ['model'], sub_input: [] },
        configFields: [
            { key: 'model', label: 'Model', type: 'select', options: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768'], default: 'llama-3.3-70b-versatile' },
            { key: 'temperature', label: 'Temperature', type: 'number', default: 0.7 },
        ],
    },
    openrouter_chat: {
        type: 'llm', label: 'OpenRouter', icon: '🟣', color: '#8b5cf6',
        description: 'Multi-model via OpenRouter',
        ports: { input: [], output: ['model'], sub_input: [] },
        configFields: [
            { key: 'model', label: 'Model', type: 'text', default: 'meta-llama/llama-3.3-70b-instruct' },
            { key: 'temperature', label: 'Temperature', type: 'number', default: 0.7 },
        ],
    },
    ollama_chat: {
        type: 'llm', label: 'Ollama (Local)', icon: '🦙', color: '#8b5cf6',
        description: 'Local LLM via Ollama',
        ports: { input: [], output: ['model'], sub_input: [] },
        configFields: [
            { key: 'model', label: 'Model', type: 'text', default: 'llama3.2' },
            { key: 'base_url', label: 'Base URL', type: 'text', default: 'http://localhost:11434' },
            { key: 'temperature', label: 'Temperature', type: 'number', default: 0.7 },
        ],
    },

    // ---- Memory ----
    buffer_memory: {
        type: 'memory', label: 'Window Buffer Memory', icon: '📋', color: '#3b82f6',
        description: 'Short-term sliding window',
        ports: { input: [], output: ['memory'], sub_input: [] },
        configFields: [
            { key: 'window_size', label: 'Window Size', type: 'number', default: 20 },
        ],
    },
    persistent_memory: {
        type: 'memory', label: 'Persistent Memory', icon: '🗄️', color: '#3b82f6',
        description: 'Long-term DB-backed',
        ports: { input: [], output: ['memory'], sub_input: [] },
        configFields: [
            { key: 'session_id', label: 'Session ID', type: 'text', default: 'default' },
            { key: 'ttl_hours', label: 'TTL (hours)', type: 'number', default: 720 },
        ],
    },

    // ---- Tools ----
    http_request: {
        type: 'tool', label: 'HTTP Request', icon: '🌐', color: '#10b981',
        description: 'Make HTTP API calls',
        ports: { input: [], output: ['tool'], sub_input: [] },
        configFields: [
            { key: 'url', label: 'URL', type: 'text', default: '' },
            { key: 'method', label: 'Method', type: 'select', options: ['GET', 'POST', 'PUT', 'DELETE'], default: 'GET' },
        ],
    },
    code_executor: {
        type: 'tool', label: 'Code Executor', icon: '💻', color: '#10b981',
        description: 'Execute Python code',
        ports: { input: [], output: ['tool'], sub_input: [] },
        configFields: [
            { key: 'code', label: 'Code', type: 'textarea', default: '# Python code here\nresult = "Hello!"' },
        ],
    },
    search_web: {
        type: 'tool', label: 'Web Search', icon: '🔍', color: '#10b981',
        description: 'Search the web',
        ports: { input: [], output: ['tool'], sub_input: [] },
        configFields: [],
    },
    custom_function: {
        type: 'tool', label: 'Custom Function', icon: '⚙️', color: '#10b981',
        description: 'Custom tool function',
        ports: { input: [], output: ['tool'], sub_input: [] },
        configFields: [
            { key: 'function_name', label: 'Function Name', type: 'text', default: '' },
            { key: 'description', label: 'Description', type: 'textarea', default: '' },
            { key: 'code', label: 'Code', type: 'textarea', default: '' },
        ],
    },

    // ---- Flow Control ----
    if_condition: {
        type: 'condition', label: 'If/Else', icon: '🔀', color: '#eab308',
        description: 'Conditional branching',
        ports: { input: ['input'], output: ['true', 'false'], sub_input: [] },
        configFields: [
            { key: 'condition', label: 'Condition', type: 'textarea', default: 'data.get("result") == True' },
        ],
    },
    switch_condition: {
        type: 'condition', label: 'Switch', icon: '🔀', color: '#eab308',
        description: 'Multi-way branching',
        ports: { input: ['input'], output: ['case1', 'case2', 'default'], sub_input: [] },
        configFields: [
            { key: 'cases', label: 'Cases (JSON)', type: 'textarea', default: '{}' },
        ],
    },

    // ---- Output ----
    send_response: {
        type: 'output', label: 'Send Response', icon: '📤', color: '#f43f5e',
        description: 'Send final reply',
        ports: { input: ['input'], output: [], sub_input: [] },
        configFields: [
            { key: 'format', label: 'Format', type: 'select', options: ['text', 'json'], default: 'text' },
        ],
    },
    output_parser: {
        type: 'output', label: 'Output Parser', icon: '📋', color: '#f43f5e',
        description: 'Parse & structure output',
        ports: { input: ['input'], output: ['output_parser'], sub_input: [] },
        configFields: [
            { key: 'schema', label: 'Output Schema (JSON)', type: 'textarea', default: '{}' },
        ],
    },
};

/**
 * Get node categories for palette display.
 */
function getNodeCategories() {
    const categories = {};
    for (const [subType, def] of Object.entries(NODE_TYPES)) {
        const cat = def.type;
        if (!categories[cat]) {
            categories[cat] = {
                label: cat.charAt(0).toUpperCase() + cat.slice(1) + 's',
                items: [],
            };
        }
        categories[cat].items.push({ subType, ...def });
    }
    // Order
    const order = ['trigger', 'agent', 'llm', 'memory', 'tool', 'condition', 'output'];
    const labels = {
        trigger: '⚡ Triggers',
        agent: '🤖 AI Agents',
        llm: '🧠 LLM Models',
        memory: '💾 Memory',
        tool: '🔧 Tools',
        condition: '🔀 Flow Control',
        output: '📤 Output',
    };
    return order.map(key => ({
        key,
        label: labels[key] || key,
        items: categories[key]?.items || [],
    }));
}
