# 🚀 Databricks AI Chatbot - Deployment Guide

This guide provides two options for deploying your AI Chatbot to any Databricks workspace.

## 🎯 Quick Start

**Recommended:** Use our smart Python deployment script that handles everything automatically:

```bash
# Interactive dry run (perfect for demos)
python deploy.py --dry-run --interactive

# Preview what will be done
python deploy.py --dry-run

# Deploy to your workspace
python deploy.py
```

## 📋 Prerequisites

1. **Databricks CLI** (v0.213.0+)
   ```bash
   curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/v0.254.0/install.sh | sudo sh
   ```

2. **Configure CLI** for your workspace
   ```bash
   databricks configure --token
   ```

3. **OpenAI API Key** (get from https://platform.openai.com/api-keys)

## 🐍 Option 1: Smart Python Deploy (Recommended)

Our intelligent Python script (`deploy.py`) provides:

- ✅ **Beautiful UI** with progress bars and colors
- ✅ **Smart conflict detection** - avoids workspace limits
- ✅ **Demo-safe** - uses unique names per user
- ✅ **Dry run mode** - preview without changes
- ✅ **Interactive mode** - perfect for demos
- ✅ **Error handling** with troubleshooting tips
- ✅ **JSON parsing** that handles CLI warnings

### 🔧 Technical Implementation

The deployment script uses the **Databricks CLI** via subprocess calls, not the Python SDK or direct APIs. This approach:

- **Uses:** `subprocess.run(["databricks"] + cmd, ...)` for all operations
- **Commands:** `databricks apps create`, `databricks secrets list-scopes`, etc.
- **Benefits:** Leverages existing CLI tooling, authentication, and error handling
- **Perfect for:** Deployment automation where CLI is the standard interface

**Why CLI over Python SDK?**
- ✅ Target audience expects CLI for deployment scripts
- ✅ Users already have CLI configured for workspace access
- ✅ CLI provides rich formatted output and error messages
- ✅ Apps API is relatively new - CLI is the primary deployment interface
- ✅ Simpler authentication (uses existing CLI config)

### Usage

```bash
# Help and examples
python deploy.py --help

# Interactive dry run (recommended for first time)
python deploy.py -d -i

# Quick preview
python deploy.py --dry-run

# Deploy for real
python deploy.py

# Interactive deployment (with pauses)
python deploy.py --interactive

# Quick redeploy after code changes
python deploy.py --redeploy

# Check current app status
python deploy.py --status
```

The script will:
1. Check your CLI configuration
2. Create a unique secret scope (e.g., `arao-chatbot`)
3. Add your OpenAI API key securely
4. Create and deploy your app
5. Provide the live URL

**Perfect for demo environments** - uses your email prefix to avoid conflicts!

### 📊 Additional Commands

**Status Check:** Monitor your deployed app
```bash
python deploy.py --status
# Shows: health status, app URL, deployment details, troubleshooting tips
```

**Quick Redeploy:** Update app with latest code changes
```bash
python deploy.py --redeploy  
# Syncs code and redeploys without reconfiguration
```

## 🛠️ Option 2: Manual Deployment

If you prefer manual control, follow these steps:

### Step 1: Create Secret Scope
```bash
# Use a unique name to avoid conflicts
databricks secrets create-scope "yourname-chatbot"
```

### Step 2: Add OpenAI API Key
```bash
# Add your OpenAI key securely
echo "your-openai-api-key" | databricks secrets put-secret "yourname-chatbot" "openai_api_key"
```

### Step 3: Configure app.yaml
Create `app.yaml` with your scope/secret names:
```yaml
command: ['streamlit', 'run', 'app.py', '--server.port=8501', '--server.address=0.0.0.0', '--server.headless=true']
env:
  - name: 'OPENAI_API_KEY'
    value: '{{secrets/yourname-chatbot/openai_api_key}}'
```

### Step 4: Deploy App
```bash
# Create the app
databricks apps create "yourname-ai-chatbot"

# Sync your code
databricks sync . "/Workspace/Users/your.email@company.com/yourname-ai-chatbot" \
  --exclude "*.pyc" --exclude ".git" --exclude "venv"

# Deploy
databricks apps deploy "yourname-ai-chatbot" \
  --source-code-path "/Workspace/Users/your.email@company.com/yourname-ai-chatbot"
```

### Step 5: Get Your App URL
```bash
databricks apps get "yourname-ai-chatbot"
```

## 🔧 Troubleshooting

### Common Issues

**"Scope already exists"** or **"App limit reached"**
- Use unique names with your initials/email prefix
- The Python script handles this automatically

**"Permission denied on scope"**
- Use a different scope name
- Check with `databricks secrets list-acls <scope-name>`

**"CLI not configured"**
- Run `databricks configure --token`
- Get your token from your workspace → Settings → Developer → Access tokens

**"Secret interpolation failed"**
- Check your `app.yaml` syntax
- Verify scope and secret names exist
- Use `{{secrets/scope/secret}}` format (double braces)

### Useful Commands

```bash
# Check your configuration
databricks current-user me

# List your scopes
databricks secrets list-scopes

# Check app status
databricks apps get "your-app-name"

# View app logs
databricks apps logs "your-app-name"

# Delete app if needed
databricks apps delete "your-app-name"
```

## 🎨 Features Your Deployed App Will Have

- 💬 **Chat Interface** - Clean Streamlit UI
- 🎭 **Themes** - Light/Dark mode toggle
- 🧠 **Model Selection** - GPT-4, GPT-3.5-turbo, etc.
- 📚 **Chat History** - Save/load conversations
- 🔍 **Web Search** - Real-time information lookup
- 📱 **Responsive** - Works on mobile/desktop
- 🔒 **Secure** - Uses Databricks secrets management

## 🎯 Next Steps After Deployment

1. **Visit your app URL** (provided after deployment)
2. **Login** with your Databricks credentials
3. **Start chatting** with your AI assistant!

## 🤝 Sharing Your App

Grant access to others:
```bash
databricks apps set-permissions "your-app-name" --json '{
  "access_control_list": [
    {"user_name": "colleague@company.com", "permission_level": "CAN_USE"}
  ]
}'
```

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Use `python deploy.py --dry-run` to debug
3. Verify your CLI configuration and permissions
4. Check Databricks workspace limits (apps, scopes)

---

**Ready to deploy?** Run `python deploy.py --dry-run --interactive` to start! 🚀 