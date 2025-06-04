# Databricks AI Chatbot

An intelligent chatbot assistant built with Streamlit and LangChain that helps users with Databricks-related questions and information.

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
git clone https://github.com/[your-username]/databricks-chatbot-app.git
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