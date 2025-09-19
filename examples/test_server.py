#!/usr/bin/env python3
"""Script de ejemplo para probar el servidor MCP localmente."""

import asyncio
import json
import sys
from pathlib import Path

# Añadir el directorio src al path para importar nuestro módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_test.server import server


async def test_tools():
    """Prueba todas las herramientas del servidor MCP."""
    print("🧪 Probando herramientas del servidor MCP...\n")
    
    # Test 1: Echo
    print("1️⃣ Testing herramienta 'echo':")
    from mcp.types import CallToolRequest
    request = CallToolRequest(
        method="tools/call",
        params={"name": "echo", "arguments": {"message": "¡Hola desde el test!"}}
    )
    result = await server.call_tool(request)
    print(f"   Resultado: {result.content[0].text}\n")
    
    # Test 2: Calculate
    print("2️⃣ Testing herramienta 'calculate':")
    expressions = ["2 + 2", "sqrt(16)", "sin(pi/2)", "2 * 3 + 4"]
    for expr in expressions:
        request = CallToolRequest(name="calculate", arguments={"expression": expr})
        result = await server.call_tool(request)
        print(f"   {expr} -> {result.content[0].text}")
    print()
    
    # Test 3: Get time
    print("3️⃣ Testing herramienta 'get_time':")
    formats = ["iso", "human", "timestamp"]
    for fmt in formats:
        request = CallToolRequest(name="get_time", arguments={"format": fmt})
        result = await server.call_tool(request)
        print(f"   Formato {fmt}: {result.content[0].text}")
    print()
    
    # Test 4: File operations
    print("4️⃣ Testing operaciones de archivo:")
    
    # Escribir archivo
    test_content = "¡Este es un archivo de prueba!\nCreado por el test del servidor MCP.\n\nFecha: 2025-09-17"
    request = CallToolRequest(name="write_file", arguments={
        "filename": "test_example.txt",
        "content": test_content
    })
    result = await server.call_tool(request)
    print(f"   Escribir: {result.content[0].text}")
    
    # Leer archivo
    request = CallToolRequest(name="read_file", arguments={"filename": "test_example.txt"})
    result = await server.call_tool(request)
    print(f"   Leer: {result.content[0].text[:50]}...")
    
    # Listar archivos
    request = CallToolRequest(name="list_files", arguments={"directory": ".", "pattern": "*.txt"})
    result = await server.call_tool(request)
    print(f"   Listar: {result.content[0].text[:100]}...")
    print()


async def test_prompts():
    """Prueba los prompts del servidor."""
    print("💬 Probando prompts del servidor MCP...\n")
    
    # Test help prompt
    print("1️⃣ Testing 'help_prompt':")
    from mcp.types import GetPromptRequest
    request = GetPromptRequest(name="help_prompt", arguments={})
    result = await server.get_prompt(request)
    print(f"   Descripción: {result.description}")
    print(f"   Contenido: {result.messages[0].content.text[:100]}...\n")
    
    # Test prompt with arguments
    print("2️⃣ Testing 'test_prompt' con argumentos:")
    request = GetPromptRequest(name="test_prompt", arguments={"topic": "Desarrollo con Python"})
    result = await server.get_prompt(request)
    print(f"   Descripción: {result.description}")
    print(f"   Contenido: {result.messages[0].content.text[:150]}...\n")


async def test_resources():
    """Prueba los recursos del servidor."""
    print("📊 Probando recursos del servidor MCP...\n")
    
    # Test info resource
    print("1️⃣ Testing recurso 'test://info':")
    from mcp.types import ReadResourceRequest
    request = ReadResourceRequest(uri="test://info")
    result = await server.read_resource(request)
    info = json.loads(result.contents[0].text)
    print(f"   Nombre: {info['name']}")
    print(f"   Versión: {info['version']}")
    print(f"   Herramientas: {info['tools_count']}")
    print()
    
    # Test config resource
    print("2️⃣ Testing recurso 'test://config':")
    request = ReadResourceRequest(uri="test://config")
    result = await server.read_resource(request)
    config = json.loads(result.contents[0].text)
    print(f"   Servidor: {config['server_name']}")
    print(f"   Operaciones de archivo: {'✅' if config['file_operations']['allowed'] else '❌'}")
    print()


async def main():
    """Ejecuta todos los tests."""
    print("🚀 Iniciando tests del servidor MCP de prueba\n")
    print("=" * 50)
    
    try:
        await test_tools()
        await test_prompts()
        await test_resources()
        
        print("=" * 50)
        print("✅ Todos los tests completados exitosamente!")
        
        # Limpiar archivo de prueba
        test_file = Path("test_example.txt")
        if test_file.exists():
            test_file.unlink()
            print("🧹 Archivo de prueba eliminado")
            
    except Exception as e:
        print(f"❌ Error durante los tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())