from agent.data_agent import data_agent
from agents import Runner
import asyncio

async def main():
    result = await Runner.run(data_agent, "What is the electricity consumption in Adana in 2020?")
    print(result.final_output)

asyncio.run(main())