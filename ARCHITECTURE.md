# ShellGPT v2 - Architecture Documentation

System architecture and design documentation for ShellGPT v2.

---

## 🏗️ System Overview

ShellGPT v2 is an **autonomous red-team automation agent** that combines:
- LLM-powered reasoning for decision making
- Tool orchestration for security testing
- Human-in-the-loop approval for safety
- Persistent state management
- Professional reporting

**Total:** ~6,400 lines across 38+ modules

---

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      CLI Layer                          │
│  (User commands: agent, run, tools, config, report)     │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                   Agent Loop                            │
│  ┌─────────┐  ┌──────┐  ┌────────┐  ┌────────────┐     │
│  │  THINK  │→ │ PLAN │→ │PROPOSE │→ │  EXECUTE   │     │
│  └─────────┘  └──────┘  └────────┘  └────────────┘     │
│       ↑                                     │            │
│       │                                     ▼            │
│  ┌─────────┐                          ┌─────────┐       │
│  │ OBSERVE │ ←────────────────────────│ RESULTS │       │
│  └─────────┘                          └─────────┘       │
└────────────────┬────────────────────────────────────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
┌─────▼──────┐    ┌────────▼────────┐
│  LLM Layer │    │   Tool Registry │
│            │    │                 │
│ AsyncLLM   │    │  8 Tools:       │
│ Handler    │    │  - nmap         │
│            │    │  - gobuster     │
│ Retry      │    │  - nikto        │
│ & Fallback │    │  - etc...       │
└────────────┘    └─────────────────┘
      │                     │
┌─────▼─────────────────────▼────────┐
│       Storage & State Layer        │
│                                    │
│  ┌──────────┐  ┌────────────────┐  │
│  │  State   │  │   Execution    │  │
│  │Persistence│  │    Tracker     │  │
│  └──────────┘  └────────────────┘  │
│                                    │
│  ┌──────────┐  ┌────────────────┐  │
│  │  Facts   │  │     Logs       │  │
│  │  Merger  │  │  (3 formats)   │  │
│  └──────────┘  └────────────────┘  │
└────────────────────────────────────┘
```

---

## 🧠 Core Components

### 1. Agent Loop (`sgpt/agent/loop.py`)

**Purpose**: Main orchestration engine

**Cycle**:
1. **THINK** - Analyze current state, check if goal satisfied
2. **PLAN** - Determine next objective and intent
3. **PROPOSE** - Generate specific command for execution
4. **APPROVE** - Human-in-the-loop gate
5. **EXECUTE** - Track command execution
6. **OBSERVE** - Extract facts from results
7. **Loop** - Return to THINK

**Key Methods**:
- `run()` - Main loop
- `think()` - LLM-powered analysis
- `plan()` - Intent selection
- `propose()` - Command generation
- `observe()` - Fact extraction

**Size**: ~600 lines

---

### 2. State Management (`sgpt/agent/state.py`)

**Purpose**: Track agent state across sessions

**State Components**:
```python
class AgentState:
    session_id: str
    goal: str
    phase: RedTeamPhase
    facts: FactDatabase
    commands_executed: List[Command]
    failures: List[Error]
    done: bool
```

**Phases**:
- `recon` - Initial reconnaissance
- `enumeration` - Detailed enumeration
- `vulnerability` - Vulnerability assessment  
- `exploitation` - Exploitation attempts

**Size**: ~300 lines

---

### 3. LLM Integration (`sgpt/llm/async_handler.py`)

**Purpose**: Bridge synchronous v1 LLM handlers with async agent

**Features**:
- ThreadPoolExecutor for async/sync bridging
- Retry with exponential backoff (3 attempts)
- Fallback responses on failure
- JSON extraction from markdown
- Support for all v1 interfaces (OpenAI, Gemini, Ollama)

**Methods**:
- `generate()` - Async text generation with retry
- `generate_json()` - JSON response extraction
- `_get_fallback_response()` - Fallback when LLM fails

**Size**: ~270 lines

---

### 4. Tool Registry (`sgpt/tools/registry.py`)

**Purpose**: Central tool management and discovery

**Features**:
- Auto-loading from `specs/` directory
- Tool availability checking
- Intent-to-tool mapping
- Category organization

**Tool Structure**:
```python
class BaseTool:
    name: str
    category: ToolCategory
    intents: List[str]
    
    def build_command(params) -> str
    def validate_params(params) -> bool
```

**Size**: ~140 lines

---

### 5. Execution Tracker (`sgpt/agent/execution.py`)

**Purpose**: Track real command execution

**Workflow**:
1. Agent submits command → receives `exec_id`
2. User runs `sgpt run exec_id`
3. Command executes, results saved
4. Agent polls for completion
5. Results returned to agent

**States**:
- `PENDING` - Awaiting execution
- `RUNNING` - Currently executing
- `COMPLETE` - Finished (success or failure)

**Storage**:
```
~/.sgpt/agent_sessions/{session_id}/executions/
├── pending/
│   └── exec_abc123.json
└── complete/
    └── exec_abc123.json
```

**Size**: ~230 lines

---

### 6. Safety Validator (`sgpt/tools/safety.py`)

**Purpose**: Prevent destructive commands

**Validation Layers**:
1. **Pattern Matching** - 23 destructive patterns
2. **Flag Whitelisting** - Only allow known-safe flags
3. **Network Restrictions** - Limit to allowed subnets
4. **Human Approval** - Final gate

**Blocked Patterns**:
- File destruction: `rm -rf`, `mkfs`, `dd`
- Privilege escalation: `sudo`, `chmod 777`
- Network attacks: `iptables DROP`, `route del`
- Data exfiltration: `nc -e`, `curl upload`

**Size**: ~400 lines

---

### 7. Fact Merger (`sgpt/agent/fact_merger.py`)

**Purpose**: Intelligent fact consolidation

**Features**:
- **Host Deduplication** - Merge IPs, hostnames, DNS
- **Target Consolidation** - Prevent duplicate targeting
- **Vulnerability Deduplication** - Merge by type + CVE
- **Credential Tracking** - Unique credentials only

**Algorithms**:
- IP normalization
- Hostname canonicalization
- CVE-based dedup
- Hash-based comparison

**Size**: ~250 lines

---

### 8. Report Generator (`sgpt/reporting/generator.py`)

**Purpose**: Professional markdown reports

**Report Sections**:
1. **Executive Summary** - High-level overview
2. **Scope & Timeline** - What was tested, when
3. **Summary Statistics** - Counts and metrics
4. **Command History** - What was executed
5. **Discovered Assets** - Hosts, ports, services
6. **Vulnerabilities** - By severity with details
7. **Recommendations** - Security improvements

**Size**: ~280 lines

---

## 🔄 Data Flow

### Agent Decision Cycle

```
State → THINK → Decision
            ↓
         Is goal satisfied?
            ↓
    ┌───────┴──────┐
    │              │
   Yes            No
    │              │
    │           PLAN → Intent
    │              ↓
    │           PROPOSE → Command
    │              ↓
    │           VALIDATE → Safe?
    │              ↓
    │           APPROVE → Human OK?
    │              ↓
    │           EXECUTE → Submit
    │              ↓
    │           WAIT → Poll status
    │              ↓
    │           OBSERVE → Extract facts
    │              ↓
    └──────────> Update State
                   ↓
                Auto-save
```

### Execution Flow

```
Agent                User                Tracker
  │                   │                    │
  ├─ submit() ────────┼──────────────────> │
  │                   │                    ├─ create pending
  │ <─ exec_id ───────┼──────────────────┤ │
  │                   │                    │
  │                   ├─ sgpt run id ────> │
  │                   │                    ├─ mark running
  │                   │                    ├─ execute command
  │                   │                    ├─ save result
  │                   │                    ├─ move to complete
  │                   │                    │
  ├─ check() ─────────┼──────────────────> │
  │ <─ RUNNING ───────┼──────────────────┤ │
  │                   │                    │
  ├─ check() ─────────┼──────────────────> │
  │ <─ COMPLETE ──────┼──────────────────┤ │
  │ <─ result ────────┼──────────────────┤ │
  │                   │                    │
```

---

## 🛠️ Tool Architecture

### Tool Specification

Each tool implements `BaseTool`:

```python
class NmapTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="nmap",
            category=ToolCategory.DISCOVERY,
            intents=[
                "host_discovery",
                "port_scan",
                "service_detection",
                "os_detection",
                "script_scan"
            ]
        )
    
    def build_command(self, intent, params):
        # Generate nmap command
        if intent == "host_discovery":
            return f"nmap -sn {params['subnet']}"
        elif intent == "port_scan":
            return f"nmap -p {params['ports']} {params['target']}"
        # ... more intents
    
    def validate_params(self, intent, params):
        # Validate parameters
        required = self.get_spec(intent)['parameters']
        return all(k in params for k in required)
```

### Intent System

Intents map high-level goals to specific tool actions:

```python
# Agent thinks: "Need to discover hosts"
# Planner selects intent: "host_discovery"
# Proposer picks tool: "nmap"
# Tool builds command: "nmap -sn 192.168.1.0/24"
```

### Available Tools

| Tool | Category | Intents | Description |
|------|----------|---------|-------------|
| nmap | Discovery | 5 | Network scanning |
| curl | Web | 4 | HTTP requests |
| gobuster | Web | 3 | Directory brute-force |
| nikto | Web | 2 | Vuln scanning |
| enum4linux | Enumeration | 4 | SMB enumeration |
| hydra | Exploitation | 4 | Password attacks |
| whatweb | Web | 3 | Tech fingerprinting |
| python_script | Scripting | 4 | Custom scripts |

---

## 🧪 LLM Prompt Chain

### 1. THINK Prompt

**Purpose**: Analyze state and decide if goal is satisfied

**Input**: Current state, facts, goal, executed commands

**Output**: JSON with `goal_satisfied`, `should_transition`, `reasoning`

**Example**:
```json
{
  "goal_satisfied": false,
  "should_transition": false,
  "reasoning": "Need to discover live hosts first"
}
```

### 2. PLAN Prompt

**Purpose**: Determine next objective and intent

**Input**: Current phase, available facts, goal

**Output**: JSON with `objective`, `intent`

**Example**:
```json
{
  "objective": "Discover live hosts in subnet",
  "intent": "host_discovery"
}
```

### 3. PROPOSE Prompt

**Purpose**: Generate specific command

**Input**: Intent, available tools, target info

**Output**: JSON with `tool`, `action`, `parameters`

**Example**:
```json
{
  "tool": "nmap",
  "action": "host_discovery",
  "parameters": {"subnet": "192.168.1.0/24"}
}
```

### 4. SUMMARIZE Prompt

**Purpose**: Extract structured facts from command output

**Input**: Command, raw output

**Output**: JSON with discovered facts

**Example**:
```json
{
  "hosts": ["192.168.1.1", "192.168.1.10"],
  "confidence": "high"
}
```

---

## 💾 Storage Architecture

### Directory Structure

```
~/.sgpt/
├── config.yaml              # User configuration
├── agent_sessions/
│   └── {session_id}/
│       ├── state.json       # Current state
│       ├── backups/         # State backups
│       └── executions/
│           ├── pending/     # Awaiting execution
│           └── complete/    # Execution results
├── logs/
│   ├── sgpt.log            # Main log
│   ├── sgpt_structured.json # JSON log
│   └── sgpt.log.{date}     # Archived logs
└── reports/
    └── {session_id}.md     # Generated reports
```

### State Persistence

**File**: `state.json`

**Format**:
```json
{
  "session_id": "agent_abc123",
  "goal": "Enumerate network",
  "phase": "enumeration",
  "facts": {
    "live_hosts": [...],
    "open_ports": [...],
    "vulnerabilities": [...]
  },
  "commands_executed": [...],
  "done": false
}
```

**Backup Strategy**:
- Auto-backup after each step
- Keep last 10 backups
- Timestamped filenames

---

## 🔒 Security Features

### Defense in Depth

1. **Safety Validation** - Block 23 destructive patterns
2. **Flag Whitelisting** - Only known-safe flags allowed
3. **Network Restrictions** - Configurable allowed subnets
4. **Human Approval** - Every command requires consent
5. **Execution Tracking** - Full audit trail
6. **Read-only Filesystem** - Agent can't write files (except state)

### Safety Patterns

See `sgpt/tools/safety.py` for complete list:
- Destructive file operations
- Privilege escalation
- Network manipulation
- Data exfiltration
- Service disruption

---

## 📊 Error Handling

### Retry Logic

**Component**: `RetryHandler`

**Strategy**: Exponential backoff

```python
delay = base_delay * (2 ** attempt)
# Attempt 1: 2s
# Attempt 2: 4s  
# Attempt 3: 8s
```

### Recovery System

**Component**: `StateRecovery`

**Features**:
- State validation
- Automatic backups
- Corruption detection
- Rollback capability

### LLM Failures

**Handling**:
1. Retry 3x with backoff
2. If still fails → fallback response
3. Log error for debugging
4. Continue gracefully

---

## 📈 Scalability Considerations

### Current Limits

- **Max Pending Executions**: 10 (configurable)
- **Execution Timeout**: 300s (configurable)
- **Log File Size**: 10MB with rotation
- **Backup Retention**: 10 per session

### Performance

- **LLM Calls**: Async with ThreadPoolExecutor
- **State Persistence**: JSON (fast for small states)
- **Tool Detection**: Cached on startup
- **Fact Merging**: O(n) deduplication

### Future Optimizations

- Use SQLite for large fact databases
- Parallel tool execution
- Distributed agent coordination
- Cached LLM responses

---

## 🔌 Extension Points

### Adding New Tools

1. Create `sgpt/tools/specs/newtool.py`
2. Extend `BaseTool` class
3. Implement `build_command()` and `validate_params()`
4. Auto-loaded by registry

### Adding New Intents

1. Add to tool's `intents` list
2. Implement intent in `build_command()`
3. Update prompt context if needed

### Custom LLM Providers

1. Implement v1 handler interface
2. Add to `async_handler.py` factory
3. Configure via `config.yaml`

---

## 🎯 Design Principles

1. **Modularity** - Components are independent
2. **Extensibility** - Easy to add tools/intents
3. **Safety First** - Multiple validation layers
4. **Observability** - Comprehensive logging
5. **Reliability** - Retry, recovery, fallbacks
6. **User Control** - Human-in-the-loop always

---

## 📚 Key Technologies

- **Python 3.8+** - Core language
- **asyncio** - Async/await for non-blocking
- **Rich** - Beautiful CLI formatting
- **YAML** - Configuration management
- **JSON** - State persistence
- **ThreadPoolExecutor** - LLM async bridge

---

**Total Architecture:** ~6,400 lines across 38+ modules, production-ready! 🚀
