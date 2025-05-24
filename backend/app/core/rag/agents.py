"""
RaceBuddy AI Agents using LangGraph and ChromaDB
- race_expert_agent: Answers questions about Lidingöloppet 
- training_coach_agent: Provides training advice and tips
- supervisor_agent: Directs questions to the right agent
"""

from typing import Dict, List, Any, Optional, TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.tools import tool
import json
import logging

from settings import settings
from core.vector_store import vector_store

logger = logging.getLogger(__name__)

# ============================================================================
# STATE DEFINITION
# ============================================================================


class AgentState(TypedDict):
    """State shared between all agents"""
    messages: List[BaseMessage]
    user_query: str
    agent_type: str
    context_data: Optional[Dict[str, Any]]
    final_response: Optional[str]

# ============================================================================
# TOOLS/FUNCTIONS FOR RAG
# ============================================================================


@tool
def search_race_information(query: str) -> str:
    """Search for information about Lidingöloppet from the vector database."""
    try:
        results = vector_store.query_race_data(query, n_results=3)

        if not results:
            return "Ingen specifik information hittades om det du frågade efter."

        # Format results
        formatted_info = []
        for i, result in enumerate(results[:3], 1):
            content = result['content'][:800]  # Limit length
            formatted_info.append(f"Information {i}:\n{content}")

        return "\n\n".join(formatted_info)

    except Exception as e:
        logger.error(f"Error searching race information: {e}")
        return "Kunde inte hämta loppinformation just nu."


@tool
def search_training_advice(query: str) -> str:
    """Search for training advice and tips from the vector database."""
    try:
        results = vector_store.query_training_data(query, n_results=3)

        if not results:
            return "Ingen specifik träningsinformation hittades."

        # Format results
        formatted_advice = []
        for i, result in enumerate(results[:3], 1):
            content = result['content'][:800]  # Limit length
            formatted_advice.append(f"Träningsråd {i}:\n{content}")

        return "\n\n".join(formatted_advice)

    except Exception as e:
        logger.error(f"Error searching training advice: {e}")
        return "Kunde inte hämta träningsråd just nu."

# ============================================================================
# AGENT DEFINITIONS
# ============================================================================


class RaceBuddyAgents:
    """Collects all AI agents for RaceBuddy"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_CHAT_MODEL,
            temperature=settings.AGENT_TEMPERATURE,
            max_tokens=settings.AGENT_MAX_TOKENS,
            openai_api_key=settings.OPENAI_API_KEY
        )

        # Create graph
        self.graph = self._build_agent_graph()

    def _build_agent_graph(self):
        """Build LangGraph with all agents"""

        # Define workflow
        workflow = StateGraph(AgentState)

        # Add nodes (agents)
        workflow.add_node("supervisor", self._supervisor_agent)
        workflow.add_node("race_expert", self._race_expert_agent)
        workflow.add_node("training_coach", self._training_coach_agent)
        workflow.add_node("general_assistant", self._general_assistant_agent)

        # Define flow
        workflow.set_entry_point("supervisor")

        # Supervisor determines which agent should handle the question
        workflow.add_conditional_edges(
            "supervisor",
            self._route_to_agent,
            {
                "race_expert": "race_expert",
                "training_coach": "training_coach",
                "general_assistant": "general_assistant",
                "end": END
            }
        )

        # All agents go to END when finished
        workflow.add_edge("race_expert", END)
        workflow.add_edge("training_coach", END)
        workflow.add_edge("general_assistant", END)

        return workflow.compile()

    def _supervisor_agent(self, state: AgentState) -> AgentState:
        """Supervisor that directs questions to the right specialist agent"""

        user_query = state["user_query"].lower()

        # Simple classification based on keywords
        race_keywords = [
            "lopp", "lidingöloppet", "tävling", "bana", "distans", "höjdmeter",
            "svenska klassiker", "anmälan", "resultat", "starttid", "väder",
            "utrustning", "race", "tävlingsdag"
        ]

        training_keywords = [
            "träning", "träna", "förberedelse", "schema", "plan", "pass",
            "intervall", "längdpass", "tempo", "återhämtning", "volym",
            "periodisering", "coaching", "coach", "kondition", "form"
        ]

        # Count matches
        race_score = sum(
            1 for keyword in race_keywords if keyword in user_query)
        training_score = sum(
            1 for keyword in training_keywords if keyword in user_query)

        # Determine agent
        if race_score > training_score and race_score > 0:
            agent_type = "race_expert"
        elif training_score > 0:
            agent_type = "training_coach"
        else:
            agent_type = "general_assistant"

        logger.info(
            f"Supervisor routing to: {agent_type} (race:{race_score}, training:{training_score})")

        return {
            **state,
            "agent_type": agent_type
        }

    def _route_to_agent(self, state: AgentState) -> str:
        """Router function for conditional edges"""
        return state["agent_type"]

    def _race_expert_agent(self, state: AgentState) -> AgentState:
        """Expert on Lidingöloppet - answers race-specific questions"""

        user_query = state["user_query"]

        # Get relevant information from RAG
        race_info = search_race_information.invoke({"query": user_query})

        # System prompt for race expert
        system_prompt = f"""Du är en expert på Lidingöloppet och En Svensk Klassiker. 
Du hjälper användare med information om:
- Loppets bana, distans och svårighetsgrad
- Anmälan och praktisk information  
- Tävlingsstrategier och tips för loppet
- Historik och statistik
- Utrustning specifikt för Lidingöloppet

Basera dina svar på denna information från databasen:
{race_info}

Svara på svenska, var hjälpsam och konkret. Om du inte vet något specifikt, säg det ärligt.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query)
        ]

        try:
            response = self.llm.invoke(messages)
            final_response = response.content
        except Exception as e:
            logger.error(f"Error in race expert agent: {e}")
            final_response = "Ursäkta, jag har problem att svara på din fråga om loppet just nu. Försök igen senare."

        return {
            **state,
            "final_response": final_response,
            "context_data": {"source": "race_expert", "rag_data": race_info}
        }

    def _training_coach_agent(self, state: AgentState) -> AgentState:
        """Training coach - provides training advice and tips"""

        user_query = state["user_query"]

        # Get training advice from RAG
        training_advice = search_training_advice.invoke({"query": user_query})

        # System prompt for training coach
        system_prompt = f"""Du är en erfaren löpträningscoach specialiserad på terränglopp och Lidingöloppet.
Du hjälper användare med:
- Träningsplaner och periodisering
- Specifika träningspass och intensiteter
- Förberedelser för Lidingöloppet
- Återhämtning och skadeförebyggande
- Mental träning och motivation
- Nutrition och vätskebalans

Basera dina råd på denna expertinformation:
{training_advice}

Ge konkreta, praktiska råd på svenska. Anpassa råden efter användarens nivå när det är möjligt.
Var alltid säker och ansvarsfull med träningsråd.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query)
        ]

        try:
            response = self.llm.invoke(messages)
            final_response = response.content
        except Exception as e:
            logger.error(f"Error in training coach agent: {e}")
            final_response = "Ursäkta, jag har problem att ge träningsråd just nu. Försök igen senare."

        return {
            **state,
            "final_response": final_response,
            "context_data": {"source": "training_coach", "rag_data": training_advice}
        }

    def _general_assistant_agent(self, state: AgentState) -> AgentState:
        """General assistant for other questions"""

        user_query = state["user_query"]

        system_prompt = """Du är RaceBuddy, en hjälpsam assistent för löpare som förbereder sig för Lidingöloppet.
        
Du hjälper med allmänna frågor om:
- Löpning i allmänhet
- Hälsa och välmående
- Motivation och mental träning
- Allmänna frågor om RaceBuddy-appen

Svara på svenska, var vänlig och uppmuntrande. Om frågan är specifik om Lidingöloppet eller träning,
hänvisa gärna användaren att ställa mer specifika frågor så kan jag ge bättre hjälp.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query)
        ]

        try:
            response = self.llm.invoke(messages)
            final_response = response.content
        except Exception as e:
            logger.error(f"Error in general assistant: {e}")
            final_response = "Ursäkta, jag har tekniska problem just nu. Försök igen senare."

        return {
            **state,
            "final_response": final_response,
            "context_data": {"source": "general_assistant"}
        }

    def chat(self, user_message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Main method for chatting with the agents"""

        # Build message history
        messages = []
        if conversation_history:
            for msg in conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_message))

        # Initial state
        initial_state: AgentState = {
            "messages": messages,
            "user_query": user_message,
            "agent_type": "",
            "context_data": None,
            "final_response": None
        }

        try:
            # Run agent graph
            result = self.graph.invoke(initial_state)

            response = {
                "response": result.get("final_response", "Ursäkta, jag kunde inte generera ett svar."),
                "agent_used": result.get("context_data", {}).get("source", "unknown"),
                "success": True
            }

            logger.info(
                f"Chat completed successfully with agent: {response['agent_used']}")
            return response

        except Exception as e:
            logger.error(f"Error in chat processing: {e}")
            return {
                "response": "Ursäkta, jag har tekniska problem just nu. Försök igen om en stund.",
                "agent_used": "error",
                "success": False,
                "error": str(e)
            }


# Singleton instance
race_buddy_agents = RaceBuddyAgents()
