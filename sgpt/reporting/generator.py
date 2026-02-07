"""
Session Report Generator
Generate comprehensive markdown reports from agent sessions
"""

from sgpt.agent.state import AgentState
from datetime import datetime
from pathlib import Path


class ReportGenerator:
    """Generate markdown reports from agent sessions"""
    
    @staticmethod
    def generate(state: AgentState, output_path: Path = None) -> str:
        """
        Generate full markdown report
        
        Args:
            state: Agent state
            output_path: Optional path to save report
            
        Returns:
            Markdown report string
        """
        sections = []
        
        # Header
        sections.append(ReportGenerator._generate_header(state))
        
        # Executive Summary
        sections.append(ReportGenerator._generate_summary(state))
        
        # Timeline
        sections.append(ReportGenerator._generate_timeline(state))
        
        # Discovered Assets
        sections.append(ReportGenerator._generate_assets(state))
        
        # Vulnerabilities
        if state.facts.vulnerabilities:
            sections.append(ReportGenerator._generate_vulnerabilities(state))
        
        # Credentials
        if state.facts.credentials:
            sections.append(ReportGenerator._generate_credentials(state))
        
        # Recommendations
        sections.append(ReportGenerator._generate_recommendations(state))
        
        # Appendix
        sections.append(ReportGenerator._generate_appendix(state))
        
        # Combine all sections
        report = "\n\n---\n\n".join(sections)
        
        # Save if path provided
        if output_path:
            output_path.write_text(report, encoding='utf-8')
        
        return report
    
    @staticmethod
    def _generate_header(state: AgentState) -> str:
        """Generate report header"""
        duration = ""
        if state.commands_executed:
            start_time = state.created_at
            last_cmd_time = state.commands_executed[-1].timestamp
            duration_delta = last_cmd_time - start_time
            hours = duration_delta.total_seconds() / 3600
            duration = f"{hours:.1f} hours"
        
        return f"""# Red-Team Assessment Report

**Session ID:** `{state.session_id}`  
**Goal:** {state.goal}  
**Phase:** {state.phase.value.upper()}  
**Duration:** {duration}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
"""
    
    @staticmethod
    def _generate_summary(state: AgentState) -> str:
        """Generate executive summary"""
        summary = f"""## Executive Summary

This report documents an automated red-team assessment conducted by ShellGPT v2.

**Objective:** {state.goal}

**Results:**
- **Hosts Discovered:** {len(state.facts.live_hosts)}
- **Targets Identified:** {len(state.facts.targets)}
- **Open Ports:** {sum(len(t.ports) for t in state.facts.targets)}
- **Vulnerabilities Found:** {len(state.facts.vulnerabilities)}
- **Credentials Captured:** {len(state.facts.credentials)}
- **Commands Executed:** {len(state.commands_executed)}
- **Failed Attempts:** {len(state.failures)}

**Status:** {"✅ COMPLETE" if state.done else "🔵 IN PROGRESS"}
"""
        return summary
    
    @staticmethod
    def _generate_timeline(state: AgentState) -> str:
        """Generate command timeline"""
        timeline = "## Command Timeline\n\n"
        
        if not state.commands_executed:
            timeline += "*No commands executed yet.*\n"
            return timeline
        
        timeline += "| # | Time | Phase | Command | Status |\n"
        timeline += "|---|------|-------|---------|--------|\n"
        
        for i, cmd in enumerate(state.commands_executed, 1):
            time_str = cmd.timestamp.strftime('%H:%M:%S')
            phase_str = cmd.phase.value[:4].upper()
            command_str = cmd.command[:50] + "..." if len(cmd.command) > 50 else cmd.command
            status_str = "✅ OK" if cmd.exit_code == 0 else f"❌ {cmd.exit_code}"
            
            timeline += f"| {i} | {time_str} | {phase_str} | `{command_str}` | {status_str} |\n"
        
        return timeline
    
    @staticmethod
    def _generate_assets(state: AgentState) -> str:
        """Generate discovered assets section"""
        assets = "## Discovered Assets\n\n"
        
        if not state.facts.targets:
            assets += "*No targets identified yet.*\n"
            return assets
        
        assets += "### Targets\n\n"
        
        for target in state.facts.targets:
            assets += f"#### {target.ip}"
            if target.hostname:
                assets += f" ({target.hostname})"
            assets += "\n\n"
            
            # Ports
            if target.ports:
                assets += f"**Open Ports:** {', '.join(map(str, sorted(target.ports)))}\n\n"
            
            # Services
            if target.services:
                assets += "**Services:**\n"
                for port, service in sorted(target.services.items()):
                    assets += f"- Port {port}: {service}\n"
                assets += "\n"
            
            # OS
            if target.os:
                assets += f"**Operating System:** {target.os}\n\n"
            
            # Vulnerabilities
            if target.vulnerabilities:
                assets += f"**Vulnerabilities:** {len(target.vulnerabilities)} found\n\n"
        
        return assets
    
    @staticmethod
    def _generate_vulnerabilities(state: AgentState) -> str:
        """Generate vulnerabilities section"""
        vulns = "## Vulnerabilities\n\n"
        
        # Group by severity
        by_severity = {}
        for vuln in state.facts.vulnerabilities:
            severity = vuln.severity.lower()
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(vuln)
        
        # Sort by severity
        severity_order = ['critical', 'high', 'medium', 'low', 'unknown']
        
        for severity in severity_order:
            if severity not in by_severity:
                continue
            
            severity_vulns = by_severity[severity]
            icon = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢',
                'unknown': '⚪'
            }.get(severity, '⚪')
            
            vulns += f"### {icon} {severity.upper()} Severity ({len(severity_vulns)})\n\n"
            
            for vuln in severity_vulns:
                vulns += f"**{vuln.name}**"
                if vuln.cve_id:
                    vulns += f" ({vuln.cve_id})"
                vulns += "\n\n"
                
                vulns += f"- **Target:** {vuln.target}"
                if vuln.port:
                    vulns += f":{vuln.port}"
                vulns += "\n"
                
                if vuln.description:
                    vulns += f"- **Description:** {vuln.description}\n"
                
                if vuln.exploit_available:
                    vulns += "- **Exploit:** ⚠️ PUBLIC EXPLOIT AVAILABLE\n"
                
                vulns += "\n"
        
        return vulns
    
    @staticmethod
    def _generate_credentials(state: AgentState) -> str:
        """Generate credentials section"""
        creds = "## 🔐 Captured Credentials\n\n"
        
        creds += "> ⚠️ **CONFIDENTIAL** - Handle with care\n\n"
        
        creds += "| Host | Username | Password |\n"
        creds += "|------|----------|----------|\n"
        
        for cred in state.facts.credentials:
            host = cred.get('host', 'unknown')
            username = cred.get('username', 'unknown')
            password = cred.get('password', 'unknown')
            creds += f"| {host} | {username} | `{password}` |\n"
        
        creds += "\n"
        return creds
    
    @staticmethod
    def _generate_recommendations(state: AgentState) -> str:
        """Generate recommendations"""
        recs = "## Recommendations\n\n"
        
        # Based on findings
        if state.facts.vulnerabilities:
            high_severity = [v for v in state.facts.vulnerabilities 
                           in ('critical', 'high')]
            
            if high_severity:
                recs += "### Immediate Actions\n\n"
                recs += "1. **Patch Critical Vulnerabilities:** Address high/critical severity issues immediately\n"
                recs += f"2. **Review {len(high_severity)} High-Risk Findings:** Prioritize remediation\n\n"
        
        if state.facts.credentials:
            recs += "### Security Improvements\n\n"
            recs += "1. **Strengthen Passwords:** Implement password complexity requirements\n"
            recs += "2. **Enable MFA:** Deploy multi-factor authentication\n"
            recs += "3. **Review Access Controls:** Audit user permissions\n\n"
        
        # General recommendations
        recs += "### General\n\n"
        recs += "1. **Regular Scanning:** Implement continuous security monitoring\n"
        recs += "2. **Patch Management:** Establish systematic patching process\n"
        recs += "3. **Network Segmentation:** Isolate critical assets\n"
        recs += "4. **Security Training:** Educate staff on security best practices\n"
        
        return recs
    
    @staticmethod
    def _generate_appendix(state: AgentState) -> str:
        """Generate appendix"""
        appendix = "## Appendix\n\n"
        
        appendix += "### Tools Used\n\n"
        tools_used = set()
        for cmd in state.commands_executed:
            tools_used.add(cmd.tool_used)
        
        for tool in sorted(tools_used):
            appendix += f"- {tool}\n"
        
        appendix += "\n### Phase Transitions\n\n"
        
        if state.phase_history:
            for trans in state.phase_history:
                time_str = trans.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                appendix += f"- **{time_str}:** {trans.from_phase.value} → {trans.to_phase.value}\n"
                appendix += f"  - Reason: {trans.reason}\n"
        else:
            appendix += "*No phase transitions yet.*\n"
        
        appendix += "\n---\n\n"
        appendix += "*Report generated by ShellGPT v2 - Red-Team Automation Agent*\n"
        
        return appendix
