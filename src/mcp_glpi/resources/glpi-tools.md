# Herramientas específicas de tickets, cambios y archivos GLPI

Usar las herramientas `ticket_*` y `change_*` cuando la operación necesite crear o actualizar tickets y cambios. Usar `file_*` para gestionar archivos de tipo `Document` (subida, descarga, vínculo/desvínculo con un ticket o cambio). Usar `assistance_item_*` para asignar usuarios/grupos, agregar/actualizar comentarios o soluciones, y vincular/desvincular un ticket con un cambio (ver más abajo).

Para descubrir `itemtype`/`subtype` soportados, o para listar, consultar y eliminar elementos de forma genérica, ver el recurso `mcp-glpi://docs/glpi-items` (`item_list`, `item_get`, `item_delete`, `item_subitem_list`).

## Crear o actualizar Ticket/Change

`ticket_save`/`change_save` reemplazan a `ticket_add`/`ticket_update` y `change_add`/`change_update`: una sola herramienta por elemento en vez de dos. El parámetro `id` decide el comportamiento: sin `id` se crea uno nuevo (`name` es obligatorio); con `id` se actualiza el existente, usando los mismos nombres de parámetro (`name`, `content`, `status`, `impact`, `priority`, `urgency`, `category_id`, `additional`, `pr_links`) — solo se envían los que se indiquen.

```json
{"name":"Impresora no imprime","content":"Detalle del problema","priority":"Alta"}
```

```json
{"id":123,"status":"Solucionado","additional":{"solutiontypes_id":3}}
```

`pr_links` ahora funciona igual en ambas herramientas (`ticket_save` y `change_save`): antes solo `change_add`/`change_update` lo aplicaban de verdad — `ticket_add`/`ticket_update` lo aceptaban en el schema pero lo ignoraban silenciosamente. Con la unificación, ambas rutas usan el mismo mecanismo (`_merge_pr_links`), así que `ticket_save` ya soporta `pr_links` correctamente.

## Asignar usuario a Ticket o Change

`item_user_add` reemplaza a `ticket_user_assign`/`change_user_assign`/`assistance_item_user_add`: una sola herramienta para ambos itemtypes, ya que comparten la misma forma de asignación (solo cambia el campo GLPI y el subtype). Recibe `itemtype` (`"Ticket"` o `"Change"`, sin otros valores), `id` (el ticket/change) y `users`; internamente arma el campo `tickets_id`/`changes_id` y llama a `Ticket_User`/`Change_User` segun corresponda. **`users` solo admite un objeto por llamada** — GLPI soporta un `POST` en lote tambien para `Ticket_User`/`Change_User`, pero la tool se restringe a proposito a un usuario por llamada:

```json
{"itemtype":"Change","id":2620,"users":{"users_id":18,"type":1,"use_notification":0}}
```

Esto envía a GLPI (`POST Change_User`) el payload `{"input":[{"changes_id":2620,"users_id":18,"type":1,"use_notification":0}]}`. `users_id` es obligatorio; `type` (1 solicitante, 2 asignado, 3 observador), `use_notification`, `is_dynamic`, `alternative_email` son opcionales — si se omite `type`, GLPI mismo lo asume como `1` (solicitante).

## Asignar grupo a Ticket o Change

`item_group_add` reemplaza a `ticket_group_assign`/`change_group_assign`/`assistance_item_group_add`, con el mismo patrón que `item_user_add`: `itemtype` (`"Ticket"` o `"Change"`), `id` y `groups`; arma internamente `tickets_id`/`changes_id` y llama a `Group_Ticket`/`Change_Group` según corresponda. **`groups` solo admite un objeto por llamada** — GLPI soporta un `POST` en lote tambien para `Group_Ticket`/`Change_Group`, pero la tool se restringe a proposito a un grupo por llamada:

```json
{"itemtype":"Ticket","id":2079,"groups":{"groups_id":5,"type":1,"use_notification":0}}
```

Esto envía a GLPI (`POST Group_Ticket`) el payload `{"input":[{"tickets_id":2079,"groups_id":5,"type":1,"use_notification":0}]}`. `groups_id` es obligatorio; `type` (1 solicitante, 2 asignado, 3 observador), `use_notification`, `is_dynamic`, `alternative_email` son opcionales — si se omite `type`, GLPI mismo lo asume como `1` (solicitante).

## Agregar/actualizar comentarios en Ticket o Change

`item_followup_add` unifica creación y actualización de un comentario (`ITILFollowup`) en un Ticket o Change en una sola herramienta, con el mismo patrón crear-o-actualizar que `ticket_save`/`change_save`/`item_solution_add` (reemplaza a `ticket_follow_add`/`change_follow_add` y a las posteriores `assistance_item_followup_add`/`assistance_item_followup_update`). A diferencia de `Ticket_User`/`Change_User` o `Group_Ticket`/`Change_Group`, `ITILFollowup` ya es itemtype-genérico del lado de GLPI: el payload siempre usa los campos `itemtype`/`items_id` (nunca `tickets_id`/`changes_id`), asi que solo cambia el valor de `itemtype`. Recibe `itemtype` (`"Ticket"` o `"Change"`), `id` y `content` obligatorios; sin `followup_id` crea un comentario nuevo:

```json
{"itemtype":"Change","id":2620,"content":"pruebas de ticketssss","is_private":0}
```

Con `followup_id` (el id propio del comentario, distinto de `id`, que sigue siendo el ticket/cambio) actualiza el existente:

```json
{"itemtype":"Change","id":2620,"followup_id":20016,"content":"xxxxx de ticketssss","is_private":0}
```

Esto envía a GLPI `POST`/`PATCH ITILFollowup` segun corresponda; la actualización anterior envía `{"input":[{"id":20016,"itemtype":"Change","items_id":2620,"content":"xxxxx de ticketssss","is_private":0}]}`. `is_private` y `additional` son opcionales; para listar los comentarios ya registrados seguir usando `item_subitem_list` con `subtype: "ITILFollowup"` (ver `mcp-glpi://docs/glpi-items`).

## Agregar/actualizar soluciones en Ticket o Change

`item_solution_add` unifica creación y actualización de una solución (`ITILSolution`) en un Ticket o Change en una sola herramienta, con el mismo patrón crear-o-actualizar que `ticket_save`/`change_save` (reemplaza a `ticket_solution_add`/`change_solution_add` y a las posteriores `assistance_item_solution_add`/`assistance_item_solution_update`). Al igual que `ITILFollowup`, `ITILSolution` ya es itemtype-genérico en GLPI (campos `itemtype`/`items_id`), asi que solo cambia el valor de `itemtype`. Recibe `itemtype`, `id` y `content` obligatorios (sin `solution_type_id`); sin `solution_id` crea una solución nueva:

```json
{"itemtype":"Change","id":2620,"content":"solucion de prueba"}
```

Con `solution_id` (el id propio de la solución) actualiza la existente:

```json
{"itemtype":"Change","id":2620,"solution_id":555,"content":"solucion actualizada"}
```

Esto envía a GLPI `POST`/`PATCH ITILSolution` segun corresponda, con el mismo patrón de payload que `ITILFollowup`. Para listar soluciones ya registradas seguir usando `item_subitem_list` con `subtype: "ITILSolution"`.

## Vincular/desvincular Ticket y Change

`item_ticketchange_link` reemplaza a `ticket_change_link`/`change_ticket_link` (mecánicamente idénticos, solo con nombres/orden de parámetros distintos). Recibe `itemtype` (`"Ticket"` o `"Change"`), `id` (el id de ese lado) y `link_id` — aquí **`link_id` es el id del lado complementario**: un `change_id` si `itemtype` es `"Ticket"`, o un `ticket_id` si `itemtype` es `"Change"`:

```json
{"itemtype":"Ticket","id":47,"link_id":2620}
```

Esto vincula el ticket 47 con el cambio 2620 (`POST Change_Ticket` con `{"tickets_id":47,"changes_id":2620}`), sin importar cual de los dos itemtypes se use como ancla.

`item_ticketchange_unlink` reemplaza a `ticket_change_unlink`/`change_ticket_unlink`, y usa la **misma forma** que `item_ticketchange_link` (`itemtype`, `id`, `link_id` con el mismo significado: el lado complementario), en vez de pedir el id de la relación `Change_Ticket` en sí — ese id es opaco y difícil de referenciar sin antes consultar `item_subitem_list`. La herramienta busca la relación correspondiente internamente antes de eliminarla:

```json
{"itemtype":"Ticket","id":47,"link_id":2620,"purge":true}
```

## Transferir documentos

Usar `file_upload` para subir un archivo local como un nuevo `Document`. Requiere `file_path`; `name` define el título en GLPI y `file_name` es opcional.

```json
{"file_path":"C:/archivos/informe.pdf","name":"Informe de cambio"}
```

Usar `file_download` con el `document_id` obtenido mediante `item_list` o `item_get`, y una ruta local de destino:

```json
{"document_id":456,"destination_path":"C:/descargas/informe.pdf"}
```

No existe una herramienta llamada `file_unload` en este servidor; usar `file_upload` para la subida de archivos.

Usar `file_link` para vincular un `Document` existente a un Ticket o Change, y `file_unlink` para eliminar esa relación (`Document_Item`). Para ver los documentos ya vinculados a un ticket o cambio, usar `item_subitem_list` con `subtype: "Document_Item"` (ver `mcp-glpi://docs/glpi-items`).

## Matriz de rutas y capacidades

Construir las rutas relativas sustituyendo `{id}`/`{ticket_id}`/`{change_id}`/`{link_id}`/`{document_id}` por el identificador obtenido. Las opciones `entity_id` y `profile_id` se pueden incluir en todas las herramientas de esta tabla.

| Nombre | Herramienta | URL relativa | Opciones | Puede hacer | No puede hacer |
| --- | --- | --- | --- | --- | --- |
| Listar Ticket | `ticket_list` | `/Ticket` | `limit`, `offset`, `sort_by`, `order`, `fields`, `filters`, `expand_dropdowns`, `include_deleted`. Sin `output`: siempre responde JSON. | Listar tickets con filtros. | Consultar un ticket puntual; usar `item_get`; obtener tabla/raw (usar `item_list` con `itemtype: "Ticket"`). |
| Crear/actualizar Ticket | `ticket_save` | `/Ticket` · `/Ticket/{id}` | Sin `id`: `name` obligatorio, resto opcional (crea). Con `id`: todos opcionales, solo se envían los indicados (actualiza). `content`, `status`, `impact`, `priority`, `urgency`, `category_id`, `additional`, `pr_links` disponibles en ambos casos. | Crear un ticket nuevo o actualizar uno existente. | Eliminar el ticket; usar `item_delete` con `itemtype: "Ticket"`. |
| Listar Change | `change_list` | `/Change` | `limit`, `offset`, `sort_by`, `order`, `fields`, `filters`, `expand_dropdowns`, `include_deleted`. Sin `output`: siempre responde JSON. | Listar cambios con filtros. | Consultar un cambio puntual; usar `item_get`; obtener tabla/raw (usar `item_list` con `itemtype: "Change"`). |
| Crear/actualizar Change | `change_save` | `/Change` · `/Change/{id}` | Sin `id`: `name` obligatorio, resto opcional (crea). Con `id`: todos opcionales, solo se envían los indicados (actualiza). `content`, `status`, `impact`, `priority`, `urgency`, `category_id`, `additional`, `pr_links` disponibles en ambos casos. | Crear un cambio nuevo o actualizar uno existente. | Eliminar el cambio; usar `item_delete` con `itemtype: "Change"`. |
| Asignar usuario a Ticket/Change | `item_user_add` | `/Ticket_User` · `/Change_User` | `itemtype` (`Ticket`\|`Change`), `id` y `users` obligatorios. `users` es un solo objeto (no lista); requiere `users_id`, admite `type`, `use_notification`, `is_dynamic`, `alternative_email`. | Añadir un usuario a un ticket o cambio. | Asignar mas de un usuario en la misma llamada; quitar o editar asignaciones existentes; asignar a otro itemtype. |
| Asignar grupo a Ticket/Change | `item_group_add` | `/Group_Ticket` · `/Change_Group` | `itemtype` (`Ticket`\|`Change`), `id` y `groups` obligatorios. `groups` es un solo objeto (no lista); requiere `groups_id`, admite `type`, `use_notification`, `is_dynamic`, `alternative_email`. | Añadir un grupo a un ticket o cambio. | Asignar mas de un grupo en la misma llamada; quitar o editar asignaciones existentes; asignar a otro itemtype. |
| Crear/actualizar comentario de Ticket/Change | `item_followup_add` | `/ITILFollowup` · `/ITILFollowup` (PATCH) | `itemtype` (`Ticket`\|`Change`), `id` y `content` obligatorios. Sin `followup_id`: crea. Con `followup_id`: actualiza el existente. `is_private`, `additional` opcionales. | Crear un comentario nuevo o actualizar uno existente en un ticket o cambio. | Listar comentarios existentes; usar `item_subitem_list` con `subtype: "ITILFollowup"` (ver `mcp-glpi://docs/glpi-items`). |
| Crear/actualizar solución de Ticket/Change | `item_solution_add` | `/ITILSolution` · `/ITILSolution` (PATCH) | `itemtype`, `id` y `content` obligatorios. Sin `solution_id`: crea. Con `solution_id`: actualiza la existente. `additional` opcional. | Registrar una solución nueva o actualizar una existente en un ticket o cambio. | Listar soluciones existentes; usar `item_subitem_list` con `subtype: "ITILSolution"` (ver `mcp-glpi://docs/glpi-items`). |
| Vincular Ticket y Change | `item_ticketchange_link` | `/Change_Ticket` | `itemtype` (`Ticket`\|`Change`), `id` y `link_id` obligatorios (`link_id` es el id del lado complementario); `additional` opcional. | Crear relación Ticket–Change. | Eliminar una relación existente; usar `item_ticketchange_unlink`. |
| Desvincular Ticket y Change | `item_ticketchange_unlink` | `/Change_Ticket/{relacion_id}` | `itemtype` (`Ticket`\|`Change`), `id` y `link_id` obligatorios (misma forma que vincular: `link_id` es el lado complementario); `purge`, `keep_history` opcionales. | Eliminar relación Ticket–Change (resuelve el id de la relación internamente). | Eliminar el ticket o el cambio. |
| Subir Document | `file_upload` | `/Document` | `file_path` obligatorio; `name`, `file_name`, `additional` opcionales. | Crear un `Document` a partir de un archivo local. | Modificar un documento existente o vincularlo a un ticket/cambio. |
| Descargar Document | `file_download` | `/Document/{document_id}` | `document_id` y `destination_path` obligatorios. | Guardar un `Document` de GLPI en una ruta local. | Consultar documentos sin su ID ni modificar el documento descargado. |
| Vincular Document | `file_link` | `/Document_Item` | `document_id`, `item_type`, `item_id` obligatorios; `additional` opcional. | Vincular un documento a un Ticket o Change. | Crear un documento o modificar su archivo. |
| Desvincular Document | `file_unlink` | `/Document_Item/{link_id}` | `document_id` y `link_id` obligatorios; `purge`, `keep_history` opcionales. | Eliminar una relación `Document_Item`. | Eliminar el documento. |
