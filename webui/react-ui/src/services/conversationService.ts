export interface ConversationResponse {
  message: string;
  conversation_id?: string;
  tasks?: Task[];
  structured_data?: any;
  requires_confirmation?: boolean;
  next_actions?: string[];
  executed_tasks?: Array<{
    task_id: string;
    status: string;
    result?: any;
    error?: string;
  }>;
}

export interface Task {
  id: string;
  type: string;
  description: string;
  agent: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  result?: any;
  error?: string;
}

export interface TaskExecutionRequest {
  action: string;
  parameters?: Record<string, any>;
}

export interface TaskExecutionResponse {
  task_id: string;
  status: string;
  result?: any;
  message: string;
}

class ConversationService {
  private baseUrl = 'http://localhost:8004';

  async processConversation(
    message: string,
    userId: string,
    conversationId?: string
  ): Promise<ConversationResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          user_id: userId,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error processing conversation:', error);
      throw error;
    }
  }

  async executeTask(
    conversationId: string,
    taskId: string,
    request: TaskExecutionRequest
  ): Promise<TaskExecutionResponse> {
    try {
      console.log('Executing task:', { conversationId, taskId, request });
      
      const response = await fetch(`${this.baseUrl}/conversation/${conversationId}/task/${taskId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          task_id: taskId,
          action: request.action,
          parameters: request.parameters || {}
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Task execution failed:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      const data = await response.json();
      console.log('Task execution result:', data);
      return data;
    } catch (error) {
      console.error('Error executing task:', error);
      throw error;
    }
  }

  async getConversation(conversationId: string): Promise<ConversationResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/conversation/${conversationId}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting conversation:', error);
      throw error;
    }
  }
}

export const conversationService = new ConversationService(); 