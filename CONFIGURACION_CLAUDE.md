# Pasos para configurar Claude Desktop con tu servidor MCP

## 1. Localizar archivo de configuración
Windows: %APPDATA%\Claude\claude_desktop_config.json
macOS: ~/Library/Application Support/Claude/claude_desktop_config.json

## 2. Editar el archivo (crear si no existe)
Si el archivo no existe, créalo con este contenido:

{
  "mcpServers": {
    "mcp-glpi": {
      "command": "D:/Desktop/proyectos/mcp-glpi/.venv/Scripts/python.exe",
      "args": ["-m", "mcp_test.server"],
      "cwd": "D:/Desktop/proyectos/mcp-glpi",
      "env": {
        "PYTHONPATH": "D:/Desktop/proyectos/mcp-glpi/src"
      }
    }
  }
}

Si ya tienes otros servidores MCP configurados, agrega solo la entrada "mcp-glpi" dentro de "mcpServers".

## 3. Reiniciar Claude Desktop
Cierra y vuelve a abrir Claude Desktop para que cargue la nueva configuración.

## 4. Verificar conexión
En Claude Desktop, deberías ver un indicador de que el servidor MCP está conectado.

## 5. Usar las herramientas
Puedes pedirle a Claude que use las herramientas de tu servidor:
- "Usa la herramienta echo para decir hola"
- "Calcula 2 + 2 * 3 usando la calculadora"
- "¿Qué hora es?"
- "Crea un archivo llamado test.txt con contenido de prueba"