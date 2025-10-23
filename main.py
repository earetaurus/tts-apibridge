import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import config
from models import OpenAISpeechRequest, ErrorResponse
from runpod_client import RunPodClient

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TTS API Bridge",
    description="OpenAI-compatible Text-to-Speech API bridge for RunPod",
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
runpod_client = RunPodClient()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TTS API Bridge",
        "version": "1.0.0",
        "endpoints": {
            "speech": f"{config.OPENAI_API_PREFIX}/audio/speech",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "tts-apibridge"}

@app.post(f"{config.OPENAI_API_PREFIX}/audio/speech")
async def create_speech(request: OpenAISpeechRequest):
    """
    OpenAI-compatible speech generation endpoint
    
    This endpoint mimics OpenAI's /v1/audio/speech endpoint but uses
    RunPod as the backend TTS service.
    """
    try:
        logger.info(f"Received speech request: {request.input[:100]}...")
        
        # Generate speech using RunPod
        base64_audio = await runpod_client.generate_speech(request.input)
        
        if base64_audio is None:
            logger.error("Failed to generate speech from RunPod API")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "message": "Failed to generate speech from backend service",
                        "type": "api_error",
                        "code": "speech_generation_failed"
                    }
                }
            )
        
        # Decode base64 audio
        try:
            audio_bytes = runpod_client.decode_base64_audio(base64_audio)
        except ValueError as e:
            logger.error(f"Failed to decode audio: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "message": "Invalid audio data received from backend",
                        "type": "api_error",
                        "code": "invalid_audio_data"
                    }
                }
            )
        
        # Determine content type based on requested format
        content_type = "audio/mpeg"  # Default for mp3
        if request.response_format == "wav":
            content_type = "audio/wav"
        elif request.response_format == "opus":
            content_type = "audio/opus"
        elif request.response_format == "aac":
            content_type = "audio/aac"
        elif request.response_format == "flac":
            content_type = "audio/flac"
        
        logger.info(f"Returning {len(audio_bytes)} bytes of audio as {content_type}")
        
        # Return audio as streaming response
        return StreamingResponse(
            iter([audio_bytes]),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=speech.{request.response_format}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in speech generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "Internal server error",
                    "type": "api_error",
                    "code": "internal_error"
                }
            }
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions and return OpenAI-compatible error format"""
    return Response(
        content=ErrorResponse(error=exc.detail).model_dump_json(),
        status_code=exc.status_code,
        media_type="application/json"
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return Response(
        content=ErrorResponse(error={
            "message": "Internal server error",
            "type": "api_error",
            "code": "internal_error"
        }).model_dump_json(),
        status_code=500,
        media_type="application/json"
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )
