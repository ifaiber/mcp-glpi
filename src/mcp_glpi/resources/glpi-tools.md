# Herramientas específicas de tickets, cambios y archivos GLPI

Usar las herramientas `ticket_*` y `change_*` cuando la operación necesite crear, actualizar, comentar, solucionar o relacionar tickets y cambios. Usar `file_*` para gestionar archivos de tipo `Document` (subida, descarga, vínculo/desvínculo con un ticket o cambio). Usar `assistance_item_user_add`/`assistance_item_group_add` para asignar usuarios/grupos a un Ticket o Change (ver más abajo).

Para descubrir `itemtype`/`subtype` soportados, o para listar, consultar y eliminar elementos de forma genérica, ver el recurso `mcp-glpi://docs/glpi-items` (`item_list`, `item_get`, `item_delete`, `item_subitem_list`).

## Asignar usuarios a Ticket o Change

`assistance_item_user_add` reemplaza a `ticket_user_assign`/`change_user_assign`: una sola herramienta para ambos itemtypes, ya que comparten la misma forma de asignación (solo cambia el campo GLPI y el subtype). Recibe `itemtype` (`"Ticket"` o `"Change"`, sin otros valores), `id` (el ticket/change) y `users`; internamente arma el campo `tickets_id`/`changes_id` y llama a `Ticket_User`/`Change_User` segun corresponda:

```json
{"itemtype":"Change","id":2620,"users":{"users_id":18,"type":1,"use_notification":0}}
```

Esto envía a GLPI (`POST Change_User`) el payload `{"input":[{"changes_id":2620,"users_id":18,"type":1,"use_notification":0}]}`. Cada entrada de `users` admite `users_id` (obligatorio), `type` (1 solicitante, 2 asignado, 3 observador), `use_notification`, `is_dynamic`, `alternative_email` — igual que antes.

## Asignar grupos a Ticket o Change

`assistance_item_group_add` reemplaza a `ticket_group_assign`/`change_group_assign`, con el mismo patrón que `assistance_item_user_add`: `itemtype` (`"Ticket"` o `"Change"`), `id` y `groups`; arma internamente `tickets_id`/`changes_id` y llama a `Group_Ticket`/`Change_Group` según corresponda:

```json
{"itemtype":"Ticket","id":2079,"groups":{"groups_id":5,"type":1,"use_notification":0}}
```

Esto envía a GLPI (`POST Group_Ticket`) el payload `{"input":[{"tickets_id":2079,"groups_id":5,"type":1,"use_notification":0}]}`. Cada entrada de `groups` admite `groups_id` (obligatorio), `type`, `use_notification`, `is_dynamic`, `alternative_email` — igual que antes.

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
| Listar Ticket | `ticket_list` | `/Ticket` | `limit`, `offset`, `sort_by`, `order`, `output`, `fields`, `filters`, `expand_dropdowns`, `include_deleted`. | Listar tickets con filtros. | Consultar un ticket puntual; usar `item_get`. |
| Crear Ticket | `ticket_add` | `/Ticket` | `name` obligatorio; `content`, `status`, `impact`, `priority`, `urgency`, `category_id`, `additional`, `pr_links` opcionales. | Crear un ticket. | Actualizar un ticket existente. |
| Actualizar Ticket | `ticket_update` | `/Ticket/{ticket_id}` | `ticket_id` y `fields` obligatorios; `pr_links` opcional. | Actualizar campos del ticket. | Crear o eliminar el ticket. |
| Eliminar Ticket | `ticket_delete` | `/Ticket/{ticket_id}` | `ticket_id` obligatorio; `purge`, `keep_history` opcionales. | Enviar a papelera o purgar el ticket. | Eliminar solo una relación o subelemento. |
| Listar Change | `change_list` | `/Change` | `limit`, `offset`, `sort_by`, `order`, `output`, `fields`, `filters`, `expand_dropdowns`, `include_deleted`. | Listar cambios con filtros. | Consultar un cambio puntual; usar `item_get`. |
| Crear Change | `change_add` | `/Change` | `name` obligatorio; `content`, `status`, `impact`, `priority`, `urgency`, `category_id`, `additional`, `pr_links` opcionales. | Crear un cambio. | Actualizar un cambio existente. |
| Actualizar Change | `change_update` | `/Change/{change_id}` | `change_id` y `fields` obligatorios; `pr_links` opcional. | Actualizar campos del cambio. | Crear o eliminar el cambio. |
| Eliminar Change | `change_delete` | `/Change/{change_id}` | `change_id` obligatorio; `purge`, `keep_history` opcionales. | Enviar a papelera o purgar el cambio. | Eliminar solo una relación o subelemento. |
| Agregar seguimiento a Ticket | `ticket_follow_add` | `/ITILFollowup` | `ticket_id` y `content` obligatorios; `is_private`, `additional` opcionales. | Crear un seguimiento asociado al ticket. | Editar o eliminar un seguimiento existente; para listarlos usar `item_subitem_list` con `itemtype: "Ticket"`, `subtype: "ITILFollowup"` (ver `mcp-glpi://docs/glpi-items`). |
| Agregar solución a Ticket | `ticket_solution_add` | `/ITILSolution` | `ticket_id` y `content` obligatorios; `solution_type_id`, `additional` opcionales. | Registrar una solución del ticket. | Editar o eliminar una solución existente; para listarlas usar `item_subitem_list` con `itemtype: "Ticket"`, `subtype: "ITILSolution"` (ver `mcp-glpi://docs/glpi-items`). |
| Vincular Change a Ticket | `ticket_change_link` | `/Change_Ticket` | `ticket_id` y `change_id` obligatorios; `additional` opcional. | Crear relación Ticket–Change. | Eliminar una relación existente. |
| Desvincular Change de Ticket | `ticket_change_unlink` | `/Change_Ticket/{link_id}` | `ticket_id` y `link_id` obligatorios; `purge`, `keep_history` opcionales. | Eliminar relación Ticket–Change. | Eliminar el ticket o el cambio. |
| Agregar seguimiento a Change | `change_follow_add` | `/ITILFollowup` | `change_id` y `content` obligatorios; `is_private`, `additional` opcionales. | Crear un seguimiento asociado al cambio. | Editar o eliminar un seguimiento existente; para listarlos usar `item_subitem_list` con `itemtype: "Change"`, `subtype: "ITILFollowup"` (ver `mcp-glpi://docs/glpi-items`). |
| Agregar solución a Change | `change_solution_add` | `/ITILSolution` | `change_id` y `content` obligatorios; `solution_type_id`, `additional` opcionales. | Registrar una solución del cambio. | Editar o eliminar una solución existente; para listarlas usar `item_subitem_list` con `itemtype: "Change"`, `subtype: "ITILSolution"` (ver `mcp-glpi://docs/glpi-items`). |
| Asignar usuarios a Ticket/Change | `assistance_item_user_add` | `/Ticket_User` · `/Change_User` | `itemtype` (`Ticket`\|`Change`), `id` y `users` obligatorios. Cada usuario requiere `users_id`; admite `type`, `use_notification`, `is_dynamic`, `alternative_email`. | Añadir usuarios a un ticket o cambio. | Quitar o editar asignaciones existentes; asignar a otro itemtype. |
| Asignar grupos a Ticket/Change | `assistance_item_group_add` | `/Group_Ticket` · `/Change_Group` | `itemtype` (`Ticket`\|`Change`), `id` y `groups` obligatorios. Cada grupo requiere `groups_id`; admite `type`, `use_notification`, `is_dynamic`, `alternative_email`. | Añadir grupos a un ticket o cambio. | Quitar o editar asignaciones existentes; asignar a otro itemtype. |
| Vincular Ticket a Change | `change_ticket_link` | `/Change_Ticket` | `change_id` y `ticket_id` obligatorios; `additional` opcional. | Crear relación Change–Ticket. | Eliminar una relación existente. |
| Desvincular Ticket de Change | `change_ticket_unlink` | `/Change_Ticket/{link_id}` | `change_id` y `link_id` obligatorios; `purge`, `keep_history` opcionales. | Eliminar relación Change–Ticket. | Eliminar el cambio o el ticket. |
| Subir Document | `file_upload` | `/Document` | `file_path` obligatorio; `name`, `file_name`, `additional` opcionales. | Crear un `Document` a partir de un archivo local. | Modificar un documento existente o vincularlo a un ticket/cambio. |
| Descargar Document | `file_download` | `/Document/{document_id}` | `document_id` y `destination_path` obligatorios. | Guardar un `Document` de GLPI en una ruta local. | Consultar documentos sin su ID ni modificar el documento descargado. |
| Vincular Document | `file_link` | `/Document_Item` | `document_id`, `item_type`, `item_id` obligatorios; `additional` opcional. | Vincular un documento a un Ticket o Change. | Crear un documento o modificar su archivo. |
| Desvincular Document | `file_unlink` | `/Document_Item/{link_id}` | `document_id` y `link_id` obligatorios; `purge`, `keep_history` opcionales. | Eliminar una relación `Document_Item`. | Eliminar el documento. |
