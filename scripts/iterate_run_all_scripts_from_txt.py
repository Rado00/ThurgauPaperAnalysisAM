#!/usr/bin/env python3
"""
Script to run multiple scenarios by updating config.ini and executing run_all_scripts.sh
Windows-compatible version with SSH support for remote execution
"""

import os
import sys
import subprocess
import configparser
from pathlib import Path
import time
from datetime import datetime
import platform


def read_scenarios(scenarios_file):
    """
    Read scenario names from a text file.
    
    Args:
        scenarios_file: Path to the text file containing scenario names (one per line)
    
    Returns:
        List of scenario names
    """
    scenarios = []
    
    if not os.path.exists(scenarios_file):
        print(f"Error: Scenarios file '{scenarios_file}' not found!")
        sys.exit(1)
    
    with open(scenarios_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                scenarios.append(line)
    
    return scenarios


def update_config_ini(config_file, scenario_name):
    """
    Update the scenario parameter in config.ini file.
    
    Args:
        config_file: Path to config.ini file
        scenario_name: Name of the scenario to set
    """
    if not os.path.exists(config_file):
        print(f"Error: Config file '{config_file}' not found!")
        sys.exit(1)
    
    # Read the config file
    config = configparser.ConfigParser()
    config.read(config_file)
    
    # Update the scenario parameter
    if 'config' not in config:
        print("Error: [config] section not found in config.ini!")
        sys.exit(1)
    
    config['config']['scenario'] = scenario_name
    
    # Write back to the file
    with open(config_file, 'w') as configfile:
        config.write(configfile)
    
    print(f"✓ Updated config.ini with scenario: {scenario_name}")


def convert_windows_path_to_linux(windows_path):
    """
    Convert Windows SSHFS path to Linux path.
    Example: \\sshfs\sarf@gpro1.cloudlab.zhaw.ch\projects\... -> /home/sarf/projects/...
    
    Args:
        windows_path: Windows path string
    
    Returns:
        Tuple of (linux_path, ssh_host, ssh_user) or (None, None, None) if not an SSHFS path
    """
    path_str = str(windows_path).replace('\\', '/')
    
    # Check if it's an SSHFS path
    if path_str.startswith('//sshfs/'):
        # Extract user@host and path
        parts = path_str.replace('//sshfs/', '').split('/', 1)
        if len(parts) == 2:
            user_host = parts[0]
            remote_path = parts[1]
            
            # Parse user@host
            if '@' in user_host:
                ssh_user, ssh_host = user_host.split('@', 1)
                linux_path = f"/home/{ssh_user}/{remote_path}"
                return linux_path, ssh_host, ssh_user
    
    return None, None, None


def run_shell_script_ssh(ssh_host, ssh_user, remote_script_path):
    """
    Execute the shell script on a remote Linux server via SSH.
    
    Args:
        ssh_host: SSH hostname
        ssh_user: SSH username
        remote_script_path: Path to the script on the remote server
    
    Returns:
        True if script executed successfully, False otherwise
    """
    print(f"\n{'='*80}")
    print(f"Executing remotely via SSH: {ssh_user}@{ssh_host}")
    print(f"Remote script: {remote_script_path}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Ensure we have Linux-style paths (forward slashes)
    remote_script_path = remote_script_path.replace('\\', '/')
    
    # Get the directory containing the script and script name
    script_parts = remote_script_path.rsplit('/', 1)
    if len(script_parts) == 2:
        script_dir = script_parts[0]
        script_name = script_parts[1]
    else:
        script_dir = '.'
        script_name = remote_script_path
    
    try:
        # SSH command to execute the script
        # Use proper quoting and ensure forward slashes
        remote_command = f'cd "{script_dir}" && bash "{script_name}"'
        ssh_command = [
            'ssh',
            f'{ssh_user}@{ssh_host}',
            remote_command
        ]
        
        print(f"SSH Command: {' '.join(ssh_command)}\n")
        
        # Run the SSH command and capture output in real-time
        process = subprocess.Popen(
            ssh_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line, end='')
        
        # Wait for the process to complete
        return_code = process.wait()
        
        if return_code == 0:
            print(f"\n{'='*80}")
            print(f"✓ Script completed successfully!")
            print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}\n")
            return True
        else:
            print(f"\n{'='*80}")
            print(f"✗ Script failed with return code: {return_code}")
            print(f"{'='*80}\n")
            return False
            
    except FileNotFoundError:
        print(f"\n✗ Error: SSH command not found. Please install OpenSSH client.")
        print("On Windows, you can install it via: Settings > Apps > Optional Features > OpenSSH Client")
        return False
    except Exception as e:
        print(f"\n✗ Error executing script via SSH: {e}")
        return False


def run_shell_script_local(script_path):
    """
    Execute the shell script locally (for Linux/Mac).
    
    Args:
        script_path: Path to the shell script to run
    
    Returns:
        True if script executed successfully, False otherwise
    """
    if not os.path.exists(script_path):
        print(f"Error: Shell script '{script_path}' not found!")
        return False
    
    # Make sure the script is executable
    os.chmod(script_path, 0o755)
    
    print(f"\n{'='*80}")
    print(f"Executing locally: {script_path}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    try:
        # Run the script and capture output in real-time
        process = subprocess.Popen(
            [script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line, end='')
        
        # Wait for the process to complete
        return_code = process.wait()
        
        if return_code == 0:
            print(f"\n{'='*80}")
            print(f"✓ Script completed successfully!")
            print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}\n")
            return True
        else:
            print(f"\n{'='*80}")
            print(f"✗ Script failed with return code: {return_code}")
            print(f"{'='*80}\n")
            return False
            
    except Exception as e:
        print(f"\n✗ Error executing script: {e}")
        return False


def main():
    """
    Main function to orchestrate the scenario runs.
    """
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.resolve()
    
    # File paths based on your directory structure
    SCENARIOS_FILE = script_dir / "scenarios.txt"
    CONFIG_FILE = script_dir.parent / "config" / "config.ini"
    SHELL_SCRIPT = script_dir / "run_all_scripts.sh"
    
    # Detect if running on Windows with SSHFS
    is_windows = platform.system() == 'Windows'
    linux_path, ssh_host, ssh_user = convert_windows_path_to_linux(str(SHELL_SCRIPT))
    
    print("="*80)
    print("SCENARIO BATCH RUNNER")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Operating System: {platform.system()}")
    print(f"Script directory: {script_dir}")
    print(f"Scenarios file: {SCENARIOS_FILE}")
    print(f"Config file: {CONFIG_FILE}")
    print(f"Shell script: {SHELL_SCRIPT}")
    
    if is_windows and linux_path:
        print(f"\n⚠ Windows detected with SSHFS mount")
        print(f"SSH Host: {ssh_host}")
        print(f"SSH User: {ssh_user}")
        print(f"Remote Linux path: {linux_path}")
        print(f"\nThe script will use SSH to execute commands on the remote server.")
    
    print("="*80 + "\n")
    
    # Read scenarios from file
    scenarios = read_scenarios(str(SCENARIOS_FILE))
    
    if not scenarios:
        print("No scenarios found in the scenarios file!")
        sys.exit(1)
    
    print(f"Found {len(scenarios)} scenario(s) to run:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"  {i}. {scenario}")
    print()
    
    # Run each scenario
    successful_runs = []
    failed_runs = []
    
    start_time = time.time()
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'#'*80}")
        print(f"# SCENARIO {i}/{len(scenarios)}: {scenario}")
        print(f"{'#'*80}\n")
        
        scenario_start_time = time.time()
        
        # Update config.ini with the current scenario
        update_config_ini(str(CONFIG_FILE), scenario)
        
        # Run the shell script (locally or via SSH)
        if is_windows and linux_path:
            success = run_shell_script_ssh(ssh_host, ssh_user, linux_path)
        else:
            success = run_shell_script_local(str(SHELL_SCRIPT))
        
        scenario_duration = time.time() - scenario_start_time
        
        if success:
            successful_runs.append(scenario)
            print(f"✓ Scenario '{scenario}' completed in {scenario_duration/60:.2f} minutes")
        else:
            failed_runs.append(scenario)
            print(f"✗ Scenario '{scenario}' failed after {scenario_duration/60:.2f} minutes")
            
    
    # Print summary
    total_duration = time.time() - start_time
    
    print("\n" + "="*80)
    print("BATCH RUN SUMMARY")
    print("="*80)
    print(f"Total time: {total_duration/60:.2f} minutes ({total_duration/3600:.2f} hours)")
    print(f"Total scenarios: {len(scenarios)}")
    print(f"Successful: {len(successful_runs)}")
    print(f"Failed: {len(failed_runs)}")
    
    if successful_runs:
        print("\n✓ Successful scenarios:")
        for scenario in successful_runs:
            print(f"  - {scenario}")
    
    if failed_runs:
        print("\n✗ Failed scenarios:")
        for scenario in failed_runs:
            print(f"  - {scenario}")
    
    print("="*80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


if __name__ == "__main__":
    main()