# MCP GLPI Server

Servidor de referencia para integrar el ecosistema Model Context Protocol (MCP) con GLPI. Proporciona herramientas de gestion de tickets y cambios listas para usar en flujos de automatizacion, junto con utilidades para validacion y soporte.

## Caracteristicas
- Implementacion MCP sobre stdio lista para Claude Desktop y otros clientes compatibles.
- Coleccion de herramientas GLPI para listar, crear, actualizar y relacionar tickets y cambios.
- Validacion de configuracion impulsada por Pydantic y uso de variables de entorno con `.env`.
- Suite de pruebas unitarias (`pytest`) que cubre el manejador de comandos, los helpers GLPI y la documentacion del repositorio.

## Instalacion
1. Clonar el repositorio y crear un entorno virtual:
   ```bash
   python -m venv .venv
   .venv/Scripts/activate  # Windows
   # source .venv/bin/activate  # Linux/macOS
   ```
2. Instalar dependencias:
   ```bash
   pip install -e .
   ```
3. Configurar credenciales GLPI (tokens y URL):
   - Definir las variables `GLPI_URL`, `GLPI_APP_TOKEN` y `GLPI_USER_TOKEN` en el entorno.
   - Alternativamente, crear un archivo `.env` en la raiz del proyecto con esos valores.

## Herramientas Disponibles
Las herramientas expuestas por `GLPITools` se registran automaticamente en el servidor MCP:

| Herramienta | Descripcion breve |
|-------------|-------------------|
| `echo` | Devuelve el texto recibido, util para pruebas de conectividad. |
| `validate_session` | Muestra informacion de la sesion GLPI activa. |
| `list_tickets` | Lista tickets con filtros, paginacion y distintos formatos. |
| `list_changes` | Lista cambios con filtros, paginacion y distintos formatos. |
| `create_ticket` | Crea un ticket; soporta campos adicionales. |
| `create_change` | Crea un cambio; soporta campos adicionales. |
| `add_ticket_comment` | Agrega un seguimiento a un ticket. |
| `add_ticket_solution` | Registra una solucion de ticket. |
| `assign_ticket_users` | Asigna usuarios a un ticket. |
| `assign_ticket_groups` | Asigna grupos a un ticket. |
| `add_change_comment` | Agrega un seguimiento a un cambio. |
| `add_change_solution` | Registra una solucion de cambio. |
| `assign_change_users` | Asigna usuarios a un cambio. |
| `assign_change_groups` | Asigna grupos a un cambio. |
| `link_change_to_ticket` | Vincula un ticket existente a un cambio. |
| `link_ticket_to_change` | Vincula un cambio existente a un ticket. |
| `unlink_change_ticket` | Elimina la relacion Change_Ticket desde un cambio. |
| `unlink_ticket_change` | Elimina la relacion Change_Ticket desde un ticket. |
| `update_change` | Actualiza campos de un cambio. |

> Nota: El manejador tambien implementa `update_ticket`, disponible para invocacion directa aunque no aparece en la lista de herramientas porque requiere una llamada programatica.

## Ejecucion del Servidor
Ejecutar en modo CLI:
```bash
python -m mcp_glpi.server
# o con logging detallado
python -m mcp_glpi.server --verbose
```

Para integrarlo con Claude Desktop, utilice `examples/claude_desktop_config.json` como guia. Ajuste la ruta del ejecutable y el `cwd` segun su entorno.

## Empaquetado para Produccion
1. Instalar la herramienta de build (solo la primera vez):
   ```bash
   python -m pip install build
   ```
2. Generar el paquete wheel desde la raiz del repositorio:
   ```bash
   python -m build --wheel
   ```
   Esto crea el archivo `dist/mcp_glpi-0.1.0-py3-none-any.whl` listo para distribuir.
3. Para instalarlo en otro entorno o servidor, copiar el wheel y ejecutar:
   ```bash
   pip install dist/mcp_glpi-0.1.0-py3-none-any.whl
   ```
   Si el archivo esta en otra ubicacion, ajustar la ruta en el comando anterior.

## Depuracion y Herramientas MCP
- **Logging detallado**: pasar `--verbose` al comando principal para habilitar nivel `DEBUG`.
- **Inspector MCP**: pruebe las herramientas disponibles sin cliente externo usando:
  ```bash
  mcp-inspector C:/devIdeas/Repos-propios/mcp-glpi/.venv/Scripts/python.exe "src/mcp_glpi/server.py"
  ```
El inspector permite invocar `list_tools` y `call_tool` directamente para validar escenarios.

tambien puedes usar un archivo de configuracion
```
mcp-inspector --config .\examples\config-developer.json
```

- **Sesion GLPI**: la herramienta `validate_session` imprime los datos de la sesion activa, util para confirmar credenciales.

## Pruebas
La suite se ejecuta con `pytest` y esta localizada en `tests/`.

```bash
# Instalar dependencias de desarrollo opcionales
pip install -e .[dev]

# Ejecutar pruebas con el interprete del entorno virtual
.venv/Scripts/python.exe -m pytest
```

Las pruebas cubren:
- `CommandHandler` para uso y validacion de argumentos.
- Helpers de tickets y cambios (`glpi.tickets`, `glpi.changes`).
- Formateo de sesion GLPI (`glpi.session`).
- Validacion basica de `claude_desktop_config.json` y contenido Markdown.

## Recursos Utiles
- Archivo de configuracion: `examples/claude_desktop_config.json`.
- Script de ejemplo funcional: `examples/functional_test.py`.
- Variables de entorno soportadas: consulte `src/common/config.py`.

¡Feliz automatizacion con MCP + GLPI!
