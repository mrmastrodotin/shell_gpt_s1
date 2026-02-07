"""
Main Agent Loop
Orchestrates the agent reasoning cycle
"""

from typing import Optional
from sgpt.agent.state import AgentState, RedTeamPhase, Command, Failure
from sgpt.agent.persistence import AgentPersistence
from datetime import datetime
import asyncio


class Agent:
    """Main red-team automation agent"""
    
    def __init__(
        self, 
        state: AgentState,
        persistence: AgentPersistence,
        llm_provider=None,
        tool_registry=None
    ):
        self.state = state
        self.persistence = persistence
        self.llm = llm_provider
        self.tool_registry = tool_registry
        
        # Initialize recovery system
        from sgpt.agent.recovery import StateRecovery
        self.recovery = StateRecovery(persistence)
        
        # Auto-detect tool availability
        if self.tool_registry and not self.state.tools_available:
            self._detect_available_tools()
            
    @classmethod
    def resume_from_session(cls, session_id: str, storage_path: "Path") -> "Agent":
        """Resume agent from existing session"""
        from pathlib import Path
        if isinstance(storage_path, str):
            storage_path = Path(storage_path)
            
        persistence = AgentPersistence(storage_path)
        state = persistence.load_state(session_id)
        
        if not state:
            raise ValueError(f"Session {session_id} not found")
            
        return cls(state=state, persistence=persistence)
    
    def _auto_save(self):
        """Auto-save state after each step"""
        if hasattr(self, 'recovery'):
            self.recovery.auto_save(self.state)
        else:
            # Fallback to basic save
            self.persistence.save_state(self.state)
    
    def _detect_available_tools(self):
        """Detect which tools are installed on the system"""
        from sgpt.tools.availability import ToolAvailabilityChecker
        
        availability = ToolAvailabilityChecker.check_all(self.tool_registry)
        self.state.tools_available = availability
        
        # Print summary
        available_count = sum(1 for v in availability.values() if v)
        total_count = len(availability)
        print(f"🔧 Tools available: {available_count}/{total_count}")
        
        # Warn about missing critical tools
        if not availability.get("nmap", False):
            print("⚠️  Warning: nmap not found - core reconnaissance disabled")
        
    async def run(self):
        """
        Main agent loop
        
        Cycle: Observe → Think → Plan → Propose → HIL Gate → Execute → Loop
        """
        print(f"\n🎯 Agent started: {self.state.goal}")
        print(f"📍 Phase: {self.state.phase.value}\n")
        
        while not self.state.done:
            try:
                # 1. Observe current state
                observation = self.observe()
                
                # 2. Think (internal reasoning)
                reasoning = await self.think(observation)
                
                # Check if goal is complete
                if reasoning.get("goal_satisfied"):
                    print("\n✅ Goal satisfied!")
                    self.state.done = True
                    self.persistence.save_state(self.state)
                    break
                
                # 3. Plan next action
                plan = await self.plan(reasoning)
                
                # Handle phase transitions
                if plan.get("should_transition"):
                    new_phase = RedTeamPhase(plan["next_phase"])
                    print(f"\n📍 Phase transition: {self.state.phase.value} → {new_phase.value}")
                    self.state.transition_phase(new_phase, plan.get("transition_reason", ""))
                
                # 4. Propose command
                command_proposal = await self.propose(plan)
                
                if not command_proposal:
                    print("\n⚠️  Agent unable to propose next step")
                    break
                
                # 5. Validate safety
                if not self.validate_command(command_proposal["command"]):
                    failure = Failure(
                        timestamp=datetime.now(),
                        command=command_proposal["command"],
                        reason="Safety validation failed",
                        phase=self.state.phase
                    )
                    self.state.add_failure(failure)
                    print(f"\n❌ Command rejected: {failure.reason}")
                    continue
                
                # 6. HIL Gate - human approval
                self.state.proposed_command = command_proposal["command"]
                self.state.proposed_reasoning = command_proposal["reasoning"]
                self.state.waiting_for_approval = True
                self.persistence.save_state(self.state)
                
                # Show approval prompt
                approval = await self.hil_gate(
                    command_proposal["command"],
                    command_proposal["reasoning"]
                )
                
                if approval["action"] == "stop":
                    print("\n🛑 Agent stopped by user")
                    self.state.done = True
                    break
                
                if approval["action"] == "reject":
                    print("\n⏭️  Command skipped")
                    continue
                
                # Use edited command if provided
                final_command = approval.get("command", command_proposal["command"])
                
                # Track tool for fact extraction
                self._last_tool = command_proposal.get("tool")
                
                # 7. Wait for execution
                print(f"\n⏳ Waiting for execution: sgpt run \"{final_command}\"")
                result = await self.wait_for_execution(final_command)
                
                # 8. Extract facts from result
                facts = await self.extract_facts(result)
                
                # Update state with new facts
                for key, value in facts.items():
                    if key == "hosts":
                        for host in value:
                            self.state.facts.add_host(host)
                    elif key == "targets":
                        for target_data in value:
                            from sgpt.agent.state import Target
                            target = Target(**target_data)
                            self.state.facts.add_target(target)
                
                # Record command
                cmd = Command(
                    timestamp=datetime.now(),
                    command=final_command,
                    phase=self.state.phase,
                    tool_used=command_proposal.get("tool", "unknown"),
                    exit_code=result.get("exit_code", 0),
                    output=result.get("output", ""),
                    facts_extracted=facts
                )
                self.state.add_command(cmd)
                
                # 9. Save checkpoint
                self.persistence.save_state(self.state)
                
            except KeyboardInterrupt:
                print("\n\n⏸️  Agent paused")
                self.state.waiting_for_approval = False
                self.persistence.save_state(self.state)
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                failure = Failure(
                    timestamp=datetime.now(),
                    command=self.state.proposed_command or "",
                    reason=str(e),
                    phase=self.state.phase
                )
                self.state.add_failure(failure)
                self.persistence.save_state(self.state)
                break
        
        print(f"\n📊 Agent session complete")
        print(f"   Steps: {self.state.total_steps}")
        print(f"   Hosts found: {len(self.state.facts.live_hosts)}")
        print(f"   Targets: {len(self.state.facts.targets)}")
    
    def observe(self) -> dict:
        """Gather current context and state"""
        return {
            "goal": self.state.goal,
            "phase": self.state.phase.value,
            "auto_context": self.state.auto_context,
            "facts": self.state.facts.to_dict(),
            "last_command": (
                self.state.commands_executed[-1].to_dict()
                if self.state.commands_executed
                else None
            ),
            "total_commands": len(self.state.commands_executed),
            "failures": len(self.state.failures)
        }
    
    async def think(self, observation: dict) -> dict:
        """
        LLM internal reasoning (hidden from user)
        
        Returns JSON with:
        - goal_satisfied: bool
        - last_command_success: bool
        - new_facts_discovered: list[str]
        - should_transition_phase: bool
        - next_phase: str | null
        - recommended_next_action: str
        """
        if not self.llm:
            # Fallback for testing without LLM
            if not observation["facts"]["live_hosts"] and observation["phase"] == "recon":
                return {
                    "goal_satisfied": False,
                    "last_command_success": True,
                    "new_facts_discovered": [],
                    "should_transition_phase": False,
                    "next_phase": None,
                    "recommended_next_action": "discover_hosts"
                }
            return {
                "goal_satisfied": False,
                "last_command_success": True,
                "new_facts_discovered": [],
                "should_transition_phase": False,
                "next_phase": None,
                "recommended_next_action": "continue"
            }
        
        # Use LLM for reasoning
        from sgpt.llm.prompts.think import ThinkPrompt, THINK_SCHEMA
        
        system_prompt, user_prompt = ThinkPrompt(observation)
        
        try:
            response = await self.llm.call(
                prompt=user_prompt,
                system_prompt=system_prompt,
                output_schema=THINK_SCHEMA,
                max_tokens=1000
            )
            
            self.state.llm_calls += 1
            self.state.tokens_used += self.llm.count_tokens(user_prompt + str(response))
            
            return response
            
        except Exception as e:
            print(f"\n⚠️  LLM Think failed: {e}")
            # Fallback to simple logic
            return {
                "goal_satisfied": False,
                "last_command_success": True,
                "new_facts_discovered": [],
                "should_transition_phase": False,
                "next_phase": None,
                "recommended_next_action": "continue",
                "confidence": "low",
                "reasoning": "LLM call failed, using fallback logic"
            }
    
    async def plan(self, reasoning: dict) -> dict:
        """
        Decide next objective
        
        Returns JSON with:
        - objective: str
        - should_transition: bool
        - next_phase: str | null
        """
        if not self.llm:
            # Fallback
            action = reasoning["recommended_next_action"]
            if action == "discover_hosts":
                return {
                    "objective": "Discover live hosts on network",
                    "should_transition": False,
                    "next_phase": None,
                    "intent": "host_discovery"
                }
            return {
                "objective": "Continue enumeration",
                "should_transition": False,
                "next_phase": None,
                "intent": "enumerate"
            }
        
        # Use LLM for planning
        from sgpt.llm.prompts.plan import PlanPrompt, PLAN_SCHEMA
        
        system_prompt, user_prompt = PlanPrompt(
            reasoning=reasoning,
            phase=self.state.phase.value,
            facts=self.state.facts.to_dict(),
            goal=self.state.goal
        )
        
        try:
            response = await self.llm.call(
                prompt=user_prompt,
                system_prompt=system_prompt,
                output_schema=PLAN_SCHEMA,
                max_tokens=800
            )
            
            self.state.llm_calls += 1
            self.state.tokens_used += self.llm.count_tokens(user_prompt + str(response))
            
            return response
            
        except Exception as e:
            print(f"\n⚠️  LLM Plan failed: {e}")
            return {
                "objective": "Continue current phase",
                "should_transition": False,
                "next_phase": None,
                "intent": "continue",
                "rationale": "LLM call failed"
            }
    
    async def propose(self, plan: dict) -> Optional[dict]:
        """
        Generate command using tool registry
        
        Returns:
        {
            "command": str,
            "reasoning": str,
            "tool": str
        }
        """
        # Get eligible tools for current phase
        eligible_tools = self.tool_registry.get_for_phase(self.state.phase)
        
        # Filter by availability
        available_tools = [
            t for t in eligible_tools 
            if self.state.tools_available.get(t.binary, False)
        ]
        
        if not available_tools:
            print(f"\n⚠️  No tools available for phase: {self.state.phase.value}")
            return None
        
        if not self.llm:
            # Fallback
            if plan["intent"] == "host_discovery":
                subnet = self.state.auto_context.get("network", {}).get("subnet", "192.168.0.0/24")
                return {
                    "command": f"nmap -sn {subnet}",
                    "reasoning": "No live hosts discovered yet. Starting with ping scan.",
                    "tool": "nmap"
                }
            return None
        
        # Use LLM for tool selection
        from sgpt.llm.prompts.propose import ProposePrompt, PROPOSE_SCHEMA
        
        system_prompt, user_prompt = ProposePrompt(
            plan=plan,
            available_tools=available_tools,
            facts=self.state.facts.to_dict(),
            auto_context=self.state.auto_context
        )
        
        try:
            response = await self.llm.call(
                prompt=user_prompt,
                system_prompt=system_prompt,
                output_schema=PROPOSE_SCHEMA,
                max_tokens=600
            )
            
            self.state.llm_calls += 1
            self.state.tokens_used += self.llm.count_tokens(user_prompt + str(response))
            
            # Get selected tool
            tool_name = response.get("tool_name")
            tool = self.tool_registry.get(tool_name)
            
            if not tool:
                print(f"\n⚠️  Tool not found: {tool_name}")
                return None
            
            # Generate command using tool
            command = tool.generate_command(
                intent=response.get("action"),
                context=self.state.auto_context,
                facts=self.state.facts.to_dict()
            )
            
            if not command:
                print(f"\n⚠️  Tool could not generate command for action: {response.get('action')}")
                return None
            
            return {
                "command": command,
                "reasoning": response.get("reasoning", ""),
                "tool": tool_name,
                "expected_outcome": response.get("expected_outcome", "")
            }
            
        except Exception as e:
            print(f"\n⚠️  LLM Propose failed: {e}")
            return None
    
    def validate_command(self, command: str) -> bool:
        """
        Safety validation (non-LLM)
        
        Checks:
        - Not in destructive commands list
        - No privilege escalation without approval
        - No suspicious patterns
        """
        from sgpt.tools.safety import SafetyValidator
        
        # Validate safety
        is_safe, reason = SafetyValidator.validate(command)
        
        if not is_safe:
            print(f"\n❌ Safety check failed: {reason}")
            return False
        
        # Check if requires special approval
        requires_approval, approval_reason = SafetyValidator.requires_approval(command)
        
        if requires_approval:
            print(f"\n⚠️  Command requires approval: {approval_reason}")
            # In future, could prompt for extra confirmation
        
        return True
    
    async def hil_gate(self, command: str, reasoning: str) -> dict:
        """
        Human-in-the-loop approval gate
        
        Shows command and waits for approval
        
        Returns:
        {
            "action": "approve" | "reject" | "stop",
            "command": str (if edited)
        }
        """
        # Rich formatted output
        print(f"\n{'─' * 60}")
        print(f"[Agent | phase: {self.state.phase.value}]")
        print(f"\nProposed command:")
        print(f"  {command}")
        print(f"\nReason:")
        print(f"  {reasoning}")
        print(f"\nApprove?")
        print(f"  y - run")
        print(f"  e - edit")
        print(f"  n - skip")
        print(f"  q - stop agent")
        print(f"{'─' * 60}")
        
        choice = input("\n> ").strip().lower()
        
        if choice == "y":
            return {"action": "approve", "command": command}
        elif choice == "e":
            edited = input("Edit command: ").strip()
            return {"action": "approve", "command": edited}
        elif choice == "n":
            return {"action": "reject"}
        else:
            return {"action": "stop"}
    
    async def wait_for_execution(self, command: str) -> dict:
        """
        Wait for human to execute command via sgpt run
        
        Returns command result
        """
        from sgpt.agent.execution import ExecutionTracker
        
        # Initialize execution tracker
        if not hasattr(self, 'execution_tracker'):
            storage_path = self.persistence.storage_path.parent
            self.execution_tracker = ExecutionTracker(storage_path)
        
        # Submit command for execution
        exec_id = self.execution_tracker.submit_command(
            session_id=self.state.session_id,
            command=command,
            tool=getattr(self, '_last_tool', 'unknown'),
            phase=self.state.phase.value
        )
        
        print(f"\n📋 Execution ID: {exec_id}")
        print(f"⏳ Run: sgpt run {exec_id}")
        print(f"   Or: sgpt run \"{command}\"")
        
        # Poll for completion
        print("\n⏳ Waiting for execution...", end='', flush=True)
        
        import time
        max_wait = 300  # 5 minutes max
        elapsed = 0
        
        while elapsed < max_wait:
            await asyncio.sleep(2)
            elapsed += 2
            
            status_data = self.execution_tracker.get_status(exec_id)
            
            if status_data and status_data["status"] in ["complete", "failed"]:
                print(" ✅")
                
                return {
                    "command": command,
                    "exit_code": status_data.get("exit_code", 0),
                    "output": status_data.get("output", ""),
                    "success": status_data.get("exit_code", 0) == 0
                }
            
            # Show progress
            if elapsed % 10 == 0:
                print(".", end='', flush=True)
        
        # Timeout
        print(" ⏱️ Timeout")
        return {
            "command": command,
            "exit_code": -1,
            "output": "",
            "success": False
        }
    
    async def extract_facts(self, result: dict) -> dict:
        """
        Extract structured facts from command output
        
        Returns dict of extracted facts
        """
        output = result.get("output", "")
        command = result.get("command", "")
        
        # Try tool-specific parser first
        if hasattr(self, '_last_tool') and self._last_tool:
            tool = self.tool_registry.get(self._last_tool)
            if tool:
                try:
                    return tool.parse_output(output)
                except Exception as e:
                    print(f"\n⚠️  Tool parser failed: {e}")
        
        if not self.llm:
            # Fallback
            if "hosts found" in output.lower():
                return {
                    "hosts": ["192.168.0.1", "192.168.0.10", "192.168.0.20"]
                }
            return {}
        
        # Use LLM for fact extraction
        from sgpt.llm.prompts.summarize import SummarizePrompt, SUMMARIZE_SCHEMA
        
        system_prompt, user_prompt = SummarizePrompt(
            command=command,
            output=output,
            tool_name=getattr(self, '_last_tool', 'unknown')
        )
        
        try:
            response = await self.llm.call(
                prompt=user_prompt,
                system_prompt=system_prompt,
                output_schema=SUMMARIZE_SCHEMA,
                max_tokens=1500
            )
            
            self.state.llm_calls += 1
            self.state.tokens_used += self.llm.count_tokens(user_prompt[:500] + str(response))
            
            # Remove metadata fields
            facts = {
                "hosts": response.get("hosts", []),
                "targets": response.get("targets", []),
                "vulnerabilities": response.get("vulnerabilities", [])
            }
            
            return facts
            
        except Exception as e:
            print(f"\n⚠️  LLM Extract failed: {e}")
            return {}
