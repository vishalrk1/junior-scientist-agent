import {
    User,
    Project,
    Agent,
    Conversation,
    Report,
    MessageType,
    AgentType,
    AgentStatus,
    ReportType,
    ReportStatus,
    ModelProviders,
    ProjectStatus,
    ProjectAgentConfig,
    Message,
  } from "./types";
  
  export const dummyUsers: User[] = [
    {
      id: "usr_123456789",
      name: "Vishal Karangale",
      email: "karangalevr@gmail.com",
      created_at: "2024-01-15T08:00:00Z",
      updated_at: "2024-02-20T15:30:00Z",
      last_login: "2024-02-20T15:30:00Z",
    },
    {
      id: "usr_987654321",
      name: "Jane Smith",
      email: "jane.smith@example.com",
      created_at: "2024-02-01T10:00:00Z",
      updated_at: "2024-02-21T09:15:00Z",
      last_login: "2024-02-21T09:15:00Z",
    }
  ];
  
  export const dummyAgentConfigs: ProjectAgentConfig[] = [
    {
      agent_type: AgentType.Analyzer,
      parameters: {
        temperature: 0.7,
        max_tokens: 2000,
      },
      additional_prompt: "Focus on statistical analysis",
    },
    {
      agent_type: AgentType.Advisor,
      parameters: {
        temperature: 0.6,
        max_tokens: 1500,
      },
    },
  ];
  
  export const dummyProjects: Project[] = [
    {
      id: "9hsdncoisndcisdnocnsdco",
      user_id: dummyUsers[0].id,
      name: "Climate Change Analysis",
      description: "Analyzing global temperature changes over the past century",
      model_provider: ModelProviders.OpenAI,
      status: ProjectStatus.Active,
      created_at: "2024-02-01T10:00:00Z",
      updated_at: "2024-02-20T15:30:00Z",
      last_activity: "2024-02-20T15:30:00Z",
      default_agent_configs: dummyAgentConfigs,
      conversation_ids: ["conv_123", "conv_124"],
      report_ids: ["rep_123", "rep_124"],
      current_conversation_id: "conv_124",
      dataset: {
        path: "/data/climate_data.csv",
        description: "Global temperature records 1920-2020",
        schema: {
          year: "integer",
          temperature: "float",
          location: "string",
        },
        statistics: {
          rows: 1000,
          columns: 3,
        },
      },
      settings: {
        context_size: 10,
        max_reports_per_agent: 5,
        auto_save_interval: 300,
      },
    },
    {
      id: "8jsdn29sjd92jsd92js9d2",
      user_id: dummyUsers[0].id,
      name: "Marine Biology Study",
      description: "Research on coral reef ecosystems and their response to temperature changes in the Pacific Ocean",
      model_provider: ModelProviders.OpenAI,
      status: ProjectStatus.Active,
      created_at: "2024-02-15T09:00:00Z",
      updated_at: "2024-02-21T14:20:00Z",
      last_activity: "2024-02-21T14:20:00Z",
      default_agent_configs: dummyAgentConfigs,
      conversation_ids: ["conv_125", "conv_126"],
      report_ids: ["rep_125", "rep_126"],
      current_conversation_id: "conv_126",
      dataset: {
        path: "/data/marine_data.csv",
        description: "Pacific Ocean coral reef data 2010-2024",
        schema: {
          date: "date",
          temperature: "float",
          coral_health: "integer",
          location: "string"
        },
        statistics: {
          rows: 1500,
          columns: 4,
        },
      },
      settings: {
        context_size: 10,
        max_reports_per_agent: 5,
        auto_save_interval: 300,
      },
    },
  ];
  
  export const dummyAgents: Agent[] = [
    {
      id: "agent_123",
      project_id: "dummyProject.id",
      version: "1.0.0",
      type: AgentType.Analyzer,
      status: AgentStatus.Active,
      parameters: {
        temperature: 0.7,
        max_tokens: 2000,
      },
      is_default: true,
      context_size: 10,
      last_conversation_id: "conv_124",
      last_reports: ["rep_123"],
    },
    {
      id: "agent_124",
      project_id: "dummyProject.id",
      version: "1.0.0",
      type: AgentType.Advisor,
      status: AgentStatus.Active,
      parameters: {
        temperature: 0.6,
        max_tokens: 1500,
      },
      is_default: true,
      context_size: 10,
      last_reports: [],
    },
  ];
  
  export const dummyMessages: Message[] = [
    {
      type: MessageType.User,
      content: "Can you analyze the temperature trends in this dataset?",
      timestamp: "2024-02-20T15:25:00Z",
      metadata: {},
    },
    {
      type: MessageType.Analyzer,
      content: "I'll analyze the temperature trends. Let me prepare a report.",
      timestamp: "2024-02-20T15:26:00Z",
      metadata: {},
      agent_id: "agent_123",
    },
  ];
  
  export const dummyConversation: Conversation = {
    id: "conv_124",
    project_id: "dummyProject.id",
    messages: dummyMessages,
    active_agents: ["agent_123", "agent_124"],
    context_size: 10,
    created_at: "2024-02-20T15:25:00Z",
    updated_at: "2024-02-20T15:26:00Z",
  };
  
  export const dummyReports: Report[] = [
    {
      id: "rep_123",
      project_id: "dummyProject.id",
      type: ReportType.DataAnalysis,
      name: "Temperature Trend Analysis",
      description: "Analysis of global temperature changes from 1920-2020",
      status: ReportStatus.Completed,
      data: {
        trend: "upward",
        average_increase: "1.5°C",
        confidence: 0.95,
      },
      metadata: {
        analysis_duration: "2m 30s",
        data_points: 1000,
      },
      generated_by: MessageType.Analyzer,
      conversation_id: "conv_124",
      created_at: "2024-02-20T15:27:00Z",
      updated_at: "2024-02-20T15:29:00Z",
    },
  ];
  