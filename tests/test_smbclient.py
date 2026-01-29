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
params = {
    'target': '192.168.1.10'
}
cmd = tool.build_command('list_shares', params)
print(f"  Command: {cmd}")
assert cmd == "smbclient -L //192.168.1.10 -N"
print(f"  ✅ Anonymous share listing")

# Test 2: List shares with credentials
print("\n✓ Test 2: List Shares (Authenticated)")
params = {
    'target': '192.168.1.10',
    'username': 'admin',
    'password': 'password123'
}
cmd = tool.build_command('list_shares', params)
print(f"  Command: {cmd}")
assert cmd == "smbclient -L //192.168.1.10 -U admin%password123"
print(f"  ✅ Authenticated share listing")

# Test 3: List files in share
print("\n✓ Test 3: List Files")
params = {
    'target': '192.168.1.10',
    'share': 'Users',
    'directory': '/Documents'
}
cmd = tool.build_command('list_files', params)
print(f"  Command: {cmd}")
assert "smbclient //192.168.1.10/Users" in cmd
assert "cd /Documents; ls" in cmd
print(f"  ✅ File listing command")

# Test 4: Download file
print("\n✓ Test 4: Download File")
params = {
    'target': '192.168.1.10',
    'share': 'Users',
    'remote_file': 'document.pdf',
    'local_file': '/tmp/document.pdf',
    'username': 'user'
}
cmd = tool.build_command('download_file', params)
print(f"  Command: {cmd}")
assert "get document.pdf /tmp/document.pdf" in cmd
print(f"  ✅ File download command")

# Test 5: Check access
print("\n✓ Test 5: Check Access")
params = {
    'target': '192.168.1.10',
    'share': 'IPC$'
}
cmd = tool.build_command('check_access', params)
print(f"  Command: {cmd}")
assert "smbclient //192.168.1.10/IPC$" in cmd
print(f"  ✅ Access check command")

# Test 6: Parse share output
print("\n✓ Test 6: Parse Share Output")
sample_output = """
        Sharename       Type      Comment
        ---------       ----      -------
        ADMIN$          Disk      Remote Admin
        C$              Disk      Default share
        IPC$            IPC       Remote IPC
        Users           Disk      User files
"""
facts = tool.parse_output('list_shares', sample_output)
print(f"  Shares found: {len(facts['shares'])}")
assert len(facts['shares']) > 0
print(f"  ✅ Share parsing working")

# Test 7: Validate parameters
print("\n✓ Test 7: Parameter Validation")
valid = tool.validate_parameters('list_shares', {'target': '192.168.1.10'})
assert valid == True
print(f"  ✅ Valid parameters accepted")

invalid = tool.validate_parameters('list_files', {'target': '192.168.1.10'})  # Missing 'share'
assert invalid == False
print(f"  ✅ Invalid parameters rejected")

print("\n" + "=" * 60)
print("All Tests Passed! ✅")
print("=" * 60)
print(f"\nSMBClient tool ready:")
print(f"  Total intents: {len(tool.intents)}")
print(f"  Category: {tool.category.value}")
