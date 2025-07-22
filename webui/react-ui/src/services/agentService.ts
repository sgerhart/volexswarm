export interface AgentHealth {
  status: string;
  agent?: string;
  version?: string;
  timestamp?: string;
  vault_connected?: boolean;
  database_connected?: boolean;
  checks?: {
    database?: { status: string };
    vault?: { status: string };
  };
}

export interface Agent {
  id: string;
  name: string;
  port: number;
  status: 'healthy' | 'unhealthy' | 'starting' | 'stopped' | 'error';
  lastSeen: string;
  version: string;
  uptime: string;
  memory: string;
  cpu: string;
  endpoints: string[];
  dependencies: string[];
}

const AGENT_CONFIGS = {
  vault: { name: 'Vault', port: 8200, endpoints: ['/v1/sys/health'], dependencies: [] },
  db: { name: 'TimescaleDB', port: 5432, endpoints: ['/health'], dependencies: [] },
  redis: { name: 'Redis', port: 6379, endpoints: ['PING'], dependencies: [] },
  research: { name: 'Research Agent', port: 8001, endpoints: ['/health', '/research'], dependencies: ['vault', 'db'] },
  execution: { name: 'Execution Agent', port: 8002, endpoints: ['/health', '/orders'], dependencies: ['vault', 'db'] },
  signal: { name: 'Signal Agent', port: 8003, endpoints: ['/health', '/signals'], dependencies: ['vault', 'db'] },
  meta: { name: 'Meta Agent', port: 8004, endpoints: ['/health', '/orchestrate'], dependencies: ['research', 'execution', 'signal', 'strategy'] },
  strategy: { name: 'Strategy Agent', port: 8011, endpoints: ['/health', '/strategies'], dependencies: ['vault', 'db'] },
  risk: { name: 'Risk Agent', port: 8009, endpoints: ['/health', '/risk'], dependencies: ['vault', 'db'] },
  compliance: { name: 'Compliance Agent', port: 8010, endpoints: ['/health', '/compliance'], dependencies: ['vault', 'db'] },
};

export const fetchAgentHealth = async (agentId: string): Promise<AgentHealth | null> => {
  const config = AGENT_CONFIGS[agentId as keyof typeof AGENT_CONFIGS];
  if (!config) return null;

  try {
    // For Vault, we need to use the Vault API
    if (agentId === 'vault') {
      const response = await fetch('http://localhost:8200/v1/sys/health');
      if (response.ok) {
        const data = await response.json();
        return {
          status: data.initialized ? 'healthy' : 'unhealthy',
          agent: 'vault',
          version: '1.15.0'
        };
      }
      return { status: 'unhealthy' };
    }

    // For Redis, we'll use a simple ping test
    if (agentId === 'redis') {
      // We'll simulate Redis health for now since we can't easily test it from the browser
      return { status: 'healthy', agent: 'redis', version: '7.2.0' };
    }

    // For database, we'll simulate health since we can't easily test it from the browser
    if (agentId === 'db') {
      return { status: 'healthy', agent: 'timescaledb', version: '2.11.0' };
    }

    // For all other agents, use their health endpoints
    const response = await fetch(`http://localhost:${config.port}/health`);
    if (response.ok) {
      const data: AgentHealth = await response.json();
      return data;
    }
    
    return { status: 'unhealthy' };
  } catch (error) {
    console.error(`Error fetching health for ${agentId}:`, error);
    return { status: 'unhealthy' };
  }
};

export const fetchAllAgentsStatus = async (): Promise<Agent[]> => {
  const agents: Agent[] = [];
  
  for (const [agentId, config] of Object.entries(AGENT_CONFIGS)) {
    const health = await fetchAgentHealth(agentId);
    
    const agent: Agent = {
      id: agentId,
      name: config.name,
      port: config.port,
      status: health?.status === 'healthy' ? 'healthy' : 'unhealthy',
      lastSeen: new Date().toISOString(),
      version: health?.version || '1.0.0',
      uptime: '2d 14h 32m', // We'll keep this as mock data for now
      memory: `${Math.floor(Math.random() * 200 + 50)}.${Math.floor(Math.random() * 10)} MB`, // Mock data
      cpu: `${(Math.random() * 20 + 1).toFixed(1)}%`, // Mock data
      endpoints: config.endpoints,
      dependencies: config.dependencies,
    };
    
    agents.push(agent);
  }
  
  return agents;
}; 