"""
Fact Merger
Intelligently merge facts from multiple tool executions
"""

from sgpt.agent.state import AgentState, Target, Vulnerability, FactStore
from typing import Dict, List, Any
from datetime import datetime


class FactMerger:
    """Merge facts from different sources intelligently"""
    
    @staticmethod
    def merge(fact_store: FactStore) -> FactStore:
        """
        Deduplicate and clean up fact store
        
        Args:
            fact_store: FactStore to clean
            
        Returns:
            Cleaned FactStore
        """
        # Deduplicate live hosts
        fact_store.live_hosts = list(set(fact_store.live_hosts))
        
        # Deduplicate targets (by IP)
        unique_targets = {}
        for t in fact_store.targets:
            if t.ip not in unique_targets:
                unique_targets[t.ip] = t
            else:
                # Merge logic if needed, for now just keep first or overwrite?
                # Let's keep existing logic assume already merged via add_target
                pass
        fact_store.targets = list(unique_targets.values())
        
        return fact_store

    @staticmethod
    def merge_into_state(state: AgentState, new_facts: Dict[str, Any]):
        """
        Merge new facts into agent state
        
        Args:
            state: Current agent state
            new_facts: New facts extracted from tool output
        """
        
        # Merge hosts
        if "hosts" in new_facts:
            FactMerger.merge_hosts(state.facts, new_facts["hosts"])
        
        # Merge targets
        if "targets" in new_facts:
            FactMerger.merge_targets(state.facts, new_facts["targets"])
        
        # Merge vulnerabilities
        if "vulnerabilities" in new_facts:
            FactMerger.merge_vulnerabilities(state.facts, new_facts["vulnerabilities"])
        
        # Merge credentials
        if "credentials" in new_facts:
            FactMerger.merge_credentials(state.facts, new_facts["credentials"])
        
        # Merge services
        if "services" in new_facts:
            FactMerger.merge_services(state.facts, new_facts["services"])
        
        # Merge custom facts
        for key, value in new_facts.items():
            if key not in ["hosts", "targets", "vulnerabilities", "credentials", "services"]:
                state.facts.custom_facts[key] = value
    
    @staticmethod
    def merge_hosts(fact_store: FactStore, new_hosts: List[str]):
        """
        Merge new hosts, deduplicate
        
        Args:
            fact_store: Current fact store
            new_hosts: New host IPs to add
        """
        for host in new_hosts:
            if host and host not in fact_store.live_hosts:
                fact_store.live_hosts.append(host)
    
    @staticmethod
    def merge_targets(fact_store: FactStore, new_targets: List[Dict]):
        """
        Merge target information
        
        For existing targets, update ports and services.
        For new targets, create new Target objects.
        
        Args:
            fact_store: Current fact store
            new_targets: New target data
        """
        for new_target_data in new_targets:
            ip = new_target_data.get("ip")
            if not ip:
                continue
            
            # Find existing target
            existing_target = next(
                (t for t in fact_store.targets if t.ip == ip),
                None
            )
            
            if existing_target:
                # Update existing target
                FactMerger._update_target(existing_target, new_target_data)
            else:
                # Create new target
                new_target = FactMerger._create_target(new_target_data)
                fact_store.targets.append(new_target)
                
                # Also add to live_hosts if not present
                if ip not in fact_store.live_hosts:
                    fact_store.live_hosts.append(ip)
    
    @staticmethod
    def _update_target(target: Target, new_data: Dict):
        """Update existing target with new data"""
        
        # Merge ports (deduplicate)
        if "ports" in new_data:
            for port in new_data["ports"]:
                if port not in target.ports:
                    target.ports.append(port)
            target.ports.sort()  # Keep sorted
        
        # Merge services (prefer newer data)
        if "services" in new_data:
            target.services.update(new_data["services"])
        
        # Update hostname if provided and not already set
        if "hostname" in new_data and new_data["hostname"]:
            if not target.hostname:
                target.hostname = new_data["hostname"]
        
        # Update OS if provided and not already set
        if "os" in new_data and new_data["os"]:
            if not target.os:
                target.os = new_data["os"]
        
        # Merge vulnerabilities
        if "vulnerabilities" in new_data:
            for vuln in new_data["vulnerabilities"]:
                if vuln not in target.vulnerabilities:
                    target.vulnerabilities.append(vuln)
    
    @staticmethod
    def _create_target(data: Dict) -> Target:
        """Create new Target from dict"""
        return Target(
            ip=data.get("ip"),
            hostname=data.get("hostname"),
            ports=data.get("ports", []),
            services=data.get("services", {}),
            os=data.get("os"),
            vulnerabilities=data.get("vulnerabilities", [])
        )
    
    @staticmethod
    def merge_vulnerabilities(fact_store: FactStore, new_vulns: List[Dict]):
        """
        Merge vulnerabilities, deduplicate
        
        Vulnerabilities are considered duplicates if they have:
        - Same CVE ID (if present), OR
        - Same name + target + port
        
        Args:
            fact_store: Current fact store
            new_vulns: New vulnerability data
        """
        for new_vuln_data in new_vulns:
            # Create Vulnerability object
            new_vuln = Vulnerability(
                cve_id=new_vuln_data.get("cve_id"),
                name=new_vuln_data.get("name", "Unknown"),
                severity=new_vuln_data.get("severity", "unknown"),
                target=new_vuln_data.get("target", "unknown"),
                port=new_vuln_data.get("port"),
                description=new_vuln_data.get("description", ""),
                exploit_available=new_vuln_data.get("exploit_available", False)
            )
            
            # Check for duplicates
            is_duplicate = False
            
            for existing_vuln in fact_store.vulnerabilities:
                # Match by CVE ID
                if new_vuln.cve_id and new_vuln.cve_id == existing_vuln.cve_id:
                    is_duplicate = True
                    break
                
                # Match by name + target + port
                if (new_vuln.name == existing_vuln.name and
                    new_vuln.target == existing_vuln.target and
                    new_vuln.port == existing_vuln.port):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                fact_store.vulnerabilities.append(new_vuln)
    
    @staticmethod
    def merge_credentials(fact_store: FactStore, new_creds: List[Dict]):
        """
        Merge credentials, deduplicate
        
        Args:
            fact_store: Current fact store
            new_creds: New credential data
        """
        for new_cred in new_creds:
            # Check for duplicates (same host + username)
            is_duplicate = False
            
            for existing_cred in fact_store.credentials:
                if (existing_cred.get("host") == new_cred.get("host") and
                    existing_cred.get("username") == new_cred.get("username")):
                    # Update password if different
                    if new_cred.get("password") != existing_cred.get("password"):
                        existing_cred["password"] = new_cred.get("password")
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                fact_store.credentials.append(new_cred)
    
    @staticmethod
    def merge_services(fact_store: FactStore, new_services: Dict[str, Dict]):
        """
        Merge service information
        
        Args:
            fact_store: Current fact store
            new_services: Dict mapping IP to service info
        """
        for ip, services in new_services.items():
            if ip in fact_store.services:
                # Update existing
                fact_store.services[ip].update(services)
            else:
                # Add new
                fact_store.services[ip] = services
    
    @staticmethod
    def get_summary(fact_store: FactStore) -> Dict[str, int]:
        """
        Get summary statistics of facts
        
        Returns:
            Dict with counts of different fact types
        """
        return {
            "hosts_discovered": len(fact_store.live_hosts),
            "targets_identified": len(fact_store.targets),
            "total_ports": sum(len(t.ports) for t in fact_store.targets),
            "vulnerabilities_found": len(fact_store.vulnerabilities),
            "credentials_captured": len(fact_store.credentials),
            "services_detected": sum(len(s) for s in fact_store.services.values())
        }
