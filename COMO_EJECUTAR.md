# 🚀 GUÍA COMPLETA: CÓMO EJECUTAR TU SERVIDOR MCP

## 📋 RESUMEN RÁPIDO
Tu servidor MCP tiene **6 herramientas** listas para usar:
- `echo` - Devuelve mensajes
- `calculate` - Calculadora matemática
- `get_time` - Fecha/hora
- `write_file` - Crear archivos
- `read_file` - Leer archivos  
- `list_files` - Listar archivos

## 🎯 FORMAS DE EJECUTAR

### 1️⃣ PARA DESARROLLO Y TESTING
```bash
# Método básico
mcp-glpi

# Con logs detallados (recomendado para debugging)
mcp-glpi --verbose

# O directamente con Python
python -m mcp_test.server --verbose
```

**¿Qué verás?**
- Mensajes de inicio del servidor
- El servidor queda esperando comandos JSON-RPC
- Para parar: Ctrl+C

### 2️⃣ PARA USO REAL CON CLAUDE DESKTOP

**Paso 1: Localizar archivo de configuración**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Paso 2: Editar configuración**
```json
{
  "mcpServers": {
    "mcp-glpi": {
      "command": "D:/Desktop/proyectos/mcp-glpi/.venv/Scripts/python.exe",
      "args": ["-m", "mcp_test.server"],
      "cwd": "D:/Desktop/proyectos/mcp-glpi"
    }
  }
}
```

**Paso 3: Reiniciar Claude Desktop**

**Paso 4: ¡Usar las herramientas!**
Ejemplos de lo que puedes pedirle a Claude:
- "Usa echo para decir hola mundo"
- "Calcula 15 * 23 + 7"
- "¿Qué hora es ahora?"
- "Crea un archivo llamado mi_nota.txt con el contenido 'Hola mundo'"
- "Lee el archivo mi_nota.txt"
- "Lista todos los archivos .py en el proyecto"

### 3️⃣ TESTING FUNCIONAL

```bash
# Probar todas las funcionalidades
python examples/functional_test.py

# Validar que todo está OK
python examples/validate_server.py
```

## 🔧 DEBUGGING

### Si algo no funciona:

**1. Verificar instalación:**
```bash
mcp-glpi --help
# Debería mostrar: "Inicia el servidor MCP de prueba"
```

**2. Verificar dependencias:**
```bash
python -c "import mcp, click, pydantic; print('✅ Dependencias OK')"
```

**3. Verificar módulo:**
```bash
python -c "import mcp_test.server; print('✅ Módulo OK')"
```

**4. Logs detallados:**
```bash
mcp-glpi --verbose
# Verás todos los logs de inicio y operación
```

### Errores comunes:

**"ModuleNotFoundError: No module named 'mcp_test'"**
- Solución: `pip install -e .` desde el directorio del proyecto

**"Command 'mcp-glpi' not found"**
- Solución: Asegúrate de usar el entorno virtual correcto

**"Invalid JSON-RPC"**
- Normal si ejecutas manualmente. Usa Claude Desktop para uso real.

## 🎉 EJEMPLOS DE USO REAL

### En Claude Desktop puedes decir:

**Ejemplo 1: Testing básico**
```
Usuario: "Usa la herramienta echo para decir 'Servidor MCP funcionando'"
Claude: [Usa echo] → "Echo: Servidor MCP funcionando"
```

**Ejemplo 2: Matemáticas**
```
Usuario: "Calcula el área de un círculo con radio 5 (usa pi)"
Claude: [Usa calculate] → "Resultado: pi * 5 * 5 = 78.54"
```

**Ejemplo 3: Archivos**
```
Usuario: "Crea un archivo llamado notas.txt con mis ideas del proyecto"
Claude: [Usa write_file] → "Archivo 'notas.txt' creado con 45 caracteres"
```

**Ejemplo 4: Información**
```
Usuario: "¿Qué hora es en formato legible?"
Claude: [Usa get_time] → "Fecha y hora actual: 2025-09-17 22:50:15"
```

## 🔐 SEGURIDAD

Tu servidor es seguro porque:
- ✅ Solo opera en el directorio del proyecto
- ✅ No ejecuta comandos del sistema
- ✅ Evaluación matemática limitada a funciones seguras
- ✅ Validación de todas las entradas

## 📞 SOPORTE

Si tienes problemas:
1. Ejecuta `python examples/validate_server.py`
2. Revisa los logs con `mcp-glpi --verbose`
3. Verifica la configuración de Claude Desktop

¡Tu servidor MCP está listo para ser usado! 🚀