# VolexSwarm Robust WebUI

A comprehensive, production-ready user interface for managing the VolexSwarm AI Trading System. This WebUI provides complete control and monitoring capabilities for all system components.

## 🎯 **Features Overview**

### **1. Agent Management**
- **Real-time Agent Monitoring**: Monitor all agents (Research, Execution, Signal, Meta, Strategy, Risk, Compliance)
- **Health Status Tracking**: Visual indicators for agent health, memory usage, CPU usage
- **Agent Control**: Start, stop, restart agents with one click
- **Dependency Management**: View agent dependencies and relationships
- **Auto-refresh**: Real-time updates every 10 seconds

### **2. Trading Interface**
- **Portfolio Overview**: Total balance, P&L, open positions, active orders
- **Position Management**: View and manage all trading positions
- **Order Management**: Create, monitor, and cancel orders
- **Balance Tracking**: Real-time balance across all currencies
- **Trade History**: Complete trading history with performance metrics

### **3. Strategy Management**
- **Strategy Creation**: Create new strategies from templates
- **Performance Analytics**: Track total return, Sharpe ratio, max drawdown, win rate
- **Strategy Control**: Enable/disable strategies, edit parameters
- **Composite Strategies**: Manage multi-strategy combinations
- **Strategy Templates**: Pre-built strategy templates for quick deployment

### **4. System Monitoring**
- **Real-time Metrics**: CPU, memory, disk, network usage
- **System Alerts**: Proactive alerting for system issues
- **Performance History**: 24-hour performance tracking
- **Resource Thresholds**: Configurable warning and critical thresholds
- **Alert Management**: Acknowledge and manage system alerts

### **5. Dashboard Overview**
- **System Status**: Overall system health and status
- **Key Metrics**: Quick view of critical system metrics
- **Agent Logs**: Real-time agent activity logs
- **Trading Overview**: High-level trading performance

## 🚀 **Getting Started**

### **Prerequisites**
- Node.js 16+ 
- npm or yarn
- Docker and Docker Compose (for backend services)

### **Installation**

1. **Clone the repository**
   ```bash
   cd webui/react-ui
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm start
   ```

4. **Build for production**
   ```bash
   npm run build
   ```

### **Docker Deployment**

The WebUI is designed to run in Docker containers alongside the trading system:

```bash
# From the project root
docker-compose up webui
```

## 🏗️ **Architecture**

### **Component Structure**
```
src/
├── components/
│   ├── Dashboard.tsx          # Main dashboard with navigation
│   ├── AgentManagement.tsx    # Agent monitoring and control
│   ├── TradingInterface.tsx   # Trading operations
│   ├── StrategyManagement.tsx # Strategy management
│   ├── SystemMonitoring.tsx   # System monitoring
│   ├── AgentStatus.tsx        # Agent status cards
│   ├── SystemMetrics.tsx      # System metrics display
│   ├── TradingOverview.tsx    # Trading overview
│   └── AgentLogs.tsx          # Agent logs display
├── services/
│   └── api.ts                 # API service layer
├── hooks/
│   └── useData.ts             # Custom React hooks
└── types/                     # TypeScript type definitions
```

### **Technology Stack**
- **Frontend**: React 19, TypeScript
- **UI Framework**: Material-UI v7
- **State Management**: React Query for server state
- **Styling**: Emotion (CSS-in-JS)
- **Charts**: Recharts for data visualization
- **Real-time**: Socket.io for live updates

## 📊 **Key Components**

### **Agent Management**
- Monitors 10+ agents including infrastructure (Vault, DB, Redis)
- Real-time health checks and status updates
- Resource usage tracking (CPU, memory)
- Agent dependency visualization
- One-click agent control operations

### **Trading Interface**
- Multi-tab interface (Positions, Orders, Balances, History)
- Real-time P&L tracking with color-coded indicators
- Order creation with symbol selection and validation
- Position management with risk metrics
- Balance tracking across multiple currencies

### **Strategy Management**
- Strategy lifecycle management (create, edit, enable, disable)
- Performance metrics with visual indicators
- Strategy templates for quick deployment
- Composite strategy support
- Parameter optimization interface

### **System Monitoring**
- Real-time system metrics with progress bars
- Alert management with acknowledgment system
- Performance history tracking
- Resource threshold monitoring
- System health indicators

## 🔧 **Configuration**

### **Environment Variables**
```bash
REACT_APP_API_BASE_URL=http://localhost:8005
REACT_APP_WS_URL=ws://localhost:8005/ws
REACT_APP_ENVIRONMENT=development
```

### **API Endpoints**
The WebUI connects to various agent APIs:
- **Agent Health**: `GET /health` on each agent port
- **Trading Data**: `GET /orders`, `GET /positions` on execution agent
- **Strategy Data**: `GET /strategies` on strategy agent
- **System Metrics**: `GET /metrics` on monitoring endpoints

## 🎨 **UI/UX Features**

### **Design System**
- **Dark Theme**: Professional dark theme optimized for trading
- **Color Coding**: Intuitive color system for status and performance
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Accessibility**: WCAG compliant with keyboard navigation

### **User Experience**
- **Real-time Updates**: Live data updates without page refresh
- **Intuitive Navigation**: Clear navigation with breadcrumbs
- **Quick Actions**: One-click operations for common tasks
- **Error Handling**: Graceful error handling with user feedback
- **Loading States**: Smooth loading states and progress indicators

## 🔒 **Security**

### **Authentication**
- JWT-based authentication
- Role-based access control
- Session management
- Secure API communication

### **Data Protection**
- Encrypted data transmission
- Secure storage practices
- Input validation and sanitization
- XSS and CSRF protection

## 📈 **Performance**

### **Optimization Features**
- **Code Splitting**: Lazy loading of components
- **Memoization**: React.memo for expensive components
- **Virtual Scrolling**: For large data tables
- **Caching**: React Query for API response caching
- **Bundle Optimization**: Tree shaking and minification

### **Monitoring**
- **Performance Metrics**: Core Web Vitals tracking
- **Error Tracking**: Comprehensive error logging
- **User Analytics**: Usage analytics and metrics
- **Health Checks**: Regular health check endpoints

## 🧪 **Testing**

### **Test Coverage**
```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run e2e tests
npm run test:e2e
```

### **Testing Strategy**
- **Unit Tests**: Component and utility testing
- **Integration Tests**: API integration testing
- **E2E Tests**: Full user workflow testing
- **Performance Tests**: Load and stress testing

## 🚀 **Deployment**

### **Production Build**
```bash
npm run build
```

### **Docker Deployment**
```bash
docker build -t volexswarm-webui .
docker run -p 3000:3000 volexswarm-webui
```

### **Environment-Specific Configs**
- **Development**: Hot reloading and debug tools
- **Staging**: Production-like environment for testing
- **Production**: Optimized build with monitoring

## 📚 **API Documentation**

### **Agent Management APIs**
```typescript
// Get agent status
GET /api/agents/status

// Control agent
POST /api/agents/{id}/control
{
  "action": "start" | "stop" | "restart"
}
```

### **Trading APIs**
```typescript
// Get positions
GET /api/trading/positions

// Create order
POST /api/trading/orders
{
  "symbol": "BTC/USD",
  "side": "buy",
  "quantity": 0.1,
  "price": 45000
}
```

### **Strategy APIs**
```typescript
// Get strategies
GET /api/strategies

// Create strategy
POST /api/strategies
{
  "name": "My Strategy",
  "type": "moving_average",
  "parameters": {...}
}
```

## 🤝 **Contributing**

### **Development Workflow**
1. Create feature branch from `main`
2. Implement feature with tests
3. Run linting and tests
4. Submit pull request
5. Code review and merge

### **Code Standards**
- **TypeScript**: Strict type checking
- **ESLint**: Code quality enforcement
- **Prettier**: Code formatting
- **Conventional Commits**: Standardized commit messages

## 📞 **Support**

### **Documentation**
- **User Guide**: Complete user documentation
- **API Reference**: Detailed API documentation
- **Troubleshooting**: Common issues and solutions
- **FAQ**: Frequently asked questions

### **Contact**
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Email**: Support email for urgent issues

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

**VolexSwarm WebUI** - Professional-grade interface for AI-powered trading systems.
