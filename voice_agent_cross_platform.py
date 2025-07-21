import asyncio
import threading
import sys
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

class CrossPlatformKeyListener:
    """Cross-platform keyboard listener that doesn't require termios"""
    
    def __init__(self):
        self.paused = False
        self.running = True
        
    def start_listening(self):
        """Start keyboard listener using input() method"""
        thread = threading.Thread(target=self._input_listener, daemon=True)
        thread.start()
        return thread
        
    def _input_listener(self):
        """Simple input listener using input() function"""
        global AGENT_PAUSED, AGENT_RUNNING
        
        print("\n" + "="*50)
        print("🎤 VOICE AGENT CONTROLS")
        print("="*50)
        print("Type 'pause' or 'p' to pause listening")
        print("Type 'resume' or 'r' to resume listening") 
        print("Type 'quit' or 'q' to exit")
        print("Press Enter after each command")
        print("="*50 + "\n")
        
        try:
            while AGENT_RUNNING:
                try:
                    # Use input() which works cross-platform
                    command = input().strip().lower()
                    
                    if command in ['pause', 'p']:
                        if not AGENT_PAUSED:
                            AGENT_PAUSED = True
                            print("🎙️ [PAUSED] Agent listening is now paused")
                            print("Type 'resume' or 'r' to continue listening")
                        else:
                            print("⚠️  Agent is already paused")
                            
                    elif command in ['resume', 'r']:
                        if AGENT_PAUSED:
                            AGENT_PAUSED = False
                            print("🎙️ [RESUMED] Agent listening is now active")
                            print("Type 'pause' or 'p' to pause listening")
                        else:
                            print("⚠️  Agent is already listening")
                            
                    elif command in ['quit', 'q', 'exit']:
                        AGENT_RUNNING = False
                        print("🛑 Shutting down voice agent...")
                        break
                        
                    elif command == 'status':
                        status = "PAUSED" if AGENT_PAUSED else "LISTENING"
                        print(f"📊 Current status: {status}")
                        
                    elif command == 'help':
                        print("\n🔧 Available commands:")
                        print("  pause/p  - Pause agent listening")
                        print("  resume/r - Resume agent listening")
                        print("  status   - Show current status")
                        print("  quit/q   - Exit application")
                        print("  help     - Show this help\n")
                        
                    elif command == '':
                        # Empty input, just show current status
                        status = "PAUSED" if AGENT_PAUSED else "LISTENING"
                        print(f"Status: {status} | Commands: pause/resume/quit/help")
                        
                    else:
                        print(f"❓ Unknown command: '{command}'. Type 'help' for available commands")
                        
                except EOFError:
                    # Handle Ctrl+D or input stream closing
                    AGENT_RUNNING = False
                    break
                except KeyboardInterrupt:
                    # Handle Ctrl+C
                    AGENT_RUNNING = False
                    break
                    
        except Exception as e:
            print(f"Input listener error: {e}")
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
            print(f"[PAUSED] Ignoring message while paused: {str(message)[:50]}...")
            return
            
        # Process message normally when not paused
        await super().on_message(message)

async def entrypoint(ctx: agents.JobContext):
    global AGENT_RUNNING, AGENT_PAUSED
    
    # Setup keyboard control
    print("🚀 Starting Voice Agent with Text-Based Controls")
    keyboard_listener = CrossPlatformKeyListener()
    keyboard_thread = keyboard_listener.start_listening()
    
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
        print("🎙️ Voice agent is now LISTENING")
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
    print("🚀 Starting Cross-Platform Voice Agent")
    try:
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
    except KeyboardInterrupt:
        print("\n❌ Application terminated by user.")
    except Exception as e:
        print(f"💥 Application error: {e}")
        raise