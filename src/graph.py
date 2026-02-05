import os
import operator
from typing import Annotated, List, TypedDict, Union
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# --- Config ---
# В реальном проекте ключи берем из os.environ
llm = ChatOpenAI(model="gpt-4-turbo-preview")

# --- State ---
class AgentState(TypedDict):
    messages: Annotated[List[str], operator.add]
    next_agent: str
    task: str
    code_files: dict

# --- Agents ---
# Это заглушки. В реальном проекте тут будет сложная логика или вызов других Chain
def supervisor_node(state: AgentState):
    """Определяет, кто работает следующим"""
    last_message = state['messages'][-1]
    # Простейшая логика маршрутизации
    if "TEST_OK" in last_message:
        return {"next_agent": "FINISH"}
    if "CODE_WRITTEN" in last_message:
        return {"next_agent": "QA_AGENT"}
    return {"next_agent": "DEV_AGENT"}

def dev_agent_node(state: AgentState):
    """Пишет код"""
    # Тут логика генерации кода
    return {"messages": ["CODE_WRITTEN: Added new feature"], "next_agent": "supervisor"}

def qa_agent_node(state: AgentState):
    """Тестирует код"""
    # Тут логика тестов
    return {"messages": ["TEST_OK: All tests passed"], "next_agent": "supervisor"}

# --- Graph Construction ---
workflow = StateGraph(AgentState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("dev", dev_agent_node)
workflow.add_node("qa", qa_agent_node)

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    lambda x: x["next_agent"],
    {
        "DEV_AGENT": "dev",
        "QA_AGENT": "qa",
        "FINISH": END
    }
)

workflow.add_edge("dev", "supervisor")
workflow.add_edge("qa", "supervisor")

app = workflow.compile()

# --- Entry Point for CLI ---
if __name__ == "__main__":
    print("LangGraph Swarm Engine Loaded.")
    # Тут можно запустить граф с начальным стейтом
