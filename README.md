# Databricks AI Chatbot

[![CI Status](https://github.com/honnuanand/databricks-chatbot-app/actions/workflows/python-app.yml/badge.svg)](https://github.com/honnuanand/databricks-chatbot-app/actions/workflows/python-app.yml)
[![GitHub tag](https://img.shields.io/github/v/tag/honnuanand/databricks-chatbot-app)](https://github.com/honnuanand/databricks-chatbot-app/tags)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![Security: bandit](https://img.shields.io/badge/security-safety-green.svg)](https://github.com/pyupio/safety)

A modern AI chatbot providing expert assistance for Databricks queries. Built with Streamlit and powered by LangChain + GPT models, it features real-time web search, contextual responses, and a sleek UI. Get instant help with Databricks technology, best practices, and implementations.

## Key Features

- 🧠 Advanced AI Integration
  - Powered by OpenAI's GPT models (3.5-turbo/GPT-4)
  - Context-aware conversation management
  - Intelligent response generation with temperature control

- 🔍 Enhanced Information Access
  - Real-time web search integration
  - Up-to-date Databricks documentation references
  - Comprehensive knowledge base access

- 💫 Modern User Experience
  - Sleek, responsive interface with glass-morphism design
  - Dark/Light theme support with smooth transitions
  - Intuitive chat management and history
  - Customizable system prompts and model settings

- 🛠 Technical Capabilities
  - Persistent chat history management
  - Modular and maintainable codebase
  - Easy deployment and configuration
  - Environment-based settings management

## Features

- 🤖 AI-powered responses using GPT models
- 🔍 Real-time web search capabilities
- 💾 Chat history management
- 🎨 Dark/Light theme support
- ⚙️ Configurable model settings
- 🎯 Focused on Databricks expertise

## 🚀 Quick Deploy to Databricks Apps

Transform your local chatbot into an enterprise-ready application with **zero infrastructure management**!

### ⚡ One-Click Deployment
```bash
# 1. Configure Databricks CLI (one-time setup)
databricks configure --token

# 2. Run smart Python deployment script
python deploy.py

# Preview changes first (recommended)
python deploy.py --dry-run

# Interactive deployment for demos
python deploy.py --dry-run --interactive
```

### 🎯 What You Get
- **Enterprise URL**: `https://your-app-name-{workspace-id}.databricksapps.com`
- **SSO Authentication**: Users login with company credentials
- **Auto-scaling**: Handles multiple concurrent users
- **Zero Maintenance**: Databricks manages all infrastructure
- **Built-in Security**: Secrets management and data governance

### 📖 Comprehensive Guide
For detailed deployment instructions, troubleshooting, and advanced configuration, see:
**[📋 DEPLOYMENT.md](./DEPLOYMENT.md)**

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/honnuanand/databricks-chatbot-app.git
cd databricks-chatbot-app
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

## Environment Setup

The application supports multiple ways to manage credentials and environment variables:

### Local Development

1. **Using Environment Variables (Recommended for Local Development)**:
   ```bash
   # Set directly in your terminal
   export OPENAI_API_KEY='your-key-here'
   
   # Or create a script (don't commit this) named set_env.sh:
   echo 'export OPENAI_API_KEY="your-key-here"' > set_env.sh
   source set_env.sh
   ```

2. **Using .env File (Alternative)**:
   ```bash
   # Create .env file (already in .gitignore)
   echo 'OPENAI_API_KEY=your-key-here' > .env
   ```

   ⚠️ **Security Note**: Never commit the `.env` file or expose your API key in the codebase.

### Databricks Deployment

1. **Using Databricks Secrets (Recommended for Production)**:
   ```bash
   # Create a secret scope (one-time setup)
   databricks secrets create-scope chatbot-secrets --scope-backend-type DATABRICKS
   
   # Add your OpenAI API key to the scope
   databricks secrets put-secret --scope chatbot-secrets --key OPENAI_API_KEY --string-value 'your-key-here'
   ```

2. **Configuration Files**:
   - `app.yaml`: Defines app configuration and secret requirements
   - `databricks.yml`: Defines deployment configuration and environment setup

The application automatically handles credential management:
1. First tries to fetch from Databricks secrets (when running in Databricks)
2. Falls back to environment variables (for local development)
3. Provides clear error messages if credentials are missing

## Usage

Run the application:
```bash
streamlit run app.py
```

The app will be available at http://localhost:8501

## Project Structure

```
databricks-chatbot-app/
├── src/
│   ├── components/      # UI components
│   ├── services/       # Business logic
│   └── styles/         # Theme styling
├── app.py              # Entry point
├── setup.py           # Package configuration
└── README.md          # Documentation
```

## Configuration

- Model: Choose between GPT-3.5-turbo and GPT-4
- Temperature: Adjust response creativity (0.0 - 1.0)
- System Prompt: Customize the AI's behavior
- Theme: Toggle between dark and light modes

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Development

### Testing
Run the test suite:
```bash
pytest
```

View test coverage:
```bash
pytest --cov=src --cov-report=html
```

Current test coverage: 98%

### CI/CD Pipeline
The project uses GitHub Actions for continuous integration and testing. The pipeline:
- Runs on Python 3.9
- Executes unit tests with pytest
- Performs code quality checks with flake8
- Scans dependencies for security vulnerabilities
- Generates test coverage reports
- Builds the package

Required GitHub Secrets:
- `OPENAI_API_KEY`: Your OpenAI API key for testing

### Security Best Practices
1. **API Key Management**:
   - Use Databricks secrets for production deployment
   - Use environment variables for local development
   - Never commit credentials to the repository
   - API keys are automatically rotated in CI/CD

2. **Code Security**:
   - Regular dependency updates
   - Security scanning with safety
   - Code coverage monitoring
   - Automated testing

3. **Access Control**:
   - Scope-based secret access
   - Role-based app access
   - Audit logging enabled

### Code Quality
Before submitting a PR:
1. Run tests: `pytest`
2. Check code style: `flake8`
3. Check dependencies: `safety check`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Deploying to Databricks Apps

### Prerequisites
- Access to a Databricks workspace with Apps enabled
- Admin privileges to manage secrets and environment variables
- Git repository access

### Configuration
The app uses two main configuration files:
1. `app.yaml`: Defines app-specific settings
   ```yaml
   secrets:
     - key: OPENAI_API_KEY
       description: "OpenAI API Key for GPT models"
       required: true
   ```

2. `databricks.yml`: Defines deployment settings
   ```yaml
   service:
     env:
       - name: "OPENAI_API_KEY"
         value: "${OPENAI_API_KEY}"
   ```

### Deployment Methods

#### Method 1: Using Databricks UI
1. **Upload App Files**
   - Go to your Databricks workspace
   - Click **Workspace** in the sidebar
   - Upload your app files to a designated folder

2. **Deploy the App**
   - Click **Compute** in the sidebar
   - Go to the **Apps** tab
   - Click your app name in the **Name** column
   - Click **Deploy** and select your app folder
   - Review configuration and click **Deploy**

#### Method 2: Using Databricks CLI (Recommended)
1. **Sync Files to Workspace**
   ```bash
   databricks sync --watch . /Workspace/Users/your-email@org.com/databricks-chatbot-app
   ```

2. **Deploy the App**
   ```bash
   databricks apps deploy databricks-chatbot \
      --source-code-path /Workspace/Users/your-email@org.com/databricks-chatbot-app
   ```

### Post-Deployment
1. **Verify Secrets**:
   - Check secret scope access
   - Verify environment variables
   - Test API key rotation

2. **Monitor Security**:
   - Review access logs
   - Check secret usage
   - Monitor API usage

### Troubleshooting
- **App Fails to Start**
  - Check logs in the App's "Logs" section
  - Verify all required secrets are set
  - Ensure Python version matches app.yaml

- **Performance Issues**
  - Check resource utilization in logs
  - Consider adjusting memory/CPU allocation
  - Monitor response times

- **SSL Warnings**
  - If you see urllib3 SSL warnings, ensure your environment uses OpenSSL 1.1.1+
  - Consider upgrading urllib3 or your SSL implementation

### Best Practices
- Regularly update dependencies
- Monitor app usage and logs
- Back up chat history periodically
- Test updates locally before deploying
- Use version tags for stable releases 

## Additional Development Dependencies

To install additional development dependencies, use the following command:
```bash
pip install pytest pytest-cov flake8 safety build
``` 