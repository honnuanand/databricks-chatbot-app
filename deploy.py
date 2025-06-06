#!/usr/bin/env python3
"""
🚀 Databricks AI Chatbot - Smart Deploy (Python Edition)

Intelligent deployment script for any Databricks workspace.
Safe for demo environments with multiple users.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import yaml
import re

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("📦 Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table


class DatabricksDeployer:
    """Smart Databricks deployment with rich UI and error handling."""
    
    def __init__(self, dry_run: bool = False, interactive: bool = False):
        self.dry_run = dry_run
        self.interactive = interactive
        self.console = Console()
        
        # Deployment configuration
        self.user_email: Optional[str] = None
        self.user_name: Optional[str] = None
        self.workspace_url: Optional[str] = None
        self.scope_name: Optional[str] = None
        self.secret_name: Optional[str] = None
        self.app_name: Optional[str] = None
        self.workspace_path: Optional[str] = None
        
        # Environment info for deployment summaries
        self.cli_version: Optional[str] = None
        self.python_version: Optional[str] = None
        self.cloud_provider: Optional[str] = None
        
    def run_databricks_command(self, cmd: List[str], capture_output: bool = True, timeout: int = 30, debug: bool = False) -> Tuple[bool, str]:
        """Run a Databricks CLI command with proper error handling."""
        try:
            # Prepare environment
            env = os.environ.copy()
            
            # If we're in Cursor/VSCode, ensure we're using the system CLI
            if 'DATABRICKS_CLI_UPSTREAM' in env:
                env['DATABRICKS_CLI_DO_NOT_EXECUTE_NEWER_VERSION'] = '1'
                # Try to find system CLI
                possible_paths = [
                    '/usr/local/bin/databricks',
                    '/opt/homebrew/bin/databricks',
                    '/usr/bin/databricks'
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        if debug:
                            self.console.print(f"[dim]Using system CLI at {path}[/dim]")
                        cli_cmd = [path]
                        break
                else:
                    cli_cmd = ["databricks"]
            else:
                # Use stored CLI path if available
                cli_cmd = [self.cli_path] if hasattr(self, 'cli_path') else ["databricks"]
            
            # Build full command
            full_cmd = cli_cmd + cmd
            
            if debug:
                self.console.print(f"[dim]Running: {' '.join(full_cmd)}[/dim]")
            
            # Run command
            result = subprocess.run(
                full_cmd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                env=env
            )
            
            # Clean up output by removing CLI version messages and warnings
            output_lines = []
            if result.stdout:
                for line in result.stdout.split('\n'):
                    # Skip empty lines
                    if not line.strip():
                        continue
                        
                    # Skip CLI version related messages and common warnings
                    if any(x in line for x in [
                        "Databricks CLI v",
                        "Your current $PATH prefers running CLI",
                        "Because both are installed",
                        "If you want to disable this behavior",
                        "Executing CLI v",
                        "-------------------------",
                        "Loaded config from app.yaml",  # Skip duplicate config messages
                        "NotOpenSSLWarning",
                        "urllib3",
                        "LibreSSL",
                        "warnings.warn",
                        "version",  # Skip any version-related output
                        "Version"
                    ]):
                        continue
                        
                    output_lines.append(line)
            
            cleaned_stdout = '\n'.join(output_lines).strip()
            
            if debug and result.stderr and result.stderr.strip():
                # Clean up stderr too
                stderr_lines = []
                for line in result.stderr.split('\n'):
                    if not line.strip():
                        continue
                    if not any(x in line for x in [
                        "NotOpenSSLWarning",
                        "urllib3",
                        "LibreSSL",
                        "warnings.warn",
                        "Databricks CLI v",
                        "Your current $PATH prefers running CLI",
                        "Because both are installed",
                        "If you want to disable this behavior",
                        "Executing CLI v",
                        "-------------------------",
                        "version",  # Skip any version-related output
                        "Version"
                    ]):
                        stderr_lines.append(line)
                if stderr_lines:
                    self.console.print("[yellow]Debug - stderr: " + "\n".join(stderr_lines) + "[/yellow]")
            
            if result.returncode == 0:
                if debug and cleaned_stdout:
                    self.console.print(f"[dim]Debug - stdout: {cleaned_stdout}[/dim]")
                return True, cleaned_stdout
            else:
                # Clean up the error message for better display
                error_msg = self.clean_error_message(result.stderr)
                if debug:
                    self.console.print(f"[red]Debug - Command failed with code {result.returncode}[/red]")
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout} seconds"
        except FileNotFoundError as e:
            if debug:
                self.console.print(f"[red]Debug - FileNotFoundError: {e}[/red]")
            return False, "Databricks CLI not found"
        except Exception as e:
            if debug:
                self.console.print(f"[red]Debug - Unexpected error: {e}[/red]")
            return False, str(e)
    
    def clean_error_message(self, raw_error: str) -> str:
        """Extract and clean the actual error message from CLI output."""
        if not raw_error:
            return "Unknown error occurred"
        
        lines = raw_error.strip().split('\n')
        
        # Look for actual error lines (skip warnings)
        error_lines = []
        for line in lines:
            line = line.strip()
            # Skip common CLI warnings/noise
            if any(skip in line for skip in [
                'urllib3', 'NotOpenSSLWarning', 'LibreSSL', 'warnings.warn',
                'CLI v0.', 'found at', '$PATH prefers', 'assume you are trying',
                'disable this behavior', 'Executing CLI', '-------------------------'
            ]):
                continue
            
            # Keep lines that look like actual errors
            if line and (line.startswith('Error:') or 
                        'error' in line.lower() or 
                        'failed' in line.lower() or
                        'limit' in line.lower() or
                        'permission' in line.lower() or
                        'not found' in line.lower() or
                        'invalid' in line.lower()):
                error_lines.append(line)
        
        if error_lines:
            return '\n'.join(error_lines)
        else:
            # If no clear error found, return last non-empty line
            for line in reversed(lines):
                if line.strip() and 'CLI v0.' not in line:
                    return line.strip()
            
        return raw_error
    
    def display_friendly_error(self, error_msg: str, context: str = "") -> None:
        """Display error in a user-friendly way with helpful suggestions."""
        # Analyze error and provide suggestions
        suggestions = []
        error_type = "Error"
        
        if "max limit" in error_msg.lower() and "scope" in error_msg.lower():
            error_type = "Workspace Limit Reached"
            suggestions = [
                "Your workspace has reached the maximum number of secret scopes (1000)",
                "💡 Solutions:",
                "  • Use an existing scope: databricks secrets list-scopes",
                "  • Delete unused scopes: databricks secrets delete-scope <scope-name>",
                "  • Contact your workspace admin to clean up old scopes",
                "  • Consider using a shared scope for multiple apps"
            ]
        elif "permission" in error_msg.lower() or "access" in error_msg.lower():
            error_type = "Permission Error"
            suggestions = [
                "You don't have sufficient permissions for this operation",
                "💡 Solutions:",
                "  • Contact your workspace administrator",
                "  • Ensure you have 'workspace admin' or required permissions",
                "  • Check if you're in the correct workspace"
            ]
        elif "not found" in error_msg.lower():
            error_type = "Resource Not Found"
            suggestions = [
                "The requested resource doesn't exist",
                "💡 Solutions:",
                "  • Verify the resource name is correct",
                "  • Check if you have access to the resource",
                "  • Ensure you're in the correct workspace"
            ]
        elif "invalid" in error_msg.lower() or "bad request" in error_msg.lower():
            error_type = "Invalid Request"
            suggestions = [
                "The request parameters are invalid",
                "💡 Solutions:",
                "  • Check the format of names (no spaces, special characters)",
                "  • Verify all required parameters are provided",
                "  • Try with different names if validation failed"
            ]
        
        # Display the error
        if context:
            title = f"{error_type} - {context}"
        else:
            title = error_type
            
        error_content = f"[red]❌ {error_msg}[/red]"
        
        if suggestions:
            error_content += "\n\n" + "\n".join(f"[yellow]{s}[/yellow]" for s in suggestions)
        
        self.console.print()
        self.console.print(Panel(
            error_content,
            title=title,
            style="red",
            expand=False
        ))
        self.console.print()
    
    def extract_json_from_output(self, output: str) -> Optional[Dict]:
        """Extract JSON data from command output, handling various formats."""
        if not output or not output.strip():
            return None
            
        try:
            # First try direct JSON parsing
            return json.loads(output)
        except json.JSONDecodeError:
            try:
                # Try to find JSON in the output
                output = output.strip()
                # Find the first '{' or '[' character
                start = output.find('{')
                if start == -1:
                    start = output.find('[')
                if start == -1:
                    return None
                    
                # Find the matching closing bracket
                stack = []
                in_string = False
                escape = False
                
                for i, char in enumerate(output[start:], start):
                    if not escape and char == '"':
                        in_string = not in_string
                    elif not in_string:
                        if char in '{[':
                            stack.append(char)
                        elif char in '}]':
                            if not stack:
                                continue
                            if (char == '}' and stack[-1] == '{') or (char == ']' and stack[-1] == '['):
                                stack.pop()
                                if not stack:  # Found the matching end
                                    json_str = output[start:i+1]
                                    return json.loads(json_str)
                    escape = not escape and char == '\\'
                    
                return None
            except Exception:
                return None
    
    def interactive_pause(self, message: str = "Press Enter to continue to the next step..."):
        """Pause for user input in interactive mode."""
        if self.interactive:
            self.console.print()
            input(f"🔄 {message}")
            self.console.print()
    
    def show_header(self):
        """Display the application header."""
        mode = "DRY RUN" if self.dry_run else "DEPLOYMENT"
        title = f"🚀 Databricks AI Chatbot - Smart Deploy ({mode})"
        
        if self.dry_run:
            subtitle = "📋 DRY RUN: No changes will be made"
            style = "yellow"
        else:
            subtitle = "🛠️  LIVE DEPLOYMENT: Changes will be made to your workspace"
            style = "green"
            
        self.console.print(Panel(
            f"[bold]{title}[/bold]\n{subtitle}",
            style=style,
            expand=False
        ))
        self.console.print()
    
    def check_prerequisites(self) -> bool:
        """Check if Databricks CLI is available and configured."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🔧 Checking prerequisites...", total=None)
            
            # Check if CLI is available and get version info
            success, version_output = self.run_databricks_command(["version"])
            if not success:
                self.console.print("[red]❌ Databricks CLI not found. Please install it first:[/red]")
                self.console.print("curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/v0.254.0/install.sh | sudo sh")
                return False
            
            # Parse CLI version information using regex
            version_pattern = re.compile(r'(?:Databricks CLI v|CLI v|version[\s:]?)(\d+\.\d+\.\d+)', re.IGNORECASE)
            cli_versions = {}
            
            # First try to find versions in the version output
            for line in version_output.split('\n'):
                # Skip empty lines
                if not line.strip():
                    continue
                    
                # Match the version pattern
                match = version_pattern.search(line)
                if match:
                    version = match.group(1)
                    # If "found at" is in the line, extract the path
                    if "found at" in line:
                        path = line.split("found at")[-1].strip()
                        cli_versions[version] = path
                    # If it's a PATH preference line
                    elif "Your current $PATH prefers running CLI" in line:
                        path = line.split("at")[-1].strip()
                        cli_versions[version] = path
                    # If it's just the version line
                    else:
                        cli_versions[version] = cli_versions.get(version, 'databricks')
            
            # If no version found, try --version as fallback
            if not cli_versions:
                success, alt_version_output = self.run_databricks_command(["--version"])
                if success:
                    for line in alt_version_output.split('\n'):
                        if not line.strip():
                            continue
                        # Try both "version" and "v" formats
                        match = version_pattern.search(line)
                        if match:
                            version = match.group(1)
                            cli_versions[version] = 'databricks'
                            break
            
            # Final check for version detection
            if not cli_versions:
                # Try one more time with a more lenient pattern
                lenient_pattern = re.compile(r'v?(\d+\.\d+\.\d+)', re.IGNORECASE)
                for line in version_output.split('\n'):
                    if not line.strip():
                        continue
                    match = lenient_pattern.search(line)
                    if match:
                        version = match.group(1)
                        cli_versions[version] = 'databricks'
                        break
            
            if not cli_versions:
                self.console.print("[yellow]⚠️  Could not determine CLI version[/yellow]")
                # Continue anyway since the CLI is responding
                self.cli_version = "Unknown"
                self.cli_path = "databricks"
            else:
                # Store CLI information
                newest_version = max(cli_versions.keys(), key=lambda v: [int(x) for x in v.split('.')])
                self.cli_version = newest_version
                self.cli_path = cli_versions[newest_version]
                
                # Show version info
                if len(cli_versions) > 1:
                    self.console.print()
                    self.console.print(Panel(
                        "[yellow]⚠️  Multiple Databricks CLI versions detected:[/yellow]\n\n" +
                        "\n".join(f"  • v{ver}: {path}" for ver, path in cli_versions.items()) +
                        f"\n\n[blue]Using newest version v{newest_version} at {cli_versions[newest_version]}[/blue]\n\n" +
                        "[yellow]To avoid version conflicts, consider:[/yellow]\n" +
                        "  1. Removing older versions\n" +
                        "  2. Setting DATABRICKS_CLI_DO_NOT_EXECUTE_NEWER_VERSION=1 to use venv version\n" +
                        "  3. Updating your PATH to prioritize the desired version",
                        title="🔧 CLI Version Check",
                        style="yellow"
                    ))
                else:
                    self.console.print(f"[green]✅ Using Databricks CLI v{newest_version}[/green]")
            
            # Check if CLI is configured by trying to get user info
            success, output = self.run_databricks_command(["current-user", "me", "--output", "json"])
            if not success:
                if self.dry_run:
                    self.console.print("[yellow]⚠️  [DRY RUN] CLI not configured. For real deployment, run: databricks configure --token[/yellow]")
                    return False
                else:
                    self.console.print("[red]❌ CLI not configured. Please run:[/red]")
                    self.console.print("databricks configure --token")
                    return False
            
            # Extract user information - handle both old and new CLI formats
            user_data = self.extract_json_from_output(output)
            if not user_data:
                self.console.print("[red]❌ Failed to parse user information[/red]")
                return False
            
            # New CLI format (v0.254.0+)
            if "emails" in user_data and isinstance(user_data["emails"], list):
                for email in user_data["emails"]:
                    if email.get("primary") and "value" in email:
                        self.user_email = email["value"]
                        break
                if not self.user_email and "userName" in user_data:
                    self.user_email = user_data["userName"]
            # Old CLI format
            elif "userName" in user_data:
                self.user_email = user_data["userName"]
            else:
                self.console.print("[red]❌ Could not determine user email[/red]")
                return False
            
            self.user_name = self.user_email.split('@')[0].replace('.', '-')
            
            # Get workspace information - try multiple methods
            self.workspace_url = None
            self.cloud_provider = None
            
            # Method 1: Try getting from profiles (new CLI format)
            success, profiles_output = self.run_databricks_command(["auth", "profiles", "--output", "json"])
            if success:
                profiles_data = self.extract_json_from_output(profiles_output)
                if profiles_data and "profiles" in profiles_data:
                    for profile in profiles_data["profiles"]:
                        if profile.get("valid"):
                            self.workspace_url = profile.get("host")
                            self.cloud_provider = profile.get("cloud")
                            break
            
            # Method 2: Try getting from config if Method 1 failed
            if not self.workspace_url:
                success, config_output = self.run_databricks_command(["config", "get", "--output", "json"])
                if success:
                    config_data = self.extract_json_from_output(config_output)
                    if config_data and "host" in config_data:
                        self.workspace_url = config_data["host"]
            
            # Method 3: Parse from regular profiles output as last resort
            if not self.workspace_url:
                success, profiles_output = self.run_databricks_command(["auth", "profiles"])
                if success:
                    for line in profiles_output.split('\n'):
                        if "DEFAULT" in line and "YES" in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                self.workspace_url = parts[1]
                                break
            
            # Final check and fallback
            if not self.workspace_url:
                if self.dry_run:
                    self.console.print("[yellow]⚠️  [DRY RUN] Could not determine workspace URL[/yellow]")
                    self.workspace_url = "https://demo.cloud.databricks.com"
                else:
                    self.console.print("[red]❌ Could not determine workspace URL. Please check your Databricks CLI configuration.[/red]")
                    return False
            
            # Get additional workspace information
            success, workspace_output = self.run_databricks_command(["workspace", "get-status", "--output", "json"])
            if success:
                workspace_data = self.extract_json_from_output(workspace_output)
                if workspace_data:
                    # Store additional workspace info that might be useful later
                    self.workspace_id = workspace_data.get("workspace_id")
                    self.workspace_name = workspace_data.get("workspace_name", self.workspace_url.split('.')[1] if '.' in self.workspace_url else None)
            
            # If we don't have a workspace name, try to derive it from the URL
            if not hasattr(self, 'workspace_name') or not self.workspace_name:
                parts = self.workspace_url.split('.')
                if len(parts) > 1:
                    self.workspace_name = parts[1]
            
            return True
    
    def show_connection_info(self, context: str = "deploy"):
        """Display connection information."""
        table = Table(show_header=False, box=None)
        table.add_column(style="green bold")
        table.add_column()
        
        # Check if we have the required information
        has_user = hasattr(self, 'user_email') and self.user_email and self.user_email.strip()
        has_workspace = hasattr(self, 'workspace_url') and self.workspace_url and self.workspace_url.strip()
        
        # Only try to refresh if we're not in dry run and we don't have the info from config
        if not self.dry_run and (not has_user or not has_workspace):
            # Get user info if needed
            if not has_user:
                success, output = self.run_databricks_command(["current-user", "me", "--output", "json"])
                if success:
                    user_data = self.extract_json_from_output(output)
                    if user_data:
                        if "emails" in user_data and isinstance(user_data["emails"], list):
                            for email in user_data["emails"]:
                                if email.get("primary") and "value" in email:
                                    self.user_email = email["value"]
                                    has_user = True
                                    break
                        if not has_user and "userName" in user_data:
                            self.user_email = user_data["userName"]
                            has_user = True
            
            # Get workspace info if needed
            if not has_workspace:
                success, profiles_output = self.run_databricks_command(["auth", "profiles", "--output", "json"])
                if success:
                    profiles_data = self.extract_json_from_output(profiles_output)
                    if profiles_data and "profiles" in profiles_data:
                        for profile in profiles_data["profiles"]:
                            if profile.get("valid"):
                                self.workspace_url = profile.get("host")
                                self.cloud_provider = profile.get("cloud")
                                has_workspace = True
                                break
        
        # Display what information we have
        if has_user:
            table.add_row("✅ Connected as:", self.user_email)
        else:
            table.add_row("❌ User:", "Not available (auth issue)")
            
        if has_workspace:
            table.add_row("✅ Workspace:", self.workspace_url)
        else:
            table.add_row("❌ Workspace:", "Not available (config issue)")
        
        # Add additional workspace info if available
        if hasattr(self, 'workspace_name') and self.workspace_name:
            table.add_row("✅ Workspace Name:", self.workspace_name)
        if hasattr(self, 'workspace_id') and self.workspace_id:
            table.add_row("✅ Workspace ID:", self.workspace_id)
        if hasattr(self, 'cloud_provider') and self.cloud_provider:
            table.add_row("✅ Cloud Provider:", self.cloud_provider.upper())
        
        self.console.print(table)
        self.console.print()
        
        # Show warning if information is incomplete
        if not has_user or not has_workspace:
            self.console.print(Panel(
                "[yellow]⚠️  Connection information is incomplete[/yellow]\n\n"
                "This might be due to:\n"
                "1. CLI authentication issues\n"
                "2. Incorrect workspace configuration\n"
                "3. Network connectivity problems\n\n"
                "Try running:\n"
                "  databricks configure --token\n"
                "to reconfigure your credentials.",
                title="⚠️ Connection Warning",
                style="yellow"
            ))
        
        self.interactive_pause()
        
        # Only ask for confirmation if we have workspace info
        if has_workspace and not self.dry_run and self.workspace_url != "Unknown workspace":
            if context == "deploy":
                prompt = "Deploy to this workspace?"
            elif context == "redeploy":
                prompt = "Redeploy to this workspace?"
            elif context == "status":
                prompt = "Check status in this workspace?"
            else:
                prompt = f"Continue with {context} in this workspace?"
                
            if not Confirm.ask(prompt, default=True):
                action = context.replace("deploy", "deployment").replace("status", "status check")
                self.console.print(f"[yellow]⏹️  {action.title()} cancelled. Use 'databricks configure --token' to switch workspaces[/yellow]")
                return False
        
        return True
    
    def configure_scope(self) -> bool:
        """Configure the secret scope."""
        self.console.print("[yellow]📋 For demo environments, use unique names to avoid conflicts[/yellow]")
        
        default_scope = f"{self.user_name}-chatbot"
        
        if self.dry_run:
            self.console.print(f"❓ Enter unique scope name (default: {default_scope}): [yellow][DRY RUN: would use '{default_scope}'][/yellow]")
            self.scope_name = default_scope
        else:
            self.scope_name = Prompt.ask("❓ Enter unique scope name", default=default_scope)
        
        self.interactive_pause()
        
        # Initialize variables before progress context
        scope_exists = False
        can_manage = False
        creation_failed = False
        create_output = ""
        
        # Check if scope exists
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"🔍 Checking scope '{self.scope_name}'...", total=None)
            
            success, output = self.run_databricks_command(["secrets", "list-scopes"])
            
            if success:
                lines = output.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip().split()[0] == self.scope_name:
                        scope_exists = True
                        break
            
            if scope_exists:
                # Check permissions
                success, acl_output = self.run_databricks_command(["secrets", "list-acls", self.scope_name])
                if success and "MANAGE" in acl_output:
                    can_manage = True
                
                if can_manage:
                    progress.update(task, description=f"✅ Scope '{self.scope_name}' exists and you can manage it")
                    if self.dry_run:
                        self.console.print(f"[green]✅ [DRY RUN] Scope '{self.scope_name}' exists with MANAGE permission[/green]")
                    else:
                        self.console.print(f"[green]✅ Scope '{self.scope_name}' exists[/green]")
                else:
                    self.console.print(f"[red]❌ You don't have MANAGE permission on scope '{self.scope_name}'[/red]")
                    return False
            else:
                if self.dry_run:
                    self.console.print(f"[yellow]⚠️  [DRY RUN] Scope '{self.scope_name}' doesn't exist[/yellow]")
                    self.console.print(f"[yellow][DRY RUN] Would create new scope '{self.scope_name}'[/yellow]")
                    self.console.print(f"[blue]         Command: databricks secrets create-scope '{self.scope_name}'[/blue]")
                else:
                    self.console.print(f"[yellow]⚠️  Scope '{self.scope_name}' doesn't exist[/yellow]")
                    self.console.print(f"[blue]🔐 Creating scope '{self.scope_name}'...[/blue]")
                    
                    success, create_output = self.run_databricks_command(["secrets", "create-scope", self.scope_name])
                    if success:
                        progress.update(task, description=f"✅ Scope '{self.scope_name}' created successfully")
                        self.console.print(f"[green]✅ Scope '{self.scope_name}' created successfully[/green]")
                    else:
                        creation_failed = True
                        progress.update(task, description="❌ Scope creation failed")
                        
        # Handle scope creation failure outside the progress context
        if creation_failed:
            self.display_friendly_error(create_output, "Creating Secret Scope")
            
            # If it's a scope limit error, offer to select existing scope
            if "max limit" in create_output.lower() and "scope" in create_output.lower():
                if self.offer_existing_scope_selection():
                    return True  # Successfully selected an existing scope
            
            return False
        
        self.interactive_pause()
        return True
    
    def offer_existing_scope_selection(self) -> bool:
        """Offer to select an existing scope when scope creation fails due to limits."""
        self.console.print()
        self.console.print("[yellow]📋 You have two options:[/yellow]")
        self.console.print("[blue]  1. [bold]continue[/bold] (or [bold]c[/bold]) - Select an existing scope to use[/blue]")
        self.console.print("[red]  2. [bold]exit[/bold] (or [bold]e[/bold]) - Cancel deployment[/red]")
        self.console.print()
        
        choice = Prompt.ask(
            "❓ What would you like to do?",
            choices=["continue", "exit", "c", "e"],
            default="continue",
            show_default=True
        )
        
        if choice.lower() in ["exit", "e"]:
            self.console.print("[yellow]⏹️  Deployment cancelled by user[/yellow]")
            return False
            
        self.console.print("[blue]🔍 Let's find an existing scope you can use...[/blue]")
        
        # Get list of scopes with efficient pagination
        scopes = self.get_manageable_scopes_paginated(max_scopes=20)
        
        if not scopes:
            self.console.print("[yellow]⚠️  No existing scopes found with MANAGE permission[/yellow]")
            self.console.print("[blue]💡 Try creating a scope with a different name, or contact your admin[/blue]")
            return False
        
        # Display scopes in a nice table
        shared_count = sum(1 for s in scopes if s.lower().startswith('shared'))
        if shared_count > 0:
            self.console.print(f"\n[blue]📋 Available scopes (you have MANAGE permission) - [green]{shared_count} scopes with 'shared' in name found![/green][/blue]")
        else:
            self.console.print("\n[blue]📋 Available scopes (you have MANAGE permission):[/blue]")
        
        from rich.table import Table
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Index", style="cyan", width=6)
        table.add_column("Scope Name", style="green")
        table.add_column("Type", style="yellow", width=8)
        
        for i, scope in enumerate(scopes, 1):
            scope_type = "🤝 With 'shared'" if scope.lower().startswith('shared') else "📦 Regular"
            table.add_row(str(i), scope, scope_type)
        
        self.console.print(table)
        
        if len(scopes) == 20:
            self.console.print("[yellow]💡 Showing first 20 manageable scopes (for performance). If you don't see the scope you want, you can:[/yellow]")
            self.console.print("[blue]  • Contact your admin to clean up unused scopes[/blue]")
            self.console.print("[blue]  • Use a scope from the list above[/blue]")
            self.console.print("[blue]  • Cancel and try creating a scope with a different name[/blue]")
        
        if shared_count > 0:
            self.console.print(f"\n[green]💡 Recommendation: Use a [bold]🤝 scope with 'shared' in name[/bold] for demo deployments - they're designed for multi-user access![/green]")
        
        # Let user select
        while True:
            try:
                choice = Prompt.ask(
                    f"\n❓ Select a scope (1-{len(scopes)}) or 'q' to quit",
                    default="1"
                )
                
                if choice.lower() == 'q':
                    return False
                
                index = int(choice) - 1
                if 0 <= index < len(scopes):
                    selected_scope = scopes[index]
                    self.scope_name = selected_scope
                    self.console.print(f"[green]✅ Selected scope: {selected_scope}[/green]")
                    return True
                else:
                    self.console.print(f"[red]❌ Invalid choice. Please enter 1-{len(scopes)} or 'q'[/red]")
                    
            except ValueError:
                self.console.print(f"[red]❌ Invalid input. Please enter a number 1-{len(scopes)} or 'q'[/red]")
            except KeyboardInterrupt:
                self.console.print("\n[yellow]⏹️  Selection cancelled[/yellow]")
                return False
    
    def get_manageable_scopes_paginated(self, max_scopes: int = 20) -> List[str]:
        """Get a list of scopes the user can manage, with early stopping for performance."""
        manageable_scopes = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("📋 Finding scopes you can manage...", total=None)
            
            # Get all scopes first
            success, output = self.run_databricks_command(["secrets", "list-scopes"])
            if not success:
                self.console.print("[red]❌ Failed to list scopes[/red]")
                return []
            
            # Parse scope names (skip header line)
            lines = output.strip().split('\n')[1:] if output.strip() else []
            all_scope_names = []
            
            for line in lines:
                parts = line.strip().split()
                if parts:
                    all_scope_names.append(parts[0])
            
            # Sort alphabetically (we'll prioritize shared scopes in the checking logic)
            all_scope_names.sort()
            total_scopes = len(all_scope_names)
            
            if total_scopes > 100:
                progress.update(task, description=f"📋 Found {total_scopes} scopes - checking scopes with 'shared' in name first (limiting to {max_scopes} manageable)...")
            else:
                progress.update(task, description=f"📋 Checking permissions on {total_scopes} scopes (prioritizing scopes with 'shared' in name)...")
            
            # First pass: Look for ALL shared scopes
            shared_scopes = [name for name in all_scope_names if name.lower().startswith('shared')]
            regular_scopes = [name for name in all_scope_names if not name.lower().startswith('shared')]
            
            progress.update(task, description=f"📋 Found {len(shared_scopes)} scopes with 'shared' in name, checking permissions on all of them first...")
            
            checked_count = 0
            
            # Check ALL shared scopes first
            for scope_name in shared_scopes:
                checked_count += 1
                if checked_count % 5 == 0:
                    shared_found = sum(1 for s in manageable_scopes if s.lower().startswith('shared'))
                    progress.update(task, description=f"📋 Checked {checked_count}/{len(shared_scopes)} shared scopes, found {shared_found} manageable...")
                
                success, acl_output = self.run_databricks_command(["secrets", "list-acls", scope_name], timeout=10)
                if success and "MANAGE" in acl_output:
                    manageable_scopes.append(scope_name)
            
            shared_found = sum(1 for s in manageable_scopes if s.lower().startswith('shared'))
            if shared_found > 0:
                progress.update(task, description=f"✅ Found {shared_found} manageable scopes with 'shared' in name! Now checking regular scopes...")
            else:
                progress.update(task, description=f"⚠️  No manageable scopes with 'shared' in name found. Checking regular scopes...")
            
            # Second pass: Fill remaining slots with regular scopes
            remaining_slots = max_scopes - len(manageable_scopes)
            if remaining_slots > 0:
                for scope_name in regular_scopes:
                    if len(manageable_scopes) >= max_scopes:
                        break
                    
                    checked_count += 1
                    if checked_count % 10 == 0:
                        progress.update(task, description=f"📋 Checked {checked_count} total scopes, found {len(manageable_scopes)} manageable ({shared_found} shared)...")
                    
                    success, acl_output = self.run_databricks_command(["secrets", "list-acls", scope_name], timeout=10)
                    if success and "MANAGE" in acl_output:
                        manageable_scopes.append(scope_name)
            
            final_shared_count = sum(1 for s in manageable_scopes if s.lower().startswith('shared'))
            if len(manageable_scopes) > 0:
                if final_shared_count > 0:
                    progress.update(task, description=f"✅ Found {len(manageable_scopes)} manageable scopes ({final_shared_count} with 'shared' in name)")
                else:
                    progress.update(task, description=f"✅ Found {len(manageable_scopes)} manageable scopes (no scopes with 'shared' in name available)")
            else:
                progress.update(task, description="❌ No manageable scopes found")
        
        # Sort results to ensure shared scopes appear first
        manageable_scopes.sort(key=lambda s: (0 if s.lower().startswith('shared') else 1, s.lower()))
        return manageable_scopes
    
    def configure_secret(self) -> bool:
        """Configure the OpenAI API key secret."""
        default_secret = "openai_api_key"
        
        if self.dry_run:
            self.console.print(f"❓ Enter secret name for OpenAI key (default: {default_secret}): [yellow][DRY RUN: would use '{default_secret}'][/yellow]")
            self.secret_name = default_secret
        else:
            self.secret_name = Prompt.ask("❓ Enter secret name for OpenAI key", default=default_secret)
        
        self.interactive_pause()
        
        # Check if secret exists
        secret_exists = False
        need_to_add_secret = False
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"🔍 Checking for existing secret '{self.secret_name}' in scope '{self.scope_name}'...", total=None)
            
            success, output = self.run_databricks_command(["secrets", "list-secrets", self.scope_name])
            
            if success:
                lines = output.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip().split()[0] == self.secret_name:
                        secret_exists = True
                        break
            
            if secret_exists:
                progress.update(task, description=f"✅ Secret '{self.secret_name}' already exists")
            else:
                progress.update(task, description=f"⚠️  Secret '{self.secret_name}' doesn't exist - will need to create it")
                need_to_add_secret = True
        
        # Handle the results outside the progress context
        if secret_exists:
            if self.dry_run:
                self.console.print(f"[green]✅ [DRY RUN] Secret '{self.secret_name}' already exists in scope '{self.scope_name}'[/green]")
                self.console.print("[yellow][DRY RUN] Would ask if you want to update the existing secret[/yellow]")
                self.console.print("[yellow][DRY RUN] Assuming you would keep the existing secret[/yellow]")
            else:
                if Confirm.ask("Use existing secret?", default=True):
                    self.console.print("[green]✅ Using existing secret[/green]")
                else:
                    openai_key = Prompt.ask("🔑 Enter your OpenAI API key", password=True)
                    
                    # Update secret
                    process = subprocess.Popen(
                        ["databricks", "secrets", "put-secret", self.scope_name, self.secret_name],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate(input=openai_key)
                    
                    if process.returncode == 0:
                        self.console.print("[green]✅ Secret updated[/green]")
                    else:
                        self.console.print(f"[red]❌ Failed to update secret: {stderr}[/red]")
                        return False
        elif need_to_add_secret:
            if self.dry_run:
                self.console.print("[yellow][DRY RUN] Would prompt for OpenAI API key[/yellow]")
                self.console.print(f"[yellow][DRY RUN] Would add secret '{self.secret_name}' to scope '{self.scope_name}'[/yellow]")
                self.console.print(f"[blue]         Command: echo 'OPENAI_KEY' | databricks secrets put-secret '{self.scope_name}' '{self.secret_name}'[/blue]")
            else:
                openai_key = Prompt.ask("🔑 Enter your OpenAI API key", password=True)
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console
                ) as progress:
                    task = progress.add_task("🔑 Adding OpenAI API key...", total=None)
                    
                    # Add secret
                    process = subprocess.Popen(
                        ["databricks", "secrets", "put-secret", self.scope_name, self.secret_name],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate(input=openai_key)
                    
                    if process.returncode == 0:
                        progress.update(task, description=f"✅ Secret '{self.secret_name}' added successfully")
                    else:
                        cleaned_error = self.clean_error_message(stderr)
                        self.display_friendly_error(cleaned_error, "Adding Secret")
                        return False
        
        self.interactive_pause()
        return True
    
    def configure_app(self) -> bool:
        """Configure the app name and settings."""
        default_app = f"{self.user_name}-ai-chatbot"
        
        if self.dry_run:
            self.console.print(f"❓ Enter unique app name (default: {default_app}): [yellow][DRY RUN: would use '{default_app}'][/yellow]")
            self.app_name = default_app
        else:
            self.app_name = Prompt.ask("❓ Enter unique app name", default=default_app)
        
        self.interactive_pause()
        
        # Configure app.yaml with CORRECT port (8501 for Streamlit, NOT 8000!)
        app_yaml_content = f"""command: ['streamlit', 'run', 'app.py', '--server.port=8501', '--server.address=0.0.0.0', '--server.headless=true']
env:
  - name: 'OPENAI_API_KEY'
    value: '{{{{secrets/{self.scope_name}/{self.secret_name}}}}}'

permissions:
  - group_name: 'users'
    permission_level: 'CAN_USE'

resources:
  - name: 'default-sql-warehouse'
    description: 'SQL Warehouse for app queries'
    type: 'sql_warehouse'"""
        
        if self.dry_run:
            self.console.print("[yellow][DRY RUN] Would update app.yaml with configuration[/yellow]")
            self.console.print(f"[blue]         Scope: {self.scope_name}, Secret: {self.secret_name}[/blue]")
            self.console.print("[blue]         Content would be:[/blue]")
            self.console.print(Panel(app_yaml_content, title="app.yaml", style="blue"))
        else:
            self.console.print("📝 Updating app.yaml with your configuration...")
            
            with open("app.yaml", "w") as f:
                f.write(app_yaml_content)
            
            self.console.print(f"[green]✅ app.yaml configured for scope: {self.scope_name}, secret: {self.secret_name}[/green]")
        
        # Set workspace path
        self.workspace_path = f"/Workspace/Users/{self.user_email}/{self.app_name}"
        
        return True
    
    def show_final_configuration(self):
        """Display the final configuration summary."""
        config_content = f"""[bold cyan]📱 App Configuration:[/bold cyan]
  • [bold]App Name:[/bold] {self.app_name}
  • [bold]Secret Scope:[/bold] {self.scope_name}
  • [bold]Secret Name:[/bold] {self.secret_name}
  • [bold]Workspace Path:[/bold] {self.workspace_path}

[bold cyan]🔗 Deployment Details:[/bold cyan]
  • [bold]User:[/bold] {self.user_email}
  • [bold]Workspace:[/bold] {self.workspace_url}"""
        
        self.console.print()
        self.console.print(Panel(
            config_content,
            title="📝 Final Configuration",
            style="cyan",
            expand=False
        ))
        self.console.print()
        
        self.interactive_pause()
    
    def show_deployment_summary(self):
        """Show what would be done or was done."""
        if self.dry_run:
            self.console.print(Panel(
                "[yellow]📋 DRY RUN COMPLETE - No actual changes were made[/yellow]\n\n"
                "[blue]🚀 To perform actual deployment, run:[/blue]\n"
                "  python deploy.py\n\n"
                "[blue]📋 Target Environment:[/blue]\n"
                f"  • User: {self.user_email}\n"
                f"  • Workspace: {self.workspace_url}\n\n"
                "[blue]📋 Summary of what would be done:[/blue]\n"
                f"  1. Create/use scope: {self.scope_name}\n"
                f"  2. Add/update secret: {self.secret_name}\n"
                f"  3. Create app: {self.app_name}\n"
                f"  4. Sync code to: {self.workspace_path}\n"
                "  5. Deploy and start the app",
                title="Deployment Summary",
                style="yellow"
            ))
        else:
            # Continue with actual deployment
            return self.deploy_app()
        
        return True
    
    def deploy_app(self) -> bool:
        """Deploy the app to Databricks."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            
            # Create app (this can take time for compute provisioning)
            task1 = progress.add_task(f"🚀 Creating Databricks App '{self.app_name}' (may take 2-3 minutes for compute setup)...", total=100)
            success, output = self.run_databricks_command(["apps", "create", self.app_name], timeout=300)
            
            if success:
                progress.update(task1, advance=100, description=f"✅ App '{self.app_name}' created successfully")
            else:
                if "already exists" in output.lower():
                    progress.update(task1, advance=100, description=f"⚠️  App '{self.app_name}' already exists, continuing...")
                else:
                    self.display_friendly_error(output, "Creating App")
                    return False
            
            time.sleep(0.5)  # Brief pause for UI
            
            # Sync code
            task2 = progress.add_task("📁 Syncing code to workspace...", total=100)
            
            sync_cmd = [
                "sync", ".", self.workspace_path,
                "--exclude", "*.pyc",
                "--exclude", ".git",
                "--exclude", "venv",
                "--exclude", "*.egg-info",
                "--exclude", "__pycache__",
                "--exclude", "saved_chats"
            ]
            
            success, output = self.run_databricks_command(sync_cmd, timeout=120)
            
            if success:
                progress.update(task2, advance=100, description="✅ Code synced successfully")
            else:
                self.display_friendly_error(output, "Syncing Code")
                return False
            
            time.sleep(0.5)  # Brief pause for UI
            
            # Deploy app
            task3 = progress.add_task("🚀 Deploying app (building image and starting compute)...", total=100)
            
            success, output = self.run_databricks_command([
                "apps", "deploy", self.app_name,
                "--source-code-path", self.workspace_path
            ], timeout=600)
            
            if success:
                progress.update(task3, advance=100, description="✅ App deployed successfully!")
                
                # Get app URL
                success, url_output = self.run_databricks_command([
                    "apps", "get", self.app_name, "--output", "json"
                ], timeout=60)
                
                if success:
                    app_data = self.extract_json_from_output(url_output)
                    if app_data and "url" in app_data:
                        app_url = app_data["url"]
                        
                        self.console.print()
                        self.console.print(Panel(
                            f"[bold green]🎉 SUCCESS! Your AI Chatbot is ready![/bold green]\n\n"
                            f"[bold yellow]🌐 App URL:[/bold yellow]\n"
                            f"[bold blue]{app_url}[/bold blue]\n\n"
                            f"[bold cyan]📋 Deployment Summary:[/bold cyan]\n"
                            f"  • [bold]App Name:[/bold] {self.app_name}\n"
                            f"  • [bold]Secret Scope:[/bold] {self.scope_name}\n"
                            f"  • [bold]Port Configuration:[/bold] 8501 (Streamlit)\n"
                            f"  • [bold]Unity Catalog:[/bold] Permissions configured\n"
                            f"  • [bold]Platform:[/bold] {self.workspace_url.split('.')[0].replace('https://', '')} (Databricks)\n"
                            f"  • [bold]Deployed by:[/bold] {self.user_email}\n\n"
                            f"[bold cyan]🔧 Technical Details:[/bold cyan]\n"
                            f"  • [bold]Runtime:[/bold] Python 3.9+ with Streamlit\n"
                            f"  • [bold]Dependencies:[/bold] LangChain, OpenAI, Databricks SDK\n"
                            f"  • [bold]Storage:[/bold] Auto-saved chat history\n"
                            f"  • [bold]Compute:[/bold] Serverless (auto-scaling)\n\n"
                            "[bold cyan]🔗 Next steps:[/bold cyan]\n"
                            "  1. Visit your app URL above\n"
                            "  2. Login with your Databricks credentials\n"
                            "  3. Start chatting with your AI assistant!\n\n"
                            "[bold cyan]🔄 Development Workflow:[/bold cyan]\n"
                            f"  • [bold]Local Testing:[/bold] streamlit run app.py\n"
                            f"  • [bold]Quick Redeploy:[/bold] python deploy.py --redeploy\n"
                            f"  • [bold]Environment Setup:[/bold] source set_env.sh\n\n"
                            "[bold yellow]⚠️  If you see 'App Not Available':[/bold yellow]\n"
                            "  • Wait 30-60 seconds for app to fully start\n"
                            "  • Clear browser cache or try incognito mode\n"
                            "  • Verify port 8501 in app.yaml (common issue!)\n"
                            "  • Check Unity Catalog permissions\n"
                            f"  • Debug: databricks apps get {self.app_name} --output json\n\n"
                            "[bold cyan]👥 To share with others:[/bold cyan]\n"
                            f"  databricks apps set-permissions {self.app_name} --json '{{\"access_control_list\": [{{\"user_name\": \"user@company.com\", \"permission_level\": \"CAN_USE\"}}]}}'\n\n"
                            "[green]✨ Configuration saved in app.yaml for future deployments[/green]",
                            title="🚀 Deployment Complete",
                            style="green"
                        ))
                        return True
                
                self.console.print("[green]🎉 App deployed successfully![/green]")
                return True
            else:
                self.display_friendly_error(output, "Deploying App")
                
                # Show debugging info
                self.console.print("[blue]🔍 Troubleshooting tips:[/blue]")
                self.console.print(f"  • Check app status: databricks apps get {self.app_name}")
                self.console.print(f"  • Verify secret access: databricks secrets get-secret {self.scope_name} {self.secret_name}")
                return False
    
    def run(self) -> bool:
        """Run the complete deployment process."""
        self.show_header()
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Show connection info
        if not self.show_connection_info("deploy"):
            return False
        
        # Configure scope
        if not self.configure_scope():
            return False
        
        # Configure secret
        if not self.configure_secret():
            return False
        
        # Configure app
        if not self.configure_app():
            return False
        
        # Show final configuration
        self.show_final_configuration()
        
        # Final confirmation for real deployment
        if not self.dry_run:
            if not Confirm.ask("Proceed with deployment?", default=True):
                self.console.print("[yellow]⏹️  Deployment cancelled[/yellow]")
                return False
        
        # Deploy or show summary
        return self.show_deployment_summary()
    
    def redeploy(self) -> bool:
        """Quick redeploy: sync code and redeploy existing app."""
        self.console.print(Panel(
            "[bold cyan]🔄 Quick Redeploy Mode[/bold cyan]\n\n"
            "This will:\n"
            "  1. Load configuration from app.yaml\n"
            "  2. Sync your code to the workspace\n"
            "  3. Redeploy the existing app\n\n"
            "[yellow]⚠️  Make sure you've already run the full deployment once![/yellow]",
            title="🚀 Quick Redeploy",
            style="cyan"
        ))
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
            
        # Load configuration from app.yaml
        if not self.load_config_from_yaml():
            return False
            
        # Show connection info
        if not self.show_connection_info("redeploy"):
            return False
            
        # Show what we're about to do
        self.console.print(f"\n[bold cyan]📋 Redeploy Configuration:[/bold cyan]")
        self.console.print(f"  • [bold]App Name:[/bold] {self.app_name}")
        self.console.print(f"  • [bold]Workspace Path:[/bold] {self.workspace_path}")
        self.console.print(f"  • [bold]User:[/bold] {self.user_email}")
        self.console.print()
        
        # Confirm redeploy
        if not Confirm.ask("🔄 Proceed with redeploy?", default=True):
            self.console.print("[yellow]⏹️  Redeploy cancelled[/yellow]")
            return False
            
        # Perform sync and deploy
        return self.sync_and_deploy()
    
    def load_config_from_yaml(self) -> bool:
        """Load configuration from existing app.yaml."""
        try:
            if not os.path.exists("app.yaml"):
                self.console.print("[red]❌ app.yaml not found! Run full deployment first.[/red]")
                return False
                
            with open("app.yaml", "r") as f:
                yaml_content = f.read()
                
            # Try to auto-detect app name by listing existing apps
            success, apps_output = self.run_databricks_command(["apps", "list", "--output", "json"], timeout=30)
            if success:
                apps_data = self.extract_json_from_output(apps_output)
                if apps_data and isinstance(apps_data, dict) and "apps" in apps_data:
                    apps = apps_data["apps"]
                    if len(apps) == 1:
                        # If only one app exists, use it
                        self.app_name = apps[0]["name"]
                        self.console.print(f"[green]✅ Auto-detected app: {self.app_name}[/green]")
                    elif len(apps) > 1:
                        # Multiple apps, let user choose
                        self.console.print("[yellow]Multiple apps found. Please select:[/yellow]")
                        for i, app in enumerate(apps, 1):
                            self.console.print(f"  {i}. {app['name']}")
                        
                        while True:
                            try:
                                choice = int(Prompt.ask("Select app number", default="1"))
                                if 1 <= choice <= len(apps):
                                    self.app_name = apps[choice-1]["name"]
                                    break
                                else:
                                    self.console.print("[red]Invalid choice[/red]")
                            except ValueError:
                                self.console.print("[red]Please enter a number[/red]")
                    else:
                        self.console.print("[red]❌ No apps found. Run full deployment first.[/red]")
                        return False
                else:
                    # Fallback to known app name
                    self.app_name = "anand-rao-ai-chatbot"
            else:
                # Fallback to known app name
                self.app_name = "anand-rao-ai-chatbot"
            
            # Extract scope and secret from yaml
            import re
            secret_match = re.search(r'{{secrets/([^/]+)/([^}]+)}}', yaml_content)
            if secret_match:
                self.scope_name = secret_match.group(1)
                self.secret_name = secret_match.group(2)
            else:
                self.console.print("[red]❌ Could not find secret configuration in app.yaml[/red]")
                return False
                
            # Set workspace path
            self.workspace_path = f"/Workspace/Users/{self.user_email}/{self.app_name}"
            
            self.console.print(f"[green]✅ Loaded config from app.yaml[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]❌ Error loading app.yaml: {e}[/red]")
            return False
    
    def sync_and_deploy(self) -> bool:
        """Sync code and deploy the app."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            
            # Sync code
            task1 = progress.add_task("📁 Syncing code to workspace...", total=100)
            
            sync_cmd = [
                "sync", ".", self.workspace_path,
                "--exclude", "*.pyc",
                "--exclude", ".git", 
                "--exclude", "venv",
                "--exclude", "*.egg-info",
                "--exclude", "__pycache__",
                "--exclude", "saved_chats"
            ]
            
            success, output = self.run_databricks_command(sync_cmd, timeout=120)
            
            if success:
                progress.update(task1, advance=100, description="✅ Code synced successfully")
            else:
                self.display_friendly_error(output, "Syncing Code")
                return False
            
            time.sleep(0.5)  # Brief pause for UI
            
            # Deploy app
            task2 = progress.add_task("🚀 Redeploying app...", total=100)
            
            success, output = self.run_databricks_command([
                "apps", "deploy", self.app_name,
                "--source-code-path", self.workspace_path
            ], timeout=600)
            
            if success:
                progress.update(task2, advance=100, description="✅ App redeployed successfully!")
                
                # Get app URL
                success, url_output = self.run_databricks_command([
                    "apps", "get", self.app_name, "--output", "json"
                ], timeout=60)
                
                if success:
                    app_data = self.extract_json_from_output(url_output)
                    if app_data and "url" in app_data:
                        app_url = app_data["url"]
                        
                        self.console.print()
                        self.console.print(Panel(
                            f"[bold green]🎉 REDEPLOY SUCCESS![/bold green]\n\n"
                            f"[bold yellow]🌐 App URL:[/bold yellow]\n"
                            f"[bold blue]{app_url}[/bold blue]\n\n"
                            f"[bold cyan]📋 Redeploy Summary:[/bold cyan]\n"
                            f"  • [bold]App Name:[/bold] {self.app_name}\n"
                            f"  • [bold]Port:[/bold] 8501 (Streamlit)\n"
                            f"  • [bold]Unity Catalog:[/bold] Permissions active\n"
                            f"  • [bold]Code Sync:[/bold] ✅ Latest changes deployed\n"
                            f"  • [bold]Platform:[/bold] {self.workspace_url.split('.')[0].replace('https://', '')} (Databricks)\n"
                            f"  • [bold]Redeployed by:[/bold] {self.user_email}\n\n"
                            f"[bold cyan]💡 What Changed:[/bold cyan]\n"
                            f"  • [bold]Source Code:[/bold] Synced from local directory\n"
                            f"  • [bold]Dependencies:[/bold] Updated per requirements.txt\n"
                            f"  • [bold]Configuration:[/bold] Preserved from app.yaml\n\n"
                            "[bold cyan]🔗 Next steps:[/bold cyan]\n"
                            "  1. Visit your app URL above\n"
                            "  2. Your changes should now be live!\n"
                            "  3. Test your new features\n\n"
                            "[bold cyan]🚀 Development Tip:[/bold cyan]\n"
                            "  For local testing: streamlit run app.py\n\n"
                            "[bold yellow]⚠️  If you see 'App Not Available':[/bold yellow]\n"
                            "  • Wait 30-60 seconds for app to restart\n"
                            "  • Clear browser cache/try incognito mode\n"
                            "  • Check port 8501 in app.yaml (common fix!)\n"
                            "  • Check Unity Catalog permissions\n"
                            f"  • Debug: databricks apps get {self.app_name} --output json",
                            title="🔄 Redeploy Complete",
                            style="green"
                        ))
                        return True
                
                self.console.print("[green]🎉 App redeployed successfully![/green]")
                return True
            else:
                self.display_friendly_error(output, "Redeploying App")
                return False
    
    def show_status(self) -> bool:
        """Show current app deployment status and details."""
        self.console.print(Panel(
            "[bold cyan]📊 App Status Check[/bold cyan]\n\n"
            "This will show:\n"
            "  1. Current app status and URL\n"
            "  2. Deployment details and configuration\n"
            "  3. Recent deployment history\n"
            "  4. Troubleshooting information",
            title="🔍 Status Check",
            style="cyan"
        ))
        
        # First check if CLI is available
        success, _ = self.run_databricks_command(["version"])
        if not success:
            self.console.print("[red]❌ Databricks CLI not available. Please install and configure it first.[/red]")
            self.console.print("[blue]Install: curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/v0.254.0/install.sh | sudo sh[/blue]")
            self.console.print("[blue]Configure: databricks configure --token[/blue]")
            return False
            
        # Load configuration from app.yaml if it exists
        config_loaded = False
        try:
            config_loaded = self.load_config_from_yaml()
            if config_loaded:
                self.console.print("[green]✅ Loaded config from app.yaml[/green]")
        except Exception as e:
            self.console.print(f"[yellow]⚠️  Could not load app.yaml: {e}[/yellow]")
        
        # Show connection info
        if not self.show_connection_info("status"):
            return False
        
        # If no app name from config, try to find it
        if not hasattr(self, 'app_name') or not self.app_name:
            if not self.find_app():
                return False
        
        # Display comprehensive status
        return self.display_comprehensive_status()
    
    def find_app(self) -> bool:
        """Find the app name if not specified in app.yaml."""
        self.console.print("[yellow]No app.yaml found. Discovering existing apps...[/yellow]")
        
        success, apps_output = self.run_databricks_command(["apps", "list", "--output", "json"], timeout=30)
        if not success:
            self.console.print("[red]❌ Failed to list apps[/red]")
            return False
        
        apps_data = self.extract_json_from_output(apps_output)
        if not apps_data or "apps" not in apps_data or not apps_data["apps"]:
            self.console.print("[yellow]⚠️  No apps found in this workspace[/yellow]")
            return False
        
        apps = apps_data["apps"]
        if len(apps) == 1:
            # If only one app exists, use it
            self.app_name = apps[0]["name"]
            self.console.print(f"[green]✅ Found app: {self.app_name}[/green]")
        else:
            # Multiple apps, let user choose
            self.console.print(f"[blue]📱 Found {len(apps)} apps. Please select:[/blue]")
            for i, app in enumerate(apps, 1):
                status = app.get("app_status", {}).get("state", "Unknown")
                self.console.print(f"  {i}. {app['name']} (Status: {status})")
            
            while True:
                try:
                    choice = int(Prompt.ask("Select app number", default="1"))
                    if 1 <= choice <= len(apps):
                        self.app_name = apps[choice-1]["name"]
                        break
                    else:
                        self.console.print("[red]Invalid choice[/red]")
                except ValueError:
                    self.console.print("[red]Please enter a number[/red]")
        
        return True
    
    def display_comprehensive_status(self) -> bool:
        """Display comprehensive app status information."""
        # Get app details
        success, app_output = self.run_databricks_command([
            "apps", "get", self.app_name, "--output", "json"
        ], timeout=60)
        
        if not success:
            self.display_friendly_error(app_output, "Getting App Status")
            return False
        
        app_data = self.extract_json_from_output(app_output)
        if not app_data:
            self.console.print("[red]❌ Failed to parse app data[/red]")
            return False
        
        # Extract key information
        app_url = app_data.get("url", "Not available")
        app_status = app_data.get("app_status", {})
        compute_status = app_data.get("compute_status", {})
        active_deployment = app_data.get("active_deployment", {})
        
        # Get deployment history
        deployments = self.get_deployment_history()
        
        # Create comprehensive status display
        self.display_status_summary(app_data, app_url, app_status, compute_status, active_deployment, deployments)
        
        return True
    
    def get_deployment_history(self) -> list:
        """Get recent deployment history."""
        success, deployments_output = self.run_databricks_command([
            "apps", "list-deployments", self.app_name, "--output", "json"
        ], timeout=30)
        
        if success:
            deployments_data = self.extract_json_from_output(deployments_output)
            if deployments_data and "deployments" in deployments_data:
                return deployments_data["deployments"][:3]  # Last 3 deployments
        
        return []
    
    def display_status_summary(self, app_data, app_url, app_status, compute_status, active_deployment, deployments):
        """Display a comprehensive status summary."""
        # Main status panel
        app_state = app_status.get("state", "Unknown")
        app_message = app_status.get("message", "No message")
        compute_state = compute_status.get("state", "Unknown")
        compute_message = compute_status.get("message", "No message")
        
        # Determine overall health
        if app_state == "RUNNING" and compute_state == "ACTIVE":
            health_icon = "🟢"
            health_status = "Healthy"
            health_color = "green"
        elif app_state in ["PENDING", "STARTING"] or compute_state in ["PENDING", "STARTING"]:
            health_icon = "🟡"
            health_status = "Starting"
            health_color = "yellow"
        else:
            health_icon = "🔴"
            health_status = "Issue Detected"
            health_color = "red"
        
        status_content = f"""[bold {health_color}]{health_icon} Overall Status: {health_status}[/bold {health_color}]

[bold cyan]📱 App Information:[/bold cyan]
  • [bold]App Name:[/bold] {self.app_name}
  • [bold]App URL:[/bold] {app_url}
  • [bold]App Status:[/bold] {app_state} - {app_message}
  • [bold]Compute Status:[/bold] {compute_state} - {compute_message}

[bold cyan]🔧 Technical Configuration:[/bold cyan]
  • [bold]Port:[/bold] 8501 (Streamlit)
  • [bold]Unity Catalog:[/bold] Permissions active
  • [bold]Platform:[/bold] {app_url.split('.')[1] if '.' in app_url else 'Unknown'} (Databricks)
  • [bold]Runtime:[/bold] Python with Streamlit framework

[bold cyan]🚀 Current Deployment:[/bold cyan]"""
        
        if active_deployment:
            deployment_state = active_deployment.get("status", {}).get("state", "Unknown")
            deployment_message = active_deployment.get("status", {}).get("message", "No message")
            create_time = active_deployment.get("create_time", "Unknown")
            update_time = active_deployment.get("update_time", "Unknown")
            creator = active_deployment.get("creator", "Unknown")
            
            status_content += f"""
  • [bold]Deployment ID:[/bold] {active_deployment.get("deployment_id", "Unknown")[:8]}...
  • [bold]Status:[/bold] {deployment_state} - {deployment_message}
  • [bold]Created:[/bold] {create_time}
  • [bold]Updated:[/bold] {update_time}
  • [bold]Deployed by:[/bold] {creator}"""
        else:
            status_content += "\n  • [red]No active deployment found[/red]"
        
        # Add deployment history
        if deployments:
            status_content += f"\n\n[bold cyan]📋 Recent Deployments:[/bold cyan]"
            for i, deployment in enumerate(deployments[:3], 1):
                dep_state = deployment.get("status", {}).get("state", "Unknown")
                dep_time = deployment.get("create_time", "Unknown")
                status_content += f"\n  {i}. {dep_state} at {dep_time}"
        
        # Add configuration info if available
        if hasattr(self, 'scope_name') and self.scope_name:
            status_content += f"\n\n[bold cyan]⚙️ Secrets Configuration:[/bold cyan]"
            status_content += f"\n  • [bold]Secret Scope:[/bold] {self.scope_name}"
            if hasattr(self, 'secret_name') and self.secret_name:
                status_content += f"\n  • [bold]Secret Name:[/bold] {self.secret_name}"
            status_content += f"\n  • [bold]OpenAI Integration:[/bold] Active"
        
        self.console.print()
        self.console.print(Panel(
            status_content,
            title=f"📊 Status Report: {self.app_name}",
            style=health_color
        ))
        
        # Add troubleshooting section if there are issues
        if health_status != "Healthy":
            self.display_troubleshooting_tips(app_state, compute_state)
        
        # Add quick actions
        self.display_quick_actions(app_url)
    
    def display_troubleshooting_tips(self, app_state, compute_state):
        """Display troubleshooting tips based on current status."""
        tips = []
        
        if app_state != "RUNNING":
            tips.extend([
                "App is not running:",
                "• Check deployment logs for errors",
                "• Verify app.yaml uses port 8501 (common issue!)",
                "• Ensure all dependencies are available",
                "• Check Unity Catalog permissions"
            ])
        
        if compute_state != "ACTIVE":
            tips.extend([
                "Compute issues detected:",
                "• Wait for compute to start (can take 2-3 minutes)",
                "• Check workspace compute limits",
                "• Verify Unity Catalog permissions"
            ])
        
        if tips:
            self.console.print()
            self.console.print(Panel(
                "\n".join(f"[yellow]{tip}[/yellow]" for tip in tips),
                title="🔧 Troubleshooting Tips",
                style="yellow"
            ))
    
    def display_quick_actions(self, app_url):
        """Display quick action commands."""
        actions_content = f"""[bold cyan]🚀 Quick Actions:[/bold cyan]

[bold]Visit App:[/bold]
  {app_url}

[bold]Redeploy Latest Code:[/bold]
  python deploy.py --redeploy

[bold]Check Detailed Status:[/bold]
  databricks apps get {self.app_name} --output json

[bold]View Deployment Details:[/bold]
  databricks apps list-deployments {self.app_name}

[bold]Local Development:[/bold]
  streamlit run app.py"""
        
        self.console.print()
        self.console.print(Panel(
            actions_content,
            title="⚡ Quick Actions",
            style="blue"
        ))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="🚀 Databricks AI Chatbot - Smart Deploy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy.py                    # Normal deployment
  python deploy.py --dry-run          # Preview deployment without changes
  python deploy.py --interactive      # Interactive deployment with pauses
  python deploy.py --redeploy         # Quick redeploy (sync code + deploy only)
  python deploy.py --status           # Show current app status and details
  python deploy.py -d -i              # Interactive dry run (recommended for demos)
  python deploy.py -r                 # Quick redeploy (short form)
  python deploy.py -s                 # Check status (short form)
        """
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Pause after each step (can combine with --dry-run)"
    )
    
    parser.add_argument(
        "--redeploy", "-r",
        action="store_true",
        help="Quick redeploy: sync code and redeploy existing app (skips configuration)"
    )
    
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Show current app deployment status and details"
    )
    
    args = parser.parse_args()
    
    # Validate argument combinations
    if args.dry_run and args.redeploy:
        Console().print("[red]❌ Cannot use --dry-run with --redeploy[/red]")
        sys.exit(1)
    
    if args.status and (args.dry_run or args.redeploy):
        Console().print("[red]❌ Cannot use --status with other deployment options[/red]")
        sys.exit(1)
    
    try:
        deployer = DatabricksDeployer(
            dry_run=args.dry_run,
            interactive=args.interactive
        )
        
        if args.redeploy:
            success = deployer.redeploy()
        elif args.status:
            success = deployer.show_status()
        else:
            success = deployer.run()
            
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        Console().print("\n[yellow]⏹️  Deployment cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        Console().print(f"\n[red]❌ Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main() 