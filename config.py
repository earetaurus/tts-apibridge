import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # RunPod API Configuration
    RUNPOD_API_KEY: Optional[str] = os.getenv("RUNPOD_API_KEY")
    RUNPOD_ENDPOINT_ID: Optional[str] = os.getenv("RUNPOD_ENDPOINT_ID")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # OpenAI Compatibility
    OPENAI_API_PREFIX: str = "/v1"
    
    # Request Configuration
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "300"))  # Increased for TTS processing
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

config = Config()
