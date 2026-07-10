#!/usr/bin/env python3
"""MCP server exposing GLPI tools over stdio."""

import asyncio
import logging
from typing import Any, Dict, List, Sequence

import click
import mcp.server
import mcp.server.stdio
import mcp.types as types
from mcp.server.models import InitializationOptions

import mcp_glpi.GLPITools as GLPITools
import mcp_glpi.GLPiHandler as GLPiHandler


SERVER_VERSION = "2.0.0"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationOptions:
    """Static notification capabilities for this server."""

    def __init__(self):
        self.tools_changed = False
        self.prompts_changed = False
        self.resources_changed = False
        self.roots_changed = False


class GLPIMCPServer:
    """MCP server entry point."""

    def __init__(self):
        self.app = mcp.server.Server("mcp-glpi")
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        @self.app.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            return GLPITools.tools

        @self.app.call_tool()
        async def handle_call_tool(
            name: str,
            arguments: Dict[str, Any],
        ) -> Sequence[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            return GLPiHandler.CommandHandler(command=name, arguments=arguments).execute()

    async def run(self) -> None:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-glpi",
                    server_version=SERVER_VERSION,
                    capabilities=self.app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


server_instance = GLPIMCPServer()


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Habilitar logging detallado")
def main(verbose: bool) -> None:
    """Start the MCP GLPI server."""

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Iniciando servidor MCP GLPI")
    logger.info("Herramientas disponibles: %s", [tool.name for tool in GLPITools.tools])

    asyncio.run(server_instance.run())


if __name__ == "__main__":
    main()
