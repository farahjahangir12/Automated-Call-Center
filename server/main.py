from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent
from livekit.plugins import groq, silero, cartesia
from router import HospitalRouter  # Import the router


load_dotenv()


class Assistant(Agent):
    def __init__(self, router: HospitalRouter) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant for a hospital system.")
        self.router = router  # Store the router instance
        self.current_session_id = None

    async def on_message(self, message: agents.ChatMessage):
        # Process the user's message through the router
        response = await self.router.process_query(message.message, self.current_session_id)
        
        # Update the session ID if we got a new one
        if 'session_id' in response:
            self.current_session_id = response['session_id']
        
        # Send the response back to the user
        await self.current_room.send_text(response.get("response", "Sorry, I couldn't process your request."))

    async def handle_query(self, query: str) -> str:
        """Send the query to the router and get the response."""
        response = await self.router.process_query(query, self.current_session_id)
        
        # Update the session ID if we got a new one
        if 'session_id' in response:
            self.current_session_id = response['session_id']
        
        return response.get("response", "Sorry, I couldn't process your request.")


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    # Initialize the router and load all agents
    router = await HospitalRouter.create()
    await router.initialize()  # Ensure all agents are loaded

    session = AgentSession(
        stt=groq.STT(
            model="whisper-large-v3-turbo",
            language="en",
        ),
        llm=groq.LLM(
            model="llama3-8b-8192"
        ),
        tts=cartesia.TTS(),
        vad=silero.VAD.load(),
    )

    assistant = Assistant(router)  # Pass the router to the assistant

    await session.start(
        room=ctx.room,
        agent=assistant,
    )

    # Customize the greeting for a hospital setting
    await session.generate_reply(
        instructions="Greet the user as a hospital assistant. Say: 'Hello, I'm your hospital assistant. How can I help you today? You can ask about appointments, medical questions, or general hospital information.'"
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))