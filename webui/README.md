# VolexSwarm Web UI

A modern, responsive web interface for the VolexSwarm Autonomous AI Trading System.

## 🚀 Features

### **Real-Time Dashboard**
- **System Status Overview**: Live monitoring of all agents and system health
- **Trading Metrics**: Real-time display of active signals, trades, and performance
- **Market Data**: Current prices, 24h changes, and volume information
- **Agent Health**: Individual agent status and detailed information

### **Comprehensive Views**
- **Dashboard**: Main overview with key metrics and recent activity
- **Agents**: Detailed status and information for each AI agent
- **Signals**: Trading signals with confidence and strength indicators
- **Trades**: Complete trade history and execution details
- **Market Data**: Real-time market information and price charts
- **System Status**: Detailed system health and performance metrics

### **Modern UI/UX**
- **Dark Theme**: Professional dark interface optimized for trading
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-Time Updates**: Auto-refreshing data every 30 seconds
- **Interactive Elements**: Hover effects, tooltips, and smooth animations
- **Material Design**: Clean, modern interface using Material-UI components

## 🛠 Technology Stack

### **Frontend**
- **React 18** with TypeScript
- **Material-UI (MUI)** for components and theming
- **React Query** for data fetching and caching
- **React Router** for navigation
- **Recharts** for data visualization
- **Framer Motion** for animations

### **Backend**
- **FastAPI** for high-performance API
- **HTTPX** for async HTTP requests
- **Uvicorn** for ASGI server
- **Pydantic** for data validation

## 📦 Installation

### **Development Setup**

1. **Install Node.js dependencies**:
   ```bash
   cd webui
   npm install
   ```

2. **Install Python dependencies**:
   ```bash
   cd webui/backend
   pip install -r requirements.txt
   ```

3. **Start the development server**:
   ```bash
   # Terminal 1: Start React dev server
   npm start
   
   # Terminal 2: Start FastAPI backend
   cd backend
   python main.py
   ```

### **Production with Docker**

The web UI is included in the main `docker-compose.yml`:

```bash
# Start all services including web UI
docker-compose up -d

# Access the web interface
open http://localhost:8005
```

## 🎯 Usage

### **Accessing the Web UI**

Once running, access the web interface at:
- **Development**: `http://localhost:3000`
- **Production**: `http://localhost:8005`

### **Navigation**

The web UI features a sidebar navigation with:

1. **Dashboard** (`/`) - Main overview and metrics
2. **Agents** (`/agents`) - Individual agent status and details
3. **Signals** (`/signals`) - Trading signals and analysis
4. **Trades** (`/trades`) - Trade history and execution
5. **Market Data** (`/market-data`) - Real-time market information
6. **System Status** (`/system-status`) - System health and performance

### **Key Features**

#### **Real-Time Monitoring**
- System status updates every 30 seconds
- Live agent health monitoring
- Real-time trading signal display
- Current market data updates

#### **Interactive Elements**
- Click to expand agent details
- Hover for additional information
- Refresh button for manual updates
- Responsive design for all screen sizes

#### **Data Visualization**
- Progress bars for agent health
- Color-coded status indicators
- Percentage displays for confidence levels
- Currency formatting for prices

## 🔧 Configuration

### **Environment Variables**

The web UI backend supports the following environment variables:

```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8005/api  # Frontend API URL
VAULT_ADDR=http://vault:8200                 # Vault server address
VAULT_TOKEN=root                             # Vault authentication token

# Agent Endpoints (configured in backend/main.py)
RESEARCH_AGENT_URL=http://localhost:8001
SIGNAL_AGENT_URL=http://localhost:8003
EXECUTION_AGENT_URL=http://localhost:8002
META_AGENT_URL=http://localhost:8004
```

### **Customization**

#### **Theme Customization**
Edit `src/App.tsx` to modify the Material-UI theme:

```typescript
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00d4aa',  // VolexSwarm green
    },
    secondary: {
      main: '#ff6b35',  // VolexSwarm orange
    },
    // ... more customization
  },
});
```

#### **API Endpoints**
Modify `backend/main.py` to add new agent endpoints or change existing ones:

```python
AGENT_ENDPOINTS = {
    "research": "http://localhost:8001",
    "signal": "http://localhost:8003", 
    "execution": "http://localhost:8002",
    "meta": "http://localhost:8004",
    # Add new agents here
}
```

## 📊 API Endpoints

The web UI backend provides the following API endpoints:

### **System Status**
- `GET /api/system-status` - Overall system health and metrics
- `GET /api/health` - Backend health check
- `POST /api/refresh` - Manually trigger data refresh

### **Agent Data**
- `GET /api/agents` - Status of all agents
- `GET /api/agents/{agent_name}` - Detailed agent information

### **Trading Data**
- `GET /api/signals` - Recent trading signals
- `GET /api/trades` - Trade history
- `GET /api/market-data` - Current market data
- `GET /api/metrics` - System performance metrics

## 🚀 Deployment

### **Docker Deployment**

The web UI is designed to run in Docker containers:

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f webui

# Stop services
docker-compose down
```

### **Production Considerations**

1. **Security**: The web UI currently has no authentication. For production:
   - Add authentication middleware
   - Implement HTTPS
   - Configure CORS properly
   - Add rate limiting

2. **Performance**: 
   - Enable gzip compression
   - Configure caching headers
   - Use a production-grade ASGI server
   - Consider CDN for static assets

3. **Monitoring**:
   - Add health check endpoints
   - Configure logging
   - Set up metrics collection
   - Monitor resource usage

## 🔍 Troubleshooting

### **Common Issues**

1. **Frontend not loading**:
   - Check if React dev server is running on port 3000
   - Verify all dependencies are installed
   - Check browser console for errors

2. **Backend connection issues**:
   - Ensure FastAPI server is running on port 8005
   - Check agent endpoints are accessible
   - Verify Vault and database connectivity

3. **No data displayed**:
   - Check if agents are running and healthy
   - Verify API endpoints are responding
   - Check browser network tab for failed requests

### **Development Tips**

1. **Hot Reload**: React dev server supports hot reloading
2. **API Testing**: Use FastAPI's automatic docs at `/docs`
3. **Debug Mode**: Enable React DevTools for debugging
4. **Logs**: Check Docker logs for backend issues

## 📈 Future Enhancements

### **Planned Features**
- **Real-time Charts**: Interactive price charts with TradingView integration
- **Portfolio Management**: Account balance and position tracking
- **Alert System**: Custom notifications for signals and trades
- **Backtesting Interface**: Historical performance analysis
- **Strategy Editor**: Visual strategy builder
- **Mobile App**: Native mobile application

### **Performance Improvements**
- **WebSocket Support**: Real-time data streaming
- **Caching Layer**: Redis for improved performance
- **CDN Integration**: Faster static asset delivery
- **PWA Features**: Offline capability and app-like experience

## 🤝 Contributing

To contribute to the web UI:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is part of the VolexSwarm Autonomous AI Trading System and follows the same license terms. 