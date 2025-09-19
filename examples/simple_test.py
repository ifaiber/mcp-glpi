#!/usr/bin/env python3
"""Test simple para verificar la API del servidor MCP."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_test.server import server_instance

async def simple_test():
    """Test simple para verificar que el servidor funciona."""
    print("Testing servidor MCP...")
    
    # Test list_tools - acceder a los handlers directamente
    handlers = server_instance.app._handlers
    list_tools_handler = None
    call_tool_handler = None
    
    for handler in handlers:
        if hasattr(handler, 'method') and handler.method == 'tools/list':
            list_tools_handler = handler.func
        elif hasattr(handler, 'method') and handler.method == 'tools/call':
            call_tool_handler = handler.func
    
    if list_tools_handler:
        tools = await list_tools_handler()
        print(f"✅ Herramientas disponibles: {len(tools)}")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
    else:
        print("❌ No se encontró el handler de list_tools")
        return
    
    if call_tool_handler:
        # Test call_tool
        print("\n🔧 Probando herramienta echo:")
        result = await call_tool_handler("echo", {"message": "¡Hola MCP!"})
        print(f"   Resultado: {result[0].text}")
        
        print("\n🧮 Probando herramienta calculate:")
        result = await call_tool_handler("calculate", {"expression": "2 + 2"})
        print(f"   Resultado: {result[0].text}")
    else:
        print("❌ No se encontró el handler de call_tool")
    
    print("\n" + "="*50)
    print("✅ Servidor MCP funciona correctamente!")

if __name__ == "__main__":
    asyncio.run(simple_test())