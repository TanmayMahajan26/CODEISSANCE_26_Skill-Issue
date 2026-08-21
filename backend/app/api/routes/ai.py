"""
Nexus360 — Nexus AI Chat Router.

Provides an AI assistant endpoint powered by Google Gemini for querying
Customer 360 data, identity resolution insights, opportunities, and business rules.
"""

import os
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
import httpx

from app.core.config import settings
from app.api.deps import get_current_user
from app.schemas.auth import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Nexus AI"])

SYSTEM_PROMPT = (
    "You are Nexus AI, an intelligent assistant for Nexus360, a fintech Customer 360 "
    "and Identity Resolution platform. Help users understand customer data, identity "
    "matches, opportunities, analytics and financial relationships. Do not invent "
    "customer data. Keep answers concise and professional."
)


class ChatRequest(BaseModel):
    page: Optional[str] = Field(default="general", description="Current page name")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Contextual data if available")
    message: str = Field(..., description="User question")


class ChatResponse(BaseModel):
    response: str = Field(..., description="AI generated response")


@router.post("/ai/chat", response_model=ChatResponse, summary="Nexus AI Chat Completion")
async def chat_with_nexus_ai(
    request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user)
) -> ChatResponse:
    """
    Process a chat message using Google Gemini with Nexus360 domain context.
    """
    user_message = request.message.strip()
    if not user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty."
        )

    # 1. Retrieve Gemini API Key from environment or settings
    api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or getattr(settings, "GEMINI_API_KEY", "")
    ).strip()

    model_name = getattr(settings, "GEMINI_MODEL", "gemini-3.1-pro-preview")

    # 2. Build Prompt
    context_str = f"Current User Info: Name: {current_user.full_name}, Role: {current_user.role}, Last Login: {current_user.last_login_at}\n"
    if request.context:
        context_str += f"Current Page Context ({request.page}):\n{request.context}\n"
    elif request.page:
        context_str += f"Current Page: {request.page}\n"

    full_user_prompt = f"{context_str}User question: {user_message}"

    # 3. If API Key is provided, call Gemini REST API
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{full_user_prompt}"}]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 1024,
                }
            }

            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(url, json=payload)
                
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    first_candidate = candidates[0]
                    parts = first_candidate.get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        reply_text = parts[0]["text"].strip()
                        return ChatResponse(response=reply_text)
                
                # Fallback if structure is unexpected
                return ChatResponse(response="Nexus AI could not generate a response. Please try rephrasing.")
            else:
                err_body = resp.text
                logger.warning("Gemini API error (HTTP %d): %s", resp.status_code, err_body)
                # If quota/auth error, provide clear guidance
                if resp.status_code in (400, 401, 403):
                    return ChatResponse(
                        response=f"Gemini API returned {resp.status_code}: Please verify your GEMINI_API_KEY configuration."
                    )
                return ChatResponse(
                    response=f"Nexus AI encountered an upstream error ({resp.status_code}). Please try again shortly."
                )

        except Exception as e:
            logger.error("Error communicating with Gemini API: %s", e)
            return ChatResponse(
                response=f"Nexus AI service temporarily unreachable: {str(e)}"
            )

    # 4. Fallback response when GEMINI_API_KEY is not configured yet
    return ChatResponse(
        response=(
            f"**Nexus AI Assistant** (Running in demo mode)\n\n"
            f"I received your question about **{request.page or 'Nexus360'}**: \"{user_message}\".\n\n"
            f"To enable live generative responses with Google Gemini, please configure `GEMINI_API_KEY` in `backend/.env`.\n\n"
            f"Nexus360 provides unified identity resolution across Equity, Mutual Funds, Insurance, Loan, and Wealth silos, "
            f"with deterministic, fuzzy, and 384-dimensional semantic embedding matching."
        )
    )
