"""RAG tool for AI to search knowledge base."""

from typing import Dict, Any
from pydantic import BaseModel


class ToolDefinition(BaseModel):
    """Tool definition for OpenAI Realtime API."""
    type: str = "function"
    name: str
    description: str
    parameters: Dict[str, Any]


# Tool definition for AI
SEARCH_KNOWLEDGE_BASE_TOOL = ToolDefinition(
    name="search_knowledge_base",
    description=(
        "Search the company knowledge base for relevant information. "
        "Use this when you need to answer questions about services, pricing, "
        "policies, hours, location, or any company-specific information. "
        "Returns the most relevant information from uploaded documents."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The question or topic to search for. Be specific and use keywords from the user's question."
            },
            "num_results": {
                "type": "integer",
                "description": "Number of relevant chunks to retrieve (default: 3, max: 5)",
                "default": 3
            }
        },
        "required": ["query"]
    }
)


async def execute_search_knowledge_base(
    args: Dict[str, Any],
    vector_service
) -> Dict[str, Any]:
    """
    Execute knowledge base search.
    
    Args:
        args: Tool arguments (query, num_results)
        vector_service: VectorService instance
        
    Returns:
        Search results with relevant chunks
    """
    query = args.get("query", "")
    num_results = min(args.get("num_results", 3), 5)  # Max 5 results
    
    if not query:
        return {
            "success": False,
            "error": "Query is required"
        }
    
    try:
        # Search vector database
        chunks = await vector_service.search(
            query=query,
            limit=num_results,
            score_threshold=0.25  # Lower threshold for better recall
        )
        
        if not chunks:
            return {
                "success": True,
                "found": False,
                "message": "No relevant information found in knowledge base. You may need to connect the caller with a team member for this specific question."
            }
        
        # Format results for AI
        results_text = "\n\n".join([
            f"[Relevance: {chunk['score']:.0%}]\n{chunk['text']}"
            for chunk in chunks
        ])
        
        return {
            "success": True,
            "found": True,
            "num_results": len(chunks),
            "results": results_text,
            "message": f"Found {len(chunks)} relevant piece(s) of information. Use this to answer the caller's question."
        }
    
    except Exception as e:
        print(f"❌ Error searching knowledge base: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error searching knowledge base. Please connect caller with team."
        }
