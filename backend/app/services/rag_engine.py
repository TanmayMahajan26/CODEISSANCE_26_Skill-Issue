import logging
import json
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
                temperature=0.1,
            )

    async def test_llm_connection(self) -> str:
        """Simple health check to verify LangChain can communicate with the Groq API."""
        if not self.llm:
            return "ERROR: GROQ_API_KEY is missing from environment variables."
        try:
            response = await self.llm.ainvoke(
                [HumanMessage(content="Hello! Please reply with exactly the word: 'Connected'.")]
            )
            return response.content
        except Exception as e:
            logger.error(f"Error communicating with Groq: {e}")
            return f"ERROR: Failed to connect to Groq. Details: {str(e)}"

    async def explain_match(self, golden_record_data: dict, source_records: list) -> str:
        """Explain why source records were merged into this golden record."""
        if not self.llm:
            return "AI Explainability is currently disabled (GROQ_API_KEY not set)."
        prompt = f"""You are a data analyst explaining an identity resolution match.
Golden Record Profile: {golden_record_data}
Source Records matched: {source_records}

Explain in 2-3 short sentences WHY these records were matched.
Focus on the strongest matching attributes (e.g. Exact PAN match, highly similar names).
Be professional and concise."""
        try:
            res = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return res.content
        except Exception as e:
            logger.error(f"Groq API error during explain_match: {e}")
            return "Failed to generate match explanation due to an AI service error."

    async def explain_opportunity(self, golden_record_data: dict, opportunity_data: dict) -> str:
        """Explain the reasoning behind a cross-sell/upsell opportunity."""
        if not self.llm:
            return "AI Opportunity Reasoning is currently disabled."
        prompt = f"""You are a financial advisor assistant explaining a product recommendation.
Customer Profile: {golden_record_data}
Opportunity: {opportunity_data}

Explain in 2-3 short sentences WHY this {opportunity_data.get('product_category', 'product')} recommendation is a good fit.
Reference their existing holdings and total relationship value."""
        try:
            res = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return res.content
        except Exception as e:
            logger.error(f"Groq API error during explain_opportunity: {e}")
            return "Failed to generate opportunity reasoning."

    async def translate_nl_query(self, query: str) -> dict:
        """Translate a natural language string into a structured JSON filter."""
        if not self.llm:
            return {"error": "AI query translation is disabled."}
        prompt = f"""Given the following natural language query from a relationship manager:
"{query}"

Extract the intent into a JSON object with this schema:
{{
    "filters": {{
        "field_name": "value"
    }},
    "sort_by": "field_name",
    "sort_order": "asc|desc",
    "limit": 10
}}
Valid filter fields: name, city, segment, pan, min_trv, max_trv, product.
Respond ONLY with valid JSON. No markdown wrappers."""
        try:
            res = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = res.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            return json.loads(content)
        except Exception as e:
            logger.error(f"Groq API error during translate_nl_query: {e}")
            return {"error": "Failed to translate query."}

    async def suggest_conflict_resolution(self, record_a: dict, record_b: dict, match_score: dict = None) -> dict:
        """Suggest how to resolve a conflict between two source records."""
        if not self.llm:
            return {"recommendation": "manual", "confidence": 0.0, "reasoning": "AI disabled."}
        prompt = f"""You are a data steward assisting with identity resolution.
Two records have been flagged for manual review:
Record A: {record_a}
Record B: {record_b}
Match Scores: {match_score}

Suggest whether these should be merged or kept separate.
Respond ONLY with valid JSON in this schema:
{{
    "recommendation": "merge|separate",
    "confidence": 0.0 to 1.0,
    "reasoning": "Short 1 sentence explanation"
}}"""
        try:
            res = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = res.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            return json.loads(content)
        except Exception as e:
            logger.error(f"Groq API error during suggest_conflict_resolution: {e}")
            return {"recommendation": "manual", "confidence": 0.0, "reasoning": "AI error."}


# Singleton instance
rag_engine = RagEngine()
