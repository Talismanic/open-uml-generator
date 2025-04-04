import asyncio
from dataclasses import dataclass
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
        prompt = f"Software requirement: {message.content}"
        llm_result = await self._model_client.create(
            messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
            cancellation_token=ctx.cancellation_token,
        )
        response = llm_result.content
        print(f"{'-'*80}\n{self.id.type}:\n{response}")
        await self.publish_message(Message(response), topic_id=TopicId(uml_critic_topic_type, source=self.id.key))


# Agent 02: UmlCriticAgent
@type_subscription(topic_type=uml_critic_topic_type)
class UmlCriticAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A UML critic agent.")
        self._system_message = SystemMessage(
            content=(
                "You are the head architect of a software company and expert in PlantUML syntax and modeling. "
                "Analyze the PlantUML code, identify if any component is missing in the software architecture and fix those issues. "
                "Identify any syntax issue in the PlantUML code and fix those issues."
            )
        )
        self._model_client = model_client

    @message_handler
    async def handle_intermediate_text(self, message: Message, ctx: MessageContext) -> None:
        prompt = f"Draft copy:\n{message.content}"
        llm_result = await self._model_client.create(
            messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
            cancellation_token=ctx.cancellation_token,
        )
        response = llm_result.content
        print(f"{'-'*80}\n{self.id.type}:\n{response}")
        await self.publish_message(Message(response), topic_id=TopicId(uml_renderer_topic_type, source=self.id.key))


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
        print(f"UmlRendererAgent received: {message.content}")
        session = self._system_messages + [UserMessage(content=message.content, source="user")]

        create_result = await self._model_client.create(
            messages=session,
            tools=self._tools,
            cancellation_token=ctx.cancellation_token,
        )

        if isinstance(create_result.content, str):
            return Message(content=create_result.content)

        session.append(AssistantMessage(content=create_result.content, source="assistant"))
        results = await asyncio.gather(
            *[self._execute_tool_call(call, ctx.cancellation_token) for call in create_result.content]
        )

        session.append(FunctionExecutionResultMessage(content=results))

        create_result = await self._model_client.create(
            messages=session,
            cancellation_token=ctx.cancellation_token,
        )
        assert isinstance(create_result.content, str)
        return Message(content=create_result.content)

    async def _execute_tool_call(self, call: FunctionCall, cancellation_token: CancellationToken) -> FunctionExecutionResult:
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
# NOTE: Do NOT include main() here — handled in uml_agent_runner.py
