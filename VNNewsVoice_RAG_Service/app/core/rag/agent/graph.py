import logging
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver

from app.core.rag.agent.state import FlowState, AgentState
from app.core.rag.agent.nodes_agent import AgentNodes
from app.core.rag.agent.nodes_main import MainNodes

logger = logging.getLogger(__name__)


def create_agent_graph(
    llm, retriever, parent_repo=None, checkpointer=None, filters: dict | None = None
):
    """
    Builds and compiles the hierarchical LangGraph for Agentic RAG.

    Args:
        llm: The Langchain BaseChatModel instance (e.g. from GeminiAdapter.get_langchain_model())
        retriever: The NativeHybridRetriever instance
        parent_repo: Optional repository for fetching full context
        checkpointer: Optional checkpointer for memory (e.g. InMemorySaver)
        filters: Optional metadata filters passed to the retrieval tool (e.g. {"article_id": "..."})

    Returns:
        Compiled StateGraph instance
    """
    if checkpointer is None:
        checkpointer = InMemorySaver()

    # Instantiate node factories with dependencies
    agent_nodes = AgentNodes(
        llm=llm, retriever=retriever, parent_repo=parent_repo, filters=filters
    )
    main_nodes = MainNodes(llm=llm)

    # 1. Build Agent Subgraph (Handles individual questions)
    agent_builder = StateGraph(AgentState)
    agent_builder.add_node("orchestrator", agent_nodes.orchestrator)
    # Use our custom tools node to handle state updates properly
    agent_builder.add_node("tools", agent_nodes.tools_node)
    agent_builder.add_node("compress_context", agent_nodes.compress_context)
    agent_builder.add_node("fallback_response", agent_nodes.fallback_response)
    agent_builder.add_node("collect_answer", agent_nodes.collect_answer)

    agent_builder.add_edge(START, "orchestrator")
    agent_builder.add_conditional_edges(
        "orchestrator",
        agent_nodes.route_after_orchestrator,
        {
            "tools": "tools",
            "fallback_response": "fallback_response",
            "collect_answer": "collect_answer",
        },
    )
    agent_builder.add_conditional_edges("tools", agent_nodes.should_compress_context)
    agent_builder.add_edge("compress_context", "orchestrator")
    agent_builder.add_edge("fallback_response", "collect_answer")
    agent_builder.add_edge("collect_answer", END)

    # Compile Subgraph
    agent_subgraph = agent_builder.compile()

    # 2. Build Main Graph (Orchestrates workflow)
    graph_builder = StateGraph(FlowState)
    graph_builder.add_node("summarize_history", main_nodes.summarize_history)
    graph_builder.add_node("rewrite_query", main_nodes.rewrite_query)
    graph_builder.add_node("request_clarification", main_nodes.request_clarification)
    graph_builder.add_node("agent_subgraph", agent_subgraph)
    graph_builder.add_node("aggregate_answers", main_nodes.aggregate_answers)

    graph_builder.add_edge(START, "summarize_history")
    graph_builder.add_edge("summarize_history", "rewrite_query")
    graph_builder.add_conditional_edges("rewrite_query", main_nodes.route_after_rewrite)
    graph_builder.add_edge(
        "request_clarification", "rewrite_query"
    )  # loop back after clarification
    graph_builder.add_edge(["agent_subgraph"], "aggregate_answers")
    graph_builder.add_edge("aggregate_answers", END)

    # Compile Main graph with interruption point
    app_graph = graph_builder.compile(
        checkpointer=checkpointer, interrupt_before=["request_clarification"]
    )

    logger.info("LangGraph hierarchical agent successfully built.")
    return app_graph
