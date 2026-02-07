# ShellGPT v2 - Usage Guide

Complete guide for using ShellGPT v2 autonomous red-team agent.

---

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize configuration
sgpt config init

# Check tool availability
sgpt tools
```

### Your First Session

```bash
# Start an agent session
sgpt agent start --goal "enumerate 192.168.1.0/24"

# Agent will propose commands - approve them
# When prompted: Approve command? (y/N): y

# Execute approved commands
sgpt run exec_abc123

# Agent continues until goal is satisfied

# Generate report
sgpt agent report agent_abc123 -o report.md
```

---

## 📋 Commands Reference

### Agent Management

#### Start Agent Session
```bash
sgpt agent start --goal "your security objective" [OPTIONS]

Options:
  --goal TEXT       Security objective (required)
  --interface TEXT  LLM interface: openai, gemini, ollama (default: openai)
  --model TEXT      Model name override
  --session TEXT    Custom session ID
  
Examples:
  sgpt agent start --goal "enumerate 10.0.0.0/24"
  sgpt agent start --goal "find SQL injection in example.com" --interface gemini
```

#### Check Status
```bash
sgpt agent status SESSION_ID

Examples:
  sgpt agent status agent_abc123
```

#### List Sessions
```bash
sgpt agent list [--active|--all]

Examples:
  sgpt agent list --active    # Only running sessions
  sgpt agent list --all       # All sessions
```

#### Resume Session
```bash
sgpt agent resume SESSION_ID

Examples:
  sgpt agent resume agent_abc123
```

#### Stop Session
```bash
sgpt agent stop SESSION_ID

Examples:
  sgpt agent stop agent_abc123
```

#### Generate Report
```bash
sgpt agent report SESSION_ID [-o OUTPUT]

Options:
  -o, --output PATH   Output file (default: stdout)
  
Examples:
  sgpt agent report agent_abc123
  sgpt agent report agent_abc123 -o report.md
```

---

### Command Execution

#### Execute by ID
```bash
sgpt run EXEC_ID [--session SESSION_ID]

Examples:
  sgpt run exec_abc123
  sgpt run exec_abc123 --session agent_xyz
```

#### Execute by Command
```bash
sgpt run "command to execute"

Examples:
  sgpt run "nmap -sn 192.168.1.0/24"
```

---

### Tool Management

#### List Available Tools
```bash
sgpt tools

# Shows table of all tools with installation status
```

---

### Configuration

#### Initialize Config
```bash
sgpt config init [--output PATH]

Examples:
  sgpt config init
  sgpt config init --output ~/my-config.yaml
```

#### Show Configuration
```bash
sgpt config show

# Displays current configuration from all sources
```

#### Set Value
```bash
sgpt config set SECTION.KEY VALUE

Examples:
  sgpt config set llm.interface gemini
  sgpt config set llm.temperature 0.5
  sgpt config set logging.console_level DEBUG
  sgpt config set safety.require_approval false
```

#### Validate Config
```bash
sgpt config validate

# Checks configuration for errors and warnings
```

---

### Report Generation

#### Generate from Session
```bash
sgpt report SESSION_ID [-o OUTPUT] [--format markdown|json]

Options:
  -o, --output PATH      Output file
  --format TYPE         Report format (default: markdown)
  
Examples:
  sgpt report agent_abc123
  sgpt report agent_abc123 -o pentest-report.md
  sgpt report agent_abc123 --format json -o data.json
```

---

## 🎯 Usage Scenarios

### Scenario 1: Network Enumeration

```bash
# Start enumeration session
sgpt agent start --goal "enumerate network 10.0.0.0/24"

# Agent proposes: nmap -sn 10.0.0.0/24
# You approve: y

# Execute
sgpt run exec_001

# Agent discovers hosts, proposes port scan
# You approve: y

# Execute
sgpt run exec_002

# Continue until complete...

# Generate report
sgpt agent report agent_001 -o network-report.md
```

### Scenario 2: Web Application Assessment

```bash
# Start web assessment
sgpt agent start --goal "assess web app at https://example.com"

# Agent proposes technology fingerprinting
# Approve and execute commands as they come

# Agent will:
# 1. Fingerprint technologies (whatweb)
# 2. Spider directories (gobuster)  
# 3. Scan for vulnerabilities (nikto)
# 4. Test for common issues

# Generate report
sgpt agent report agent_002 -o webapp-report.md
```

### Scenario 3: Custom Script-Based Testing

```bash
# Start custom testing
sgpt agent start --goal "test authentication on example.com"

# Agent may propose Python scripts for:
# - Brute force testing
# - Token extraction
# - Session analysis

# Review scripts before approving!
# Execute with: sgpt run exec_id
```

---

## ⚙️ Configuration Guide

### Configuration File Location

Default: `~/.sgpt/config.yaml`

### Configuration Priority

1. **Environment Variables** (highest)
2. **User Config File** (`~/.sgpt/config.yaml`)
3. **Default Values** (lowest)

### Example Configuration

```yaml
# ~/.sgpt/config.yaml

llm:
  interface: gemini
  model: gemini-pro
  temperature: 0.7
  max_tokens: 2000
  retry_attempts: 3

execution:
  timeout: 300
  max_pending: 10
  auto_cleanup: true

logging:
  console_level: INFO
  file_level: DEBUG
  enable_rotation: true
  max_file_size_mb: 10
  backup_count: 7

safety:
  require_approval: true
  enable_validation: true
  allowed_networks: 
    - 192.168.1.0/24
    - 10.0.0.0/8

storage:
  sessions_dir: ~/.sgpt/agent_sessions
  logs_dir: ~/.sgpt/logs
  reports_dir: ~/.sgpt/reports
```

### Environment Variables

```bash
# LLM Configuration
export SGPT_LLM_INTERFACE=gemini
export SGPT_LLM_MODEL=gemini-pro
export SGPT_LLM_TEMPERATURE=0.7

# Execution
export SGPT_EXEC_TIMEOUT=600

# Logging
export SGPT_LOG_LEVEL=DEBUG

# Safety
export SGPT_REQUIRE_APPROVAL=true

# Storage
export SGPT_STORAGE_DIR=~/my-sgpt-data
```

---

## 🛡️ Safety Guidelines

### Human-in-the-Loop

- **Every command requires approval**
- Review commands carefully before approving
- Understand what each command does
- Never approve destructive commands blindly

### Built-in Safety

23 destructive command patterns are blocked:
- `rm -rf`, `mkfs`, `dd`
- `chmod 777`, `chown`
- Privilege escalation (`sudo`, `su`)
- Network manipulation (`iptables`)
- Data exfiltration (`nc -e`, `curl upload`)

### Network Restrictions

Configure allowed networks in config:

```yaml
safety:
  allowed_networks:
    - 192.168.1.0/24  # Lab network only
```

### Best Practices

1. **Test in isolated environments** - Use VMs or lab networks
2. **Review generated scripts** - Especially Python scripts
3. **Monitor execution** - Watch command outputs
4. **Keep logs** - Review agent decisions in logs
5. **Generate reports** - Document all activities

---

## 📊 Understanding Agent Phases

The agent progresses through standard red-team phases:

### 1. Reconnaissance
- Network discovery
- Host identification
- Service fingerprinting

### 2. Enumeration
- Port scanning
- Version detection
- Banner grabbing

### 3. Vulnerability Assessment
- Known vulnerability scanning
- Configuration issues
- Weak credentials

### 4. Exploitation
- Proof-of-concept exploits
- Credential testing
- Access verification

---

## 📝 Logs and Debugging

### Log Locations

```
~/.sgpt/logs/
├── sgpt.log              # Main log (rotated daily)
├── sgpt_structured.json  # JSON log for parsing
└── sgpt.log.2024-01-29   # Archived logs
```

### Log Levels

- `DEBUG` - Detailed trace (file only)
- `INFO` - Major events (console + file)
- `WARNING` - Recoverable issues
- `ERROR` - Failures
- `CRITICAL` - Fatal errors

### Enable Debug Mode

```bash
# Via config
sgpt config set logging.console_level DEBUG

# Via environment
export SGPT_LOG_LEVEL=DEBUG
sgpt agent start --goal "..."
```

### View Logs

```bash
# Real-time monitoring
tail -f ~/.sgpt/logs/sgpt.log

# Search logs
grep "ERROR" ~/.sgpt/logs/sgpt.log

# Parse JSON logs
cat ~/.sgpt/logs/sgpt_structured.json | jq '.[] | select(.level=="ERROR")'
```

---

## 🔧 Troubleshooting

### Common Issues

#### "Tool not found"
```bash
# Check tool availability
sgpt tools

# Install missing tools
sudo apt install nmap gobuster nikto  # Debian/Ubuntu
brew install nmap gobuster            # macOS
```

#### "LLM generation failed"
```bash
# Check API keys
echo $OPENAI_API_KEY
echo $GOOGLE_API_KEY

# Try different interface
sgpt config set llm.interface ollama

# Enable debug logging
sgpt config set logging.console_level DEBUG
```

#### "Execution timeout"
```bash
# Increase timeout
sgpt config set execution.timeout 600

# Or via environment
export SGPT_EXEC_TIMEOUT=600
```

#### "Permission denied"
```bash
# Some tools need sudo
# Run the command manually with sudo:
sudo nmap -sS 192.168.1.1
```

---

## 🎨 Shell Completions

### Bash

Add to `~/.bashrc`:
```bash
source /path/to/shell_gpt_s1/completions/bash_completion.sh
```

### Zsh

Add to `~/.zshrc`:
```bash
source /path/to/shell_gpt_s1/completions/zsh_completion.zsh
```

Then reload: `source ~/.bashrc` or `source ~/.zshrc`

---

## 📚 Additional Resources

- **Architecture**: See `ARCHITECTURE.md`
- **Project Walkthrough**: See artifacts in `~/.gemini/antigravity/brain/`
- **Tool Specifications**: `sgpt/tools/specs/`
- **Examples**: `tests/` directory

---

## 🆘 Getting Help

```bash
# Command help
sgpt --help
sgpt agent --help
sgpt config --help

# Check version
sgpt --version

# Validate setup
sgpt config validate
sgpt tools
```

---

**Remember**: Always use responsibly and only on networks/systems you have permission to test! 🛡️
