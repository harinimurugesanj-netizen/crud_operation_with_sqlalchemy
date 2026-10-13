from typing import TypedDict, Optional
import requests
from sqlalchemy import text
from langgraph.graph import StateGraph, END

from database import SessionLocal
from safegraud import validate_sql

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.1"

SYSTEM_PROMPT = """You are a PostgreSQL expert. Given a database schema and a user question,
write a single SELECT SQL query that answers it.

Rules:
- Only SELECT statements. Never INSERT, UPDATE, DELETE, DROP, or ALTER.
- Table and column names are case-sensitive. Wrap every table and column name in
  double quotes exactly as given in the schema, e.g. "Organisation"."Org_id".
- Always include a LIMIT clause (max 500), unless it's an aggregation returning one row.
- Use explicit column names, never SELECT *.
- Return ONLY the raw SQL. No explanation, no markdown, no backticks, no commentary.
"""


def call_ollama(system: str, user: str) -> str:
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0},
    })
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


class AgentState(TypedDict):
    user_query: str
    schema_context: str
    generated_sql: Optional[str]
    is_valid: bool
    validation_message: Optional[str]
    execution_result: Optional[dict]
    error_message: Optional[str]
    retry_count: int
    final_response: Optional[str]


def generate_sql_node(state: AgentState) -> AgentState:
    prompt = f"""Schema:
{state['schema_context']}

Question: {state['user_query']}

Previous error to fix (if any): {state.get('error_message') or 'none'}
"""
    raw = call_ollama(SYSTEM_PROMPT, prompt)
    # Llama sometimes wraps output in markdown fences despite instructions — strip defensively
    raw = raw.replace("```sql", "").replace("```", "").strip()
    state["generated_sql"] = raw
    return state


def validate_node(state: AgentState) -> AgentState:
    is_valid, message, cleaned_sql = validate_sql(state["generated_sql"])
    state["is_valid"] = is_valid
    state["validation_message"] = message
    if is_valid:
        state["generated_sql"] = cleaned_sql
    return state


def execute_node(state: AgentState) -> AgentState:
    db = SessionLocal()
    try:
        result = db.execute(text(state["generated_sql"]))
        rows = result.fetchall()
        state["execution_result"] = {
            "columns": list(result.keys()),
            "rows": [list(r) for r in rows],
        }
        state["error_message"] = None
    except Exception as e:
        state["error_message"] = str(e)
        state["execution_result"] = None
    finally:
        db.close()
    return state


def format_node(state: AgentState) -> AgentState:
    result = state.get("execution_result")
    if result is None:
        state["final_response"] = "I couldn't retrieve an answer for that. Try rephrasing."
        return state

    prompt = f"""User asked: {state['user_query']}

Query result — columns: {result['columns']}, rows: {result['rows']}

Write a short, natural language answer based on this data. Be concise."""
    state["final_response"] = call_ollama("You are a helpful assistant.", prompt)
    return state


def route_after_validation(state: AgentState) -> str:
    if state["is_valid"]:
        return "execute"
    state["retry_count"] += 1
    if state["retry_count"] >= 3:
        state["final_response"] = f"Couldn't generate a safe query: {state['validation_message']}"
        return "end"
    state["error_message"] = state["validation_message"]
    return "retry"


def route_after_execution(state: AgentState) -> str:
    if state["error_message"] is None:
        return "format"
    state["retry_count"] += 1
    if state["retry_count"] >= 3:
        state["final_response"] = "I wasn't able to run a valid query after several attempts."
        return "end"
    return "retry"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("generate_sql", generate_sql_node)
    graph.add_node("validate", validate_node)
    graph.add_node("execute", execute_node)
    graph.add_node("format", format_node)

    graph.set_entry_point("generate_sql")
    graph.add_edge("generate_sql", "validate")
    graph.add_conditional_edges("validate", route_after_validation,
        {"execute": "execute", "retry": "generate_sql", "end": END})
    graph.add_conditional_edges("execute", route_after_execution,
        {"format": "format", "retry": "generate_sql", "end": END})
    graph.add_edge("format", END)

    return graph.compile()


ai_graph = build_graph()