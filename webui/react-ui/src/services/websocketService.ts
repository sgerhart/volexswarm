/**
 * Enhanced WebSocket Service for Real-Time Communication
 * Replaces HTTP polling with WebSocket connections for live data updates
 */

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  id: string;
}

export interface ConnectionStatus {
  connected: boolean;
  reconnecting: boolean;
  lastConnected?: Date;
  connectionId?: string;
  error?: string;
}

export interface SubscriptionOptions {
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
}

type MessageHandler = (message: WebSocketMessage) => void;
type ConnectionHandler = (status: ConnectionStatus) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private subscriptions: Map<string, Set<MessageHandler>> = new Map();
  private connectionHandlers: Set<ConnectionHandler> = new Set();
  private connectionStatus: ConnectionStatus = { connected: false, reconnecting: false };
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 3000; // 3 seconds
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private heartbeatInterval = 30000; // 30 seconds
  private pendingMessages: any[] = [];
  private autoReconnect = true;

  constructor(url?: string, options?: SubscriptionOptions) {
    // Default to localhost:8004 for Meta Agent WebSocket endpoint
    this.url = url || `ws://${window.location.hostname}:8004/ws`;
    
    if (options) {
      this.autoReconnect = options.autoReconnect ?? true;
      this.maxReconnectAttempts = options.maxReconnectAttempts ?? 5;
      this.reconnectInterval = options.reconnectInterval ?? 3000;
    }
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.updateConnectionStatus({ connected: false, reconnecting: false });
        
        this.ws = new WebSocket(this.url);

        this.ws.onopen = (event) => {
          console.log('WebSocket connected to:', this.url);
          this.reconnectAttempts = 0;
          this.updateConnectionStatus({ 
            connected: true, 
            reconnecting: false, 
            lastConnected: new Date() 
          });
          
          // Start heartbeat
          this.startHeartbeat();
          
          // Send any pending messages
          this.sendPendingMessages();
          
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.cleanup();
          
          if (this.autoReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          } else {
            this.updateConnectionStatus({ 
              connected: false, 
              reconnecting: false,
              error: 'Connection lost'
            });
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.updateConnectionStatus({ 
            connected: false, 
            reconnecting: false,
            error: 'Connection error'
          });
          reject(error);
        };

      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.autoReconnect = false;
    this.cleanup();
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    
    this.updateConnectionStatus({ connected: false, reconnecting: false });
  }

  /**
   * Subscribe to a specific topic for real-time updates
   */
  subscribe(topic: string, handler: MessageHandler): () => void {
    // Add handler to subscriptions
    if (!this.subscriptions.has(topic)) {
      this.subscriptions.set(topic, new Set());
    }
    this.subscriptions.get(topic)!.add(handler);

    // Send subscription message to server
    this.sendMessage({
      type: 'subscribe',
      data: { topic }
    });

    console.log(`Subscribed to topic: ${topic}`);

    // Return unsubscribe function
    return () => this.unsubscribe(topic, handler);
  }

  /**
   * Unsubscribe from a topic
   */
  unsubscribe(topic: string, handler: MessageHandler): void {
    const handlers = this.subscriptions.get(topic);
    if (handlers) {
      handlers.delete(handler);
      
      // If no more handlers for this topic, unsubscribe from server
      if (handlers.size === 0) {
        this.subscriptions.delete(topic);
        this.sendMessage({
          type: 'unsubscribe',
          data: { topic }
        });
        console.log(`Unsubscribed from topic: ${topic}`);
      }
    }
  }

  /**
   * Send a command to the server
   */
  sendCommand(command: string): Promise<any> {
    return new Promise((resolve, reject) => {
      const messageId = this.generateId();
      
      // Create one-time handler for command response
      const responseHandler = (message: WebSocketMessage) => {
        if (message.type === 'command' && message.id === messageId) {
          this.removeMessageHandler('command', responseHandler);
          resolve(message.data);
        }
      };

      this.subscribe('command', responseHandler);

      // Send command
      this.sendMessage({
        type: 'command',
        data: { command },
        id: messageId
      });

      // Set timeout for command response
      setTimeout(() => {
        this.removeMessageHandler('command', responseHandler);
        reject(new Error('Command timeout'));
      }, 10000); // 10 second timeout
    });
  }

  /**
   * Get current connection status
   */
  getConnectionStatus(): ConnectionStatus {
    return { ...this.connectionStatus };
  }

  /**
   * Add connection status change handler
   */
  onConnectionChange(handler: ConnectionHandler): () => void {
    this.connectionHandlers.add(handler);
    
    // Send current status immediately
    handler(this.connectionStatus);
    
    // Return unsubscribe function
    return () => this.connectionHandlers.delete(handler);
  }

  /**
   * Get WebSocket connection statistics
   */
  async getConnectionStats(): Promise<any> {
    try {
      const response = await fetch(`http://${window.location.hostname}:8004/websocket/stats`);
      return await response.json();
    } catch (error) {
      console.error('Failed to get connection stats:', error);
      return null;
    }
  }

  // Private methods

  private sendMessage(message: any): void {
    const messageToSend = {
      ...message,
      timestamp: new Date().toISOString(),
      id: message.id || this.generateId()
    };

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(messageToSend));
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
        this.pendingMessages.push(messageToSend);
      }
    } else {
      // Queue message for when connection is restored
      this.pendingMessages.push(messageToSend);
    }
  }

  private sendPendingMessages(): void {
    if (this.pendingMessages.length > 0) {
      console.log(`Sending ${this.pendingMessages.length} pending messages`);
      this.pendingMessages.forEach(message => {
        this.sendMessage(message);
      });
      this.pendingMessages = [];
    }
  }

  private handleMessage(message: WebSocketMessage): void {
    // Handle special message types
    switch (message.type) {
      case 'ping':
        // Respond to ping with pong
        this.sendMessage({ type: 'pong', data: message.data });
        break;
        
      case 'notification':
        if (message.data.connection_id) {
          this.updateConnectionStatus({ 
            ...this.connectionStatus,
            connectionId: message.data.connection_id 
          });
        }
        break;
    }

    // Notify topic subscribers
    const handlers = this.subscriptions.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in message handler:', error);
        }
      });
    }
  }

  private removeMessageHandler(topic: string, handler: MessageHandler): void {
    const handlers = this.subscriptions.get(topic);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  private updateConnectionStatus(status: Partial<ConnectionStatus>): void {
    this.connectionStatus = { ...this.connectionStatus, ...status };
    
    // Notify all connection handlers
    this.connectionHandlers.forEach(handler => {
      try {
        handler(this.connectionStatus);
      } catch (error) {
        console.error('Error in connection handler:', error);
      }
    });
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;

    this.reconnectAttempts++;
    this.updateConnectionStatus({ connected: false, reconnecting: true });

    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${this.reconnectInterval}ms`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect().catch(error => {
        console.error('Reconnect failed:', error);
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        } else {
          this.updateConnectionStatus({ 
            connected: false, 
            reconnecting: false,
            error: 'Max reconnect attempts reached'
          });
        }
      });
    }, this.reconnectInterval);
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.sendMessage({
          type: 'ping',
          data: { timestamp: new Date().toISOString() }
        });
      }
    }, this.heartbeatInterval);
  }

  private cleanup(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private generateId(): string {
    return Math.random().toString(36).substr(2, 9);
  }
}

// Create singleton instance
export const webSocketService = new WebSocketService();

// Manual connection - no auto-connect
// webSocketService.connect().catch(error => {
//   console.warn('Initial WebSocket connection failed:', error);
// });

export default webSocketService; 