# Voice Agent with Spacebar Control

This voice agent can host events and includes pause/resume functionality controlled by the spacebar.

## Features

- 🎤 Voice agent for event hosting
- ⏸️ Spacebar pause/resume control
- 🎙️ Real-time audio processing with Google's Gemini model
- 🔄 Seamless start/stop functionality

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables in a `.env` file:
```env
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-credentials.json
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
```

## Usage

### Status Indicators

- `🎙️ [RESUMED]` - Agent is actively listening
- `🎙️ [PAUSED]` - Agent is paused and ignoring audio input
- `[PAUSED] Ignoring message while paused` - Message received while paused


## Configuration

The agent is configured as "SPARK", an AI co-host for events at Renault Nissan Tech, working alongside human host "Jegan". You can modify these settings in the code:

```python
CO_HOST = "Jegan"  # Change the human host name
AI_NAME = "SPARK"  # Change the AI assistant name
```

## Technical Details

- Uses Google's Gemini 2.0 Flash model for real-time conversation
- Implements async keyboard listening for responsive controls
- Maintains terminal compatibility with proper cleanup
- Thread-safe pause/resume state management

## Troubleshooting

If you encounter issues:

1. Ensure your `.env` file is properly configured
2. Check that your microphone permissions are enabled
3. Verify LiveKit credentials are valid
4. Run in a terminal that supports TTY for keyboard input