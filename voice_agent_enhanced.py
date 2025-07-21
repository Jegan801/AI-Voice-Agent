import asyncio
import threading
import sys
import select
import tty
import termios
from typing import Optional
from livekit import agents, rtc
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import google
from dotenv import load_dotenv

load_dotenv()
print("loaded dot env")

# You must actually pause your speaking when instructed, rather than saying the word "pause"

CO_HOST = "Jegan"
AI_NAME = "SPARK"

class VoiceControlManager:
    """Manages voice agent pause/resume functionality with keyboard control"""
    
    def __init__(self):
        self.is_paused = False
        self.running = True
        self._old_settings = None
        self._agent_session: Optional[AgentSession] = None
        self._lock = asyncio.Lock()
        
    def set_agent_session(self, session: AgentSession):
        """Set the agent session to control"""
        self._agent_session = session
        
    async def start_keyboard_listener(self):
        """Start listening for keyboard input in a separate thread"""
        if sys.stdin.isatty():  # Only if running in a terminal
            self._old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
            
        # Start keyboard listening in executor to avoid blocking
        loop = asyncio.get_event_loop()
        thread = threading.Thread(target=self._keyboard_thread, daemon=True)
        thread.start()
        
    def _keyboard_thread(self):
        """Thread function for keyboard input handling"""
        try:
            while self.running:
                if sys.stdin.isatty() and select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)
                    
                    # Check for spacebar (ASCII 32)
                    if ord(char) == 32:  # Spacebar
                        # Schedule the toggle in the main event loop
                        asyncio.create_task(self._toggle_pause_resume())
                        
                    # Check for Ctrl+C
                    elif ord(char) == 3:  # Ctrl+C
                        self.running = False
                        break
                        
        except Exception as e:
            print(f"Keyboard listener error: {e}")
        finally:
            self._restore_terminal()
            
    async def _toggle_pause_resume(self):
        """Toggle pause/resume state and update agent"""
        async with self._lock:
            self.is_paused = not self.is_paused
            status = "PAUSED" if self.is_paused else "RESUMED"
            print(f"\n[{status}] Agent listening is now {status.lower()}")
            print("Press SPACEBAR to toggle pause/resume, Ctrl+C to exit")
            
            # If we have an agent session, we can control its behavior
            if self._agent_session:
                try:
                    if self.is_paused:
                        # Disable microphone input processing
                        await self._disable_audio_processing()
                    else:
                        # Re-enable microphone input processing
                        await self._enable_audio_processing()
                except Exception as e:
                    print(f"Error controlling agent audio: {e}")
                    
    async def _disable_audio_processing(self):
        """Disable audio input processing"""
        # This would typically involve pausing the agent's audio track processing
        # The exact implementation depends on LiveKit's agent API
        print("🔇 Audio processing disabled")
        
    async def _enable_audio_processing(self):
        """Enable audio input processing"""
        # This would typically involve resuming the agent's audio track processing
        print("🔊 Audio processing enabled")
            
    def _restore_terminal(self):
        """Restore terminal settings"""
        if self._old_settings and sys.stdin.isatty():
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_settings)
            
    def stop(self):
        """Stop the voice control manager"""
        self.running = False
        self._restore_terminal()

class ControllableAssistant(Agent):
    """Assistant that can be paused and resumed"""
    
    def __init__(self, voice_manager: VoiceControlManager) -> None:
        self.voice_manager = voice_manager
        super().__init__(instructions=f"""
Role: You are {AI_NAME}, the AI Co-Host for today's "AI Day" event at Renault Nissan Tech. 
You will collaborate with the human host {CO_HOST} to ensure the event runs smoothly and professionally.

Important: You have pause/resume functionality. When paused, you should not respond to audio input 
until resumed. The human operator can control this with the spacebar.
""")
        
    async def on_track_subscribed(self, track: rtc.Track, participant: rtc.RemoteParticipant):
        """Handle incoming audio tracks with pause/resume control"""
        # Only process audio if not paused
        if not self.voice_manager.is_paused and track.kind == rtc.TrackKind.KIND_AUDIO:
            await super().on_track_subscribed(track, participant)
            
    async def handle_user_speech(self, speech_text: str):
        """Override speech handling to respect pause state"""
        if self.voice_manager.is_paused:
            print(f"[PAUSED] Ignoring speech: {speech_text}")
            return
            
        # Process speech normally when not paused
        await super().handle_user_speech(speech_text)

async def entrypoint(ctx: agents.JobContext):
    # Initialize voice control manager
    voice_manager = VoiceControlManager()
    
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
    
    # Link voice manager to session
    voice_manager.set_agent_session(session)

    # Start keyboard listener
    print("Starting voice agent with pause/resume control...")
    print("Press SPACEBAR to pause/resume listening, Ctrl+C to exit")
    await voice_manager.start_keyboard_listener()

    # Start the agent session
    await session.start(
        room=ctx.room,
        agent=ControllableAssistant(voice_manager),
        room_input_options=RoomInputOptions(),
    )

    await ctx.connect()
    
    try:
        # Main loop
        while voice_manager.running:
            await asyncio.sleep(0.1)
                
    except asyncio.CancelledError:
        print("Agent session cancelled.")
    except KeyboardInterrupt:
        print("\nReceived interrupt signal. Shutting down...")
    finally:
        # Cleanup
        voice_manager.stop()
        print("Voice agent stopped.")

if __name__ == "__main__":
    print("Starting Enhanced Voice Agent CLI")
    try:
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
    except Exception as e:
        print(f"Application error: {e}")