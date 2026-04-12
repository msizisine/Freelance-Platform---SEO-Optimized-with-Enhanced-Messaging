#!/usr/bin/env python3
"""
Quick fix for Docker phone_utils import issue
This script will copy the fixed files directly to the container
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("Quick Fix for Docker phone_utils Import Issue")
    print("=" * 50)
    
    # Check if Docker is running
    success, _, _ = run_command("docker ps")
    if not success:
        print("Error: Docker is not running or accessible")
        return False
    
    # Get container name
    success, stdout, _ = run_command("docker-compose ps -q web")
    if not success or not stdout.strip():
        print("Error: Could not find web container")
        return False
    
    container_id = stdout.strip().split('\n')[0]
    print(f"Found web container: {container_id}")
    
    # Copy the fixed forms.py to container
    print("Copying fixed forms.py to container...")
    success, _, stderr = run_command(f"docker cp users/forms.py {container_id}:/app/users/forms.py")
    if not success:
        print(f"Error copying forms.py: {stderr}")
        return False
    
    # Copy the phone_utils.py to container
    print("Copying phone_utils.py to container...")
    success, _, stderr = run_command(f"docker cp users/phone_utils.py {container_id}:/app/users/phone_utils.py")
    if not success:
        print(f"Error copying phone_utils.py: {stderr}")
        return False
    
    # Restart the web service
    print("Restarting web service...")
    success, _, stderr = run_command("docker-compose restart web")
    if not success:
        print(f"Error restarting web service: {stderr}")
        return False
    
    print("Quick fix completed successfully!")
    print("The Docker container should now have the updated code.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
