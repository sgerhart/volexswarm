import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Chip,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Card,
  CardContent,
  Alert,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  Fade,
  Zoom,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as AiIcon,
  Person as PersonIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  AttachFile as AttachFileIcon,
  Mic as MicIcon,
  Stop as StopIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AccountBalance as AccountBalanceIcon,
  Psychology as PsychologyIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { useWebSocketConnection } from '../hooks/useWebSocket';
import { conversationService } from '../services/conversationService';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  tasks?: Task[];
  structured_data?: any;
  requires_confirmation?: boolean;
  next_actions?: string[];
}

interface Task {
  id: string;
  type: string;
  description: string;
  agent: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  result?: any;
  error?: string;
}

interface ChatInterfaceProps {
  onClose?: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [userId] = useState('default_user');
  const [showTaskDialog, setShowTaskDialog] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // WebSocket connection for real-time updates
  const { isConnected } = useWebSocketConnection();

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Debug dialog state changes
  useEffect(() => {
    console.log('Dialog state changed:', { showTaskDialog, selectedTask });
  }, [showTaskDialog, selectedTask]);

  // Initialize conversation
  useEffect(() => {
    const initConversation = async () => {
      try {
        const response = await conversationService.processConversation(
          "Hello! I'm ready to help you with your trading. What would you like to do today?",
          userId
        );
        
        if (response.conversation_id) {
          setConversationId(response.conversation_id);
        }
        
        // Add welcome message
        setMessages([{
          id: 'welcome',
          role: 'assistant',
          content: "Hello! I'm your AI trading assistant. I can help you with:\n\n" +
                   "• Researching markets and analyzing tokens\n" +
                   "• Executing trades with your budget\n" +
                   "• Monitoring your portfolio\n" +
                   "• Optimizing strategies\n\n" +
                   "Just tell me what you'd like to do! For example:\n" +
                   "• \"I have $200 in Binance. Research the best tokens to buy\"\n" +
                   "• \"Analyze BTC/USDT and execute a trade if conditions are good\"\n" +
                   "• \"Show me my current portfolio status\"",
          timestamp: new Date().toISOString(),
          tasks: [],
          structured_data: null,
          requires_confirmation: false,
          next_actions: []
        }]);
      } catch (error) {
        console.error('Failed to initialize conversation:', error);
        setMessages([{
          id: 'error',
          role: 'assistant',
          content: "I'm having trouble connecting right now. Please try again in a moment.",
          timestamp: new Date().toISOString(),
          tasks: [],
          structured_data: null,
          requires_confirmation: false,
          next_actions: []
        }]);
      }
    };

    initConversation();
  }, [userId]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      const response = await conversationService.processConversation(
        inputMessage,
        userId,
        conversationId || undefined
      );

      if (response.conversation_id && !conversationId) {
        setConversationId(response.conversation_id);
      }

      // Use the structured data from the response directly
      const structuredData = response.structured_data;

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date().toISOString(),
        tasks: response.tasks,
        structured_data: structuredData,
        requires_confirmation: response.requires_confirmation,
        next_actions: response.next_actions,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I'm sorry, I encountered an error processing your request. Please try again.",
        timestamp: new Date().toISOString(),
        tasks: [],
        structured_data: null,
        requires_confirmation: false,
        next_actions: []
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handleTaskAction = async (taskId: string, action: string) => {
    if (!conversationId) return;

    try {
      const response = await conversationService.executeTask(conversationId!, taskId, {
        action,
        parameters: {}
      });

      // Update the task status in messages
      setMessages(prev => prev.map(msg => {
        if (msg.tasks) {
          const updatedTasks = msg.tasks.map(task => 
            task.id === taskId 
              ? { ...task, status: response.status as 'pending' | 'in_progress' | 'completed' | 'failed', result: response.result }
              : task
          );
          return { ...msg, tasks: updatedTasks };
        }
        return msg;
      }));

      setShowTaskDialog(false);
      setSelectedTask(null);
    } catch (error) {
      console.error('Failed to execute task:', error);
    }
  };

  const renderStructuredData = (data: any) => {
    if (!data) return null;

    if (data.type === 'portfolio_summary') {
      return (
        <Card variant="outlined" sx={{ mt: 2, backgroundColor: 'rgba(0, 212, 170, 0.1)' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Portfolio Summary
            </Typography>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Total Value
                </Typography>
                <Typography variant="h5" color="primary">
                  ${data.total_value?.toFixed(2) || '0.00'}
                </Typography>
              </Box>
              <Box textAlign="right">
                <Typography variant="body2" color="text.secondary">
                  24h Change
                </Typography>
                <Typography 
                  variant="h6" 
                  color={data.daily_change >= 0 ? 'success.main' : 'error.main'}
                >
                  {data.daily_change >= 0 ? '+' : ''}{data.daily_change?.toFixed(2) || '0.00'}%
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      );
    }

    if (data.type === 'market_data') {
      return (
        <Card variant="outlined" sx={{ mt: 2, backgroundColor: 'rgba(0, 212, 170, 0.1)' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📊 Live Market Data
            </Typography>
            {data.results && data.results.map((result: any, index: number) => (
              <Box key={index} sx={{ mb: 2, p: 2, border: '1px solid rgba(0, 212, 170, 0.3)', borderRadius: 1 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="h5" fontWeight="bold">
                    {result.symbol}
                  </Typography>
                  <Typography variant="h4" color="primary" fontWeight="bold">
                    ${result.price?.toLocaleString() || 'N/A'}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Bid: ${result.bid?.toLocaleString() || 'N/A'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Ask: ${result.ask?.toLocaleString() || 'N/A'}
                    </Typography>
                  </Box>
                  <Box textAlign="right">
                    <Typography variant="body2" color="text.secondary">
                      Volume: {result.volume?.toLocaleString() || 'N/A'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Exchange: {result.exchange}
                    </Typography>
                  </Box>
                </Box>
                <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                  Last updated: {new Date(result.timestamp).toLocaleTimeString()}
                </Typography>
              </Box>
            ))}
          </CardContent>
        </Card>
      );
    }

    if (data.type === 'research_recommendations') {
      return (
        <Card variant="outlined" sx={{ mt: 2, backgroundColor: 'rgba(76, 175, 80, 0.1)' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              🔍 Investment Research & Recommendations
            </Typography>
            {data.results && data.results.map((result: any, index: number) => (
              <Box key={index} sx={{ mb: 3 }}>
                {result.recommendations && (
                  <>
                    {/* Top Picks */}
                    {result.recommendations.top_picks && result.recommendations.top_picks.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="h6" color="success.main" gutterBottom>
                          🏆 Top Investment Picks
                        </Typography>
                        {result.recommendations.top_picks.map((pick: any, pickIndex: number) => (
                          <Box key={pickIndex} sx={{ mb: 1, p: 1, border: '1px solid rgba(76, 175, 80, 0.3)', borderRadius: 1 }}>
                            <Box display="flex" justifyContent="space-between" alignItems="center">
                              <Typography variant="h6" fontWeight="bold">
                                {pick.symbol}
                              </Typography>
                              <Typography variant="h5" color="success.main" fontWeight="bold">
                                ${pick.price?.toLocaleString() || 'N/A'}
                              </Typography>
                            </Box>
                            <Box display="flex" justifyContent="space-between" alignItems="center">
                              <Typography variant="body2" color="text.secondary">
                                24h Change: {pick.price_change >= 0 ? '+' : ''}{pick.price_change?.toFixed(2) || 'N/A'}%
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                Volume: {pick.volume?.toLocaleString() || 'N/A'}
                              </Typography>
                            </Box>
                            <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
                              {pick.reason}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    )}

                    {/* High Potential */}
                    {result.recommendations.high_potential && result.recommendations.high_potential.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="h6" color="warning.main" gutterBottom>
                          🚀 High Growth Potential
                        </Typography>
                        {result.recommendations.high_potential.map((pick: any, pickIndex: number) => (
                          <Box key={pickIndex} sx={{ mb: 1, p: 1, border: '1px solid rgba(255, 152, 0, 0.3)', borderRadius: 1 }}>
                            <Box display="flex" justifyContent="space-between" alignItems="center">
                              <Typography variant="h6" fontWeight="bold">
                                {pick.symbol}
                              </Typography>
                              <Typography variant="h5" color="warning.main" fontWeight="bold">
                                ${pick.price?.toLocaleString() || 'N/A'}
                              </Typography>
                            </Box>
                            <Box display="flex" justifyContent="space-between" alignItems="center">
                              <Typography variant="body2" color="text.secondary">
                                24h Change: {pick.price_change >= 0 ? '+' : ''}{pick.price_change?.toFixed(2) || 'N/A'}%
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                Volume: {pick.volume?.toLocaleString() || 'N/A'}
                              </Typography>
                            </Box>
                            <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
                              {pick.reason}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    )}

                    {/* Summary */}
                    {result.recommendations.summary && (
                      <Box sx={{ mt: 2, p: 2, backgroundColor: 'rgba(76, 175, 80, 0.1)', borderRadius: 1 }}>
                        <Typography variant="body1" fontWeight="bold">
                          📋 Investment Summary
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          {result.recommendations.summary}
                        </Typography>
                      </Box>
                    )}
                  </>
                )}
              </Box>
            ))}
          </CardContent>
        </Card>
      );
    }

    if (data.type === 'trade_recommendation') {
      return (
        <Card variant="outlined" sx={{ mt: 2, backgroundColor: 'rgba(255, 107, 53, 0.1)' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Trade Recommendation
            </Typography>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Symbol
                </Typography>
                <Typography variant="h5">
                  {data.symbol}
                </Typography>
              </Box>
              <Box textAlign="center">
                <Typography variant="body2" color="text.secondary">
                  Action
                </Typography>
                <Chip 
                  label={data.action?.toUpperCase()} 
                  color={data.action === 'buy' ? 'success' : 'error'}
                  variant="filled"
                />
              </Box>
              <Box textAlign="right">
                <Typography variant="body2" color="text.secondary">
                  Confidence
                </Typography>
                <Typography variant="h6" color="primary">
                  {(data.confidence * 100).toFixed(1)}%
                </Typography>
              </Box>
            </Box>
            {data.reason && (
              <Typography variant="body2" sx={{ mt: 2 }}>
                <strong>Reason:</strong> {data.reason}
              </Typography>
            )}
          </CardContent>
        </Card>
      );
    }

    return null;
  };

  const renderTaskChip = (task: Task) => {
    const getStatusColor = (status: string) => {
      switch (status) {
        case 'completed': return 'success';
        case 'in_progress': return 'warning';
        case 'failed': return 'error';
        default: return 'default';
      }
    };

    const getStatusIcon = (status: string) => {
      switch (status) {
        case 'completed': return <CheckCircleIcon />;
        case 'in_progress': return <CircularProgress size={16} />;
        case 'failed': return <ErrorIcon />;
        default: return <InfoIcon />;
      }
    };

    return (
      <Chip
        key={task.id}
        label={task.description}
        color={getStatusColor(task.status)}
        icon={getStatusIcon(task.status)}
        onClick={() => {
          console.log('Task clicked:', task);
          setSelectedTask(task);
          setShowTaskDialog(true);
        }}
        sx={{ m: 0.5 }}
        variant="outlined"
      />
    );
  };

  const renderNextActions = (actions: string[]) => {
    if (!actions || actions.length === 0) return null;

    return (
      <Box sx={{ mt: 2 }}>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Suggested next actions:
        </Typography>
        <Box display="flex" flexWrap="wrap" gap={1}>
          {actions.map((action, index) => (
            <Chip
              key={index}
              label={action}
              variant="outlined"
              size="small"
              onClick={() => setInputMessage(action)}
              sx={{ cursor: 'pointer' }}
            />
          ))}
        </Box>
      </Box>
    );
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper 
        elevation={2} 
        sx={{ 
          p: 2, 
          backgroundColor: 'background.paper',
          borderBottom: 1,
          borderColor: 'divider'
        }}
      >
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={2}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              <AiIcon />
            </Avatar>
            <Box>
              <Typography variant="h6">
                AI Trading Assistant
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {isConnected ? 'Connected' : 'Connecting...'}
              </Typography>
            </Box>
          </Box>
          <Box display="flex" gap={1}>
            <Tooltip title="Refresh">
              <IconButton size="small">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Settings">
              <IconButton size="small">
                <SettingsIcon />
              </IconButton>
            </Tooltip>
            {onClose && (
              <Tooltip title="Close">
                <IconButton size="small" onClick={onClose}>
                  <CloseIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>
      </Paper>

      {/* Messages */}
      <Box 
        sx={{ 
          flex: 1, 
          overflow: 'auto', 
          p: 2,
          backgroundColor: 'background.default'
        }}
      >
        <List sx={{ p: 0 }}>
          {messages.map((message) => (
            <ListItem
              key={message.id}
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: message.role === 'user' ? 'flex-end' : 'flex-start',
                p: 0,
                mb: 2,
              }}
            >
              <Box
                sx={{
                  maxWidth: '70%',
                  minWidth: '200px',
                }}
              >
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <Avatar 
                    sx={{ 
                      width: 32, 
                      height: 32,
                      bgcolor: message.role === 'user' ? 'secondary.main' : 'primary.main'
                    }}
                  >
                    {message.role === 'user' ? <PersonIcon /> : <AiIcon />}
                  </Avatar>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </Typography>
                </Box>
                
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    backgroundColor: message.role === 'user' 
                      ? 'primary.main' 
                      : 'background.paper',
                    color: message.role === 'user' 
                      ? 'primary.contrastText' 
                      : 'text.primary',
                    borderRadius: 2,
                    borderTopLeftRadius: message.role === 'user' ? 2 : 0,
                    borderTopRightRadius: message.role === 'user' ? 0 : 2,
                  }}
                >
                  <Typography 
                    variant="body1" 
                    sx={{ 
                      whiteSpace: 'pre-wrap',
                      lineHeight: 1.6
                    }}
                  >
                    {message.content}
                  </Typography>

                  {/* Render structured data */}
                  {message.structured_data && renderStructuredData(message.structured_data)}

                  {/* Render task chips */}
                  {message.tasks && message.tasks.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Tasks:
                      </Typography>
                      <Box display="flex" flexWrap="wrap" gap={1}>
                        {message.tasks.map(renderTaskChip)}
                      </Box>
                    </Box>
                  )}

                  {/* Render next actions */}
                  {message.next_actions && renderNextActions(message.next_actions)}

                  {/* Confirmation required */}
                  {message.requires_confirmation && (
                    <Alert severity="info" sx={{ mt: 2 }}>
                      This action requires your confirmation. Please review the details above.
                    </Alert>
                  )}
                </Paper>
              </Box>
            </ListItem>
          ))}
          
          {/* Typing indicator */}
          {isTyping && (
            <ListItem sx={{ display: 'flex', justifyContent: 'flex-start', p: 0, mb: 2 }}>
              <Box sx={{ maxWidth: '70%', minWidth: '200px' }}>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                    <AiIcon />
                  </Avatar>
                  <Typography variant="caption" color="text.secondary">
                    AI is typing...
                  </Typography>
                </Box>
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    backgroundColor: 'background.paper',
                    borderRadius: 2,
                    borderTopLeftRadius: 0,
                  }}
                >
                  <Box display="flex" alignItems="center" gap={1}>
                    <CircularProgress size={16} />
                    <Typography variant="body2" color="text.secondary">
                      Processing your request...
                    </Typography>
                  </Box>
                </Paper>
              </Box>
            </ListItem>
          )}
        </List>
        <div ref={messagesEndRef} />
      </Box>

      {/* Input area */}
      <Paper 
        elevation={2} 
        sx={{ 
          p: 2, 
          backgroundColor: 'background.paper',
          borderTop: 1,
          borderColor: 'divider'
        }}
      >
        <Box display="flex" alignItems="flex-end" gap={1}>
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={4}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
            variant="outlined"
            disabled={isTyping}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
              }
            }}
          />
          <Box display="flex" flexDirection="column" gap={1}>
            <Tooltip title="Voice input">
              <IconButton 
                color={isRecording ? 'error' : 'default'}
                onClick={() => setIsRecording(!isRecording)}
                disabled={isTyping}
              >
                {isRecording ? <StopIcon /> : <MicIcon />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Attach file">
              <IconButton disabled={isTyping}>
                <AttachFileIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Send message">
              <IconButton 
                color="primary"
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isTyping}
              >
                <SendIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Paper>

      {/* Task execution dialog */}
      <Dialog 
        open={showTaskDialog} 
        onClose={() => {
          console.log('Dialog closing');
          setShowTaskDialog(false);
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Task Details: {selectedTask?.description}
        </DialogTitle>
        <DialogContent>
          {selectedTask && (
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Type: {selectedTask.type}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Agent: {selectedTask.agent}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Status: {selectedTask.status}
              </Typography>
              {selectedTask.error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  Error: {selectedTask.error}
                </Alert>
              )}
              {selectedTask.result && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Result:
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <pre style={{ margin: 0, fontSize: '12px' }}>
                      {JSON.stringify(selectedTask.result, null, 2)}
                    </pre>
                  </Paper>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowTaskDialog(false)}>
            Close
          </Button>
          {selectedTask?.status === 'pending' && (
            <Button 
              onClick={() => handleTaskAction(selectedTask.id, 'execute')}
              variant="contained"
            >
              Execute Task
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ChatInterface; 