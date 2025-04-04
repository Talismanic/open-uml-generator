import os
from typing import List
from tools import render_plantuml

from autogen_core import SingleThreadedAgentRuntime, TopicId
from autogen_core.tools import Tool, FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient
# from utils import generate_filename_from_requirement


from autogen_logic import (
    UmlGeneratorAgent,
    UmlCriticAgent,
    UmlRendererAgent,
    Message,
    uml_generator_topic_type,
    uml_critic_topic_type,
    uml_renderer_topic_type,
)


# Main callable function for the backend
async def generate_uml(requirement: str) -> str:
    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")
    runtime = SingleThreadedAgentRuntime()


    tools: List[Tool] = [FunctionTool(render_plantuml, description="Render the PlantUML code.")]

    # Register all agents with shared topic types
    await UmlGeneratorAgent.register(
        runtime, type=uml_generator_topic_type, factory=lambda: UmlGeneratorAgent(model_client)
    )

    await UmlCriticAgent.register(
        runtime, type=uml_critic_topic_type, factory=lambda: UmlCriticAgent(model_client)
    )

    await UmlRendererAgent.register(
        runtime, type=uml_renderer_topic_type, factory=lambda: UmlRendererAgent(model_client, tool_schema=tools)
    )

    # Start the message processing loop
    runtime.start()

    # Publish requirement to the generator agent
    await runtime.publish_message(
        Message(content=requirement),
        topic_id=TopicId(uml_generator_topic_type, source="web"),
    )

    # Wait for all agents to complete
    await runtime.stop_when_idle()

    # Return most recently created diagram path
    diagram_dir = "diagrams"
    if not os.path.exists(diagram_dir):
        return ""

    files = sorted(
        os.listdir(diagram_dir),
        key=lambda f: os.path.getctime(os.path.join(diagram_dir, f)),
        reverse=True
    )
    if not files:
        return ""

    return f"/diagrams/{os.path.basename(files[0])}"


