# 🏗️ AgentForge Architecture Documentation

## Project Architecture Diagram

```mermaid
graph TB
    subgraph Frontend["🖥️ Frontend (SPA)"]
        HTML["index.html"]
        CSS["styles.css<br/>Dark/Light Theme"]
        JS_API["api.js"]
        JS_Canvas["canvas.js<br/>Workflow Editor"]
        JS_Dash["dashboard.js"]
        JS_Exec["execution.js"]
        JS_App["app.js<br/>Router & Auth"]
    end

    subgraph API["⚡ FastAPI Backend"]
        Auth_Route["Auth API<br/>/api/auth/*"]
        Agent_Route["Agent API<br/>/api/agents/*"]
        Exec_Route["Execution API<br/>/api/executions/*"]
        Provider_Route["Provider API<br/>/api/providers/*"]
        Health["Health Check"]
    end

    subgraph Core["🔐 Core"]
        Security["security.py<br/>JWT + bcrypt"]
        Deps["dependencies.py<br/>Auth Middleware"]
        Config["config.py<br/>YAML Loader"]
    end

    subgraph Engine["🤖 Execution Engine"]
        Executor["Workflow Executor<br/>DAG Processor"]
        NodeReg["Node Registry<br/>Factory Pattern"]
        subgraph LLM["LLM Providers"]
            OpenAI["OpenAI"]
            Gemini["Gemini"]
            Groq["Groq"]
            OpenRouter["OpenRouter"]
            Ollama["Ollama"]
        end
        subgraph Memory["Memory System"]
            Buffer["Buffer Memory<br/>Short-term"]
            Persistent["Persistent Memory<br/>Long-term"]
        end
        subgraph Tools["Tools"]
            HTTP_Tool["HTTP Request"]
            Code_Tool["Code Executor"]
            Search_Tool["Web Search"]
        end
        subgraph Nodes["Node Types"]
            Trigger["Trigger"]
            Agent_Node["AI Agent"]
            Condition["Condition"]
            Output["Output"]
        end
    end

    subgraph Workers["⚙️ Celery Workers"]
        CeleryApp["celery_app.py"]
    end

    subgraph Data["💾 Data Stores"]
        PG["PostgreSQL"]
        Redis["Redis"]
        RabbitMQ["RabbitMQ"]
    end

    Frontend -->|HTTP/JSON| API
    API --> Core
    API --> Engine
    Exec_Route --> Workers
    Workers -->|Async Tasks| Engine
    Executor --> NodeReg
    NodeReg --> LLM
    NodeReg --> Memory
    NodeReg --> Tools
    Engine --> PG
    Workers -->|Broker| RabbitMQ
    Workers -->|Results| Redis
    API --> PG

    style Frontend fill:#1e293b,stroke:#00d4aa,color:#e6edf3
    style API fill:#1e293b,stroke:#7c3aed,color:#e6edf3
    style Engine fill:#1e293b,stroke:#3b82f6,color:#e6edf3
    style Core fill:#1e293b,stroke:#eab308,color:#e6edf3
    style Workers fill:#1e293b,stroke:#f97316,color:#e6edf3
    style Data fill:#1e293b,stroke:#f43f5e,color:#e6edf3
```

---

## Process Flow Diagram

```mermaid
flowchart TD
    Start([User Opens App]) --> Auth{Authenticated?}
    Auth -->|No| Login[Login/Register Page]
    Login --> JWT[Generate JWT Token]
    JWT --> Dashboard

    Auth -->|Yes| Dashboard[Dashboard]
    Dashboard --> Create[Create New Agent]
    Dashboard --> Open[Open Existing Agent]

    Create --> Canvas[Workflow Canvas]
    Open --> Canvas

    Canvas --> AddNodes[Add Nodes<br/>Drag from Palette]
    AddNodes --> ConfigNodes[Configure Nodes<br/>LLM, Memory, Tools]
    ConfigNodes --> ConnectEdges[Connect Edges<br/>Click and Drag Ports]
    ConnectEdges --> Save[Save Workflow<br/>API PUT]

    Save --> Execute[Execute Workflow]
    Execute --> Celery{Celery Available?}
    
    Celery -->|Yes| Queue[Queue to RabbitMQ]
    Queue --> Worker[Celery Worker]
    Worker --> DAG[DAG Executor]
    
    Celery -->|No| DAG
    
    DAG --> Topo[Topological Sort]
    Topo --> ForEach[For Each Node]
    
    ForEach --> NodeType{Node Type}
    NodeType -->|Trigger| RunTrigger[Execute Trigger]
    NodeType -->|Agent| ResolveSubNodes[Resolve Sub-nodes<br/>LLM + Memory + Tools]
    NodeType -->|Condition| EvalCondition[Evaluate Condition]
    NodeType -->|Output| FormatOutput[Format Output]
    
    ResolveSubNodes --> LLMCall[Call LLM Provider]
    LLMCall --> ToolLoop{Tool Calls?}
    ToolLoop -->|Yes| ExecTool[Execute Tool]
    ExecTool --> LLMCall
    ToolLoop -->|No| NextNode[Next Node]
    
    RunTrigger --> NextNode
    EvalCondition --> NextNode
    FormatOutput --> NextNode
    NextNode --> ForEach
    
    NextNode --> Done[Execution Complete]
    Done --> SaveResults[Save Results & Logs]
    SaveResults --> Monitor[Execution Monitor]
    
    Monitor --> ViewLogs[View Step-by-Step Logs]

    style Start fill:#00d4aa,color:#000
    style Done fill:#2ea043,color:#fff
    style DAG fill:#7c3aed,color:#fff
    style LLMCall fill:#3b82f6,color:#fff
```

---

## ER Diagram (Entity Relationship)

```mermaid
erDiagram
    TENANT {
        uuid id PK
        string name
        string slug UK
        timestamp created_at
    }

    USER {
        uuid id PK
        uuid tenant_id FK
        string email UK
        string hashed_password
        string full_name
        string role
        boolean is_active
        timestamp created_at
    }

    AGENT {
        uuid id PK
        uuid tenant_id FK
        uuid user_id FK
        string name
        text description
        string status
        json tags
        timestamp created_at
        timestamp updated_at
    }

    AGENT_NODE {
        uuid id PK
        uuid agent_id FK
        uuid parent_node_id FK
        string node_type
        string sub_type
        string label
        json config
        float position_x
        float position_y
        timestamp created_at
    }

    AGENT_EDGE {
        uuid id PK
        uuid agent_id FK
        uuid source_node_id FK
        uuid target_node_id FK
        string source_port
        string target_port
        string edge_type
        json config
        timestamp created_at
    }

    EXECUTION {
        uuid id PK
        uuid agent_id FK
        uuid tenant_id FK
        uuid user_id FK
        string status
        json input_data
        json output_data
        string error_message
        string celery_task_id
        float duration_seconds
        timestamp started_at
        timestamp completed_at
        timestamp created_at
    }

    EXECUTION_LOG {
        uuid id PK
        uuid execution_id FK
        string node_id
        string node_label
        string node_type
        string status 
        json input_data
        json output_data
        string error_message
        float duration_ms
        timestamp created_at
    }

    MEMORY_STORE {
        uuid id PK
        uuid agent_id FK
        string session_id
        string memory_type
        string role
        text content
        json metadata
        timestamp expires_at
        timestamp created_at
    }

    TENANT ||--o{ USER : "has"
    TENANT ||--o{ AGENT : "owns"
    USER ||--o{ AGENT : "creates"
    AGENT ||--o{ AGENT_NODE : "contains"
    AGENT ||--o{ AGENT_EDGE : "connects"
    AGENT ||--o{ EXECUTION : "runs"
    AGENT ||--o{ MEMORY_STORE : "remembers"
    AGENT_NODE ||--o| AGENT_NODE : "parent"
    EXECUTION ||--o{ EXECUTION_LOG : "logs"
    USER ||--o{ EXECUTION : "initiates"
```

---

## State Diagram (Agent Lifecycle)

```mermaid
stateDiagram-v2
    [*] --> Draft : Create Agent
    
    Draft --> Draft : Edit Workflow
    Draft --> Draft : Add/Remove Nodes
    Draft --> Draft : Configure Nodes
    Draft --> Active : Activate
    
    Active --> Active : Execute Workflow
    Active --> Draft : Edit
    Active --> Archived : Archive
    
    Archived --> Draft : Restore
    Archived --> [*] : Delete

    state Active {
        [*] --> Idle
        Idle --> Pending : Trigger Execution
        Pending --> Queued : Celery Dispatched
        Pending --> Running : Direct Execute
        Queued --> Running : Worker Picks Up
        Running --> Completed : All Nodes Pass
        Running --> Failed : Node Error
        Completed --> Idle
        Failed --> Idle
    }
```

---

## Sequence Diagram (Agent Execution Flow)

```mermaid
sequenceDiagram
    actor User
    participant UI as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant MQ as RabbitMQ
    participant Worker as Celery Worker
    participant Engine as Executor
    participant LLM as LLM Provider

    User->>UI: Click "Execute" on Canvas
    UI->>API: POST /api/agents/:id/execute
    API->>DB: Create Execution (status=pending)
    API->>MQ: Dispatch Celery Task
    API-->>UI: 202 Accepted (execution_id)

    MQ->>Worker: Pick up task
    Worker->>DB: Update status=running
    Worker->>DB: Load Agent + Nodes + Edges
    Worker->>Engine: Execute Workflow
    
    Engine->>Engine: Topological Sort Nodes

    loop For Each Node
        Engine->>Engine: Resolve sub-nodes (LLM, Memory, Tools)
        
        alt Agent Node
            Engine->>LLM: Send messages + tools
            LLM-->>Engine: Response (or tool_calls)
            
            opt Tool Calls
                Engine->>Engine: Execute Tool
                Engine->>LLM: Send tool results
                LLM-->>Engine: Final response
            end
        else Trigger Node
            Engine->>Engine: Pass through input
        else Condition Node
            Engine->>Engine: Evaluate condition
        else Output Node
            Engine->>Engine: Format output
        end
        
        Engine->>DB: Save ExecutionLog (per node)
    end

    Engine-->>Worker: Final output
    Worker->>DB: Update Execution (completed, output_data)

    User->>UI: Check Execution Monitor
    UI->>API: GET /api/executions/:id
    API->>DB: Load Execution + Logs
    API-->>UI: Execution details + step logs
    UI->>User: Display results
```

---

## Component Interaction Diagram

```mermaid
graph LR
    subgraph Browser["🌐 Browser"]
        SPA["SPA<br/>index.html"]
    end

    subgraph Server["🖥️ Server"]
        FastAPI["FastAPI<br/>:8000"]
        Celery["Celery Worker"]
    end

    subgraph Services["🔧 Services"]
        PG["PostgreSQL<br/>:5432"]
        RD["Redis<br/>:6379"]
        RMQ["RabbitMQ<br/>:5672"]
    end

    subgraph External["🌍 External APIs"]
        OAI["OpenAI API"]
        GEM["Gemini API"]
        GRQ["Groq API"]
        OR["OpenRouter API"]
        OLL["Ollama<br/>:11434"]
    end

    SPA -->|REST API| FastAPI
    FastAPI -->|SQLAlchemy| PG
    FastAPI -->|Dispatch Task| RMQ
    Celery -->|Consume Task| RMQ
    Celery -->|Store Result| RD
    Celery -->|Read/Write| PG
    Celery -->|API Call| OAI
    Celery -->|API Call| GEM
    Celery -->|API Call| GRQ
    Celery -->|API Call| OR
    Celery -->|API Call| OLL

    style Browser fill:#0d1117,stroke:#00d4aa,color:#e6edf3
    style Server fill:#0d1117,stroke:#7c3aed,color:#e6edf3
    style Services fill:#0d1117,stroke:#3b82f6,color:#e6edf3
    style External fill:#0d1117,stroke:#f97316,color:#e6edf3
```
