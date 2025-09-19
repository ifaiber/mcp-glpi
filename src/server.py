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
            return [
                types.Tool(
                    name="echo",
                    description="Devuelve el texto que se le proporciona (útil para testing)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "El mensaje a devolver"
                            }
                        },
                        "required": ["message"]
                    }
                ),
                types.Tool(
                    name="calculate",
                    description="Realiza cálculos matemáticos básicos",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Expresión matemática a evaluar (ej: 2+2, 10*5, sqrt(16))"
                            }
                        },
                        "required": ["expression"]
                    }
                ),
                types.Tool(
                    name="get_time",
                    description="Obtiene la fecha y hora actual",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "format": {
                                "type": "string",
                                "description": "Formato de fecha (default: ISO format)",
                                "default": "iso"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="write_file",
                    description="Escribe contenido a un archivo (para testing)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Nombre del archivo"
                            },
                            "content": {
                                "type": "string",
                                "description": "Contenido a escribir"
                            }
                        },
                        "required": ["filename", "content"]
                    }
                ),
                types.Tool(
                    name="read_file",
                    description="Lee el contenido de un archivo",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Nombre del archivo a leer"
                            }
                        },
                        "required": ["filename"]
                    }
                ),
                types.Tool(
                    name="list_files",
                    description="Lista los archivos en un directorio",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "Directorio a listar (default: directorio actual)",
                                "default": "."
                            },
                            "pattern": {
                                "type": "string",
                                "description": "Patrón de archivos a buscar (ej: *.py, *.txt)",
                                "default": "*"
                            }
                        }
                    }
                )
            ]

        @self.app.call_tool()
        async def handle_call_tool(
            name: str, 
            arguments: Dict[str, Any]
        ) -> Sequence[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Ejecuta la herramienta especificada."""
            
            if name == "echo":
                message = arguments.get("message", "")
                return [types.TextContent(type="text", text=f"Echo: {message}")]
            
            elif name == "calculate":
                expression = arguments.get("expression", "")
                try:
                    # Para seguridad, solo permitimos operaciones básicas
                    allowed_names = {
                        "abs": abs, "round": round, "min": min, "max": max,
                        "sum": sum, "pow": pow, "sqrt": lambda x: x**0.5,
                        "sin": lambda x: __import__("math").sin(x),
                        "cos": lambda x: __import__("math").cos(x),
                        "tan": lambda x: __import__("math").tan(x),
                        "pi": __import__("math").pi,
                        "e": __import__("math").e
                    }
                    
                    # Evaluar la expresión de forma segura
                    result = eval(expression, {"__builtins__": {}}, allowed_names)
                    return [types.TextContent(type="text", text=f"Resultado: {expression} = {result}")]
                except Exception as e:
                    return [types.TextContent(type="text", text=f"Error al calcular '{expression}': {str(e)}")]
            
            elif name == "get_time":
                format_type = arguments.get("format", "iso")
                now = datetime.now()
                
                if format_type == "iso":
                    time_str = now.isoformat()
                elif format_type == "human":
                    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
                elif format_type == "timestamp":
                    time_str = str(int(now.timestamp()))
                else:
                    time_str = now.strftime(format_type)
                    
                return [types.TextContent(type="text", text=f"Fecha y hora actual: {time_str}")]
            
            elif name == "write_file":
                filename = arguments.get("filename", "")
                content = arguments.get("content", "")
                
                try:
                    file_path = Path(filename)
                    # Solo permitir archivos en el directorio actual o subdirectorios
                    if file_path.is_absolute() or ".." in str(file_path):
                        raise ValueError("Solo se permiten rutas relativas sin '..'")
                        
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content, encoding="utf-8")
                    
                    return [types.TextContent(
                        type="text",
                        text=f"Archivo '{filename}' escrito exitosamente ({len(content)} caracteres)"
                    )]
                except Exception as e:
                    return [types.TextContent(
                        type="text",
                        text=f"Error al escribir archivo '{filename}': {str(e)}"
                    )]
            
            elif name == "read_file":
                filename = arguments.get("filename", "")
                
                try:
                    file_path = Path(filename)
                    if file_path.is_absolute() or ".." in str(file_path):
                        raise ValueError("Solo se permiten rutas relativas sin '..'")
                        
                    if not file_path.exists():
                        raise FileNotFoundError(f"El archivo '{filename}' no existe")
                        
                    content = file_path.read_text(encoding="utf-8")
                    
                    return [types.TextContent(
                        type="text",
                        text=f"Contenido de '{filename}':\n\n{content}"
                    )]
                except Exception as e:
                    return [types.TextContent(
                        type="text",
                        text=f"Error al leer archivo '{filename}': {str(e)}"
                    )]
            
            elif name == "list_files":
                directory = arguments.get("directory", ".")
                pattern = arguments.get("pattern", "*")
                
                try:
                    dir_path = Path(directory)
                    if dir_path.is_absolute() or ".." in str(dir_path):
                        raise ValueError("Solo se permiten rutas relativas sin '..'")
                        
                    if not dir_path.exists():
                        raise FileNotFoundError(f"El directorio '{directory}' no existe")
                        
                    files = list(dir_path.glob(pattern))
                    file_list = []
                    
                    for file_path in sorted(files):
                        if file_path.is_file():
                            size = file_path.stat().st_size
                            modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                            file_list.append(f"{file_path.name} ({size} bytes, modificado: {modified.strftime('%Y-%m-%d %H:%M:%S')})")
                        elif file_path.is_dir():
                            file_list.append(f"{file_path.name}/ (directorio)")
                    
                    if not file_list:
                        result_text = f"No se encontraron archivos que coincidan con el patrón '{pattern}' en '{directory}'"
                    else:
                        result_text = f"Archivos en '{directory}' que coinciden con '{pattern}':\n\n" + "\n".join(file_list)
                    
                    return [types.TextContent(type="text", text=result_text)]
                except Exception as e:
                    return [types.TextContent(
                        type="text",
                        text=f"Error al listar archivos en '{directory}': {str(e)}"
                    )]
            
            else:
                return [types.TextContent(type="text", text=f"Herramienta desconocida: {name}")]

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
    logger.info("Herramientas disponibles: echo, calculate, get_time, write_file, read_file, list_files")
    
    asyncio.run(server_instance.run())


if __name__ == "__main__":
    main()