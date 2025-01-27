import { useState, useEffect } from "react";
import useProjects from "./useProjects";
import useAuthStore from "./useAuthStore";

export interface ChatMessage {
  id: string;
  type: "system" | "user" | "analyzer" | "advisor" | "planner";
  content: string;
  timestamp: Date;
  dataset?: {
    name: string;
    path: string;
    statistics?: {
      rows: number;
      columns: number;
      column_names: string[];
      missing_values: Record<string, number>;
    };
  };
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { activeProjectId } = useProjects();
  const { tokens } = useAuthStore();

  const fetchConversationHistory = async (projectId: string) => {
    try {
      const projectResponse = await fetch(
        `${import.meta.env.VITE_BASE_API_URL}projects/${projectId}`,
        {
          headers: {
            Authorization: `Bearer ${tokens?.access_token}`,
          },
        }
      );

      if (projectResponse.ok) {
        const projectData = await projectResponse.json();
        const dataset = projectData.dataset?.path ? projectData.dataset : null;

        try {
          const response = await fetch(
            `${
              import.meta.env.VITE_BASE_API_URL
            }workflow/${projectId}/conversation`,
            {
              headers: {
                Authorization: `Bearer ${tokens?.access_token}`,
              },
            }
          );

          const data = await response.json();

          if (response.ok && data.messages && data.messages.length > 0) {
            setMessages(
              data.messages.map((msg: any) => ({
                id: msg.id || Date.now().toString(),
                type: msg.type,
                content: msg.content,
                timestamp: new Date(msg.timestamp),
                dataset: msg.dataset?.path
                  ? msg.dataset
                  : msg.type === "analyzer" && dataset
                  ? {
                      name: dataset.name,
                      path: dataset.path,
                      statistics: dataset.statistics,
                    }
                  : undefined,
              }))
            );
            return true;
          } else if (dataset) {
            setMessages([
              {
                id: "1",
                type: "analyzer",
                content: "Welcome back! Your dataset is ready for analysis.",
                timestamp: new Date(),
                dataset: {
                  name: dataset.name,
                  path: dataset.path,
                  statistics: dataset.statistics,
                },
              },
            ]);
            return true;
          }
        } catch (error) {
          console.error("Error fetching conversation:", error);
          if (dataset) {
            setMessages([
              {
                id: "1",
                type: "analyzer",
                content: "Welcome back! Your dataset is ready for analysis.",
                timestamp: new Date(),
                dataset: {
                  name: dataset.name,
                  path: dataset.path,
                  statistics: dataset.statistics,
                },
              },
            ]);
            return true;
          }
        }
      }

      // If no valid dataset exists, show initial messages
      setMessages([
        {
          id: "1",
          type: "analyzer",
          content:
            "Hello! I am your data analysis assistant. I will help you analyze your data and provide insights.",
          timestamp: new Date(),
        },
        {
          id: "2",
          type: "analyzer",
          content:
            "To get started, please upload a CSV file containing your dataset.",
          timestamp: new Date(),
          dataset: {
            name: "",
            path: "",
          },
        },
      ]);
      return false;
    } catch (error) {
      console.error("Error fetching project data:", error);
      return false;
    }
  };

  useEffect(() => {
    if (!activeProjectId || !tokens?.access_token) {
      if (socket) {
        socket.close();
        setSocket(null);
      }
      setIsConnected(false);
      setIsLoading(false);
      return;
    }

    const initializeChat = async () => {
      setIsLoading(true);
      if (socket) {
        socket.close();
        setSocket(null);
      }

      const hasExistingConversation = await fetchConversationHistory(
        activeProjectId
      );

      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsHost =
        window.location.hostname === "localhost"
          ? "localhost:8000"
          : window.location.host;
      const ws = new WebSocket(
        `${wsProtocol}//${wsHost}/api/workflow/${activeProjectId}/ws?token=${encodeURIComponent(
          tokens.access_token
        )}`
      );

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setIsLoading(false);
        setIsConnected(false);
      };

      ws.onopen = () => {
        setIsConnected(true);
        if (!hasExistingConversation) {
          setMessages([
            {
              id: "1",
              type: "analyzer",
              content:
                "Hello! I am your data analysis assistant. I will help you analyze your data and provide insights.",
              timestamp: new Date(),
            },
            {
              id: "2",
              type: "analyzer",
              content:
                "To get started, please upload a CSV file containing your dataset.",
              timestamp: new Date(),
              dataset: {
                name: "",
                path: "",
              },
            },
          ]);
        }
        setIsLoading(false);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "message") {
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now().toString(),
              type: data.messageType,
              content: data.content,
              timestamp: new Date(),
              dataset: data.dataset,
            },
          ]);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        setIsLoading(false);
      };

      setSocket(ws);

      return () => {
        ws.close();
      };
    };

    initializeChat();

    // Cleanup function to close socket when component unmounts or project changes
    return () => {
      if (socket) {
        socket.close();
        setSocket(null);
        setIsConnected(false);
      }
    };
  }, [activeProjectId, tokens?.access_token]);

  const sendMessage = (content: string) => {
    if (socket && isConnected) {
      socket.send(
        JSON.stringify({
          type: "message",
          content,
        })
      );

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          type: "user",
          content,
          timestamp: new Date(),
        },
      ]);
    }
  };

  return { messages, sendMessage, isConnected, isLoading };
}
