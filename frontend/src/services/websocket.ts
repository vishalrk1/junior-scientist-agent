export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private readonly MAX_RECONNECT_ATTEMPTS = 5;
  private messageHandlers: ((data: any) => void)[] = [];

  constructor(private sessionId: string) {}

  connect() {
    const token = localStorage.getItem("auth-token");
    this.ws = new WebSocket(
      `${import.meta.env.VITE_BASE_API_URL}ws/${this.sessionId}/chat?token=${token}`
    );

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data);  // Debug log
      this.messageHandlers.forEach((handler) => handler(data));
    };

    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.MAX_RECONNECT_ATTEMPTS) {
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect();
        }, 1000 * Math.pow(2, this.reconnectAttempts));
      }
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000);
  }

  sendMessage(message: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ message }));
    }
  }

  addMessageHandler(handler: (data: any) => void) {
    this.messageHandlers.push(handler);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
