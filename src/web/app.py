#!/usr/bin/env python3
"""
ThinkingModels Web Application

FastAPI-based web server providing REST API endpoints and web UI for
the ThinkingModels project.
"""

import sys
import os
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# FastAPI imports
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.model_parser import ModelParser
from core.llm_client import get_llm_client
from core.query_processor import QueryProcessor, QueryResult

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app instance
app = FastAPI(
    title="ThinkingModels API",
    description="AI-powered problem solving using thinking models",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for components
query_processor: Optional[QueryProcessor] = None
model_parser: Optional[ModelParser] = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Remove disconnected clients
                self.active_connections.remove(connection)

# WebSocket manager instance
websocket_manager = ConnectionManager()

# Pydantic models for API
class QueryRequest(BaseModel):
    query: str = Field(..., description="The problem or question to solve")
    model_preference: Optional[str] = Field(None, description="Preferred output format")

class QueryResponse(BaseModel):
    query: str
    selected_models: List[str]
    solution: str
    processing_time: float
    timestamp: datetime
    error: Optional[str] = None

class ModelInfo(BaseModel):
    id: str
    type: str
    field: Optional[str]
    definition: str
    examples: List[str]

class SystemStatus(BaseModel):
    status: str
    total_models: int
    api_configured: bool
    uptime_seconds: float

class BatchQueryRequest(BaseModel):
    queries: List[str] = Field(..., description="List of queries to process")

class BatchQueryResponse(BaseModel):
    results: List[QueryResponse]
    total_queries: int
    successful_queries: int
    total_processing_time: float

# App startup time for uptime calculation
app_start_time = datetime.now()

@app.on_event("startup")
async def startup_event():
    """Initialize the application components on startup"""
    global query_processor, model_parser
    
    try:
        logger.info("Starting ThinkingModels Web Application...")
        
        # Initialize model parser
        models_dir = os.getenv('THINKING_MODELS_DIR', 'models')
        model_parser = ModelParser(models_dir)
        models = model_parser.load_all_models()
        logger.info(f"Loaded {len(models)} thinking models")
        
        # Initialize LLM client (if configured)
        api_url = os.getenv('LLM_API_URL')
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if api_url or gemini_api_key:
            llm_client = get_llm_client()

            # Initialize query processor
            query_processor = QueryProcessor(model_parser, llm_client)
            logger.info("Query processor initialized with LLM client")
        else:
            logger.warning("LLM_API_URL not set - query processing will be limited")
        
        logger.info("Web application startup complete")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

# Static files and templates
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")
templates = Jinja2Templates(directory=str(current_dir / "templates"))

# API Routes

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main web UI"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/status", response_model=SystemStatus)
async def get_system_status():
    """Get system status and health information"""
    uptime = (datetime.now() - app_start_time).total_seconds()
    
    return SystemStatus(
        status="healthy" if query_processor else "limited",
        total_models=len(model_parser.models) if model_parser else 0,
        api_configured=query_processor is not None,
        uptime_seconds=uptime
    )

@app.get("/api/models", response_model=List[ModelInfo])
async def get_models():
    """Get list of all available thinking models"""
    if not model_parser:
        raise HTTPException(status_code=503, detail="Model parser not initialized")
    
    models_info = []
    for model in model_parser.models.values():
        models_info.append(ModelInfo(
            id=model.id,
            type=model.type,
            field=model.field,
            definition=model.definition,
            examples=model.examples
        ))
    
    return models_info

@app.get("/api/models/summary")
async def get_models_summary():
    """Get summary statistics of available models"""
    if not model_parser:
        raise HTTPException(status_code=503, detail="Model parser not initialized")
    
    return model_parser.get_model_summary()

@app.post("/api/query", response_model=QueryResponse)
async def process_query(query_request: QueryRequest):
    """Process a single query using thinking models"""
    if not query_processor:
        raise HTTPException(
            status_code=503, 
            detail="Query processor not initialized. Please configure LLM_API_URL and LLM_API_KEY."
        )
    
    try:
        logger.info(f"Processing query: {query_request.query}")
        
        # Process the query
        result = query_processor.process_query(query_request.query)
        
        # Convert to response model
        response = QueryResponse(
            query=result.query,
            selected_models=result.selected_models,
            solution=result.solution,
            processing_time=result.processing_time or 0.0,
            timestamp=datetime.now(),
            error=result.error
        )
        
        logger.info(f"Query processed successfully in {response.processing_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/api/query/batch", response_model=BatchQueryResponse)
async def process_batch_queries(batch_request: BatchQueryRequest):
    """Process multiple queries in batch"""
    if not query_processor:
        raise HTTPException(
            status_code=503,
            detail="Query processor not initialized. Please configure LLM_API_URL and LLM_API_KEY."
        )
    
    try:
        logger.info(f"Processing batch of {len(batch_request.queries)} queries")
        
        results = []
        total_time = 0.0
        successful_count = 0
        
        for query_text in batch_request.queries:
            try:
                result = query_processor.process_query(query_text)
                
                response = QueryResponse(
                    query=result.query,
                    selected_models=result.selected_models,
                    solution=result.solution,
                    processing_time=result.processing_time or 0.0,
                    timestamp=datetime.now(),
                    error=result.error
                )
                
                results.append(response)
                total_time += response.processing_time
                
                if not result.error:
                    successful_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing query '{query_text}': {str(e)}")
                results.append(QueryResponse(
                    query=query_text,
                    selected_models=[],
                    solution="",
                    processing_time=0.0,
                    timestamp=datetime.now(),
                    error=str(e)
                ))
        
        return BatchQueryResponse(
            results=results,
            total_queries=len(batch_request.queries),
            successful_queries=successful_count,
            total_processing_time=total_time
        )
        
    except Exception as e:
        logger.error(f"Error processing batch queries: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")

@app.get("/api/models/{model_id}", response_model=ModelInfo)
async def get_model_details(model_id: str):
    """Get detailed information about a specific model"""
    if not model_parser:
        raise HTTPException(status_code=503, detail="Model parser not initialized")
    
    if model_id not in model_parser.models:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    
    model = model_parser.models[model_id]
    return ModelInfo(
        id=model.id,
        type=model.type,
        field=model.field,
        definition=model.definition,
        examples=model.examples
    )

# WebSocket endpoint for real-time query processing
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time query processing and updates"""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Receive query from client
            data = await websocket.receive_json()
            
            if data.get("type") == "query":
                query_text = data.get("query", "")
                
                if not query_processor:
                    await websocket_manager.send_personal_message({
                        "type": "error",
                        "error": "Query processor not configured. Please set LLM_API_URL and LLM_API_KEY."
                    }, websocket)
                    continue
                
                try:
                    # Send processing status
                    await websocket_manager.send_personal_message({
                        "type": "status",
                        "message": "Processing query...",
                        "query": query_text
                    }, websocket)
                    
                    # Process the query
                    result = query_processor.process_query(query_text)
                    
                    # Send result
                    await websocket_manager.send_personal_message({
                        "type": "result",
                        "query": result.query,
                        "selected_models": result.selected_models,
                        "solution": result.solution,
                        "processing_time": result.processing_time,
                        "error": result.error
                    }, websocket)
                    
                except Exception as e:
                    await websocket_manager.send_personal_message({
                        "type": "error",
                        "error": str(e)
                    }, websocket)
            
            elif data.get("type") == "ping":
                # Respond to ping for connection health
                await websocket_manager.send_personal_message({
                    "type": "pong"
                }, websocket)
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        websocket_manager.disconnect(websocket)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "models_loaded": len(model_parser.models) if model_parser else 0,
        "query_processor_ready": query_processor is not None
    }

# Configuration endpoint
@app.get("/api/config")
async def get_config():
    """Get current configuration (non-sensitive data only)"""
    return {
        "models_directory": os.getenv('THINKING_MODELS_DIR', 'models'),
        "api_configured": os.getenv('LLM_API_URL') is not None,
        "model_name": os.getenv('LLM_MODEL_NAME', 'gpt-3.5-turbo'),
        "temperature": float(os.getenv('LLM_TEMPERATURE', '0.7')),
        "max_tokens": int(os.getenv('LLM_MAX_TOKENS', '2000')),
        "total_models": len(model_parser.models) if model_parser else 0
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "path": str(request.url.path)}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    
    # Configuration from environment variables
    host = os.getenv('WEB_HOST', '127.0.0.1')
    port = int(os.getenv('WEB_PORT', '8000'))
    debug = os.getenv('WEB_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting ThinkingModels Web Server on {host}:{port}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
