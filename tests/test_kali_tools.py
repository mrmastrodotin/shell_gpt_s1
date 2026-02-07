"""
Test New Kali Linux Tools
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sgpt.tools.specs.masscan import MasscanTool
from sgpt.tools.specs.sqlmap import SQLMapTool
from sgpt.tools.specs.wpscan import WPScanTool
from sgpt.tools.specs.crackmapexec import CrackMapExecTool
from sgpt.tools.specs.netcat import NetcatTool

print("=" * 60)
print("Testing New Kali Linux Tools")
print("=" * 60)

# Test 1: Masscan
print("\n✓ Test 1: Masscan Tool")
masscan = MasscanTool()
masscan = MasscanTool()
context = {'network': {'subnet': '192.168.1.0/24'}}
cmd = masscan.generate_command('fast_port_scan', context, {})
print(f"  Command: {cmd}")
assert "masscan" in cmd and "192.168.1.0/24" in cmd
print(f"  ✅ Masscan working")

# Test 2: SQLMap
print("\n✓ Test 2: SQLMap Tool")
sqlmap = SQLMapTool()
context = {'url': 'http://example.com?id=1'}
cmd = sqlmap.generate_command('test_injection', context, {})
print(f"  Command: {cmd}")
assert "sqlmap" in cmd and "http://example.com?id=1" in cmd
print(f"  ✅ SQLMap working")

# Test 3: WPScan
print("\n✓ Test 3: WPScan Tool")
wpscan = WPScanTool()
context = {'url': 'https://wordpress.example.com'}
cmd = wpscan.generate_command('enumerate_users', context, {})
print(f"  Command: {cmd}")
assert "wpscan" in cmd and "enumerate u" in cmd
print(f"  ✅ WPScan working")

# Test 4: CrackMapExec
print("\n✓ Test 4: CrackMapExec Tool")
cme = CrackMapExecTool()
facts = {'live_hosts': ['192.168.1.10']}
cmd = cme.generate_command('smb_login', {}, facts)
print(f"  Command: {cmd}")
assert "crackmapexec smb" in cmd and "admin" in cmd
print(f"  ✅ CrackMapExec working")

# Test 5: Netcat
print("\n✓ Test 5: Netcat Tool")
nc = NetcatTool()
context = {'target': '192.168.1.10'}
cmd = nc.generate_command('port_check', context, {})
print(f"  Command: {cmd}")
assert "nc" in cmd and "192.168.1.10" in cmd
print(f"  ✅ Netcat working")

# Summary
print("\n" + "=" * 60)
print("All Tests Passed! ✅")
print("=" * 60)

total_intents = 5 # Placeholder

print(f"\n🎉 5 New Kali Tools Added!")
print(f"📊 Total New Intents: {total_intents}")
print(f"\n🛠️  Tools:")
print(f"   - Masscan: Ultra-fast port scanning")
print(f"   - SQLMap: SQL injection testing")
print(f"   - WPScan: WordPress security")
print(f"   - CrackMapExec: SMB exploitation")
print(f"   - Netcat: Network utilities")
print(f"\n🚀 Total Arsenal: 14 tools!")
