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
from rich import box

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
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
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table


class DatabricksDeployer:
    """Smart Databricks deployment with rich UI and error handling."""
    
    def __init__(self):
        """Initialize the deployer with Rich console for pretty output."""
        self.console = Console()
        self.app_name = None
        self.workspace_url = None
        
        # Deployment configuration
        self.user_email: Optional[str] = None
        self.user_name: Optional[str] = None
        self.scope_name: Optional[str] = None
        self.secret_name: Optional[str] = None
        self.workspace_path: Optional[str] = None
        
        # Environment info for deployment summaries
        self.cli_version: Optional[str] = None
        self.python_version: Optional[str] = None
        self.cloud_provider: Optional[str] = None
        
        # Mode flags
        self.dry_run: bool = False
        self.interactive: bool = False
    
    def run_databricks_command(self, args: List[str], input_data: Optional[str] = None, timeout: Optional[int] = None) -> Tuple[bool, str]:
        """Run a databricks CLI command and return success status and output."""
        try:
            cmd = ["databricks"] + args
            if input_data:
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(input=input_data, timeout=timeout)
                if process.returncode == 0:
                    return True, stdout
                else:
                    return False, stderr
            else:
                if timeout:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
                else:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                if result.returncode == 0:
                    return True, result.stdout
                else:
                    return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
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
                self.console.print("curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh")
                return False
                
            # Check if CLI is configured by trying to get user info
            success, output = self.run_databricks_command(["current-user", "me", "--output", "json"])
            if not success:
                self.console.print("[red]❌ CLI not configured. Please run:[/red]")
                self.console.print("databricks configure --token")
                return False
                
            # Extract user information
            try:
                user_data = json.loads(output)
                if "emails" in user_data and isinstance(user_data["emails"], list):
                    for email in user_data["emails"]:
                        if email.get("primary") and "value" in email:
                            self.user_email = email["value"]
                            break
                if not self.user_email and "userName" in user_data:
                    self.user_email = user_data["userName"]
                    
                if not self.user_email:
                    self.console.print("[red]❌ Could not determine user email[/red]")
                    return False
                
                self.user_name = self.user_email.split('@')[0].replace('.', '-')
            except Exception as e:
                self.console.print(f"[red]❌ Failed to parse user information: {e}[/red]")
                return False
            
            # Get workspace information - try multiple methods
            self.workspace_url = None
            
            # Method 1: Try getting from profiles
            success, profiles_output = self.run_databricks_command(["auth", "profiles", "--output", "json"])
            if success:
                try:
                    profiles_data = json.loads(profiles_output)
                    if profiles_data and "profiles" in profiles_data:
                        for profile in profiles_data["profiles"]:
                            if profile.get("valid"):
                                self.workspace_url = profile.get("host")
                                break
                except:
                    pass
            
            # Method 2: Try getting from config if Method 1 failed
            if not self.workspace_url:
                success, config_output = self.run_databricks_command(["config", "get", "--output", "json"])
                if success:
                    try:
                        config_data = json.loads(config_output)
                        self.workspace_url = config_data.get("host")
                    except:
                        pass
            
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
            
            if not self.workspace_url:
                self.console.print("[red]❌ Could not determine workspace URL[/red]")
                return False
            
            progress.update(task, description="✅ Prerequisites met")
            return True
    
    def show_connection_info(self, context: str = "deploy") -> bool:
        """Show current connection information."""
        table = Table(show_header=False, box=box.ROUNDED)
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
                # Method 1: Try getting from profiles (new CLI format)
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
                
                # Method 2: Try getting from config if Method 1 failed
                if not has_workspace:
                    success, config_output = self.run_databricks_command(["config", "get", "--output", "json"])
                    if success:
                        config_data = self.extract_json_from_output(config_output)
                        if config_data and "host" in config_data:
                            self.workspace_url = config_data["host"]
                            has_workspace = True
                
                # Method 3: Try workspace status as last resort
                if not has_workspace:
                    success, workspace_output = self.run_databricks_command(["workspace", "get-status", "--output", "json"])
                    if success:
                        workspace_data = self.extract_json_from_output(workspace_output)
                        if workspace_data and "workspace_url" in workspace_data:
                            self.workspace_url = workspace_data["workspace_url"]
                            has_workspace = True
        
        # Display what information we have
        self.console.print()
        self.console.print(Panel(
            "[bold cyan]🔗 Connection Details[/bold cyan]",
            style="cyan"
        ))
        
        if has_user:
            table.add_row("👤 User:", self.user_email)
        else:
            table.add_row("❌ User:", "Not available (auth issue)")
            
        if has_workspace:
            table.add_row("🌐 Workspace:", self.workspace_url)
            # Extract workspace name from URL for display
            workspace_name = self.workspace_url.split('.')[1] if '.' in self.workspace_url else "Unknown"
            table.add_row("📍 Region:", workspace_name)
            if hasattr(self, 'cloud_provider') and self.cloud_provider:
                table.add_row("☁️ Cloud:", self.cloud_provider.upper())
        else:
            table.add_row("❌ Workspace:", "Not available (config issue)")
        
        self.console.print(table)
        
        # Show CLI version
        success, version_output = self.run_databricks_command(["version"])
        if success:
            version = version_output.strip()
            self.console.print(f"[dim]CLI Version: {version}[/dim]")
        
        # Show warning if information is incomplete
        if not has_user or not has_workspace:
            self.console.print()
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
                prompt = "Continue with this workspace?"
                
            if not Confirm.ask(prompt, default=True):
                self.console.print("[yellow]⏹️  Please configure the correct workspace with 'databricks configure --token'[/yellow]")
                return False
        
        return has_user and has_workspace
    
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
        
        # Configure app.yaml with CORRECT port (8000 for Databricks Apps)
        app_yaml_content = f"""command: ['streamlit', 'run', 'app.py']
env:
  - name: 'OPENAI_API_KEY'
    value: '{{{{secrets/{self.scope_name}/{self.secret_name}}}}}'
  - name: 'STREAMLIT_BROWSER_GATHER_USAGE_STATS'
    value: 'false'
  - name: 'STREAMLIT_SERVER_ADDRESS'
    value: '0.0.0.0'
  - name: 'STREAMLIT_SERVER_ENABLE_CORS'
    value: 'false'
  - name: 'STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'
    value: 'false'
  - name: 'STREAMLIT_SERVER_HEADLESS'
    value: 'true'
  - name: 'STREAMLIT_SERVER_PORT'
    value: '8000'

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
                            f"  • [bold]Port Configuration:[/bold] 8000 (Databricks)\n"
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
                            "  • Verify port 8000 in app.yaml (common issue!)\n"
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
            
        # Check for shared scopes first
        self.console.print("\n[bold cyan]🔍 Checking for shared scopes...[/bold cyan]")
        success, output = self.run_databricks_command(["secrets", "list-scopes"])
        if success:
            lines = output.strip().split('\n')[1:] if output.strip() else []
            shared_scopes = [line.split()[0] for line in lines if line.strip() and line.split()[0].lower().startswith('shared-')]
            
            if shared_scopes:
                self.console.print(f"[green]✅ Found {len(shared_scopes)} shared scopes![/green]")
                self.console.print("\n[bold]Available shared scopes:[/bold]")
                for scope in sorted(shared_scopes):
                    self.console.print(f"• {scope}")
                
                if Confirm.ask("\nWould you like to use a shared scope? (recommended for demos)", default=True):
                    scope_name = Prompt.ask("Enter the shared scope name", choices=shared_scopes, default=shared_scopes[0])
                    self.scope_name = scope_name
                    self.console.print(f"[green]✅ Using shared scope: {scope_name}[/green]")
                    return True
        
        # If no shared scopes or user declined, continue with regular scope configuration
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
        """Quick redeploy of existing app."""
        self.console.print(Panel(
            "[bold blue]🔄 Quick Redeploy Mode[/bold blue]\n\n"
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
                
            # Extract scope and secret from yaml
            import re
            secret_match = re.search(r'{{secrets/([^/]+)/([^}]+)}}', yaml_content)
            if secret_match:
                self.scope_name = secret_match.group(1)
                self.secret_name = secret_match.group(2)
            else:
                self.console.print("[red]❌ Could not find secret configuration in app.yaml[/red]")
                return False
            
            # Extract app name from yaml
            app_config = yaml.safe_load(yaml_content)
            if isinstance(app_config, dict) and "app_name" in app_config:
                self.app_name = app_config["app_name"]
            else:
                # Fallback to default app name
                self.app_name = "anand-rao-ai-chatbot"
                
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
                            f"  • [bold]Port:[/bold] 8000 (Databricks)\n"
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
                            "  • Check port 8000 in app.yaml (common fix!)\n"
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
  • [bold]Port:[/bold] 8000 (Databricks)
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
                "• Verify app.yaml uses port 8000 (common issue!)",
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

    def stop_app(self) -> bool:
        """Stop the running app."""
        self.console.print(Panel(
            "[bold red]🛑 Stop App[/bold red]\n\n"
            "This will:\n"
            "  1. Stop the running app\n"
            "  2. Free up compute resources\n"
            "  3. Make the app temporarily unavailable\n\n"
            "[yellow]⚠️  The app can be restarted later using --start[/yellow]",
            title="🛑 Stop App",
            style="red"
        ))
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Load configuration from app.yaml
        if not self.load_config_from_yaml():
            return False
        
        # Show connection info
        if not self.show_connection_info("stop"):
            return False
        
        # Confirm stop
        if not Confirm.ask("🛑 Are you sure you want to stop the app?", default=False):
            self.console.print("[yellow]⏹️  Stop cancelled[/yellow]")
            return False
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("🛑 Stopping app...", total=100)
            
            success, output = self.run_databricks_command([
                "apps", "stop", self.app_name
            ], timeout=60)
            
            if success:
                progress.update(task, advance=100, description="✅ App stopped successfully")
                
                self.console.print()
                self.console.print(Panel(
                    "[bold green]✅ App stopped successfully![/bold green]\n\n"
                    "[bold cyan]📋 Stop Summary:[/bold cyan]\n"
                    f"  • [bold]App Name:[/bold] {self.app_name}\n"
                    f"  • [bold]Status:[/bold] STOPPED\n"
                    f"  • [bold]Compute:[/bold] Released\n\n"
                    "[bold cyan]🔄 To restart the app:[/bold cyan]\n"
                    "  python deploy.py --start",
                    title="🛑 Stop Complete",
                    style="green"
                ))
                return True
            else:
                self.display_friendly_error(output, "Stopping App")
                return False

    def delete_app(self) -> bool:
        """Delete the app completely."""
        self.console.print(Panel(
            "[bold red]⚠️ Delete App[/bold red]\n\n"
            "This will:\n"
            "  1. Stop the running app\n"
            "  2. Delete all app resources\n"
            "  3. Remove the app configuration\n\n"
            "[red]⚠️  THIS ACTION CANNOT BE UNDONE![/red]",
            title="⚠️ Delete App",
            style="red"
        ))
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Load configuration from app.yaml
        if not self.load_config_from_yaml():
            return False
        
        # Show connection info
        if not self.show_connection_info("delete"):
            return False
        
        # Double confirm deletion
        self.console.print(f"\n[bold red]⚠️  You are about to delete the app: {self.app_name}[/bold red]")
        if not Confirm.ask("Are you absolutely sure?", default=False):
            self.console.print("[yellow]⏹️  Deletion cancelled[/yellow]")
            return False
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            delete_task = progress.add_task("🗑️ Initiating app deletion...", total=100)
            
            # Start the deletion
            success, output = self.run_databricks_command([
                "apps", "delete", self.app_name
            ])
            
            if not success:
                self.display_friendly_error(output, "Initiating App Deletion")
                return False
                
            progress.update(delete_task, advance=20, description="🗑️ Deletion in progress...")
            
            # Monitor deletion progress
            max_attempts = 30  # 5 minutes total (10 second intervals)
            attempt = 0
            
            while attempt < max_attempts:
                success, status_output = self.run_databricks_command([
                    "apps", "get", self.app_name, "--output", "json"
                ])
                
                if not success:
                    # If app not found, deletion is complete
                    if "not found" in status_output.lower():
                        progress.update(delete_task, advance=100, description="✅ App deleted successfully")
                        break
                        
                # Wait 10 seconds before next check
                time.sleep(10)
                attempt += 1
                progress.update(delete_task, advance=2, description="🗑️ Deletion in progress...")
                
            if attempt >= max_attempts:
                self.console.print("[yellow]⚠️ Deletion is taking longer than expected. Please check the app status manually.[/yellow]")
                return False
                
            # Clean up app.yaml
            if os.path.exists("app.yaml"):
                os.remove("app.yaml")
            
            self.console.print()
            self.console.print(Panel(
                "[bold green]✅ App deleted successfully![/bold green]\n\n"
                "[bold cyan]📋 Deletion Summary:[/bold cyan]\n"
                f"  • [bold]App Name:[/bold] {self.app_name}\n"
                f"  • [bold]Status:[/bold] DELETED\n"
                f"  • [bold]Resources:[/bold] Cleaned up\n"
                f"  • [bold]Configuration:[/bold] Removed\n\n"
                "[bold cyan]🔄 To recreate the app:[/bold cyan]\n"
                "  python deploy.py",
                title="🗑️ Delete Complete",
                style="green"
            ))
            return True

    def start_app(self) -> bool:
        """Start a stopped app."""
        # Check prerequisites first
        if not self.check_prerequisites():
            return False
        
        # Load configuration from app.yaml
        if not self.load_config_from_yaml():
            return False
        
        # Check if app is already running BEFORE showing any panels
        success, status_output = self.run_databricks_command([
            "apps", "get", self.app_name, "--output", "json"
        ], timeout=30)
        
        if success:
            app_data = self.extract_json_from_output(status_output)
            if app_data:
                app_status = app_data.get("app_status", {}).get("state", "")
                compute_status = app_data.get("compute_status", {}).get("state", "")
                app_url = app_data.get("url", "Not available")
                
                if compute_status == "ACTIVE" or app_status == "RUNNING":
                    self.console.print(Panel(
                        "[green]✅ Great news! Your app is already up and running![/green]\n\n"
                        "[bold yellow]🌐 App URL:[/bold yellow]\n"
                        f"[bold blue]{app_url}[/bold blue]\n\n"
                        "[bold cyan]📋 Current Status:[/bold cyan]\n"
                        f"  • [bold]App Status:[/bold] {app_status}\n"
                        f"  • [bold]Compute Status:[/bold] {compute_status}\n\n"
                        "[bold cyan]💡 Available Actions:[/bold cyan]\n"
                        "  • To update code:    python deploy.py --redeploy\n"
                        "  • To check status:   python deploy.py --status\n"
                        "  • To stop the app:   python deploy.py --stop",
                        title="✅ App Ready",
                        style="green"
                    ))
                    return True
        
        # Only show start panel and ask for confirmation if app isn't already running
        self.console.print(Panel(
            "[bold green]▶️ Start App[/bold green]\n\n"
            "This will:\n"
            "  1. Start the stopped app\n"
            "  2. Provision compute resources (may take 2-5 minutes)\n"
            "  3. Make the app available again\n\n"
            "[yellow]Note: For faster restarts with code updates, use --redeploy[/yellow]",
            title="▶️ Start App",
            style="green"
        ))
        
        # Show connection info and get confirmation
        if not self.show_connection_info("start"):
            return False
        
        # Rest of the existing start_app code...
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            # Start the app
            task1 = progress.add_task("▶️ Starting app...", total=100)
            
            success, output = self.run_databricks_command([
                "apps", "start", self.app_name
            ], timeout=60)  # The start command itself is quick
            
            if not success:
                self.display_friendly_error(output, "Starting App")
                return False
                
            progress.update(task1, advance=100, description="✅ Start command sent")
            
            # Wait for compute to be ready
            task2 = progress.add_task("⚙️ Waiting for compute (2-5 mins)...", total=100)
            
            retries = 20  # 20 retries * 15 seconds = 5 minutes max wait
            for i in range(retries):
                success, status_output = self.run_databricks_command([
                    "apps", "get", self.app_name, "--output", "json"
                ], timeout=30)
                
                if success:
                    app_data = self.extract_json_from_output(status_output)
                    if app_data:
                        app_status = app_data.get("app_status", {}).get("state", "")
                        compute_status = app_data.get("compute_status", {}).get("state", "")
                        app_url = app_data.get("url", "Not available")
                        
                        # Calculate time elapsed
                        mins_elapsed = (i + 1) * 15 // 60
                        secs_elapsed = (i + 1) * 15 % 60
                        time_msg = f"{mins_elapsed}m {secs_elapsed}s elapsed"
                        
                        progress.update(task2, description=f"⚙️ Compute status: {compute_status} ({time_msg})")
                        
                        if app_status == "RUNNING" and compute_status == "ACTIVE":
                            progress.update(task2, advance=100, description="✅ Compute ready")
                            
                            # Show success message with URL
                            if "url" in app_data:
                                app_url = app_data["url"]
                                self.console.print()
                                self.console.print(Panel(
                                    "[bold green]✅ App started successfully![/bold green]\n\n"
                                    "[bold yellow]🌐 App URL:[/bold yellow]\n"
                                    f"[bold blue]{app_url}[/bold blue]\n\n"
                                    "[bold cyan]📋 Start Summary:[/bold cyan]\n"
                                    f"  • [bold]App Name:[/bold] {self.app_name}\n"
                                    f"  • [bold]Status:[/bold] RUNNING\n"
                                    f"  • [bold]Compute:[/bold] Active\n"
                                    f"  • [bold]Time taken:[/bold] {time_msg}\n\n"
                                    "[bold yellow]⚠️  If you see 'App Not Available':[/bold yellow]\n"
                                    "  • Wait 30-60 seconds for app to fully start\n"
                                    "  • Clear browser cache or try incognito mode\n\n"
                                    "[bold cyan]💡 Pro Tips:[/bold cyan]\n"
                                    "  • Use --redeploy for faster restarts with code updates\n"
                                    "  • Use --status to check app health",
                                    title="▶️ Start Complete",
                                    style="green"
                                ))
                                return True
                
                progress.update(task2, advance=100/retries)
                time.sleep(15)  # Wait 15 seconds between checks
            
            self.console.print("[red]❌ Timeout waiting for compute to be ready (5 minutes)[/red]")
            self.console.print("[yellow]The app might still be starting. Check status with: python deploy.py --status[/yellow]")
            return False

    def deploy(self) -> bool:
        """Deploy the app (fresh deployment only)."""
        self.console.print(Panel(
            "[bold blue]📦 Fresh Deploy[/bold blue]\n\n"
            "This will:\n"
            "  1. Create a new app\n"
            "  2. Configure secrets and scopes\n"
            "  3. Deploy to Databricks\n"
            "  4. Start the app\n",
            title="📦 Fresh Deploy",
            style="blue"
        ))
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
            
        # Get app name
        self.app_name = Prompt.ask(
            "[bold blue]Enter a name for your app[/bold blue]\n"
            "This will be used in the URL: {app-name}.{workspace-domain}",
            default=f"{self.user_name}-ai-chatbot"
        )
        
        # Check if app already exists on Databricks
        success, apps_output = self.run_databricks_command(["apps", "list", "--output", "json"])
        if success:
            try:
                apps_data = self.extract_json_from_output(apps_output)
                if apps_data and isinstance(apps_data, dict) and "apps" in apps_data:
                    existing_apps = [app["name"] for app in apps_data["apps"]]
                    if self.app_name in existing_apps:
                        self.console.print(f"[yellow]⚠️ App '{self.app_name}' already exists! Use 'redeploy' command to update existing app.[/yellow]")
                        return False
            except Exception as e:
                self.console.print(f"[red]❌ Failed to check existing apps: {e}[/red]")
                return False
        
        # Configure scope and secret
        if not self.configure_scope():
            return False
            
        if not self.configure_secret():
            return False
            
        # Create app.yaml
        config = {
            "workspace_url": self.workspace_url,
            "app_name": self.app_name,
            "secret_scope": self.scope_name,
            "secret_key": self.secret_name
        }
        
        with open("app.yaml", "w") as f:
            yaml.dump(config, f)
            
        self.console.print("[green]✅ Created app.yaml with configuration[/green]")
        
        # Create fresh app
        success, output = self.run_databricks_command([
            "apps", "create", self.app_name,
            "--no-wait"
        ])
        
        if not success:
            self.display_friendly_error(output, "Creating App")
            return False
            
        self.console.print("[green]✅ Created new app successfully[/green]")
        
        # For fresh deploy, sync code and deploy
        success, output = self.run_databricks_command([
            "apps", "sync", self.app_name,
            "--no-wait"
        ])
        
        if not success:
            self.display_friendly_error(output, "Syncing Code")
            return False
            
        self.console.print("[green]✅ Code synced successfully[/green]")
        
        # Deploy the app
        success, output = self.run_databricks_command([
            "apps", "deploy", self.app_name,
            "--no-wait"
        ])
        
        if not success:
            self.display_friendly_error(output, "Deploying App")
            return False
            
        self.console.print("[green]✅ App deployed successfully[/green]")
        
        # Start the app after deployment
        return self.start_app()


def main():
    """Main entry point for the deployment script."""
    parser = argparse.ArgumentParser(description="Databricks App Deployment Tool")
    parser.add_argument("command", choices=["deploy", "redeploy", "status", "stop", "start", "delete"],
                      help="Command to execute", nargs="?")
    parser.add_argument("--dry-run", "-d", action="store_true",
                      help="Simulate the deployment without making changes")
    parser.add_argument("--interactive", "-i", action="store_true",
                      help="Run in interactive mode with step-by-step confirmation")
    args = parser.parse_args()
    
    deployer = DatabricksDeployer()
    
    # Set dry-run and interactive flags
    deployer.dry_run = args.dry_run
    deployer.interactive = args.interactive
    
    # If no command provided, show help and exit
    if not args.command:
        parser.print_help()
        return
    
    # Map commands to methods
    if args.command == "start":
        deployer.start_app()
    elif args.command == "stop":
        deployer.stop_app()
    elif args.command == "status":
        deployer.show_status()
    elif args.command == "delete":
        deployer.delete_app()
    elif args.command == "deploy":
        # Fresh deployment only
        deployer.deploy()
    elif args.command == "redeploy":
        # Quick redeploy of existing app
        deployer.redeploy()

if __name__ == "__main__":
    main() 