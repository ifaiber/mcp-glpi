#!/usr/bin/env python3
"""Test simple del método echo del servidor MCP GLPI."""

import asyncio
import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_glpi.server import GLPIMCPServer

async def test_echo():
    """Prueba el método echo del servidor MCP."""
    print("🧪 Probando método echo del servidor MCP GLPI...\n")
    
    # Crear instancia del servidor
    server = GLPIMCPServer()
    
    print("1️⃣ Listando herramientas disponibles:")
    
    # Obtener los handlers
    list_tools_handler = None
    call_tool_handler = None
    
    for handler in server.app._handlers:
        if hasattr(handler, '_method') and handler._method == 'tools/list':
            list_tools_handler = handler._handler
        elif hasattr(handler, '_method') and handler._method == 'tools/call':
            call_tool_handler = handler._handler
    
    if list_tools_handler:
        try:
            tools = await list_tools_handler()
            print(f"   ✅ Herramientas encontradas: {len(tools)}")
            for tool in tools:
                print(f"   - {tool.name}: {tool.description}")
        except Exception as e:
            print(f"   ❌ Error listando herramientas: {e}")
    
    print("\n2️⃣ Probando método echo:")
    
    if call_tool_handler:
        try:
            # Probar echo con mensaje "prueba"
            result = await call_tool_handler("echo", {"message": "prueba"})
            print(f"   ✅ Resultado: {result[0].text}")
            
            # Probar echo con otro mensaje
            result2 = await call_tool_handler("echo", {"message": "¡Hola MCP GLPI!"})
            print(f"   ✅ Resultado 2: {result2[0].text}")
            
        except Exception as e:
            print(f"   ❌ Error ejecutando echo: {e}")
    else:
        print("   ❌ No se encontró el handler de call_tool")
    
    print("\n" + "="*50)
    print("✅ Test completado!")

if __name__ == "__main__":
    asyncio.run(test_echo())