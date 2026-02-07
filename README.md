# ShellGPT v2 - Autonomous Penetration Testing Agent

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tools](https://img.shields.io/badge/tools-14-orange.svg)](#tools)

**Complete autonomous red-team agent** with 14 Kali Linux tools, LLM-powered reasoning, and production-grade reliability.

---

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/mrmastrodotin/shell_gpt_s2.git
cd shell_gpt_s2

# Install dependencies
pip install -r requirements.txt

# Initialize configuration
python -m sgpt config init

# Start agent
python -m sgpt agent start --goal "enumerate 192.168.1.0/24"
```

---

## ⭐ Features

- **14 Kali Tools** - masscan, nmap, sqlmap, wpscan, crackmapexec, hydra, nikto, gobuster, whatweb, enum4linux, smbclient, netcat, curl, python_script
- **48 Intents** - Comprehensive penetration testing capabilities
- **LLM-Powered** - Autonomous decision making with 4-step reasoning chain
- **Human-in-Loop** - Every command requires approval for safety
- **Session Resume** - Continue from any checkpoint with full context
- **Professional Reports** - Markdown reports with executive summary
- **Rich CLI** - Beautiful formatting with colors, tables, progress bars
- **Production Ready** - Error recovery, comprehensive logging, configuration management

---

## 🛠️ Tools

### Discovery
- **nmap** - Network/port scanning, service detection
- **masscan** - Ultra-fast port scanning (1000+ pps)

### Web Testing
- **curl** - HTTP requests
- **gobuster** - Directory/subdomain brute-forcing
- **nikto** - Web vulnerability scanning
- **whatweb** - Technology fingerprinting
- **wpscan** - WordPress security

### Enumeration
- **enum4linux** - SMB enumeration
- **smbclient** - SMB file operations

### Exploitation
- **hydra** - Password attacks
- **sqlmap** - SQL injection
- **crackmapexec** - SMB/WinRM exploitation
- **netcat** - Reverse shells, file transfers

### Scripting
- **python_script** - Custom Python automation

---

## 📚 Documentation

- **[USAGE.md](USAGE.md)** - Complete usage guide with examples
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design

---

## 🎯 Example Usage

### Network Enumeration
```bash
python -m sgpt agent start --goal "enumerate 10.0.0.0/24"
# Agent proposes: nmap -sn 10.0.0.0/24
# You approve: y
# Execute: python -m sgpt run exec_001
```

### Web Assessment
```bash
python -m sgpt agent start --goal "assess https://example.com"
# Agent automatically:
# 1. Fingerprints technologies (whatweb)
# 2. Brute-forces directories (gobuster)
# 3. Scans for vulnerabilities (nikto)
# 4. Tests for SQL injection (sqlmap)
```

### Resume Session
```bash
python -m sgpt agent resume agent_xyz789
```

### Generate Report
```bash
python -m sgpt agent report agent_xyz789 -o report.md
```

---

## ⚙️ Configuration

Create `~/.sgpt/config.yaml`:

```yaml
llm:
  interface: gemini  # or openai, ollama
  temperature: 0.7

execution:
  timeout: 300

logging:
  console_level: INFO
  
safety:
  require_approval: true
  allowed_networks:
    - 192.168.1.0/24
```

---

## 🛡️ Safety

- **Human approval required** for every command
- **23 destructive patterns** blocked (rm -rf, mkfs, etc.)
- **Network restrictions** configurable
- **Full audit trail** of all operations

---

## 📊 Architecture

```
Agent Loop (THINK → PLAN → PROPOSE → EXECUTE → OBSERVE)
     ↓
State Management (Facts, Commands, Phase)
     ↓
Tool Registry (14 tools, 48 intents)
     ↓
Execution Tracker (Pending/Complete)
     ↓
Report Generator (Markdown)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

---

## 🧪 Testing

```bash
# Run E2E workflow test (mocked - safe)
python tests/test_e2e_workflow.py

# Test individual tools
python tests/test_kali_tools.py
```

---

## 📈 Project Stats

- **7,600 lines** of Python code
- **45 modules** across 8 packages
- **14 tools** with 48 intents
- **Complete documentation** (USAGE + ARCHITECTURE)
- **Production-grade** reliability

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---

## ⚠️ Disclaimer

**FOR AUTHORIZED TESTING ONLY**

This tool is designed for legitimate security testing and research. Only use on systems you own or have explicit permission to test. Unauthorized access to computer systems is illegal.

---

## 🙏 Acknowledgments

Built with:
- Python 3.8+
- Rich (CLI formatting)
- OpenAI/Gemini/Ollama (LLM interfaces)
- Kali Linux tools

---

**ShellGPT v2** - Professional autonomous penetration testing 🚀
