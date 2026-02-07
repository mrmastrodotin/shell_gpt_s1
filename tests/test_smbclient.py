"""
Test SMBClient Tool
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sgpt.tools.specs.smbclient import SMBClientTool

print("=" * 60)
print("Testing SMBClient Tool")
print("=" * 60)

tool = SMBClientTool()

# Test 1: List shares
print("\n✓ Test 1: List Shares")
facts = {'live_hosts': ['192.168.1.10']}
cmd = tool.generate_command('list_shares', {}, facts)
print(f"  Command: {cmd}")
assert cmd == "smbclient -L //192.168.1.10 -N"
print(f"  ✅ Anonymous share listing")

# Test 2: List shares with credentials
print("\n✓ Test 2: List Shares (Authenticated)")
facts = {
    'live_hosts': ['192.168.1.10'],
    'credentials': [{'ip': '192.168.1.10', 'username': 'admin', 'password': 'password123'}]
}
cmd = tool.generate_command('list_shares', {}, facts)
print(f"  Command: {cmd}")
assert cmd == "smbclient -L //192.168.1.10 -U admin%password123"
print(f"  ✅ Authenticated share listing")

# Test 3: List files in share
print("\n✓ Test 3: List Files")
facts = {'live_hosts': ['192.168.1.10']}
context = {
    'share': 'Users',
    'directory': '/Documents'
}
cmd = tool.generate_command('list_files', context, facts)
print(f"  Command: {cmd}")
assert "smbclient //192.168.1.10/Users" in cmd
assert "cd /Documents; ls" in cmd
print(f"  ✅ File listing command")

# Test 4: Download file
print("\n✓ Test 4: Download File")
facts = {'live_hosts': ['192.168.1.10']}
context = {
    'share': 'Users',
    'remote_file': 'document.pdf',
    'local_file': '/tmp/document.pdf'
}
cmd = tool.generate_command('download_file', context, facts)
print(f"  Command: {cmd}")
assert "get document.pdf /tmp/document.pdf" in cmd
print(f"  ✅ File download command")

# Test 5: Check access
print("\n✓ Test 5: Check Access")
facts = {'live_hosts': ['192.168.1.10']}
context = {'share': 'IPC$'}
cmd = tool.generate_command('check_access', context, facts)
print(f"  Command: {cmd}")
assert "smbclient //192.168.1.10/IPC$" in cmd
print(f"  ✅ Access check command")

# Summary
print("\n" + "=" * 60)
print("All Tests Passed! ✅")
print("=" * 60)
print(f"\nSMBClient tool ready:")
print(f"  Category: {tool.spec.category.value}")
