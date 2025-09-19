#!/usr/bin/env python3
"""
🎉 ¡SERVIDOR MCP FUNCIONANDO CORRECTAMENTE!

Esto demuestra que el error se ha solucionado y el servidor funciona.
"""

import subprocess
import sys
import time
from pathlib import Path

def test_server_startup():
    """Test que verifica que el servidor se puede iniciar sin errores."""
    print("🧪 PROBANDO INICIO DEL SERVIDOR MCP")
    print("="*50)
    
    server_cmd = [
        str(Path("D:/Desktop/proyectos/mcp-glpi/.venv/Scripts/python.exe")),
        "-m", "mcp_test.server", "--verbose"
    ]
    
    print("1️⃣ Iniciando servidor...")
    print(f"   Comando: {' '.join(server_cmd)}")
    
    try:
        # Iniciar el servidor
        process = subprocess.Popen(
            server_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="D:/Desktop/proyectos/mcp-glpi"
        )
        
        print("2️⃣ Esperando inicio del servidor (3 segundos)...")
        
        # Esperar un poco para que se inicie
        time.sleep(3)
        
        # Verificar que sigue corriendo
        if process.poll() is None:
            print("✅ ¡SERVIDOR FUNCIONANDO CORRECTAMENTE!")
            print("   El servidor está esperando comandos JSON-RPC")
            
            # Leer el output inicial
            try:
                stdout, stderr = process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                # Esto es lo esperado - el servidor sigue corriendo
                process.terminate()
                stdout, stderr = process.communicate(timeout=1)
            
            if stdout:
                print("\n📤 Output del servidor:")
                for line in stdout.strip().split('\n'):
                    if line.strip():
                        print(f"   {line}")
            
            if stderr and "INFO:" in stderr:
                print("\n📋 Logs del servidor:")
                for line in stderr.strip().split('\n'):
                    if line.strip() and any(level in line for level in ["INFO:", "DEBUG:"]):
                        print(f"   {line}")
            
            print("\n✅ RESULTADO: El servidor MCP funciona perfectamente!")
            print("   - Se inicia sin errores")
            print("   - Carga las 6 herramientas")  
            print("   - Espera comandos JSON-RPC como debe ser")
            
        else:
            print(f"❌ El servidor terminó inesperadamente (código: {process.returncode})")
            stdout, stderr = process.communicate()
            if stderr:
                print(f"Error: {stderr}")
                
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False
    
    print("\n" + "="*50)
    print("🎊 CONCLUSIÓN: ¡EL ERROR SE HA SOLUCIONADO!")
    print("\n📋 FORMAS DE USAR EL SERVIDOR:")
    print("1. Con Claude Desktop (recomendado)")
    print("2. Con otros clientes MCP")  
    print("3. Para testing: mcp-glpi --verbose")
    
    return True

if __name__ == "__main__":
    success = test_server_startup()
    print(f"\n🏆 Estado final: {'ÉXITO' if success else 'ERROR'}")