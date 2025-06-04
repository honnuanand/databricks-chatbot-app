# Databricks AI Chatbot

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Deploying to Databricks Apps

### Prerequisites
- Access to a Databricks workspace with Apps enabled
- Admin privileges to manage secrets and environment variables
- Git repository access

### Deployment Steps

1. **Access Apps Section**
   - Navigate to your Databricks workspace
   - Click on "Apps" in the left sidebar
   - Select "Create App"

2. **Configure App Source**
   - Choose "Import from Git"
   - Enter repository URL: `https://github.com/honnuanand/databricks-chatbot-app.git`
   - Select the branch (e.g., `main`)

3. **Configure Environment**
   - In the App configuration, set the following:
     ```
     PYTHON_VERSION=3.9
     ```

4. **Set Required Secrets**
   - Go to "App Settings" > "Secrets"
   - Add the following secret:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

5. **Configure Resources**
   - Recommended minimum settings:
     - Memory: 4 GB
     - CPU: 2 cores

6. **Access Control**
   - Under "Permissions":
     - Add users/groups who should have access
     - Set appropriate permission levels (Can Use, Can Manage, etc.)

7. **Deploy**
   - Click "Create" to deploy the app
   - Wait for the deployment to complete
   - Access your app using the provided URL

### Updating the App

1. **Push Changes**
   - Make changes to your local repository
   - Commit and push to GitHub
   ```bash
   git add .
   git commit -m "Your update message"
   git push origin main
   ```

2. **Redeploy**
   - In Databricks Apps, find your app
   - Click "Update"
   - Select "Redeploy" to pull latest changes

### Troubleshooting

- **App Fails to Start**
  - Check logs in the App's "Logs" section
  - Verify all required secrets are set
  - Ensure Python version is correct

- **Performance Issues**
  - Consider increasing memory/CPU allocation
  - Check app logs for memory usage
  - Monitor response times in logs

### Best Practices

- Regularly update dependencies
- Monitor app usage and logs
- Back up chat history periodically
- Test updates locally before deploying
- Use version tags for stable releases 