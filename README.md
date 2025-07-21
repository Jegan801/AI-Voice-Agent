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

### Option 1: Cross-Platform (Recommended)
```bash
python voice_agent_cross_platform.py
```
**Text-based controls:** Type commands like 'pause', 'resume', 'quit' and press Enter.

### Option 2: With Keyboard Library (Real-time spacebar)
```bash
pip install keyboard  # May require admin/sudo privileges
python voice_agent_keyboard.py
```
**Real-time controls:** Press SPACEBAR to toggle, ESC to exit (no Enter needed).

### Controls

#### Cross-Platform Version:
- Type `pause` or `p` + Enter → Pause listening
- Type `resume` or `r` + Enter → Resume listening  
- Type `quit` or `q` + Enter → Exit
- Type `status` or `s` + Enter → Show current status

#### Keyboard Library Version:
- **SPACEBAR** → Toggle pause/resume instantly
- **ESC** → Exit application
- **Ctrl+C** → Force exit

### Status Indicators

- `🎙️ [RESUMED]` - Agent is actively listening
- `🎙️ [PAUSED]` - Agent is paused and ignoring audio input
- `[PAUSED] Ignoring message while paused` - Message received while paused

## Files

- `voice_agent_cross_platform.py` - **Cross-platform solution (recommended)**
- `voice_agent_keyboard.py` - Real-time spacebar control (requires keyboard lib)
- `voice_agent_final.py` - Unix/Linux only (requires termios)
- `voice_agent_enhanced.py` - Advanced features
- `voice_agent.py` - Basic implementation

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