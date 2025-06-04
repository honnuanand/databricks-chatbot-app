# Databricks AI Chatbot

[![CI Status](https://github.com/honnuanand/databricks-chatbot-app/actions/workflows/python-app.yml/badge.svg)](https://github.com/honnuanand/databricks-chatbot-app/actions/workflows/python-app.yml)
[![codecov](https://codecov.io/gh/honnuanand/databricks-chatbot-app/branch/main/graph/badge.svg)](https://codecov.io/gh/honnuanand/databricks-chatbot-app)
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

4. Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

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
- `CODECOV_TOKEN`: Token for uploading coverage reports (optional)

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

### Configuration
The app uses `app.yaml` for deployment configuration:
- Python version: 3.9
- Memory: 4-8 GB
- CPU: 2-4 cores
- Required secrets: OPENAI_API_KEY

### Post-Deployment
1. **Monitor Deployment**
   - Check the app overview page for deployment status
   - View logs in the **Logs** tab for debugging

2. **Access Control**
   - Configure user access in the **Permissions** tab
   - Set appropriate permission levels

3. **Updates and Maintenance**
   - Push code changes to the repository
   - Redeploy using the same method as initial deployment
   - Monitor app performance and logs

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