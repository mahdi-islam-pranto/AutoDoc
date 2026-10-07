from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain_core.messages import HumanMessage, AIMessage
from config.fast_api import lifespan
from schemas import ChatRequest
from utilities.helper import generate_graph_config
from dotenv import load_dotenv
import traceback
import os
import mlflow
from mlflow.entities import SpanType

# Load environment variables from .env file
load_dotenv()


# setup mlflow: traces are stored in the local mlflow.db (SQLite) by default,
# override with MLFLOW_TRACKING_URI in .env (e.g. http://localhost:5000)
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
mlflow.set_experiment("Medical Booking Agent - LLM Observability")

# Enabling tracing for LangGraph (LangChain): captures graph nodes, tools and LLM calls
mlflow.langchain.autolog()

# Initialize Langfuse client
#need to remove
""" langfuse = get_client() """
# Initialize Langfuse CallbackHandler for Langchain (tracing)
#need to remove
""" langfuse_handler = CallbackHandler() """


app = FastAPI(
    title="Medical Booking Agent",
    description="Multi-agent appointment booking system",
    #   lifespan=lifespan  # we will define this in a moment
    lifespan=lifespan
)

# Serve the web frontend (static assets + chat page)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serves the AutoDoc chat frontend."""
    return templates.TemplateResponse(request, "index.html")

# mlflow.trace decorator to trace the entire conversation turn through the graph
@mlflow.trace(name="handle_message", span_type=SpanType.AGENT)
async def run_agent(graph, request: ChatRequest, config: dict):
    """Runs one conversation turn through the graph inside a single MLflow trace."""
    # Tag the trace so all turns of a conversation can be grouped in the MLflow UI
    mlflow.update_current_trace(
        metadata={
            "mlflow.trace.user": request.user_id,
            "mlflow.trace.session": config["configurable"]["thread_id"],
        },
        tags={"channel": request.channel},
    )
    return await graph.ainvoke(
        {
            "messages": [HumanMessage(content=request.message)],
        },
        config=config
    )


# This endpoint receives a user message from the frontend (WhatsApp/Facebook).
@app.post("/message")
async def handle_message(request: ChatRequest):
    """
    This endpoint receives a user message from the frontend (WhatsApp/Facebook).
    It creates or updates the conversation state, runs the graph, and returns the agent's response.
    """
     # Access the graph from app.state (set during startup) which declared in config -- fast_api and ensure it's initialized before invoking
    _graph = getattr(app.state, "graph", None)

    # Ensure the graph is initialized (should be, since it's built at startup)
    if _graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")

    # Generate the graph configuration for this request
    # request-specific config can include things like user ID, channel, or any other metadata needed for processing
    # config = generate_graph_config(request.channel, request.user_id, langfuse_handler)
    config = generate_graph_config(request.channel, request.user_id)
    
    # trace data api calls with Langfuse (example usage, can be used in any part of the codebase)
    # traces = langfuse.api.trace.list()  
    # pagination via cursor
    # trace = langfuse.api.trace.get("traceId")
    # print("Recent traces for this user:", traces)
    
    # get individual trace details (example usage, can be used in any part of the codebase)
    # if traces:
    #     trace_datas = traces.data
    #     costs = []
    #     latency = []
    #     for trace in trace_datas:
    #         latency.append(trace.latency)
    #         trace_total_cost = trace.total_cost
    #         costs.append(trace_total_cost)
            
    try:
        # Invoke the graph with the user message and config. The graph will process the message through the graph nodes and return the updated state.
        result = await run_agent(_graph, request, config)
        
    except Exception as e:
        error_detail = {
            "type": type(e).__name__,
            "message": str(e) or repr(e),   # repr() as fallback
            "traceback": traceback.format_exc()
    }
        print("❌ ERROR:", error_detail)     # always log server-side
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: [{type(e).__name__}] {repr(e)}"
    )
    
    # Extract the agent's response (last message in the updated state)
    last_message = result["messages"][-1]
    
    #need to changes in future for next step to send the message to the frontend ***
    #also user id channel id and other metadata can be sent to the frontend for better user experience and tracking
    return {"response": last_message,
            "langfuse_traces" : {"costs": "none", "latency": "none"}}