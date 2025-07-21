import asyncio
import threading
import sys
import termios
import tty
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import google
from dotenv import load_dotenv

load_dotenv()
print("loaded dot env")

# You must actually pause your speaking when instructed, rather than saying the word "pause"

CO_HOST = "Jegan"
AI_NAME = "SPARK"

# Global pause state
AGENT_PAUSED = False
AGENT_RUNNING = True

def setup_keyboard_listener():
    """Setup keyboard listener for spacebar control"""
    global AGENT_PAUSED, AGENT_RUNNING
    
    original_settings = None
    if sys.stdin.isatty():
        original_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())
    
    def keyboard_listener():
        global AGENT_PAUSED, AGENT_RUNNING
        try:
            while AGENT_RUNNING:
                if sys.stdin.isatty():
                    char = sys.stdin.read(1)
                    if ord(char) == 32:  # Spacebar
                        AGENT_PAUSED = not AGENT_PAUSED
                        status = "PAUSED" if AGENT_PAUSED else "RESUMED"
                        print(f"\n🎙️ [{status}] Agent listening is now {status.lower()}")
                        print("Press SPACEBAR to toggle pause/resume, Ctrl+C to exit")
                    elif ord(char) == 3:  # Ctrl+C
                        AGENT_RUNNING = False
                        break
        except Exception as e:
            print(f"Keyboard error: {e}")
        finally:
            if original_settings and sys.stdin.isatty():
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_settings)
    
    # Start keyboard listener in a daemon thread
    thread = threading.Thread(target=keyboard_listener, daemon=True)
    thread.start()
    return thread

class ControllableAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=f"""
Role: You are {AI_NAME}, the AI Co-Host for today's "AI Day" event at Renault Nissan Tech.  
You will collaborate with the human host {CO_HOST} to ensure the event runs smoothly and professionally.

IMPORTANT: You have pause/resume capability controlled by spacebar. When paused, you should not 
respond to any audio input until resumed. Only respond when the system is in an active listening state.
""")

    async def on_message(self, message):
        """Override message handling to respect pause state"""
        global AGENT_PAUSED
        
        if AGENT_PAUSED:
            print(f"[PAUSED] Ignoring message while paused")
            return
            
        # Process message normally when not paused
        await super().on_message(message)

async def entrypoint(ctx: agents.JobContext):
    global AGENT_RUNNING, AGENT_PAUSED
    
    # Setup keyboard control
    print("🎤 Starting Voice Agent with Spacebar Control")
    print("Press SPACEBAR to pause/resume listening, Ctrl+C to exit")
    keyboard_thread = setup_keyboard_listener()
    
    # Create agent session
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="kore", 
            modalities=["AUDIO"]
        ),
        tts=google.TTS(
            speaking_rate=0.80,
        ),
        min_consecutive_speech_delay=2,
    )

    # Start the session
    await session.start(
        room=ctx.room,
        agent=ControllableAssistant(),
        room_input_options=RoomInputOptions(),
    )

    await ctx.connect()
    
    try:
        # Main loop with pause state monitoring
        while AGENT_RUNNING:
            if not AGENT_PAUSED:
                # Agent is listening - normal operation
                await asyncio.sleep(0.1)
            else:
                # Agent is paused - minimal processing
                await asyncio.sleep(0.2)
                
    except asyncio.CancelledError:
        print("Agent session cancelled.")
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal. Shutting down...")
    finally:
        AGENT_RUNNING = False
        print("✅ Voice agent stopped.")

if __name__ == "__main__":
    print("🚀 Starting Voice Agent CLI")
    try:
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
    except KeyboardInterrupt:
        print("\n❌ Application terminated by user.")
    except Exception as e:
        print(f"💥 Application error: {e}")
        raise