# VolexSwarm React UI

A modern, responsive React-based web interface for the VolexSwarm AI Trading System.

## 🚀 Features

### **Dashboard Overview**
- **Real-time System Metrics** - CPU, memory, disk, and network usage
- **Agent Status Monitoring** - Live health checks for all AI agents
- **Trading Performance** - Portfolio value, P&L tracking, and active positions
- **System Status** - Overall system health and component status

### **Modern UI/UX**
- **Dark Theme** - Professional dark interface optimized for trading
- **Responsive Design** - Works on desktop, tablet, and mobile devices
- **Real-time Updates** - Live data refresh with React Query
- **Interactive Charts** - Performance visualization with Recharts
- **Material-UI Components** - Professional, accessible UI components

### **Advanced Features**
- **Agent Management** - Start/stop agents, view logs, configure settings
- **Trading Interface** - Order placement, portfolio management (coming soon)
- **Analytics Dashboard** - Performance charts and market analysis (coming soon)
- **AI Research Panel** - AI-powered insights and market research (coming soon)
- **System Administration** - Vault management, database monitoring (coming soon)

## 🛠 Technology Stack

- **React 18** - Modern React with hooks and functional components
- **TypeScript** - Type-safe development
- **Material-UI (MUI)** - Professional UI component library
- **React Query** - Server state management and caching
- **Recharts** - Beautiful, responsive charts
- **Axios** - HTTP client for API communication
- **Date-fns** - Modern date utility library

## 📦 Installation

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Docker (for containerized deployment)

### Development Setup

1. **Clone and navigate to the React UI directory:**
   ```bash
   cd webui/react-ui
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm start
   ```

4. **Open in browser:**
   ```
   http://localhost:3000
   ```

### Production Build

1. **Build the application:**
   ```bash
   npm run build
   ```

2. **Serve with Docker:**
   ```bash
   docker build -t volexswarm-react-ui .
   docker run -p 3000:80 volexswarm-react-ui
   ```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

The React UI is included in the main `docker-compose.yml`:

```bash
# Start all services including React UI
docker-compose up -d

# Access the React UI
http://localhost:3000
```

### Standalone Docker

```bash
# Build the image
docker build -t volexswarm-react-ui .

# Run the container
docker run -p 3000:80 volexswarm-react-ui
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `webui/react-ui` directory:

```env
# API Configuration
REACT_APP_API_URL=http://localhost:8005

# Development Settings
REACT_APP_DEBUG=true
REACT_APP_ENVIRONMENT=development

# Feature Flags
REACT_APP_ENABLE_WEBSOCKET=true
REACT_APP_ENABLE_ANALYTICS=true
```

### API Endpoints

The React UI connects to the following backend services:

- **Web UI Backend**: `http://localhost:8005` (FastAPI)
- **Research Agent**: `http://research:8001/health`
- **Signal Agent**: `http://signal:8002/health`
- **Execution Agent**: `http://execution:8003/health`
- **Meta Agent**: `http://meta:8004/health`
- **Monitor Agent**: `http://monitor:8005/health`
- **Optimize Agent**: `http://optimize:8006/health`

## 📁 Project Structure

```
src/
├── components/          # React components
│   ├── Dashboard.tsx   # Main dashboard component
│   ├── AgentStatusCard.tsx
│   ├── SystemMetrics.tsx
│   ├── TradingOverview.tsx
│   └── AgentLogs.tsx
├── hooks/              # Custom React hooks
│   └── useData.ts      # Data fetching hooks
├── services/           # API services
│   └── api.ts          # API client and functions
├── types/              # TypeScript type definitions
├── App.tsx             # Main app component
└── index.tsx           # App entry point
```

## 🎨 Customization

### Theme Customization

The app uses a custom dark theme defined in `App.tsx`:

```typescript
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00d4aa',  // VolexSwarm green
    },
    // ... other theme options
  },
});
```

### Adding New Components

1. Create a new component in `src/components/`
2. Import and use in `Dashboard.tsx`
3. Add to navigation if needed

### Adding New API Endpoints

1. Add endpoint to `src/services/api.ts`
2. Create a custom hook in `src/hooks/useData.ts`
3. Use the hook in your component

## 🔍 Development

### Available Scripts

```bash
npm start          # Start development server
npm run build      # Build for production
npm run test       # Run tests
npm run eject      # Eject from Create React App
```

### Code Style

- Use TypeScript for all new code
- Follow React hooks best practices
- Use Material-UI components consistently
- Implement proper error handling
- Add loading states for async operations

### Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watch
```

## 🚀 Performance

### Optimization Features

- **Code Splitting** - Automatic route-based code splitting
- **Lazy Loading** - Components loaded on demand
- **Caching** - React Query provides intelligent caching
- **Bundle Optimization** - Tree shaking and minification
- **Image Optimization** - Optimized asset loading

### Monitoring

- **Error Boundaries** - Graceful error handling
- **Performance Monitoring** - React DevTools integration
- **Network Monitoring** - Axios interceptors for API calls

## 🔒 Security

### Security Features

- **Content Security Policy** - Configured in nginx
- **HTTPS Ready** - Secure headers and configurations
- **Input Validation** - TypeScript and form validation
- **XSS Protection** - Sanitized user inputs

## 📱 Responsive Design

The UI is fully responsive and works on:

- **Desktop** (1200px+) - Full dashboard with sidebar
- **Tablet** (768px-1199px) - Adaptive layout
- **Mobile** (<768px) - Mobile-optimized interface

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is part of the VolexSwarm AI Trading System.

## 🆘 Support

For issues and questions:

1. Check the main project documentation
2. Review existing issues
3. Create a new issue with detailed information

---

**Built with ❤️ for the VolexSwarm AI Trading Platform**
