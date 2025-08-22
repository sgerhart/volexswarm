# VolexSwarm Deployment Guide

## 🚀 **Quick Deployment**

### **Prerequisites**
- Docker and Docker Compose installed
- Git
- At least 4GB RAM and 10GB disk space

### **Step 1: Clone and Setup**
```bash
# Clone the repository
git clone https://github.com/sgerhart/volexswarm.git
cd volexswarm

# Copy environment template
cp env.example .env
```

### **Step 2: Configure Environment**
Edit `.env` file with your settings:
```bash
# Security Configuration (Phase 7)
JWT_SECRET=your-super-secure-jwt-secret-here
REDIS_PASSWORD=your-redis-password-here

# Vault Configuration
VAULT_ROOT_TOKEN=your-vault-root-token

# Database Configuration
DB_PASSWORD=your-database-password

# OpenAI Configuration (for AI agents)
OPENAI_API_KEY=your-openai-api-key
```

### **Step 3: Deploy with Phase 7 Security**
```bash
# Deploy the entire system with security
docker-compose -f docker-compose.phase7.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### **Step 4: Access the Application**

- **Default Admin**: `admin` / `Admin123!`
- **Vault**: http://localhost:8200
- **Database**: localhost:5432

---

## 🔐 **Phase 7 Security Features**

### **Authentication**
```bash
# Login via API
curl -X POST http://localhost:8004/security/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123!"}'

# Response includes JWT tokens
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_id",
    "username": "admin",
    "role": "admin",
    "permissions": ["system:admin", "trade:execute", ...]
  }
}
```

### **Using JWT Tokens**
```bash
# Access protected endpoints
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8004/security/me

# Refresh token
curl -X POST http://localhost:8004/security/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

### **User Management**
```bash
# Create new user (admin only)
curl -X POST http://localhost:8004/security/users \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "trader1",
    "email": "trader1@example.com",
    "password": "SecurePass123!",
    "role": "trader"
  }'

# List users (admin only)
curl -H "Authorization: Bearer ADMIN_TOKEN" \
  http://localhost:8004/security/users
```

---

## 📊 **Monitoring and Health Checks**

### **System Health**
```bash
# Check overall system health
curl http://localhost:8004/health

# Check security system health
curl http://localhost:8004/security/health

# Check security status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8004/security/status
```

### **Security Events**
```bash
# View security events (audit permission required)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8004/security/events

# Filter events by user
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8004/security/events?user_id=USER_ID"
```

### **Container Monitoring**
```bash
# Check container status
docker-compose ps

# View container logs
docker-compose logs -f meta
docker-compose logs -f security-monitor

# Monitor resource usage
docker stats
```

---

## 🔧 **Configuration Options**

### **Security Configuration**
```python
# Security settings in common/security.py
SECURITY_CONFIG = {
    "jwt_secret": "your-secret-key",
    "jwt_expiration": 3600,  # 1 hour
    "jwt_refresh_expiration": 604800,  # 7 days
    "rate_limit": 100,  # requests per minute
    "max_login_attempts": 5,
    "password_min_length": 8,
    "password_require_special": True,
    "password_require_numbers": True,
    "password_require_uppercase": True,
}
```

### **Environment Variables**
```bash
# Security
SECURITY_ENABLED=true
JWT_SECRET=your-jwt-secret
SECURITY_LOG_LEVEL=INFO

# Infrastructure
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=your-vault-token
DB_HOST=db
DB_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379

# Monitoring
MONITOR_VAULT=true
MONITOR_DB=true
MONITOR_AGENTS=true
```

---

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **1. Container Won't Start**
```bash
# Check logs
docker-compose logs [service-name]

# Check environment variables
docker-compose config

# Restart specific service
docker-compose restart [service-name]
```

#### **2. Authentication Issues**
```bash
# Check JWT secret is set
echo $JWT_SECRET

# Verify Vault is running
curl http://localhost:8200/v1/sys/health

# Check security logs
docker-compose logs -f meta | grep security
```

#### **3. Database Connection Issues**
```bash
# Check database status
docker-compose exec db pg_isready -U volex

# Check database logs
docker-compose logs -f db
```

#### **4. Security Health Check Fails**
```bash
# Check security module
docker-compose exec meta python -c "
from common.security import security_manager
print('Security manager:', security_manager)
"

# Check security API
curl http://localhost:8004/security/health
```

### **Reset and Recovery**
```bash
# Reset entire system
docker-compose down -v
docker-compose up -d

# Reset security data only
docker-compose exec meta python -c "
from common.security import security_manager
security_manager.users.clear()
security_manager.refresh_tokens.clear()
print('Security data reset')
"
```

---

## 🔒 **Production Security Checklist**

### **Before Deployment**
- [ ] Change default passwords
- [ ] Set secure JWT secret
- [ ] Configure Redis password
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting

### **Security Hardening**
- [ ] Enable HTTPS for all services
- [ ] Configure rate limiting
- [ ] Set up intrusion detection
- [ ] Enable audit logging
- [ ] Configure backup encryption
- [ ] Set up security monitoring

### **Ongoing Security**
- [ ] Regular security updates
- [ ] Monitor security events
- [ ] Review access logs
- [ ] Update dependencies
- [ ] Security penetration testing
- [ ] Compliance audits

---

## 📈 **Scaling and Performance**

### **Horizontal Scaling**
```bash
# Scale specific services
docker-compose up -d --scale research=3
docker-compose up -d --scale signal=2

# Load balancing
# Add nginx or traefik for load balancing
```

### **Performance Optimization**
```bash
# Monitor performance
docker stats

# Optimize database
docker-compose exec db psql -U volex -d volextrades -c "
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
"

# Cache optimization
docker-compose exec redis redis-cli INFO memory
```

---

## 🎯 **Next Steps**

### **Phase 8: Production Monitoring**
- Set up Prometheus and Grafana
- Configure alerting rules
- Implement log aggregation
- Set up performance monitoring

### **Advanced Security**
- Implement intrusion detection
- Set up vulnerability scanning
- Configure advanced threat protection
- Implement zero-trust architecture

### **Production Deployment**
- Set up Kubernetes cluster
- Configure CI/CD pipelines
- Implement blue-green deployments
- Set up disaster recovery

---

This deployment guide provides everything needed to get VolexSwarm running with Phase 7 security features in a production-ready environment. 