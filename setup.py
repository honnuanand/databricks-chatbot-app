from setuptools import setup, find_packages

setup(
    name="databricks-chatbot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "langchain",
        "langchain-openai",
        "langchain-community",
        "python-dotenv",
        "duckduckgo-search"
    ],
    python_requires=">=3.9",
) 