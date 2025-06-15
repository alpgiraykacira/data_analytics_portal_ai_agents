from langchain_openai import ChatOpenAI
from logger import setup_logger

class LLM:
    def __init__(self):
        """Initialize the language model class"""
        self.logger = setup_logger()
        self.llm_fast = None
        self.llm_reasoning = None
        self.llm_low = None
        self.llm_mid = None
        self.llm_high = None
        self.initialize_llms()

    def initialize_llms(self):
        """Initialize language models"""
        try:
            self.llm_fast = ChatOpenAI(model="gpt-4.1-nano-2025-04-14", temperature=0, max_completion_tokens=4096)
            self.llm_reasoning = ChatOpenAI(model="o4-mini-2025-04-16", max_completion_tokens=4096)
            self.llm_low = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_completion_tokens=4096)
            self.llm_mid = ChatOpenAI(model="gpt-4.1-mini", temperature=0, max_completion_tokens=4096)
            self.llm_high = ChatOpenAI(model="gpt-4.1", temperature=0.5, max_completion_tokens=4096)
            self.logger.info("Language models initialized successfully.")
        except Exception as e:
            self.logger.error(f"Error initializing language models: {str(e)}")
            raise

    def get_models(self):
        """Return all initialized language models"""
        return {
            "llm_fast": self.llm_fast,
            "llm_reasoning": self.llm_reasoning,
            "llm_low": self.llm_low,
            "llm_mid": self.llm_mid,
            "llm_high": self.llm_high
        }
