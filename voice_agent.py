import asyncio
import threading
import sys
import select
import tty
import termios
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import google
from dotenv import load_dotenv

load_dotenv()
print("loaded dot env")

# You must actually pause your speaking when instructed, rather than saying the word "pause"

CO_HOST = "Jegan"
AI_NAME = "SPARK"

class KeyboardListener:
    """Handle keyboard input for pause/resume functionality"""
    
    def __init__(self):
        self.is_paused = False
        self.running = True
        self._old_settings = None
        
    def start_listening(self):
        """Start listening for keyboard input in a separate thread"""
        if sys.stdin.isatty():  # Only if running in a terminal
            self._old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
            
        thread = threading.Thread(target=self._listen_for_keys, daemon=True)
        thread.start()
        return thread
        
    def _listen_for_keys(self):
        """Listen for spacebar press to toggle pause/resume"""
        try:
            while self.running:
                if sys.stdin.isatty() and select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)
                    
                    # Check for spacebar (ASCII 32)
                    if ord(char) == 32:  # Spacebar
                        self.is_paused = not self.is_paused
                        status = "PAUSED" if self.is_paused else "RESUMED"
                        print(f"\n[{status}] Agent listening is now {status.lower()}")
                        print("Press SPACEBAR to toggle pause/resume, Ctrl+C to exit")
                        
                    # Check for Ctrl+C
                    elif ord(char) == 3:  # Ctrl+C
                        self.running = False
                        break
                        
                else:
                    # Small delay to prevent busy waiting
                    asyncio.sleep(0.1)
                    
        except Exception as e:
            print(f"Keyboard listener error: {e}")
        finally:
            self._restore_terminal()
            
    def _restore_terminal(self):
        """Restore terminal settings"""
        if self._old_settings and sys.stdin.isatty():
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_settings)
            
    def stop(self):
        """Stop the keyboard listener"""
        self.running = False
        self._restore_terminal()

class Assistant(Agent):
    def __init__(self, keyboard_listener: KeyboardListener) -> None:
        self.keyboard_listener = keyboard_listener
        super().__init__(instructions=f"""
Role: You are {AI_NAME}, the AI Co-Host for today's "AI Day" event at Renault Nissan Tech. 
You will collaborate with the human host {CO_HOST} to ensure the event runs smoothly and professionally.

Important: You are currently in listening mode. When paused, you should not respond to audio input 
until resumed. Always check your pause status before responding.
""")

async def entrypoint(ctx: agents.JobContext):
    # Initialize keyboard listener
    keyboard_listener = KeyboardListener()
    
    # Create session with enhanced configuration
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

    # Start keyboard listener
    print("Starting voice agent...")
    print("Press SPACEBAR to pause/resume listening, Ctrl+C to exit")
    keyboard_thread = keyboard_listener.start_listening()

    # Start the agent session
    await session.start(
        room=ctx.room,
        agent=Assistant(keyboard_listener),
        room_input_options=RoomInputOptions(),
    )

    await ctx.connect()
    
    try:
        # Main loop with pause/resume control
        while keyboard_listener.running:
            # Check if agent should be listening
            if not keyboard_listener.is_paused:
                # Agent is active and listening
                await asyncio.sleep(0.1)
            else:
                # Agent is paused - skip processing
                await asyncio.sleep(0.1)
                
    except asyncio.CancelledError:
        print("Agent session cancelled.")
    except KeyboardInterrupt:
        print("\nReceived interrupt signal. Shutting down...")
    finally:
        # Cleanup
        keyboard_listener.stop()
        print("Voice agent stopped.")

if __name__ == "__main__":
    print("Starting CLI")
    try:
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
    except Exception as e:
        print(f"Application error: {e}")