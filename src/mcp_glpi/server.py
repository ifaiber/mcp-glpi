#!/usr/bin/env python3
"""Servidor MCP de pruebas con herramientas básicas para testing."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence

import click
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
import mcp_glpi.GLPITools as GLPITools
import mcp_glpi.GLPiHandler as GLPiHandler

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GLPIMCPServer:
    """Servidor MCP de prueba."""
    
    def __init__(self):
        self.app = mcp.server.Server("mcp-glpi")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Configura los handlers del servidor."""
        
        @self.app.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """Lista todas las herramientas disponibles."""
            return GLPITools.tools

        @self.app.call_tool()
        async def handle_call_tool(
            name: str, 
            arguments: Dict[str, Any]
        ) -> Sequence[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Ejecuta la herramienta especificada."""

            return GLPiHandler.CommandHandler(command=name, arguments=arguments).execute()
            

    async def run(self):
        """Ejecuta el servidor."""
        # Crear opciones de notificación básicas
        class NotificationOptions:
            def __init__(self):
                self.tools_changed = False
                self.prompts_changed = False
                self.resources_changed = False
                self.roots_changed = False
        
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-glpi",
                    server_version="0.1.0",
                    capabilities=self.app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )

# Instancia global del servidor
server_instance = GLPIMCPServer()

@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Habilitar logging detallado")
def main(verbose: bool) -> None:
    """Inicia el servidor MCP de prueba."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Iniciando servidor MCP de prueba...")
    logger.info("Herramientas disponibles: %s", [tool.name for tool in GLPITools.tools])
    
    asyncio.run(server_instance.run())


if __name__ == "__main__":
    main()