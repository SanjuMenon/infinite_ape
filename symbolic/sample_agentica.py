import asyncio
import sys
from dotenv import load_dotenv

# Windows compatibility: Patch signal handler registration before importing Agentica
if sys.platform == 'win32':
    # Monkey-patch add_signal_handler to be a no-op on Windows
    # This prevents NotImplementedError when Agentica tries to register signal handlers
    original_add_signal_handler = asyncio.AbstractEventLoop.add_signal_handler
    
    def patched_add_signal_handler(self, sig, callback, *args, **kwargs):
        """No-op signal handler for Windows compatibility"""
        try:
            return original_add_signal_handler(self, sig, callback, *args, **kwargs)
        except NotImplementedError:
            # Signal handlers not supported on Windows, silently ignore
            pass
    
    asyncio.AbstractEventLoop.add_signal_handler = patched_add_signal_handler
    
    # Set Windows-compatible event loop policy
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

load_dotenv()

from agentica import spawn
from agentica.logging import set_default_agent_listener
from agentica.logging.loggers import StreamLogger

set_default_agent_listener(None)

# Define your tools here!
def my_tool(arg: str) -> str:
    """Describe what your tool does."""
    return f"Result for: {arg}"

async def main():
    agent = await spawn(premise="You are a helpful assistant.")

    print("Agent ready! Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break

        # Stream the agent's response
        stream = StreamLogger()
        with stream:
            result = asyncio.create_task(
                agent.call(str, user_input, my_tool=my_tool)  # Pass your tools here
            )

        async for chunk in stream:
            if chunk.role == "agent":
                print(chunk, end="", flush=True)
        print()

        print(f"Agent: {await result}\n")

if __name__ == "__main__":
    # Windows compatibility: Use ProactorEventLoop which works better on Windows
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(main())
        finally:
            loop.close()
    else:
        asyncio.run(main())