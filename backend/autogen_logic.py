import asyncio
from dataclasses import dataclass
import time
from typing import List
from dotenv import load_dotenv
import json

from autogen_core import (
    MessageContext,
    RoutedAgent,
    SingleThreadedAgentRuntime,
    TopicId,
    FunctionCall,
    CancellationToken,
    type_subscription,
    message_handler,
)

from autogen_core.models import (
    ChatCompletionClient,
    SystemMessage,
    UserMessage,
    LLMMessage,
    AssistantMessage,
    FunctionExecutionResult,
    FunctionExecutionResultMessage,
)
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.tools import Tool, FunctionTool
from tools import render_plantuml

load_dotenv()

@dataclass
class Message:
    content: str

uml_generator_topic_type = "UmlGeneratorAgent"
uml_critic_topic_type = "UmlCriticAgent"
uml_renderer_topic_type = "UmlRendererAgent"

# Agent 01: UmlGeneratorAgent
@type_subscription(topic_type=uml_generator_topic_type)
class UmlGeneratorAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A UML generator agent.")
        self._system_message = SystemMessage(
            content=(
                "You are a helpful software architect agent. You can produce high-quality PlantUML class diagram syntax. "
                "But sometimes you may make mistakes. If you make a mistake, the head architect will fix those."
            )
        )
        self._model_client = model_client

    @message_handler
    async def handle_user_description(self, message: Message, ctx: MessageContext) -> None:
        payload = json.loads(message.content)
        requirement = payload["requirement"]
        mode = payload.get("mode", 2)
        prompt = f"Software requirement: {message.content}"
        llm_result = await self._model_client.create(
            messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
            cancellation_token=ctx.cancellation_token,
        )
        uml_code = llm_result.content
        print(f"{'-'*80}\n{self.id.type}:\n{uml_code}")
        
        if mode == 2:
            await self.publish_message(
                Message(content=json.dumps({
                    "base_diagram": uml_code,
                    "mode": mode
                    })),
                    topic_id=TopicId(uml_critic_topic_type, source=self.id.key)
                    )

            
        else:
            publishable_payload = json.dumps({
            "diagrams": [uml_code],
            "mode": mode
        })
            await self.publish_message(
                Message(content=publishable_payload),
                topic_id=TopicId(uml_renderer_topic_type, source=self.id.key)
            )
       


# Agent 02: UmlCriticAgent
@type_subscription(topic_type=uml_critic_topic_type)
class UmlCriticAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A UML critic agent.")
        self._system_message = SystemMessage(
            content=("""
                    **#Persona:**  You are an expert Head Software Architect and a master of PlantUML syntax and modeling. 
                    **#Task:** Analyze the provided PlantUML code. Your goal is to improve its architectural representation and correctness. 
                    **#Instructions:** 
                        1. Identify & Fix Syntax Errors: Correct any PlantUML syntax mistakes. 
                        2. Analyze Architecture and follow below instructions: 
                            a. Identify any logical essential components that appear to be missing based on the existing elements and common architectural patterns and add the missing components.
                            b. Examine relationships. If any existing class/component is isolated but clearly should be connected to others based on its name or context, add the appropriate relationship(s) (e.g., association, dependency, inheritance) using correct PlantUML syntax. 
                            c. Constraint: Do not remove or discard any existing classes, interfaces, or components present in the original code. Do not add new any comments or extra information in the plantuml code.
                    **#Output:** Provide the corrected and potentially enhanced PlantUML code.

                """
                
            )
        )
        self._model_client = model_client

    @message_handler
    async def handle_intermediate_text(self, message: Message, ctx: MessageContext) -> None:
        payload = json.loads(message.content)
        base_diagram = payload["base_diagram"]
        mode = payload.get("mode", 2)
        prompt = f"Draft copy:\n{base_diagram}"
        llm_result = await self._model_client.create(
            messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
            cancellation_token=ctx.cancellation_token,
        )
        enhanced_diagram = llm_result.content
        print(f"{'-'*80}\n{self.id.type}:\n{enhanced_diagram}")
        publishable_payload = json.dumps({
            "diagrams": [base_diagram, enhanced_diagram],
            "mode": mode
        })
        await self.publish_message(Message(content=publishable_payload), topic_id=TopicId(uml_renderer_topic_type, source=self.id.key))


# Agent 03: UmlRendererAgent
@type_subscription(topic_type=uml_renderer_topic_type)
class UmlRendererAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, tool_schema: List[Tool]) -> None:
        super().__init__("An agent with tools")
        self._system_messages = [SystemMessage(content="You are a helpful AI assistant.")]
        self._model_client = model_client
        self._tools = tool_schema

    @message_handler
    async def handle_user_message(self, message: Message, ctx: MessageContext) -> Message:
        payload = json.loads(message.content)
        diagrams = payload["diagrams"]
        mode = payload.get("mode", 2)
        print(f"UmlRendererAgent received {len(diagrams)} diagrams with mode = {mode}")

        all_results = []

        for idx, diagram in enumerate(diagrams):
            file_tag = "base" if idx == 0 else "enhanced"
            timestamp = str(int(time.time()))
            file_name = f"{file_tag}_{timestamp}.png"
            print(f"Rendering {file_tag} diagram to file: {file_name}")
            session = self._system_messages + [UserMessage(content=diagram, source="user")]
            create_result = await self._model_client.create(
                messages=session,
                tools=self._tools,
                cancellation_token=ctx.cancellation_token,
            )
            if isinstance(create_result.content, str):
                all_results.append(Message(content=create_result.content))
                continue
            session.append(AssistantMessage(content=create_result.content, source="assistant"))
            tool_results = await asyncio.gather(
                *[self._execute_tool_call(call, ctx.cancellation_token, file_name) for call in create_result.content]
            )
            session.append(FunctionExecutionResultMessage(content=tool_results))

            final_response = await self._model_client.create(
                messages=session,
                cancellation_token=ctx.cancellation_token,
            )
            if isinstance(final_response.content, str):
                all_results.append(Message(content=final_response.content))
        
        combined_diagram = "\n\n".join([msg.content for msg in all_results])

        return Message(content=json.dumps({
        "diagram_urls": [f"/diagrams/uml_{i}.puml" for i in range(len(all_results))],
        "combined_diagram": combined_diagram
    }))

    async def _execute_tool_call(self, call: FunctionCall, cancellation_token: CancellationToken, file_name: str) -> FunctionExecutionResult:
        print(f"Executing tool: {call.name} with arguments: {call.arguments}")
        tool = next((tool for tool in self._tools if tool.name == call.name), None)
        if not tool:
            return FunctionExecutionResult(
                call_id=call.id,
                content="Error: Tool not found.",
                is_error=True,
                name=call.name
            )

        try:
            arguments = json.loads(call.arguments)
            arguments["file_name"] = file_name
            result = await tool.run_json(arguments, cancellation_token)

            return FunctionExecutionResult(
                call_id=call.id,
                content=str(result),
                is_error=False,
                name=tool.name
            )
        except Exception as e:
            return FunctionExecutionResult(
                call_id=call.id,
                content=str(e),
                is_error=True,
                name=call.name
            )
