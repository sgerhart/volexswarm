import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import {
  PortfolioData,
  AgentIntelligence,
  TradingSignal,
  ProductionStrategy,
  UIState,
  Notification,
  AgentTask,
  AgentWorkflow,
  MarketData
} from '../types';

interface AppState {
  // Portfolio and Investment Data
  portfolio: PortfolioData | null;
  marketData: MarketData[];
  
  // Agent Intelligence
  agents: AgentIntelligence[];
  selectedAgent: string | null;
  
  // Trading Intelligence
  tradingSignals: TradingSignal[];
  activeStrategies: ProductionStrategy[];
  
  // Agent Tasks and Workflows
  tasks: AgentTask[];
  workflows: AgentWorkflow[];
  
  // UI State
  ui: UIState;
  notifications: Notification[];
  
  // Actions
  setPortfolio: (portfolio: PortfolioData) => void;
  updateMarketData: (data: MarketData[]) => void;
  setAgents: (agents: AgentIntelligence[]) => void;
  selectAgent: (agentName: string | null) => void;
  addTradingSignal: (signal: TradingSignal) => void;
  updateTradingSignals: (signals: TradingSignal[]) => void;
  setActiveStrategies: (strategies: ProductionStrategy[]) => void;
  addTask: (task: AgentTask) => void;
  updateTask: (taskId: string, updates: Partial<AgentTask>) => void;
  addWorkflow: (workflow: AgentWorkflow) => void;
  updateWorkflow: (workflowId: string, updates: Partial<AgentWorkflow>) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  toggleSidebar: () => void;
  setSelectedTimeframe: (timeframe: string) => void;
  setSelectedSymbol: (symbol: string) => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  markNotificationRead: (id: string) => void;
  clearNotifications: () => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial State
        portfolio: null,
        marketData: [],
        agents: [],
        selectedAgent: null,
        tradingSignals: [],
        activeStrategies: [],
        tasks: [],
        workflows: [],
        ui: {
          theme: 'dark',
          sidebarOpen: true,
          selectedTimeframe: '1D',
          selectedSymbol: 'BTCUSDT',
          notifications: []
        },
        notifications: [],

        // Actions
        setPortfolio: (portfolio) => {
          console.log('🏪 Store: setPortfolio called with:', portfolio);
          set({ portfolio });
        },
        
        updateMarketData: (data) => set({ marketData: data }),
        
        setAgents: (agents) => set({ agents }),
        
        selectAgent: (agentName) => set({ selectedAgent: agentName }),
        
        addTradingSignal: (signal) => set((state) => ({
          tradingSignals: [signal, ...state.tradingSignals].slice(0, 100) // Keep last 100
        })),
        
        updateTradingSignals: (signals) => set({ tradingSignals: signals }),
        
        setActiveStrategies: (strategies) => set({ activeStrategies: strategies }),
        
        addTask: (task) => set((state) => ({
          tasks: [...state.tasks, task]
        })),
        
        updateTask: (taskId, updates) => set((state) => ({
          tasks: state.tasks.map(task =>
            task.id === taskId ? { ...task, ...updates } : task
          )
        })),
        
        addWorkflow: (workflow) => set((state) => ({
          workflows: [...state.workflows, workflow]
        })),
        
        updateWorkflow: (workflowId, updates) => set((state) => ({
          workflows: state.workflows.map(workflow =>
            workflow.id === workflowId ? { ...workflow, ...updates } : workflow
          )
        })),
        
        setTheme: (theme) => set((state) => ({
          ui: { ...state.ui, theme }
        })),
        
        toggleSidebar: () => set((state) => ({
          ui: { ...state.ui, sidebarOpen: !state.ui.sidebarOpen }
        })),
        
        setSelectedTimeframe: (timeframe) => set((state) => ({
          ui: { ...state.ui, selectedTimeframe: timeframe }
        })),
        
        setSelectedSymbol: (symbol) => set((state) => ({
          ui: { ...state.ui, selectedSymbol: symbol }
        })),
        
        addNotification: (notification) => {
          const newNotification: Notification = {
            ...notification,
            id: Date.now().toString(),
            timestamp: new Date().toISOString()
          };
          set((state) => ({
            notifications: [newNotification, ...state.notifications]
          }));
        },
        
        markNotificationRead: (id) => set((state) => ({
          notifications: state.notifications.map(notif =>
            notif.id === id ? { ...notif, read: true } : notif
          )
        })),
        
        clearNotifications: () => set({ notifications: [] })
      }),
      {
        name: 'volexswarm-ui-storage',
        partialize: (state) => ({
          ui: state.ui,
          selectedAgent: state.selectedAgent,
          selectedTimeframe: state.ui.selectedTimeframe,
          selectedSymbol: state.ui.selectedSymbol
        })
      }
    )
  )
);

// Selector hooks for better performance
export const usePortfolio = () => useAppStore((state) => state.portfolio);
export const useMarketData = () => useAppStore((state) => state.marketData);
export const useAgents = () => useAppStore((state) => state.agents);
export const useSelectedAgent = () => useAppStore((state) => state.selectedAgent);
export const useTradingSignals = () => useAppStore((state) => state.tradingSignals);
export const useActiveStrategies = () => useAppStore((state) => state.activeStrategies);
export const useTasks = () => useAppStore((state) => state.tasks);
export const useWorkflows = () => useAppStore((state) => state.workflows);
export const useUI = () => useAppStore((state) => state.ui);
export const useNotifications = () => useAppStore((state) => state.notifications);
