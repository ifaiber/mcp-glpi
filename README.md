# MCP GLPI Server

Servidor de referencia para integrar el ecosistema Model Context Protocol (MCP) con GLPI. Proporciona herramientas de gestion de tickets, cambios y sesion listas para usar en flujos de automatizacion, junto con utilidades para validacion y soporte.

## Caracteristicas
- Implementacion MCP sobre stdio lista para Claude Desktop y otros clientes compatibles.
- Coleccion de herramientas GLPI para listar, crear, actualizar y relacionar tickets y cambios, ademas de operaciones de sesion del usuario logueado.
- Subida y descarga de archivos (Document de GLPI), y vinculo/desvinculo de documentos con tickets y cambios.
- Recurso MCP (`resources/list` + `resources/read`) con una guia de uso de las herramientas de elementos/archivos GLPI, para que el cliente MCP la cargue como contexto de referencia.
- Validacion de configuracion impulsada por Pydantic y uso de variables de entorno con `.env`.
- Respuestas normalizadas en JSON para facilitar integracion con clientes MCP y automatizaciones.
- Organizacion modular por paquetes (`tickets/`, `changes/`, `session/`) para extender nuevas funcionalidades con menor acoplamiento.
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
Las herramientas expuestas por `GLPITools` se registran automaticamente en el servidor MCP. Los nombres siguen la convencion `elemento_funcion` / `elemento_subelemento_funcion` (ver detalle y motivacion en la nota de documentacion `Documentacion MCP-GLPI.md`):

| Herramienta | Descripcion breve |
|-------------|-------------------|
| `session_validate` | Muestra informacion de la sesion GLPI activa. |
| `entityprofile_list` | Lista los perfiles del usuario logueado, cada uno con sus entidades asociadas. |
| `ticket_list` | Lista tickets con filtros, paginacion y distintos formatos. |
| `change_list` | Lista cambios con filtros, paginacion y distintos formatos. |
| `ticket_add` | Crea un ticket; soporta campos adicionales. |
| `change_add` | Crea un cambio; soporta campos adicionales. |
| `assistance_item_user_add` | Asigna usuarios a un Ticket o Change (itemtype indica cual). |
| `assistance_item_group_add` | Asigna grupos a un Ticket o Change (itemtype indica cual). |
| `assistance_item_followup_add` | Agrega un comentario (ITILFollowup) a un Ticket o Change. |
| `assistance_item_followup_update` | Actualiza un comentario existente en un Ticket o Change. |
| `assistance_item_solution_add` | Registra una solucion (ITILSolution) en un Ticket o Change. |
| `assistance_item_solution_update` | Actualiza una solucion existente en un Ticket o Change. |
| `assistance_item_ticketchange_link` | Vincula un ticket y un cambio existentes (Change_Ticket). |
| `assistance_item_ticketchange_unlink` | Elimina una relacion Change_Ticket existente. |
| `change_update` | Actualiza campos de un cambio. |
| `ticket_update` | Actualiza campos de un ticket. |
| `ticket_delete` | Elimina un ticket (papelera o purga definitiva). |
| `change_delete` | Elimina un cambio (papelera o purga definitiva). |
| `item_type_list` | Lista los itemtypes de GLPI soportados por `item_list`/`item_get`/`item_subitem_list`. |
| `item_subtype_list` | Lista los subtypes soportados por `item_subitem_list` (opcionalmente filtrados por itemtype). |
| `item_list` | Acceso generico de solo lectura: lista elementos de un itemtype soportado. |
| `item_get` | Acceso generico de solo lectura a un elemento puntual (por id) de un itemtype soportado. |
| `item_subitem_list` | Acceso generico de solo lectura a los sub-items de un elemento (itemtype/id/subtype soportados). |
| `item_delete` | Elimina un elemento de un itemtype soportado (papelera o purga definitiva). |
| `file_upload` | Sube un archivo local como Document de GLPI (multipart/form-data). |
| `file_download` | Descarga un Document de GLPI y lo escribe en una ruta local. |
| `file_link` | Vincula un Document existente a un ticket o cambio (Document_Item). |
| `file_unlink` | Elimina la relacion Document_Item entre un documento y el elemento al que estaba vinculado. |

Para listar los comentarios (`ITILFollowup`) o soluciones (`ITILSolution`) ya registrados en un ticket o cambio puntual, usar `item_subitem_list` con `itemtype: "Ticket"|"Change"`, `id: <ticket_id|change_id>` y `subtype: "ITILFollowup"|"ITILSolution"` (ver la seccion siguiente y el recurso `mcp-glpi://docs/glpi-items`). No hay tools dedicadas `ticket_follow_list`/`ticket_solution_list`/`change_follow_list`/`change_solution_list`: ese listado es de solo lectura y ya lo cubre el acceso generico.

### Acceso generico (`item_list` / `item_get` / `item_subitem_list` / `item_delete`)

Ademas de las herramientas especificas, hay herramientas de acceso **generico** a cualquier itemtype/subtype de GLPI, sin necesidad de una tool nueva por combinacion. Las tres primeras son de solo lectura; `item_delete` es la unica mutacion generica:

- `item_list(itemtype, ...)`: lista elementos del itemtype (equivalente a `GET /{itemtype}`), con `limit`/`offset`/`sort_by`/`order`/`filters`/`output`/`fields`. No lleva `id`.
- `item_get(itemtype, id, ...)`: obtiene un elemento puntual por id (`GET /{itemtype}/{id}`), con `fields`/`expand_dropdowns`. `id` es obligatorio.
- `item_subitem_list(itemtype, id, subtype, ...)`: lista sub-items de un elemento (`GET /{itemtype}/{id}/{subtype}`).
- `item_delete(itemtype, id, ...)`: elimina un elemento (equivalente a `DELETE /{itemtype}/{id}`), con `purge`/`keep_history` igual que `ticket_delete`/`change_delete`.
- `item_type_list` / `item_subtype_list`: devuelven itemtypes/subtypes **conocidos y verificados** contra una instancia GLPI real, cada uno con una breve descripcion, para orientar sobre valores validos.

**No es una lista blanca restrictiva**: `ITEMTYPE_CATALOG` (lo que devuelven `item_type_list`/`item_subtype_list`) es una guia de referencia — `Ticket`, `Change`, `Document`, y activos/gestion (`Computer`, `Monitor`, `Software`, `SoftwareVersion`, `Project`, `ProjectTask`, `KnowbaseItem`, `Reminder`, `ContractType`, `Manufacturer`, `DeviceSimcard`) con sus sub-recursos conocidos — pero `item_list`/`item_get`/`item_delete`/`item_subitem_list` **no estan limitados a esos valores**: cualquier itemtype/subtype se reenvia a GLPI tal cual. GLPI es quien valida si el itemtype existe, si el subtype aplica, y si el perfil activo tiene permiso; un itemtype invalido o sin permiso produce el error que GLPI devuelva (404/400/403), no un rechazo previo del servidor. Si `item_list`/`item_get` devuelven `403`/`ERROR_RIGHT_MISSING`, pase `profile_id` (por id o por nombre, ver mas abajo) con un perfil que tenga esos derechos.

`item_list(itemtype="Document", ...)` / `item_get(itemtype="Document", id=...)` permiten buscar/consultar metadata de documentos (nombre, filename, mime, entidad, fecha), e `item_subitem_list(itemtype="Ticket"|"Change", id=..., subtype="Document_Item")` muestra que documentos ya estan vinculados a un ticket o cambio puntual — sin necesidad de una tool dedicada para listar/buscar documentos.

### Archivos (`file_upload` / `file_download` / `file_link` / `file_unlink`)

- `file_upload(file_path, ...)`: sube un archivo como Document de GLPI (`POST Document/` multipart/form-data). `file_path` es una ruta local en el sistema de archivos de la maquina donde corre el servidor MCP; `file_name` por defecto es el nombre base de `file_path`.
- `file_download(document_id, destination_path, ...)`: descarga un Document (`GET Document/:id` con `Accept: application/octet-stream`) y escribe los bytes en `destination_path` (ruta local, se crean los directorios padre si hace falta).
- `file_link(document_id, item_type, item_id, ...)` / `file_unlink(document_id, link_id, ...)`: crean/eliminan la relacion `Document_Item` entre un documento y **cualquier itemtype de GLPI** (no solo Ticket/Change) — GLPI valida si ese itemtype/permiso acepta el vinculo.

Las cuatro aceptan los mismos `entity_id`/`profile_id` opcionales que el resto de las herramientas.

### Asignar usuarios/grupos (`assistance_item_user_add` / `assistance_item_group_add`)

`ticket_user_assign`/`change_user_assign` y `ticket_group_assign`/`change_group_assign` se reemplazaron por dos herramientas genericas, porque cada par era identico salvo el campo GLPI (`tickets_id` vs `changes_id`) y el subtype (`Ticket_User`/`Change_User`, `Group_Ticket`/`Change_Group`). Ambas reciben `itemtype` (unicamente `"Ticket"` o `"Change"`, valida contra esos dos valores), `id` y `users`/`groups`, y arman el campo/subtype correcto internamente:

```json
{"itemtype":"Change","id":2620,"users":{"users_id":18,"type":1,"use_notification":0}}
```

```json
{"itemtype":"Ticket","id":2079,"groups":{"groups_id":5,"type":1,"use_notification":0}}
```

Esto envia a GLPI `POST Change_User`/`POST Group_Ticket` con `{"input":[{"changes_id":2620,"users_id":18,"type":1,"use_notification":0}]}` / `{"input":[{"tickets_id":2079,"groups_id":5,"type":1,"use_notification":0}]}` respectivamente.

### Agregar comentarios (`assistance_item_followup_add`)

`ticket_follow_add`/`change_follow_add` se reemplazaron por `assistance_item_followup_add`. A diferencia de las asignaciones (`tickets_id`/`changes_id`), `ITILFollowup` ya usa un payload itemtype-generico en GLPI (`itemtype`/`items_id`), asi que unificar solo requiere pasar el `itemtype` correcto:

```json
{"itemtype":"Change","id":2620,"content":"pruebas de ticketssss","is_private":0}
```

Esto envia a GLPI `POST ITILFollowup` con `{"input":[{"itemtype":"Change","items_id":2620,"content":"pruebas de ticketssss","is_private":0}]}`.

### Actualizar comentarios (`assistance_item_followup_update`)

Misma forma que `assistance_item_followup_add`, con `followup_id` agregado (el id propio del comentario, distinto de `id`, que sigue siendo el ticket/cambio):

```json
{"itemtype":"Change","id":2620,"followup_id":20016,"content":"xxxxx de ticketssss","is_private":0}
```

Esto envia a GLPI `PATCH ITILFollowup` con `{"input":[{"id":20016,"itemtype":"Change","items_id":2620,"content":"xxxxx de ticketssss","is_private":0}]}`.

### Agregar/actualizar soluciones (`assistance_item_solution_add` / `assistance_item_solution_update`)

`ticket_solution_add`/`change_solution_add` se reemplazaron por `assistance_item_solution_add`: igual que ITILFollowup, ITILSolution ya es itemtype-generico en GLPI, asi que unificar solo requiere el `itemtype` correcto. `assistance_item_solution_update` agrega `solution_id` (el id propio de la solucion) sobre la misma forma. Ninguna de las dos recibe `solution_type_id`:

```json
{"itemtype":"Change","id":2620,"content":"solucion de prueba"}
```

```json
{"itemtype":"Change","id":2620,"solution_id":555,"content":"solucion actualizada"}
```

### Vincular/desvincular Ticket y Change (`assistance_item_ticketchange_link` / `assistance_item_ticketchange_unlink`)

`ticket_change_link`/`change_ticket_link` y `ticket_change_unlink`/`change_ticket_unlink` se reemplazan por una sola herramienta cada uno: ambos pares eran mecanicamente identicos (mismo `POST`/`DELETE /Change_Ticket`), solo con nombres y orden de parametros distintos — no habia ninguna logica dependiente de "que lado" se llamaba.

`assistance_item_ticketchange_link` recibe `itemtype` (`"Ticket"` o `"Change"`), `id` (el id de ese lado) y `link_id` — aqui **`link_id` es el id del lado complementario** (un `change_id` si `itemtype` es `"Ticket"`, o un `ticket_id` si `itemtype` es `"Change"`):

```json
{"itemtype":"Ticket","id":47,"link_id":2620}
```

`assistance_item_ticketchange_unlink` recibe la misma forma que `assistance_item_ticketchange_link` (`itemtype`, `id`, `link_id` con el mismo significado: el lado complementario), en vez del id de la relacion `Change_Ticket` en si — referenciar ese id opaco directamente es dificil (obliga a consultar `item_subitem_list` antes). La herramienta resuelve internamente cual relacion borrar:

```json
{"itemtype":"Ticket","id":47,"link_id":2620,"purge":true}
```

Todas las herramientas que operan sobre un ticket o cambio (creacion, listados, comentarios, soluciones, asignaciones, enlaces, actualizacion y borrado) aceptan dos parametros opcionales:

- `entity_id`: cambia la entidad activa de la sesion GLPI (via `changeActiveEntities`) antes de ejecutar la operacion. El codigo `0` (entidad raiz de GLPI) es un valor valido. Use `entityprofile_list` para consultar los codigos disponibles.
- `profile_id`: cambia el perfil activo de la sesion GLPI (via `changeActiveProfile`) antes de ejecutar la operacion. Use `entityprofile_list` para consultar los codigos disponibles.

Si se omiten (o llegan vacios/`null`), se usan el perfil/entidad activos por defecto de la sesion sin fallar. Cuando se indican ambos en la misma llamada, **el perfil se cambia primero** y luego la entidad: **el perfil activo determina los permisos (crear/leer/editar) con los que se ejecuta la operacion; la entidad activa solo determina sobre que registros se opera**. En GLPI, las entidades a las que un usuario tiene acceso estan asociadas a sus perfiles (ver la respuesta de `entityprofile_list`) — para operar correctamente sobre una entidad que pertenece a un perfil distinto al activo, pase tambien `profile_id`.

Ambos parametros tambien aceptan el **nombre** de la entidad/perfil (texto no numerico) en vez del id: se resuelve automaticamente consultando `entityprofile_list` internamente, y si solo se da el nombre del perfil (sin entidad), se selecciona la primera entidad de ese perfil. La respuesta incluye un campo `resolution_notes` cuando esto ocurre. Un nombre ambiguo (coincide con mas de un perfil/entidad) o inexistente devuelve un error de validacion en vez de adivinar. Ver el recurso `mcp-glpi://docs/glpi-entity-profile-resolution` para el detalle completo.

Como cada llamada MCP abre y cierra su propia sesion GLPI, el cambio de entidad/perfil aplica solo a esa llamada puntual; no persiste para llamadas posteriores.

**Importante**: GLPI responde `HTTP 200` con cuerpo `false` (no un error HTTP) cuando la entidad o el perfil indicados no son accesibles para el usuario/token, o no existen. Cualquier herramienta invocada con `entity_id`/`profile_id` detecta este caso y devuelve un error explicito en vez de fallar en silencio; si obtenes ese error, revisa que el `entity_id`/`profile_id` este entre los que devuelve `entityprofile_list`.

**Nota de diseño**: no hay herramientas dedicadas `entity_switch`/`profile_switch` — cada llamada MCP abre y cierra su propia sesion GLPI, asi que "cambiar de entidad/perfil" como operacion aislada no tendria ningun efecto persistente. Cambiar de entidad/perfil solo tiene sentido *junto con* la operacion real que se quiere ejecutar en esa entidad/perfil, por eso `entity_id`/`profile_id` son parametros de las herramientas de negocio (`ticket_list`, `ticket_add`, etc.), no tools independientes.

Las herramientas responden en JSON serializado dentro de `TextContent`. Por ejemplo, `entityprofile_list` devuelve una lista simplificada de perfiles con sus entidades:

```json
[
  {
    "id": 22,
    "name": "Administrativo - Solicitante",
    "entities": [
      {
        "id": 2,
        "name": "Administrativo",
        "is_recursive": true
      }
    ]
  }
]
```

## Recursos MCP

Ademas de las tools, el servidor expone la capacidad `resources` del protocolo MCP (`resources/list` / `resources/read`), para que un cliente MCP pueda cargar documentacion de referencia como contexto sin necesidad de invocar una tool.

- `src/mcp_glpi/resource_catalog.py`: fuente unica de verdad de los recursos publicados (`RESOURCE_SPECS`: `uri`/`name`/`description`/`mime_type`/`path`), analogo a `TOOL_SPECS` en `tool_catalog.py`.
- `src/mcp_glpi/resources/`: contenido real de los recursos (archivos `.md`), empaquetado dentro del wheel via `[tool.setuptools.package-data]` en `pyproject.toml`.
- `src/mcp_glpi/server.py`: registra `handle_list_resources`/`handle_read_resource` sobre `self.app`, leyendo el contenido con `resource_catalog.read_resource_text(uri)`.

Recursos publicados hoy (separados por tema para poder cargar solo el que aplica):

| URI | Nombre | Contenido |
|-----|--------|-----------|
| `mcp-glpi://docs/glpi-items` | `glpi-items` | Herramientas **genericas**: descubrir itemtype/subtype (`item_type_list`/`item_subtype_list`), listar/consultar/eliminar de forma generica (`item_list`/`item_get`/`item_delete`) y listar sub-elementos (`item_subitem_list`), con su matriz de rutas/capacidades. |
| `mcp-glpi://docs/glpi-tools` | `glpi-tools` | Herramientas **especificas** de tickets/cambios (crear, actualizar, eliminar, seguimientos, soluciones, asignaciones, relaciones) y de archivos (`file_upload`/`file_download`/`file_link`/`file_unlink`), con su matriz de rutas/capacidades. |
| `mcp-glpi://docs/glpi-entity-profile-resolution` | `glpi-entity-profile-resolution` | Que pasa cuando `entity_id`/`profile_id` se dan como **nombre** en vez de id: resolucion automatica, seleccion de la primera entidad de un perfil, y manejo de nombres ambiguos/inexistentes. |

Para agregar un recurso nuevo: colocar el archivo en `src/mcp_glpi/resources/`, agregar una entrada a `RESOURCE_SPECS`, y (si es un patron de archivo nuevo, ej. `.json`) ajustar el glob en `[tool.setuptools.package-data]`.

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
   Esto crea el archivo `dist/mcp_glpi-3.0.0-py3-none-any.whl` listo para distribuir.
3. Para instalarlo en otro entorno o servidor, copiar el wheel y ejecutar:
   ```bash
   pip install dist/mcp_glpi-3.0.0-py3-none-any.whl
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

- **Sesion GLPI**: las herramientas `session_validate` y `entityprofile_list` permiten validar credenciales y consultar el contexto disponible del usuario autenticado (codigos de perfil/entidad a usar con `entity_id`/`profile_id` en el resto de las herramientas).

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
- Helpers de tickets, cambios, sesion y archivos (`mcp_glpi.glpi.tickets`, `mcp_glpi.glpi.changes`, `mcp_glpi.glpi.session`, `mcp_glpi.glpi.files`).
- El wrapper HTTP de `glpi_client` (`tests/glpi_client/`), incluyendo subida/descarga de documentos.
- Validacion basica de `claude_desktop_config.json` y contenido Markdown.

## Estructura Interna
La capa GLPI fue separada por dominio y responsabilidad:

- `src/mcp_glpi/glpi/tickets/`: lectura, creacion, actualizacion, comentarios (agregar/listar), soluciones (agregar/listar), asignaciones, enlaces y borrado.
- `src/mcp_glpi/glpi/changes/`: lectura, creacion, actualizacion, comentarios (agregar/listar), soluciones (agregar/listar), asignaciones, enlaces y borrado.
- `src/mcp_glpi/glpi/session/`: lectura de sesion, perfiles (listado y cambio de perfil activo) y entidades (listado y cambio de entidad activa) del usuario logueado.
- `src/mcp_glpi/glpi/files/`: subida (`file_upload`), descarga (`file_download`) y vinculo/desvinculo (`file_link`/`file_unlink`, itemtype `Document_Item`) de documentos.
- `src/mcp_glpi/glpi/generic.py`: acceso generico a **cualquier** itemtype/subtype de GLPI (`ITEMTYPE_CATALOG` es una guia de referencia verificada, no una restriccion), detras de `item_list`/`item_get`/`item_subitem_list`/`item_type_list`/`item_subtype_list` (solo lectura) e `item_delete` (la unica mutacion generica).
- `src/mcp_glpi/glpi/shared.py`: helpers comunes reutilizados por las entidades GLPI, incluyendo `fetch_paginated_items`/`fetch_paginated_subitems` (paginacion, apertura de sesion, cambio de entidad/perfil) y `EntityList.respond()` (dispatch de `output`/`fields`) que comparten `ticket_list`/`change_list`, los listados de seguimientos/soluciones, e `item_list`/`item_subitem_list`.

## Recursos Utiles
- Archivo de configuracion: `examples/claude_desktop_config.json`.
- Variables de entorno soportadas: consulte `src/mcp_glpi/common/config.py`.

¡Feliz automatizacion con MCP + GLPI!
