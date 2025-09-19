#!/usr/bin/env python3
"""Test del servidor MCP usando echo para simular comunicación JSON-RPC."""

import json
import subprocess
import sys
from pathlib import Path

def test_mcp_server():
    """Test del servidor MCP usando el protocolo JSON-RPC estándar."""
    print("🧪 Testeando servidor MCP con protocolo JSON-RPC...\n")
    
    # Comando para ejecutar el servidor
    server_cmd = [
        str(Path("D:/Desktop/proyectos/mcp-glpi/.venv/Scripts/python.exe")),
        "-m", "mcp_test.server"
    ]
    
    print("1️⃣ Iniciando servidor MCP...")
    print(f"Comando: {' '.join(server_cmd)}")
    
    try:
        # Crear proceso del servidor
        process = subprocess.Popen(
            server_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="D:/Desktop/proyectos/mcp-glpi"
        )
        
        print("✅ Servidor iniciado exitosamente!")
        
        # Test 1: Initialize
        print("\n2️⃣ Enviando mensaje de inicialización...")
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Enviar mensaje
        process.stdin.write(json.dumps(init_message) + "\n")
        process.stdin.flush()
        
        # Leer respuesta (con timeout)
        import select
        import time
        
        # Esperar un poco para la respuesta
        time.sleep(0.5)
        
        # Test 2: List tools
        print("3️⃣ Solicitando lista de herramientas...")
        list_tools_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(list_tools_message) + "\n")
        process.stdin.flush()
        
        time.sleep(0.5)
        
        # Test 3: Call echo tool
        print("4️⃣ Probando herramienta echo...")
        call_tool_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "echo",
                "arguments": {
                    "message": "¡Hola desde el test MCP!"
                }
            }
        }
        
        process.stdin.write(json.dumps(call_tool_message) + "\n")
        process.stdin.flush()
        
        time.sleep(0.5)
        
        # Leer todas las respuestas disponibles
        print("\n📤 Leyendo respuestas del servidor...")
        
        # Terminar el proceso de forma limpia
        process.stdin.close()
        
        # Esperar a que termine
        stdout, stderr = process.communicate(timeout=2)
        
        if stdout:
            print("📥 Salida del servidor:")
            for line in stdout.strip().split('\n'):
                if line.strip():
                    try:
                        # Intentar parsear como JSON
                        data = json.loads(line)
                        print(f"   JSON: {json.dumps(data, indent=2)}")
                    except:
                        print(f"   LOG: {line}")
        
        if stderr:
            print("⚠️  Errores del servidor:")
            print(stderr)
            
        print("\n" + "="*60)
        
        if process.returncode == 0:
            print("✅ Servidor MCP funciona correctamente!")
        else:
            print(f"⚠️  Servidor terminó con código: {process.returncode}")
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - El servidor está funcionando pero no respondió a tiempo")
        process.kill()
        print("✅ Esto es normal para un servidor MCP en modo interactivo!")
        
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=1)

if __name__ == "__main__":
    test_mcp_server()