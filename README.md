# TTS API Bridge

this is 70% vibe coded only fair to tell you
check out
https://github.com/earetaurus/runpod-voxcpm


An OpenAI-compatible Text-to-Speech API bridge that uses RunPod serverless endpoints as the backend.

## Features

- 🎯 **OpenAI Compatible**: Mimics OpenAI's `/v1/audio/speech` endpoint
- 🚀 **RunPod Backend**: Uses RunPod serverless TTS services with official SDK
- 🔄 **Format Support**: Supports multiple audio formats (mp3, wav, opus, aac, flac)
- 🛡️ **Error Handling**: Comprehensive error handling with OpenAI-style responses
- 📝 **Logging**: Detailed logging for monitoring and debugging
- ⚙️ **Configurable**: Environment-based configuration
- ✅ **Test Suite**: Included test script for validation

## Quick Start

### Prerequisites

1. **RunPod Account**: Sign up at [runpod.io](https://runpod.io)
2. **TTS Endpoint**: Create a serverless TTS endpoint in RunPod
3. **API Key**: Get your RunPod API key from the dashboard

### Installation

1. Clone the repository:
```bash
git clone https://github.com/earetaurus/tts-apibridge.git
cd tts-apibridge
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your RunPod credentials
```

4. Run the server:
```bash
uv run python main.py
```

The server will start on `http://localhost:8000`

**Alternative using pip:**
```bash
pip install -r requirements.txt
python main.py
```

### Configuration

Create a `.env` file based on `.env.example`:

```bash
# Required: RunPod API Configuration
RUNPOD_API_KEY=your_runpod_api_key_here
RUNPOD_ENDPOINT_ID=your_endpoint_id_here

# Optional: Server Configuration
HOST=0.0.0.0
PORT=8000

# Optional: Request Configuration
REQUEST_TIMEOUT=300

# Optional: Logging
LOG_LEVEL=INFO
```

**Getting your RunPod credentials:**

1. **API Key**: Go to [RunPod Dashboard](https://runpod.io/console) → Settings → API Keys
2. **Endpoint ID**: 
   - Create a serverless endpoint with your TTS model
   - Find the endpoint ID in the endpoint details (e.g., `hvdryx8l25swe6`)

## Testing

### Run Integration Test

Test your RunPod integration:

```bash
python test_runpod_integration.py
```

This will:
- Verify your environment variables
- Test the RunPod client connection
- Generate a test audio file (`test_output.wav`)

### Manual API Testing

**Endpoint**: `POST /v1/audio/speech`

**Request Body**:
```json
{
  "model": "tts-1",
  "input": "Hello, world! This is a test of the TTS API bridge.",
  "voice": "alloy",
  "response_format": "mp3",
  "speed": 1.0
}
```

**Example using curl**:
```bash
curl -X POST "http://localhost:8000/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello, world! This is a test of the TTS API bridge.",
    "voice": "alloy",
    "response_format": "mp3"
  }' \
  --output speech.mp3
```

**Example using Python**:
```python
import requests

response = requests.post(
    "http://localhost:8000/v1/audio/speech",
    json={
        "model": "tts-1",
        "input": "Hello, world! This is a test of the TTS API bridge.",
        "voice": "alloy",
        "response_format": "mp3"
    }
)

if response.status_code == 200:
    with open("speech.mp3", "wb") as f:
        f.write(response.content)
    print("Audio saved as speech.mp3")
else:
    print(f"Error: {response.json()}")
```

### Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "service": "tts-apibridge"
}
```

## Supported Audio Formats

- `mp3` (default) - audio/mpeg
- `wav` - audio/wav
- `opus` - audio/opus
- `aac` - audio/aac
- `flac` - audio/flac

## API Response Format

The RunPod serverless API returns responses in this format:

```json
{
  "delayTime": 80315,
  "executionTime": 2832,
  "id": "92537128-645f-42bd-9de4-b1c289a23566-e2",
  "output": {
    "audio_base64": "base64_wav_data_here",
    "language": "en"
  },
  "status": "COMPLETED",
  "workerId": "yc846za10ixy4d"
}
```

The API bridge automatically:
- Waits for job completion
- Extracts the base64 audio data
- Decodes it to binary audio
- Returns it in the requested format

## Error Handling

The API returns OpenAI-compatible error responses:

```json
{
  "error": {
    "message": "Failed to generate speech from backend service",
    "type": "api_error",
    "code": "speech_generation_failed"
  }
}
```

Common error scenarios:
- Missing or invalid RunPod credentials
- Endpoint not found or unavailable
- Job execution failures
- Timeout errors
- Invalid audio data

## Architecture

```
Client Request → FastAPI Server → RunPod SDK → RunPod Endpoint
                    ↓
                Base64 WAV ← Job Response ← TTS Worker
                    ↓
                Audio File ← Decoding ← Base64 Processing
```

## Development

### Running in Development Mode

```bash
python main.py
```

The server will automatically reload on code changes.

### Running in Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Support

Build and run with Docker:

```bash
docker build -t tts-apibridge .
docker run -p 8000:8000 --env-file .env tts-apibridge
```

## Monitoring

The application provides detailed logging that can be configured using the `LOG_LEVEL` environment variable:

- `DEBUG` - Detailed debugging information
- `INFO` - General information (default)
- `WARNING` - Warning messages
- `ERROR` - Error messages only

Logs include:
- Request/response details
- Job execution times
- Error diagnostics
- Performance metrics

## Troubleshooting

### Common Issues

1. **"RUNPOD_API_KEY environment variable is required"**
   - Set your API key in the `.env` file
   - Verify the key is valid in RunPod dashboard

2. **"RUNPOD_ENDPOINT_ID environment variable is required"**
   - Set your endpoint ID in the `.env` file
   - Ensure the endpoint is active and running

3. **Job timeout errors**
   - Increase `REQUEST_TIMEOUT` in configuration
   - Check if your TTS model is taking too long to process

4. **Invalid audio data**
   - Verify your TTS endpoint returns proper base64 WAV data
   - Check the endpoint logs for processing errors

### Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG python main.py
```

This will show detailed request/response information and help identify issues.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

if you want to help my runpod Balance  survive the month please use my referal link
https://runpod.io?ref=akghcny7
