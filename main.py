import logging
import asyncio
import base64
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn

from models import OpenAISpeechRequest, ErrorResponse
from runpod_client import RunPodClient
from config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TTS API Bridge",
    description="OpenAI-compatible Speech API using RunPod",
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

# Initialize RunPod client
runpod_client = None

@app.on_event("startup")
async def startup_event():
    """Initialize the RunPod client on startup"""
    global runpod_client
    try:
        runpod_client = RunPodClient()
        logger.info("RunPod client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RunPod client: {str(e)}")
        raise

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "TTS API Bridge - OpenAI-compatible Speech API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "runpod_client": runpod_client is not None}

@app.get("/voices")
async def list_voices():
    """List available voices for voice cloning"""
    if not runpod_client:
        raise HTTPException(status_code=503, detail="RunPod client not initialized")
    
    voices_info = {}
    for voice_name, voice_info in runpod_client.voice_map.voices.items():
        voices_info[voice_name] = {
            "name": voice_info.name,
            "prompt_text": voice_info.prompt_text,
            "prompt_wav_url": voice_info.prompt_wav_url
        }
    
    return {
        "voices": voices_info,
        "total_count": len(voices_info)
    }

@app.post("/v1/speech")
async def create_speech(request: OpenAISpeechRequest):
    """
    OpenAI-compatible Speech API endpoint
    
    This endpoint accepts OpenAI Speech API requests and forwards them to RunPod,
    waiting for the job to complete before returning the audio.
    """
    if not runpod_client:
        raise HTTPException(status_code=503, detail="RunPod client not initialized")
    
    try:
        logger.info(f"Received speech request for text: {request.input[:100]}...")
        logger.info(f"Request parameters: model={request.model}, voice={request.voice}, format={request.response_format}")
        
        # Generate speech using RunPod client
        # This will wait for the job to complete
        audio_base64 = await runpod_client.generate_speech(request.input, request.voice)
        
        if not audio_base64:
            logger.error("RunPod returned None for audio generation")
            raise HTTPException(status_code=500, detail="Failed to generate speech")
        
        logger.info(f"Successfully generated speech, audio data length: {len(audio_base64)} characters")
        
        # Decode base64 audio to bytes
        try:
            audio_bytes = runpod_client.decode_base64_audio(audio_base64)
            logger.info(f"Decoded audio to {len(audio_bytes)} bytes")
        except Exception as e:
            logger.error(f"Failed to decode audio: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to decode audio: {str(e)}")
        
        # Determine content type based on requested format
        content_type = "audio/mpeg"  # Default for mp3
        if request.response_format == "wav":
            content_type = "audio/wav"
        elif request.response_format == "ogg":
            content_type = "audio/ogg"
        elif request.response_format == "flac":
            content_type = "audio/flac"
        
        logger.info(f"Returning audio with content type: {content_type}")
        
        # Return the audio as binary response
        return Response(
            content=audio_bytes,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=speech.{request.response_format}"
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in speech generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return Response(
        content=ErrorResponse(error={"message": exc.detail, "type": "http_error"}).json(),
        status_code=exc.status_code,
        media_type="application/json"
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return Response(
        content=ErrorResponse(error={"message": "Internal server error", "type": "internal_error"}).json(),
        status_code=500,
        media_type="application/json"
    )

if __name__ == "__main__":
    logger.info("Starting TTS API Bridge server...")
    logger.info(f"Host: {config.HOST}, Port: {config.PORT}")
    
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=False,
        log_level=config.LOG_LEVEL.lower()
    )
