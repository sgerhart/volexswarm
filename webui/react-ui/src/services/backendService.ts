// Backend service for proxying Docker and system data
// This would connect to a backend API that can access Docker and system information

export interface BackendSystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_io: {
    bytes_sent: number;
    bytes_recv: number;
  };
  uptime: number;
  load_average: number[];
}

export interface BackendDockerContainer {
  id: string;
  name: string;
  image: string;
  status: string;
  state: string;
  ports: string[];
  created: string;
  size: string;
  memory?: string;
  cpu?: string;
}

export interface BackendDockerStats {
  containers: BackendDockerContainer[];
  total_containers: number;
  running_containers: number;
  stopped_containers: number;
  total_memory_usage: string;
  total_cpu_usage: string;
}

// For now, we'll simulate the backend API calls
// In a real implementation, these would make HTTP requests to a backend service

export const fetchBackendSystemMetrics = async (): Promise<BackendSystemMetrics> => {
  // Simulate API call delay
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // In a real implementation, this would be:
  // const response = await fetch('/api/system/metrics');
  // return response.json();
  
  return {
    cpu_usage: Math.random() * 30 + 10, // 10-40%
    memory_usage: Math.random() * 40 + 30, // 30-70%
    disk_usage: Math.random() * 20 + 15, // 15-35%
    network_io: {
      bytes_sent: Math.random() * 1000000 + 500000,
      bytes_recv: Math.random() * 2000000 + 1000000,
    },
    uptime: 7200, // 2 hours in seconds
    load_average: [Math.random() * 2 + 0.5, Math.random() * 2 + 0.5, Math.random() * 2 + 0.5]
  };
};

export const fetchBackendDockerStats = async (): Promise<BackendDockerStats> => {
  // Simulate API call delay
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // In a real implementation, this would be:
  // const response = await fetch('/api/docker/stats');
  // return response.json();
  
  const containers: BackendDockerContainer[] = [
    {
      id: 'volexswarm-vault',
      name: 'volexswarm-vault',
      image: 'hashicorp/vault:latest',
      status: 'Up 2 hours',
      state: 'running',
      ports: ['0.0.0.0:8200->8200/tcp'],
      created: '2025-07-22T01:00:00Z',
      size: '45.2 MB',
      memory: '23.1 MB',
      cpu: '2.1%'
    },
    {
      id: 'volexstorm-db',
      name: 'volexstorm-db',
      image: 'timescale/timescaledb:latest-pg14',
      status: 'Up 2 hours',
      state: 'running',
      ports: ['0.0.0.0:5432->5432/tcp'],
      created: '2025-07-22T01:00:00Z',
      size: '156.7 MB',
      memory: '89.4 MB',
      cpu: '8.3%'
    },
    {
      id: 'volexswarm-redis',
      name: 'volexswarm-redis',
      image: 'redis:7-alpine',
      status: 'Up 2 hours',
      state: 'running',
      ports: ['0.0.0.0:6379->6379/tcp'],
      created: '2025-07-22T01:00:00Z',
      size: '23.1 MB',
      memory: '12.3 MB',
      cpu: '1.2%'
    },
    {
      id: 'volexswarm-research-1',
      name: 'volexswarm-research-1',
      image: 'volexswarm-research',
      status: 'Up 2 hours',
      state: 'running',
      ports: ['0.0.0.0:8001->8000/tcp'],
      created: '2025-07-22T01:00:00Z',
      size: '134.2 MB',
      memory: '67.8 MB',
      cpu: '12.7%'
    },
    {
      id: 'volexswarm-execution-1',
      name: 'volexswarm-execution-1',
      image: 'volexswarm-execution',
      status: 'Up 2 hours',
      state: 'running',
      ports: ['0.0.0.0:8002->8002/tcp'],
      created: '2025-07-22T01:00:00Z',
      size: '167.8 MB',
      memory: '89.2 MB',
      cpu: '15.8%'
    },
    {
      id: 'volexswarm-signal-1',
      name: 'volexswarm-signal-1',
      image: 'volexswarm-signal',
      status: 'Up 2 hours',
      state: 'running',
      ports: ['0.0.0.0:8003->8003/tcp'],
      created: '2025-07-22T01:00:00Z',
      size: '145.6 MB',
      memory: '78.3 MB',
      cpu: '18.9%'
    },
    {
      id: 'volexswarm-meta-1',
      name: 'volexswarm-meta-1',
      image: 'volexswarm-meta',
      status: 'Up 2 hours',
      state: 'running',
      ports: ['0.0.0.0:8004->8004/tcp'],
      created: '2025-07-22T01:00:00Z',
      size: '123.4 MB',
      memory: '56.7 MB',
      cpu: '9.4%'
    },
    {
      id: 'volexswarm-strategy-1',
      name: 'volexswarm-strategy-1',
      image: 'volexswarm-strategy',
      status: 'Up 2 hours',
      state: 'running',
      ports: ['0.0.0.0:8011->8011/tcp'],
      created: '2025-07-22T01:00:00Z',
      size: '178.9 MB',
      memory: '112.6 MB',
      cpu: '11.3%'
    },
    {
      id: 'volexswarm-risk-1',
      name: 'volexswarm-risk-1',
      image: 'volexswarm-risk',
      status: 'Up 2 hours',
      state: 'running',
      ports: ['0.0.0.0:8009->8009/tcp'],
      created: '2025-07-22T01:00:00Z',
      size: '134.7 MB',
      memory: '95.7 MB',
      cpu: '7.8%'
    },
    {
      id: 'volexswarm-compliance-1',
      name: 'volexswarm-compliance-1',
      image: 'volexswarm-compliance',
      status: 'Up 2 hours',
      state: 'running',
      ports: ['0.0.0.0:8010->8010/tcp'],
      created: '2025-07-22T01:00:00Z',
      size: '98.3 MB',
      memory: '67.2 MB',
      cpu: '5.2%'
    },
    {
      id: 'volexswarm-webui-1',
      name: 'volexswarm-webui-1',
      image: 'volexswarm-webui',
      status: 'Up 2 hours',
      state: 'running',
      ports: ['0.0.0.0:8005->80/tcp'],
      created: '2025-07-22T01:00:00Z',
      size: '45.6 MB',
      memory: '23.4 MB',
      cpu: '3.1%'
    }
  ];

  const running = containers.filter(c => c.state === 'running').length;
  const stopped = containers.filter(c => c.state === 'stopped').length;
  
  // Calculate total memory and CPU usage
  let totalMemory = 0;
  let totalCpu = 0;
  
  containers.forEach(container => {
    if (container.memory) {
      const memoryMB = parseFloat(container.memory.replace(' MB', ''));
      totalMemory += memoryMB;
    }
    if (container.cpu) {
      const cpuPercent = parseFloat(container.cpu.replace('%', ''));
      totalCpu += cpuPercent;
    }
  });
  
  return {
    containers,
    total_containers: containers.length,
    running_containers: running,
    stopped_containers: stopped,
    total_memory_usage: `${totalMemory.toFixed(1)} MB`,
    total_cpu_usage: `${totalCpu.toFixed(1)}%`
  };
}; 