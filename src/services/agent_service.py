"""Agent service for managing the LangChain agent and related functionality."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage

class AgentService:
    def __init__(self, model_name: str, temperature: float, system_prompt: str, openai_api_key: str):
        """Initialize the agent service with the specified configuration."""
        self.validate_temperature(temperature)
        
        self.model_name = model_name
        self.temperature = temperature
        self.system_prompt = system_prompt
        self.openai_api_key = openai_api_key
        self.memory = None
        self.agent_executor = None
        self.llm = None  # Add LLM instance variable
        self.create_agent()
    
    @staticmethod
    def validate_temperature(temperature: float) -> None:
        """Validate that temperature is between 0 and 1."""
        if not isinstance(temperature, (int, float)):
            raise ValueError("Temperature must be a number")
        if temperature < 0 or temperature > 1:
            raise ValueError("Temperature must be between 0 and 1")
    
    def create_agent(self) -> None:
        """Create or recreate the agent with current settings."""
        # Initialize the chat model
        self.llm = ChatOpenAI(  # Store LLM instance
            model_name=self.model_name,
            temperature=self.temperature,
            openai_api_key=self.openai_api_key
        )
        
        # Initialize tools
        tools = [
            DuckDuckGoSearchRun(name="web_search"),
        ]
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create the agent
        agent = create_openai_functions_agent(self.llm, tools, prompt)
        
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=self.memory,
            verbose=True
        )
    
    def update_configuration(self, model_name: str = None, temperature: float = None, 
                           system_prompt: str = None) -> None:
        """Update agent configuration and recreate the agent."""
        if temperature is not None:
            self.validate_temperature(temperature)
            self.temperature = temperature
        if model_name is not None:
            self.model_name = model_name
        if system_prompt is not None:
            self.system_prompt = system_prompt
        
        self.create_agent()
    
    def get_response(self, user_input: str) -> str:
        """Get a response from the agent for the given user input."""
        if not user_input or not isinstance(user_input, str):
            raise ValueError("Input must be a non-empty string")
            
        if self.agent_executor is None:
            self.create_agent()
        
        try:
            response = self.agent_executor.invoke({
                "input": user_input,
            })
            return response["output"]
        except Exception as e:
            # Log the error here if needed
            raise e 