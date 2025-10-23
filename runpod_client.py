import base64
import json
import logging
from typing import Optional, Dict
import asyncio
import runpod
from models import RunPodJobResponse, RunPodOutput, VoiceMap, VoiceInfo
from config import config

logger = logging.getLogger(__name__)

class RunPodClient:
    def __init__(self):
        self.api_key = config.RUNPOD_API_KEY
        self.endpoint_id = config.RUNPOD_ENDPOINT_ID
        
        if not self.api_key:
            raise ValueError("RUNPOD_API_KEY environment variable is required")
        if not self.endpoint_id:
            raise ValueError("RUNPOD_ENDPOINT_ID environment variable is required")
        
        # Initialize RunPod client
        runpod.api_key = self.api_key
        self.endpoint = runpod.Endpoint(self.endpoint_id)
        
        # Load voice map
        self.voice_map = self._load_voice_map()
        
        logger.info(f"Initialized RunPod client for endpoint: {self.endpoint_id}")
        logger.info(f"Loaded {len(self.voice_map.voices)} voices from voice map")
    
    def _load_voice_map(self) -> VoiceMap:
        """Load voice map from JSON file"""
        try:
            with open('voice_map.json', 'r', encoding='utf-8') as f:
                voice_data = json.load(f)
            return VoiceMap(**voice_data)
        except Exception as e:
            logger.error(f"Failed to load voice map: {str(e)}")
            # Return empty voice map as fallback
            return VoiceMap(voices={})
    
    def get_voice_info(self, voice_name: str) -> Optional[VoiceInfo]:
        """Get voice information for voice cloning"""
        return self.voice_map.voices.get(voice_name)

    async def generate_speech(self, text: str, voice: Optional[str] = None) -> Optional[str]:
        """
        Generate speech using RunPod Endpoint SDK
        
        Args:
            text: The text to convert to speech
            
        Returns:
            Base64 encoded WAV audio data or None if failed
        """
        try:
            logger.info(f"Generating speech for text: {text[:100]}...")
            logger.info(f"Using voice: {voice or 'default'}")
            
            # Prepare the input for RunPod
            if voice and voice in self.voice_map.voices:
                # Use voice cloning
                voice_info = self.voice_map.voices[voice]
                runpod_input = {
                    "input": {
                        "text": text,
                        "prompt_text": voice_info.prompt_text,
                        "prompt_wav_url": voice_info.prompt_wav_url
                    }
                }
                logger.info(f"Using voice cloning for voice: {voice}")
                logger.info(f"Prompt text: {voice_info.prompt_text[:50]}...")
                logger.info(f"Prompt WAV URL: {voice_info.prompt_wav_url}")
            else:
                # Use regular TTS without voice cloning
                runpod_input = {
                    "text": text
                }
                logger.info("Using regular TTS without voice cloning")
            
            # Run the job in a thread pool to avoid blocking
            logger.info(f"Running job on endpoint {self.endpoint_id}")
            job = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.endpoint.run(runpod_input)
            )
            
            job_id = job.id if hasattr(job, 'id') else "unknown"
            logger.info(f"Job submitted with ID: {job_id}")
            
            # Poll for job completion with better error handling
            max_attempts = config.REQUEST_TIMEOUT // 5  # Check every 5 seconds
            attempt = 0
            
            while attempt < max_attempts:
                # Check job status
                status = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: job.status()
                )
                logger.info(f"Job {job_id} status: {status} (attempt {attempt + 1}/{max_attempts})")
                
                if status == "COMPLETED":
                    # Get the output
                    output_data = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: job.output()
                    )
                    logger.info(f"Job {job_id} completed successfully")
                    logger.info(f"Job output: {output_data}")
                    
                    # Parse the response using our model
                    job_result = {
                        "status": status,
                        "output": output_data,
                        "id": job_id
                    }
                    
                    runpod_response = RunPodJobResponse(**job_result)
                    
                    # Check if we have output with audio
                    if not runpod_response.output or not runpod_response.output.audio_base64:
                        logger.error(f"Job {job_id} completed but no audio data in output")
                        return None
                    
                    logger.info(f"Successfully received audio data. Job ID: {job_id}")
                    if runpod_response.executionTime:
                        logger.info(f"Execution time: {runpod_response.executionTime}ms")
                    
                    return runpod_response.output.audio_base64
                
                elif status == "FAILED":
                    logger.error(f"Job {job_id} failed")
                    # Try to get error details
                    try:
                        error_output = await asyncio.get_event_loop().run_in_executor(
                            None, lambda: job.output()
                        )
                        logger.error(f"Job {job_id} error details: {error_output}")
                    except Exception as e:
                        logger.error(f"Could not get error details for job {job_id}: {str(e)}")
                    return None
                
                elif status in ["IN_PROGRESS", "QUEUED", "RUNNING"]:
                    # Job is still processing, wait and retry
                    await asyncio.sleep(5)
                    attempt += 1
                else:
                    logger.warning(f"Job {job_id} has unexpected status: {status}")
                    await asyncio.sleep(5)
                    attempt += 1
            
            # Timeout reached
            logger.error(f"Job {job_id} timed out after {config.REQUEST_TIMEOUT} seconds")
            return None
                
        except Exception as e:
            logger.error(f"Error generating speech with RunPod: {str(e)}")
            return None
    
    def decode_base64_audio(self, base64_audio: str) -> bytes:
        """
        Decode base64 audio data to bytes
        
        Args:
            base64_audio: Base64 encoded audio string
            
        Returns:
            Decoded audio bytes
        """
        try:
            # Remove any data URL prefix if present
            if base64_audio.startswith('data:'):
                base64_audio = base64_audio.split(',')[1]
            
            audio_bytes = base64.b64decode(base64_audio)
            logger.info(f"Successfully decoded {len(audio_bytes)} bytes of audio data")
            return audio_bytes
        except Exception as e:
            logger.error(f"Error decoding base64 audio: {str(e)}")
            raise ValueError(f"Invalid base64 audio data: {str(e)}")
