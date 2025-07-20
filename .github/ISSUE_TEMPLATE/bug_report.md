---
name: Bug report
about: Create a report to help us improve VolexSwarm
title: '[BUG] '
labels: ['bug']
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment (please complete the following information):**
 - OS: [e.g. macOS, Ubuntu, Windows]
 - Python Version: [e.g. 3.11.0]
 - Docker Version: [e.g. 20.10.0]
 - VolexSwarm Version: [e.g. commit hash or version]

**Agent Information:**
 - Which agent(s) are affected: [e.g. research, signal, execution, meta]
 - Agent status: [e.g. healthy, unhealthy, not responding]

**Vault Configuration:**
 - Vault Status: [e.g. connected, disconnected]
 - Secrets configured: [e.g. yes, no, partially]

**Database Information:**
 - Database Status: [e.g. connected, disconnected]
 - TimescaleDB Version: [e.g. latest-pg14]

**Additional context**
Add any other context about the problem here, including:
- Log files (if applicable)
- Error messages
- Configuration files
- Steps you've already tried

**Logs**
Please include relevant log output:
```bash
# Example: Agent logs
docker logs volexswarm-research-1 --tail 50

# Example: Vault logs
docker logs volexswarm-vault --tail 20

# Example: Database logs
docker logs volexstorm-db --tail 20
``` 