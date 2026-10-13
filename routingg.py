from fastapi import APIRouter
from pydantic import BaseModel
from schema_service import get_schema_description
from ai_agent import ai_graph

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/ai/query")
def ask_ai(request: QueryRequest):
    initial_state = {
        "user_query": request.query,
        "schema_context": get_schema_description(),
        "generated_sql": None,
        "is_valid": False,
        "validation_message": None,
        "execution_result": None,
        "error_message": None,
        "retry_count": 0,
        "final_response": None,
    }
    result = ai_graph.invoke(initial_state)
    return {
        "answer": result["final_response"],
        "sql_used": result.get("generated_sql"),
        "data": result.get("execution_result"),
    }