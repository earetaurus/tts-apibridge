from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class OpenAISpeechRequest(BaseModel):
    model: str = Field(default="tts-1", description="The model to use for speech generation")
    input: str = Field(..., description="The text to generate audio for")
    voice: Optional[str] = Field(default="alloy", description="The voice to use")
    response_format: Optional[str] = Field(default="mp3", description="The format to return audio in")
    speed: Optional[float] = Field(default=1.0, description="The speed of the generated audio")

class VoiceInfo(BaseModel):
    name: str = Field(..., description="Voice name")
    prompt_text: str = Field(..., description="The text spoken in the wav file for voice cloning")
    prompt_wav_url: str = Field(..., description="URL to the wav file for voice cloning")

class VoiceMap(BaseModel):
    voices: Dict[str, VoiceInfo] = Field(..., description="Mapping of voice names to voice info")

class RunPodOutput(BaseModel):
    audio_base64: str = Field(..., description="Base64 encoded WAV audio")
    language: str = Field(default="en", description="Language code")

class RunPodJobResponse(BaseModel):
    delayTime: Optional[int] = Field(None, description="Delay time in milliseconds")
    executionTime: Optional[int] = Field(None, description="Execution time in milliseconds")
    id: Optional[str] = Field(None, description="Job ID")
    output: Optional[RunPodOutput] = Field(None, description="Job output")
    status: str = Field(..., description="Job status")
    workerId: Optional[str] = Field(None, description="Worker ID")
    
    class Config:
        extra = "allow"  # Allow extra fields to handle variations in API response

class OpenAISpeechResponse(BaseModel):
    # OpenAI returns the audio directly as binary data
    # This model is for documentation purposes
    pass

class ErrorResponse(BaseModel):
    error: Dict[str, Any] = Field(..., description="Error details")
