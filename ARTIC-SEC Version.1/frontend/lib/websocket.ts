type MessageHandler = (data: any) => void;
type StatusHandler = (connected: boolean) => void;

export class ArticWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private messageHandlers: Set<MessageHandler> = new Set();
  private statusHandlers: Set<StatusHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 20;
  private reconnectIntervalMs = 1500;
  private heartbeatTimer: any = null;
  private explicitClose = false;

  constructor(url?: string) {
    if (url) {
      this.url = url;
    } else if (typeof window !== "undefined") {
      const loc = window.location;
      const wsProto = loc.protocol === "https:" ? "wss:" : "ws:";
      const host = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
      this.url = host.startsWith("ws") ? host : `${wsProto}//${loc.host}/ws`;
    } else {
      this.url = "ws://localhost:8000/ws";
    }
  }

  public connect(): void {
    if (typeof window === "undefined") return;
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.explicitClose = false;
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.notifyStatus(true);
        this.startHeartbeat();
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const parsed = JSON.parse(event.data);
          this.messageHandlers.forEach((handler) => handler(parsed));
        } catch {
          this.messageHandlers.forEach((handler) => handler(event.data));
        }
      };

      this.ws.onerror = (err) => {
        console.warn("[WebSocket Error]", err);
      };

      this.ws.onclose = () => {
        this.stopHeartbeat();
        this.notifyStatus(false);
        if (!this.explicitClose) {
          this.scheduleReconnect();
        }
      };
    } catch (err) {
      console.warn("[WebSocket Connection Exception]", err);
      this.scheduleReconnect();
    }
  }

  public disconnect(): void {
    this.explicitClose = true;
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.notifyStatus(false);
  }

  public send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const payload = typeof data === "string" ? data : JSON.stringify(data);
      this.ws.send(payload);
    }
  }

  public onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  public onStatus(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler);
    return () => this.statusHandlers.delete(handler);
  }

  private notifyStatus(connected: boolean): void {
    this.statusHandlers.forEach((h) => h(connected));
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send("ping");
      }
    }, 20000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("[WebSocket] Max reconnect attempts reached");
      return;
    }
    this.reconnectAttempts++;
    const delay = Math.min(10000, this.reconnectIntervalMs * Math.pow(1.3, this.reconnectAttempts));
    setTimeout(() => {
      if (!this.explicitClose) {
        this.connect();
      }
    }, delay);
  }
}

export const defaultWebSocketClient = new ArticWebSocketClient();
