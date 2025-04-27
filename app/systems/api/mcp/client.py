import asyncio

from copy import deepcopy
from contextlib import asynccontextmanager
from django.conf import settings
from django.utils.timezone import now

import mcp.types as types
from mcp import ClientSession
from mcp.client.sse import sse_client

from utility.data import create_token


@asynccontextmanager
async def connect(url, token):
    async with sse_client(url=url, headers={"Authorization": f"Bearer {token}"}) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            yield session


def format_tool_schema(server_name, tool):
    argument_descriptions = []
    if "properties" in tool.inputSchema:
        for param_name, param_info in tool.inputSchema["properties"].items():
            description = f"- {param_name}: {param_info.get('description', 'No description')}"
            if param_name in tool.inputSchema.get("required", []):
                description += " <REQUIRED>"
            argument_descriptions.append(description)

    tool_description = f"""
Tool: {tool.name}@{server_name}
Description: {tool.description}
"""
    if argument_descriptions:
        tool_description += f"""Arguments:
{chr(10).join(argument_descriptions)}
"""
    return tool_description


def format_prompt_schema(server_name, prompt):
    argument_descriptions = []
    for argument in prompt.arguments:
        description = f"- {argument.name}: {argument.description}"
        if argument.required:
            description += " <REQUIRED>"
        argument_descriptions.append(description)

    prompt_description = f"""
Prompt: {prompt.name}@{server_name}
Description: {prompt.description}
"""
    if argument_descriptions:
        prompt_description += f"""Arguments:
{chr(10).join(argument_descriptions)}
"""
    return prompt_description


def format_tool_message(message):
    if isinstance(message, types.TextContent):
        return message.text
    elif isinstance(message, types.ImageContent):
        return f"Base64 encoded {message.mimeType} image: {message.data}"
    else:
        raise RuntimeError(f"Message type {type(message)} not supported")


class MCPClient(object):

    def __init__(self, command):
        self.command = command
        self.user = command.active_user
        self.servers = {}

        if settings.KUBERNETES_NAMESPACE:
            self.servers[settings.MCP_LOCAL_SERVER_NAME] = MCPLocalServer(
                self, f"http://{settings.MCP_SERVICE_NAME}.{settings.KUBERNETES_NAMESPACE}"
            )

    def add_server(self, name, url, token):
        self.servers[name] = MCPServer(self, name, url, token)

    def list_tools(self):
        return "\n\n".join([server.list_tools() for server in self.servers.values()])

    def exec_tool(self, name, arguments=None):
        (tool_name, server_name) = self._get_name(name)
        self._verify_server(server_name)
        return self.servers[server_name].exec_tool(tool_name, arguments)

    def list_prompts(self):
        return "\n\n".join([server.list_prompts() for server in self.servers.values()])

    def get_prompt(self, name, arguments=None):
        (prompt_name, server_name) = self._get_name(name)
        self._verify_server(server_name)
        return self.servers[server_name].get_prompt(prompt_name, arguments)

    def _verify_server(self, server_name):
        if server_name not in self.servers:
            self.command.error(f"Server {server_name} not found in available MCP servers")

    def _get_name(self, name):
        try:
            (resource_name, server_name) = name.split("@")
        except ValueError:
            resource_name = name
            server_name = settings.MCP_LOCAL_SERVER_NAME
        return (resource_name, server_name)


class MCPServer(object):

    def __init__(self, client, name, url, token):
        self.client = client
        self.name = name
        self.url = url
        self.token = token
        self.index = {}

    def initialize(self, reload_index=False):
        def _initialize():
            async def _run_operation():
                async with connect(self.url, self.token) as session:
                    self.index["tools"] = {}
                    # self.index["prompts"] = {}

                    tools = await session.list_tools()
                    for tool in tools.tools:
                        self.index["tools"][tool.name] = tool

                    # prompts = await session.list_prompts()
                    # for prompt in prompts.prompts:
                    #     self.index["prompts"][prompt.name] = prompt

            self._preconnect()
            asyncio.run(_run_operation())

        if reload_index or not self.index:
            if self.name == settings.MCP_LOCAL_SERVER_NAME:
                self.client.command.run_exclusive("mcp_request", _initialize)
            else:
                _initialize()

    def _preconnect(self):
        # Override in subclass if needed
        pass

    def get_index(self, reload_index=False):
        self.initialize(reload_index)
        return deepcopy(self.index)

    def list_tools(self):
        self.initialize()
        return "\n".join([format_tool_schema(self.name, tool) for tool in self.index["tools"].values()])

    def exec_tool(self, name, arguments=None):
        tool_name = name.split("@")[0]

        if arguments is None:
            arguments = {}

        self.initialize()

        if tool_name not in self.index["tools"]:
            raise RuntimeError(f"Tool {tool_name} not found in MCP server {self.name}")

        def _exec_tool():
            async def _run_operation():
                async with connect(self.url, self.token) as session:
                    messages = []

                    tool = await session.call_tool(tool_name, arguments=arguments)
                    for message in tool.content:
                        messages.append(format_tool_message(message))

                    return "\n".join(messages)

            self._preconnect()
            return asyncio.run(_run_operation())

        if self.name == settings.MCP_LOCAL_SERVER_NAME:
            return self.client.command.run_exclusive("mcp_request", _exec_tool)
        else:
            return _exec_tool()

    def list_prompts(self):
        self.initialize()
        return "\n".join([format_prompt_schema(self.name, prompt) for prompt in self.index["prompts"].values()])

    def get_prompt(self, name, arguments=None):
        prompt_name = name.split("@")[0]

        if arguments is None:
            arguments = {}

        self.initialize()

        if prompt_name not in self.index["prompts"]:
            raise RuntimeError(f"Prompt {prompt_name} not found in MCP server {self.name}")

        def _get_prompt():
            async def _run_operation():
                async with connect(self.url, self.token) as session:
                    prompt = await session.get_prompt(prompt_name, arguments=arguments)
                    return prompt.messages

            self._preconnect()
            return asyncio.run(_run_operation())

        if self.name == settings.MCP_LOCAL_SERVER_NAME:
            return self.client.command.run_exclusive("mcp_request", _get_prompt)
        else:
            return _get_prompt()


class MCPLocalServer(MCPServer):

    def __init__(self, client, url):
        super().__init__(client, settings.MCP_LOCAL_SERVER_NAME, url, None)

    def _preconnect(self):
        self.token = f"{self.client.user.name} {self._get_temp_token()}"

    def _get_temp_token(self):
        def _get_token():
            if (
                not self.client.user.temp_token
                or (now() - self.client.user.temp_token_time).total_seconds() > settings.TEMP_TOKEN_EXPIRATION
            ):
                self.client.user.temp_token = create_token(64)
                self.client.user.temp_token_time = now()
                self.client.user.save()

            return self.client.user.temp_token

        return self.client.command.run_exclusive(f"mcp_temp_token_{self.client.user.name}", _get_token)
