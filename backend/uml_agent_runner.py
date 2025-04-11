import json
import os
from typing import List
import time
from tools import render_plantuml
from utils import save_diagram

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
async def generate_uml(requirement: str, mode: int = 2 ) -> str:
    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")
    model_client_for_critique = OpenAIChatCompletionClient(model="gpt-4o-mini")
    runtime = SingleThreadedAgentRuntime()


    tools: List[Tool] = [FunctionTool(render_plantuml, description="Render the PlantUML code.")]

    # Register all agents with shared topic types
    await UmlGeneratorAgent.register(
        runtime, type=uml_generator_topic_type, factory=lambda: UmlGeneratorAgent(model_client)
    )

    await UmlCriticAgent.register(
        runtime, type=uml_critic_topic_type, factory=lambda: UmlCriticAgent(model_client_for_critique)
    )

    await UmlRendererAgent.register(
        runtime, type=uml_renderer_topic_type, factory=lambda: UmlRendererAgent(model_client, tool_schema=tools)
    )

    # Start the message processing loop
    runtime.start()

    payload = json.dumps({
        "requirement": requirement,
        "mode": mode,
    })


    # Publish requirement to the generator agent
    await runtime.publish_message(
        Message(content=payload),
        topic_id=TopicId(uml_generator_topic_type, source="web"),
    )

    # Wait for all agents to complete
    await runtime.stop_when_idle()

    # Return most recently created diagram path
    diagram_dir = "diagrams"
    if not os.path.exists(diagram_dir):
        return ""
    
    files = sorted(
        [f for f in os.listdir(diagram_dir) if f.endswith(".png")],
        key=lambda f: os.path.getctime(os.path.join(diagram_dir, f)),
        reverse=True
    )

    if mode == 1:
        return {
            "diagram_url": f"/diagrams/{files[0]}" if files else ""
        }

    if mode == 2 and len(files) >= 2:
        return {
            "base_diagram_url": f"/diagrams/{files[1]}",  # older
            "enhanced_diagram_url": f"/diagrams/{files[0]}"  # newer
        }

    return {}


