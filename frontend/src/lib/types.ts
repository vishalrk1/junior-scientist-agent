export interface Tokens {
    access_token: string;
    refresh_token?: string | null;
    expires_in: number;
}

export interface User {
    id: string;
    name: string | null;
    email: string;
    created_at: string;
    updated_at: string | null;
    last_login: string | null;
}

export enum MessageType {
    User = 'user',
    Analyzer = 'analyzer',
    Advisor = 'advisor',
    Planner = 'planner',
    Coder = 'coder'
}

export enum AgentType {
    Analyzer = 'analyzer',
    Advisor = 'advisor',
    Planner = 'planner',
    Coder = 'coder'
}

export enum AgentStatus {
    Active = 'active',
    Inactive = 'inactive'
}

export enum ReportType {
    DataAnalysis = 'data_analysis',
    ModelEvaluation = 'model_evaluation',
    FeatureImportance = 'feature_importance',
    PerformanceMetrics = 'performance_metrics',
    CodeSnippet = 'code_snippet',
    Visualization = 'visualization',
    Recommendation = 'recommendation'
}

export enum ReportStatus {
    Pending = 'pending',
    Processing = 'processing',
    Completed = 'completed',
    Failed = 'failed'
}

export enum ModelProviders {
    OpenAI = 'openai',
    Gemini = 'gemini'
}

export enum ProjectStatus {
    active = 'active',
    archived = 'archived',
    deleted = 'deleted'
}

export interface Message {
    type: MessageType;
    content: string;
    timestamp: string;
    metadata: Record<string, any>;
    report_id?: string;
    agent_id?: string;
}

export interface Conversation {
    id: string;
    project_id: string;
    messages: Message[];
    active_agents: string[];
    context_size: number;
    created_at: string;
    updated_at: string;
}

export interface ParameterSchema {
    temperature: number;
    max_tokens: number;
}

export interface Agent {
    id: string;
    project_id: string;
    version: string;
    type: AgentType;
    status: AgentStatus;
    parameters: ParameterSchema;
    additional_prompt?: string;
    is_default: boolean;
    context_size: number;
    last_conversation_id?: string;
    last_reports: string[];
}

export interface DatasetSchema {
    path: string;
    description?: string;
    schema: Record<string, any>;
    statistics: Record<string, any>;
}

export interface ProjectAgentConfig {
    agent_type: AgentType;
    parameters: ParameterSchema;
    additional_prompt?: string;
}

export interface Project {
    id: string;
    name: string;
    description: string;
    model_provider: string;
    api_key: string;
    created_at: string;
    updated_at: string;
    last_activity: string;
    status: ProjectStatus;
    conversation_ids: string[];
    report_ids: string[];
    current_conversation_id: string | null;
    settings: {
        context_size: number;
        max_reports_per_agent: number;
        auto_save_interval: number;
    };
}

export interface Report {
    id: string;
    project_id: string;
    type: ReportType;
    name: string;
    description?: string;
    status: ReportStatus;
    data: Record<string, any>;
    file_path?: string;
    metadata: Record<string, any>;
    generated_by: MessageType;
    conversation_id?: string;
    created_at: string;
    updated_at: string;
}
