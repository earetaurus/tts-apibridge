import base64
import logging
from typing import Optional
import runpod
from models import RunPodJobResponse, RunPodOutput
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
        
        logger.info(f"Initialized RunPod client for endpoint: {self.endpoint_id}")
    
    async def generate_speech(self, text: str) -> Optional[str]:
        """
        Generate speech using RunPod Endpoint SDK
        
        Args:
            text: The text to convert to speech
            
        Returns:
            Base64 encoded WAV audio data or None if failed
        """
        try:
            logger.info(f"Generating speech for text: {text[:100]}...")
            
            # Prepare the input for RunPod
            runpod_input = {
                "text": text
            }
            
            # Run the job
            logger.info(f"Running job on endpoint {self.endpoint_id}")
            job = self.endpoint.run(runpod_input)
            
            # Check initial status
            status = job.status()
            logger.info(f"Initial job status: {status}")
            
            # Wait for completion with timeout
            logger.info("Waiting for job completion...")
            if status != "COMPLETED":
                output_data = job.output(timeout=config.REQUEST_TIMEOUT)
            else:
                output_data = job.output()
            
            # Get final job status
            final_status = job.status()
            logger.info(f"Job completed. Status: {final_status}")
            logger.info(f"Job output: {output_data}")
            
            # Construct the full response object
            job_result = {
                "status": final_status,
                "output": output_data,
                "id": job.id if hasattr(job, 'id') else "unknown"
            }
            
            # Parse the response using our model
            runpod_response = RunPodJobResponse(**job_result)
            
            # Check if job completed successfully
            if runpod_response.status != "COMPLETED":
                logger.error(f"Job did not complete successfully. Status: {runpod_response.status}")
                if runpod_response.status == "FAILED":
                    logger.error(f"Job failed. Job ID: {runpod_response.id}")
                return None
            
            # Check if we have output with audio
            if not runpod_response.output or not runpod_response.output.audio_base64:
                logger.error("No audio data in job output")
                return None
            
            logger.info(f"Successfully received audio data. Job ID: {runpod_response.id}")
            logger.info(f"Execution time: {runpod_response.executionTime}ms")
            
            return runpod_response.output.audio_base64
                
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
