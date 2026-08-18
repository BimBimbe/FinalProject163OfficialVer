#!/usr/bin/env python3
"""
Quick runner to execute verify_numbers.py and save full output to a file.
Run this and paste the output here.
"""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, 'verify_numbers.py'], capture_output=True, text=True
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

# Also save to file for reference
with open('verify_output.txt', 'w') as f:
    f.write(result.stdout)
    if result.stderr:
        f.write("\n\nSTDERR:\n")
        f.write(result.stderr)

print("\n\n[Output also saved to verify_output.txt]")
