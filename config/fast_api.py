from fastapi.concurrency import asynccontextmanager
from fastapi import FastAPI
from graph.graph import build_graph
from memory.checkpointer import get_checkpointer

# Graph is built once at startup and reused for every request
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs at startup and shutdown."""

    # Initialize the checkpointer and graph at startup
    checkpointer = await get_checkpointer()
    print(f"Checkpointer type: {type(checkpointer)}")  

    # Build the graph and store it in the app state for reuse
    app.state.graph = build_graph(checkpointer)
    print("✅ Agent graph ready")

    yield
    # Cleanup: Close DB connections, etc. if needed
    print("👋 Shutting down")

    