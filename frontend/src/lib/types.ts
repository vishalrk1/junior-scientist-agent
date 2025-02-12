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
  User = "user",
  Analyzer = "analyzer",
  Advisor = "advisor",
  Planner = "planner",
  Coder = "coder",
}

export enum AgentType {
  Analyzer = "analyzer",
  Advisor = "advisor",
  Planner = "planner",
  Coder = "coder",
}

export enum AgentStatus {
  Active = "active",
  Inactive = "inactive",
}

export enum ReportType {
  DataAnalysis = "data_analysis",
  ModelEvaluation = "model_evaluation",
  FeatureImportance = "feature_importance",
  PerformanceMetrics = "performance_metrics",
  CodeSnippet = "code_snippet",
  Visualization = "visualization",
  Recommendation = "recommendation",
}

export enum ReportStatus {
  Pending = "pending",
  Processing = "processing",
  Completed = "completed",
  Failed = "failed",
}

export enum ModelProviders {
  OpenAI = "openai",
  Gemini = "gemini",
}

export enum ProjectStatus {
  active = "active",
  archived = "archived",
  deleted = "deleted",
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

export interface ModelConfig {
  name: string;
  displayName: string;
  contextLimit: number;
  isDefault: boolean;
}

export interface ProviderModels {
  [key: string]: ModelConfig[];
}

export const DefaultModels: ProviderModels = {
  openai: [
    {
      name: "gpt-4o",
      displayName: "GPT-4 Optimized",
      contextLimit: 8192,
      isDefault: true,
    },
    {
      name: "gpt-4",
      displayName: "GPT-4",
      contextLimit: 8192,
      isDefault: false,
    },
    {
      name: "gpt-3.5-turbo",
      displayName: "GPT-3.5 Turbo",
      contextLimit: 4096,
      isDefault: false,
    },
  ],
  gemini: [
    {
      name: "gemini-pro",
      displayName: "Gemini Pro",
      contextLimit: 32768,
      isDefault: true,
    },
    {
      name: "gemini-pro-vision",
      displayName: "Gemini Pro Vision",
      contextLimit: 16384,
      isDefault: false,
    },
  ],
};

export const getDefaultModelForProvider = (provider: string): string => {
  const models = DefaultModels[provider];
  if (!models) return "gpt-4o";
  const defaultModel = models.find((m) => m.isDefault);
  return defaultModel ? defaultModel.name : models[0].name;
};

export interface ProjectSettings {
  context_size: number;
  max_reports_per_agent: number;
  auto_save_interval: number;
  selected_model: string;
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
  settings: ProjectSettings;
  available_models: string[];
}

export const AVAILABLE_MODELS = {
  openai: ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
  gemini: ["gemini-pro", "gemini-pro-vision"],
} as const;

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

// Rag Types
export interface RagSettingConfig {
  use_semantic: boolean;
  use_keyword: boolean;
  use_knowledge_graph: boolean;
  semantic_weight: number;
  keyword_weight: number;
  knowledge_graph_weight: number;
  temperature: number;
  max_token: number;
}

export interface Source {
  title: string;
  similarity: string;
}

export interface Chat {
  question: string;
  answer: string;
  sources: Source[];
  timestamp: string;
}

export interface ChatMessage {
  role: 'ai' | 'user';
  content: string;
  source?: Source[]
}

export interface RagSession {
  id: string;
  user_id: string;
  title: string;
  api_key: string | null;
  messages: ChatMessage[];
  description: string | null;
  documents: string[];
  created_at: string;
  updated_at: string;
  settings: RagSettingConfig;
}
