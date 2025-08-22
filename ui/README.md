# VolexSwarm UI Framework

A modern React-based dashboard for the VolexSwarm AI-powered trading system, built with TypeScript, Material-UI, and Zustand state management.

## 🚀 **Quick Start**

### **Development Mode**
```bash
# Install dependencies
npm install

# Start development server (may have memory issues)
npm start

# Alternative: Build and serve production build
npm run build
serve -s build -l 3000
```

### **Production Mode**
```bash
# Build the application
npm run build

# Serve the built application
serve -s build -l 3000
```

## 🏗️ **Architecture**

### **Core Components**
- **Dashboard**: Portfolio overview, investment tracking, agent status
- **Trading**: Live signals, strategy performance, real-time data
- **Intelligence**: Agent capabilities, autonomous decisions, workflow visualization

### **State Management**
- **Zustand Store**: Global state management for portfolio, agents, and UI
- **Real-time Updates**: WebSocket integration for live data streaming
- **Data Persistence**: Local storage for user preferences

### **Theme & Styling**
- **Material-UI**: Modern component library with dark theme
- **Responsive Design**: Mobile-first approach with breakpoint optimization
- **Custom Components**: Trading-specific UI components and charts

## 🔧 **Configuration**

### **Agent Endpoints**
The UI connects to VolexSwarm agents on the following ports:
- **Meta Agent**: 8004 (API Gateway)
- **Research Agent**: 8001
- **Signal Agent**: 8003
- **Execution Agent**: 8002
- **Strategy Agent**: 8011
- **Risk Agent**: 8009
- **Compliance Agent**: 8010
- **Backtest Agent**: 8006
- **Optimize Agent**: 8007
- **Monitor Agent**: 8008
- **News Sentiment Agent**: 8024
- **Strategy Discovery Agent**: 8025
- **Realtime Data Agent**: 8026

### **WebSocket Configuration**
- **Meta Agent WebSocket**: ws://localhost:8005
- **Real-time Updates**: Agent status, trading signals, portfolio changes

## 📊 **Features**

### **Investment Tracking**
- Portfolio value over time charts
- Crypto holdings breakdown
- Performance metrics (Sharpe ratio, drawdown, win rate)
- Real-time P&L tracking

### **Agent Intelligence**
- Agent capability matrix
- Autonomous decision logs
- Performance metrics and uptime
- Real-time task monitoring

### **Trading Intelligence**
- Live trading signals
- Strategy performance tracking
- Risk assessment and monitoring
- Market data visualization

## 🎨 **UI Components**

### **Dashboard Components**
- `PortfolioOverview`: Portfolio value and P&L cards
- `InvestmentChart`: Time-series portfolio performance
- `HoldingsBreakdown`: Asset allocation and position details
- `PerformanceMetrics`: Risk and performance indicators
- `AgentStatus`: Real-time agent health monitoring

### **Common Components**
- `Layout`: Main navigation and sidebar
- `RealTimeChart`: Live data visualization
- `StatusIndicator`: Health and status indicators
- `DataTable`: Tabular data display

## 🔌 **Integration**

### **API Services**
- `agentService`: Communication with VolexSwarm agents
- `useDataFetching`: Custom hook for data management
- WebSocket integration for real-time updates

### **Data Flow**
1. **Initial Load**: Fetch portfolio, agent status, and market data
2. **Real-time Updates**: WebSocket messages update store
3. **User Interactions**: Actions trigger API calls to agents
4. **State Updates**: Zustand store manages all application state

## 🚀 **Development Workflow**

### **Adding New Features**
1. **Types**: Add interfaces to `src/types/index.ts`
2. **Store**: Update Zustand store in `src/store/index.ts`
3. **Components**: Create components in appropriate directories
4. **Services**: Add API calls to `src/services/agentService.ts`
5. **Hooks**: Create custom hooks for data management

### **Testing**
```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

## 📱 **Responsive Design**

The UI is built with a mobile-first approach:
- **Mobile**: Single column layout with collapsible sidebar
- **Tablet**: Two-column layout with fixed sidebar
- **Desktop**: Full three-column layout with persistent sidebar

## 🌙 **Theme Support**

- **Dark Theme**: Default theme optimized for trading dashboards
- **Light Theme**: Alternative theme for different environments
- **Custom Colors**: Trading-specific color palette (profit/loss indicators)

## 🔮 **Future Enhancements**

### **Phase 2: Advanced Features**
- Interactive portfolio charts with technical indicators
- Real-time order book visualization
- Advanced strategy backtesting interface
- Risk management dashboard

### **Phase 3: Agentic Integration**
- Natural language interface for agent communication
- Autonomous trading decision visualization
- Multi-agent workflow orchestration
- AI-powered insights and recommendations

## 🐛 **Troubleshooting**

### **Memory Issues**
If you encounter memory issues during development:
```bash
# Use production build instead
npm run build
serve -s build -l 3000

# Or increase Node.js memory limit
NODE_OPTIONS="--max-old-space-size=4096" npm start
```

### **Agent Connection Issues**
- Verify all VolexSwarm agents are running
- Check agent endpoints in `src/services/agentService.ts`
- Ensure WebSocket connection to Meta Agent (port 8005)

### **Build Issues**
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear build cache: `rm -rf build && npm run build`
- Check TypeScript compilation: `npx tsc --noEmit`

## 📚 **Dependencies**

### **Core Dependencies**
- **React 19**: Latest React with concurrent features
- **TypeScript**: Type-safe development
- **Material-UI 7**: Modern component library
- **Zustand**: Lightweight state management
- **React Router**: Client-side routing

### **Charting & Visualization**
- **Recharts**: Responsive chart library
- **Material-UI X Charts**: Advanced charting components

### **Communication**
- **Axios**: HTTP client for API calls
- **Socket.io**: WebSocket client for real-time updates

## 🤝 **Contributing**

1. Follow the existing code structure and patterns
2. Use TypeScript for all new code
3. Implement responsive design for all components
4. Add proper error handling and loading states
5. Update types and store as needed
6. Test on multiple screen sizes

---

**Status**: Phase 1 Complete - Basic UI Framework Ready  
**Next**: Phase 2 - Investment Tracking Dashboard Implementation
