from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from core.rag.agents import race_buddy_agents
from core.vector_store import vector_store

router = APIRouter()
logger = logging.getLogger(__name__)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message to send to the agent")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=[],
        description="Previous conversation history"
    )
    preferred_agent: Optional[str] = Field(
        default=None,
        description="Preferred agent: 'race_expert', 'training_coach', or 'general'"
    )


class ChatResponse(BaseModel):
    response: str = Field(..., description="Agent's response")
    agent_used: str = Field(...,
                            description="Which agent provided the response")
    success: bool = Field(...,
                          description="Whether the request was successful")
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for tracking")
    suggestions: Optional[List[str]] = Field(
        None, description="Follow-up question suggestions")


class QuickQuestionResponse(BaseModel):
    question: str
    category: str
    suggested_agent: str

# ============================================================================
# CHAT ENDPOINTS
# ============================================================================


@router.post("/ask", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Main endpoint for chatting with RaceBuddy AI agents.
    The agent is automatically selected based on question type.
    """
    try:
        logger.info(f"Received chat request: {request.message[:100]}...")

        # Convert Pydantic models to dict for agent
        conversation_history = []
        if request.conversation_history:
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        # Call agent system
        result = race_buddy_agents.chat(
            user_message=request.message,
            conversation_history=conversation_history
        )

        # Generate follow-up question suggestions
        suggestions = _generate_follow_up_suggestions(
            request.message,
            result.get("agent_used", "general")
        )

        response = ChatResponse(
            response=result["response"],
            agent_used=result["agent_used"],
            success=result["success"],
            suggestions=suggestions
        )

        logger.info(
            f"Chat response generated successfully by {result['agent_used']}")
        return response

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}"
        )


@router.get("/quick-questions", response_model=List[QuickQuestionResponse])
async def get_quick_questions():
    """
    Get predefined quick questions that users can use
    """
    quick_questions = [
        {
            "question": "Hur lång är banan på Lidingöloppet?",
            "category": "Loppinformation",
            "suggested_agent": "race_expert"
        },
        {
            "question": "Vilka är de svåraste partierna på banan?",
            "category": "Loppinformation",
            "suggested_agent": "race_expert"
        },
        {
            "question": "Hur ska jag träna inför Lidingöloppet?",
            "category": "Träning",
            "suggested_agent": "training_coach"
        },
        {
            "question": "Hur många veckor innan loppet ska jag börja träna?",
            "category": "Träning",
            "suggested_agent": "training_coach"
        },
        {
            "question": "Vilken utrustning behöver jag för loppet?",
            "category": "Utrustning",
            "suggested_agent": "race_expert"
        },
        {
            "question": "Hur många träningspass per vecka rekommenderas?",
            "category": "Träning",
            "suggested_agent": "training_coach"
        },
        {
            "question": "Vad är En Svensk Klassiker?",
            "category": "Loppinformation",
            "suggested_agent": "race_expert"
        },
        {
            "question": "Hur tränar jag bäst för terränglopp?",
            "category": "Träning",
            "suggested_agent": "training_coach"
        }
    ]

    return [QuickQuestionResponse(**q) for q in quick_questions]


@router.get("/agent-status")
async def get_agent_status():
    """
    Get status for AI agents and vector database
    """
    try:
        # Check vector database
        race_stats = vector_store.get_collection_stats(
            vector_store.RACE_DATA_COLLECTION)
        training_stats = vector_store.get_collection_stats(
            vector_store.TRAINING_COLLECTION)

        status = {
            "agents": {
                "race_expert": "online",
                "training_coach": "online",
                "general_assistant": "online",
                "supervisor": "online"
            },
            "vector_database": {
                "status": "online",
                "race_data_documents": race_stats.get("document_count", 0),
                "training_documents": training_stats.get("document_count", 0)
            },
            "llm_model": race_buddy_agents.llm.model_name,
            "system_status": "healthy"
        }

        return status

    except Exception as e:
        logger.error(f"Error checking agent status: {e}")
        return {
            "agents": {"status": "error"},
            "vector_database": {"status": "error"},
            "system_status": "unhealthy",
            "error": str(e)
        }


@router.post("/search-knowledge")
async def search_knowledge_base(query: str, category: str = "all"):
    """
    Search directly in the knowledge base without using agents
    """
    try:
        if category == "race" or category == "all":
            race_results = vector_store.query_race_data(query, n_results=3)
        else:
            race_results = []

        if category == "training" or category == "all":
            training_results = vector_store.query_training_data(
                query, n_results=3)
        else:
            training_results = []

        return {
            "query": query,
            "race_information": race_results,
            "training_information": training_results,
            "total_results": len(race_results) + len(training_results)
        }

    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search knowledge base: {str(e)}"
        )

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _generate_follow_up_suggestions(user_message: str, agent_used: str) -> List[str]:
    """Generate follow-up question suggestions based on user's question and agent"""

    suggestions = []

    if agent_used == "race_expert":
        suggestions = [
            "Vilken utrustning rekommenderar du för loppet?",
            "Hur ser höjdprofilen ut på banan?",
            "Vilka är de vanligaste misstagen på Lidingöloppet?"
        ]
    elif agent_used == "training_coach":
        suggestions = [
            "Hur många veckor innan loppet ska jag börja träna?",
            "Vilka träningspass är viktigast för terränglopp?",
            "Hur tränar jag bäst för backar?"
        ]
    else:
        suggestions = [
            "Berätta mer om Lidingöloppet",
            "Hur ska jag träna inför loppet?",
            "Vad är En Svensk Klassiker?"
        ]

    return suggestions[:3]  # Max 3 suggestions
