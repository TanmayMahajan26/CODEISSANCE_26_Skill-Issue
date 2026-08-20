import logging
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RagEngine:
    """
    Centralized AI Orchestration Engine using LangChain and Groq.
    This service will handle Match Explainability, Opportunity Reasoning,
    Natural Language Queries, and Conflict Resolution Suggestions.
    """

    def __init__(self):
        # We will only initialize if the API key is present to avoid crashes
        if not settings.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY is not set. AI features will fail or be mocked.")
            self.llm = None
        else:
            logger.info(f"Initializing ChatGroq with model: {settings.GROQ_MODEL}")
            self.llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name=settings.GROQ_MODEL,
                temperature=0.1,  # Low temperature for deterministic/factual responses
            )

    async def test_llm_connection(self) -> str:
        """
        Simple health check to verify LangChain can communicate with the Groq API.
        """
        if not self.llm:
            return "ERROR: GROQ_API_KEY is missing from environment variables."

        try:
            logger.info("Sending health check ping to Groq...")
            # We use invoke for a simple synchronous test, but we can also use ainvoke
            response = await self.llm.ainvoke(
                [HumanMessage(content="Hello! Please reply with exactly the word: 'Connected'.")]
            )
            return response.content
        except Exception as e:
            logger.error(f"Error communicating with Groq: {e}")
            return f"ERROR: Failed to connect to Groq. Details: {str(e)}"

# Singleton instance
rag_engine = RagEngine()
