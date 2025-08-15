#!/usr/bin/env python3
"""
FastAPI Chatbot Service for ScrappingBot
Provides conversational interface with LLM integration
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://scrappingbot_user:scrappingbot_pass@postgres:5432/scrappingbot')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'ollama:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1')

app = FastAPI(
    title="ScrappingBot Chatbot API",
    description="Conversational interface for real estate data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict] = None

class ChatResponse(BaseModel):
    response: str
    data: Optional[Dict] = None
    suggestions: Optional[List[str]] = None

class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                # Remove faulty connection synchronously (disconnect is not async)
                self.disconnect(connection)

manager = ConnectionManager()

class OllamaClient:
    """Client for Ollama LLM"""
    
    def __init__(self, host: str = OLLAMA_HOST):
        self.base_url = f"http://{host}"
        self.model = OLLAMA_MODEL
    
    async def chat(self, message: str, context: Optional[Dict] = None) -> str:
        """Send chat message to Ollama"""
        try:
            # Build prompt with context
            system_prompt = """Tu es un assistant intelligent pour ScrappingBot, une plateforme d'analyse immobilière de Montréal.

Tu peux aider avec:
- Recherche de propriétés par critères (prix, quartier, type)
- Analyse de tendances de marché
- Explication des données de scrapping
- Questions sur les quartiers de Montréal

Réponds en français de manière concise et utile."""

            if context:
                system_prompt += f"\n\nContexte actuel:\n{json.dumps(context, indent=2)}"
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "stream": False
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["message"]["content"]
                else:
                    logger.error(f"Ollama error: {response.status_code}")
                    return "Désolé, je rencontre des difficultés techniques. Essayez plus tard."
                    
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return "Je ne peux pas répondre pour le moment. Vérifiez que le service LLM fonctionne."

    async def generate_suggestions(self, query: str) -> List[str]:
        """Generate follow-up suggestions"""
        suggestions_prompt = f"""Basé sur cette question: "{query}"

Génère 3 suggestions de questions de suivi courtes et utiles pour un utilisateur cherchant des propriétés à Montréal.

Format: une suggestion par ligne, maximum 8 mots chacune.
Exemples:
- Prix moyen dans Plateau Mont-Royal?
- Tendances des condos downtown?
- Quartiers abordables pour familles?"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": suggestions_prompt,
                        "stream": False
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    suggestions = result["response"].strip().split('\n')
                    return [s.strip('- ').strip() for s in suggestions if s.strip()][:3]
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Suggestions error: {e}")
            return []

# Initialize Ollama client
ollama = OllamaClient()

async def get_database_context(query: str) -> Optional[Dict]:
    """Get relevant data from PostgreSQL based on query"""
    try:
        # This would connect to PostgreSQL and fetch relevant data
        # For now, return mock context
        return {
            "total_listings": 1234,
            "last_update": datetime.now().isoformat(),
            "top_areas": ["Plateau Mont-Royal", "Downtown", "Westmount"]
        }
    except Exception as e:
        logger.error(f"Database context error: {e}")
        return None

@app.get("/")
async def root():
    return {"message": "ScrappingBot Chatbot API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Ollama connection
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{OLLAMA_HOST}/api/tags", timeout=5.0)
            ollama_status = "ok" if response.status_code == 200 else "error"
    except:
        ollama_status = "error"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "ollama": ollama_status,
            "database": "ok",  # TODO: Add actual DB health check
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Main chat endpoint"""
    try:
        # Get database context if relevant
        context = await get_database_context(message.message)
        
        # Merge with provided context
        if message.context:
            if context:
                context.update(message.context)
            else:
                context = message.context
        
        # Get LLM response
        response = await ollama.chat(message.message, context)
        
        # Generate suggestions
        suggestions = await ollama.generate_suggestions(message.message)
        
        return ChatResponse(
            response=response,
            data=context,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Chat service error")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time chat"""
    await manager.connect(websocket)
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message
            message = ChatMessage(**message_data)
            
            # Get context and response
            context = await get_database_context(message.message)
            response = await ollama.chat(message.message, context)
            suggestions = await ollama.generate_suggestions(message.message)
            
            # Send response
            response_data = {
                "type": "chat_response",
                "response": response,
                "data": context,
                "suggestions": suggestions,
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.send_personal_message(json.dumps(response_data), websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        # disconnect synchronously since disconnect is not async
        manager.disconnect(websocket)
        # try to close the websocket connection if still open
        try:
            await websocket.close()
        except Exception:
            pass

@app.get("/models")
async def get_available_models():
    """Get available LLM models"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{OLLAMA_HOST}/api/tags")
            if response.status_code == 200:
                return response.json()
            else:
                return {"models": []}
    except:
        return {"models": []}

@app.post("/models/{model_name}/pull")
async def pull_model(model_name: str):
    """Pull a new model to Ollama"""
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"http://{OLLAMA_HOST}/api/pull",
                json={"name": model_name}
            )
            if response.status_code == 200:
                return {"status": "success", "message": f"Model {model_name} pulled successfully"}
            else:
                return {"status": "error", "message": "Failed to pull model"}
    except Exception as e:
        logger.error(f"Model pull error: {e}")
        raise HTTPException(status_code=500, detail="Failed to pull model")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
