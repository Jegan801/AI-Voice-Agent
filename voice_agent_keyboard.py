import asyncio
import threading
import sys
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import google
from dotenv import load_dotenv

# Try to import keyboard library for better key detection
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
    print("✅ Keyboard library available - spacebar control enabled")
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("⚠️  Keyboard library not found. Install with: pip install keyboard")
    print("🔧 Falling back to text-based controls")

load_dotenv()
print("loaded dot env")

# You must actually pause your speaking when instructed, rather than saying the word "pause"

CO_HOST = "Jegan"
AI_NAME = "SPARK"

# Global pause state
AGENT_PAUSED = False
AGENT_RUNNING = True

class KeyboardController:
    """Handles keyboard input for pause/resume control"""
    
    def __init__(self):
        self.use_keyboard_lib = KEYBOARD_AVAILABLE
        
    def start_listening(self):
        """Start appropriate keyboard listener"""
        if self.use_keyboard_lib:
            return self._start_keyboard_lib_listener()
        else:
            return self._start_text_input_listener()
            
    def _start_keyboard_lib_listener(self):
        """Use keyboard library for real-time spacebar detection"""
        print("🎮 SPACEBAR CONTROL ACTIVE")
        print("Press SPACEBAR to toggle pause/resume")
        print("Press ESC to exit")
        
        def on_spacebar():
            global AGENT_PAUSED
            AGENT_PAUSED = not AGENT_PAUSED
            status = "PAUSED" if AGENT_PAUSED else "RESUMED"
            print(f"\n🎙️ [{status}] Agent listening is now {status.lower()}")
            
        def on_escape():
            global AGENT_RUNNING
            AGENT_RUNNING = False
            print("\n🛑 ESC pressed - shutting down...")
            
        # Register hotkeys
        keyboard.on_press_key('space', lambda _: on_spacebar())
        keyboard.on_press_key('esc', lambda _: on_escape())
        
        # Return a dummy thread since keyboard lib handles everything
        return threading.Thread(target=lambda: None, daemon=True)
        
    def _start_text_input_listener(self):
        """Fallback to text-based input"""
        thread = threading.Thread(target=self._text_input_loop, daemon=True)
        thread.start()
        return thread
        
    def _text_input_loop(self):
        """Text-based control loop"""
        global AGENT_PAUSED, AGENT_RUNNING
        
        print("\n" + "="*50)
        print("🎤 VOICE AGENT CONTROLS")
        print("="*50)
        print("Commands (press Enter after typing):")
        print("  'p' or 'pause'  - Pause listening")
        print("  'r' or 'resume' - Resume listening") 
        print("  'q' or 'quit'   - Exit")
        print("  's' or 'status' - Show status")
        print("="*50 + "\n")
        
        try:
            while AGENT_RUNNING:
                try:
                    command = input("📝 Command: ").strip().lower()
                    
                    if command in ['p', 'pause']:
                        if not AGENT_PAUSED:
                            AGENT_PAUSED = True
                            print("🎙️ [PAUSED] Agent is now paused")
                        else:
                            print("⚠️  Already paused")
                            
                    elif command in ['r', 'resume']:
                        if AGENT_PAUSED:
                            AGENT_PAUSED = False
                            print("🎙️ [RESUMED] Agent is now listening")
                        else:
                            print("⚠️  Already listening")
                            
                    elif command in ['q', 'quit', 'exit']:
                        AGENT_RUNNING = False
                        break
                        
                    elif command in ['s', 'status']:
                        status = "PAUSED" if AGENT_PAUSED else "LISTENING"
                        print(f"📊 Status: {status}")
                        
                    elif command == '':
                        status = "PAUSED" if AGENT_PAUSED else "LISTENING"
                        print(f"📊 Status: {status}")
                        
                    else:
                        print(f"❓ Unknown: '{command}' | Try: p/r/q/s")
                        
                except (EOFError, KeyboardInterrupt):
                    AGENT_RUNNING = False
                    break
                    
        except Exception as e:
            print(f"Input error: {e}")
        finally:
            AGENT_RUNNING = False

class ControllableAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=f"""
Role: You are {AI_NAME}, the AI Co-Host for today's "AI Day" event at Renault Nissan Tech.  
You will collaborate with the human host {CO_HOST} to ensure the event runs smoothly and professionally.

IMPORTANT: You have pause/resume capability. When paused, you should not respond to any audio input 
until resumed. Only respond when the system is in an active listening state.
""")

    async def on_message(self, message):
        """Override message handling to respect pause state"""
        global AGENT_PAUSED
        
        if AGENT_PAUSED:
            print(f"[PAUSED] Ignoring message: {str(message)[:30]}...")
            return
            
        # Process message normally when not paused
        await super().on_message(message)

async def entrypoint(ctx: agents.JobContext):
    global AGENT_RUNNING, AGENT_PAUSED
    
    # Setup keyboard control
    controller = KeyboardController()
    controller_thread = controller.start_listening()
    
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
        print("🎙️ Voice agent is LISTENING")
        # Main loop with pause state monitoring
        while AGENT_RUNNING:
            await asyncio.sleep(0.1)
                
    except asyncio.CancelledError:
        print("Agent session cancelled.")
    except KeyboardInterrupt:
        print("\n🛑 Interrupt received. Shutting down...")
    finally:
        AGENT_RUNNING = False
        if KEYBOARD_AVAILABLE:
            keyboard.unhook_all()  # Clean up keyboard hooks
        print("✅ Voice agent stopped.")

if __name__ == "__main__":
    print("🚀 Starting Voice Agent with Smart Controls")
    try:
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
    except KeyboardInterrupt:
        print("\n❌ Application terminated.")
    except Exception as e:
        print(f"💥 Error: {e}")
        raise