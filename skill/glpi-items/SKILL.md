---
name: glpi-items
description: "Opera tickets, cambios y documentos de GLPI mediante herramientas genéricas y específicas: listar, crear, consultar, actualizar, eliminar, gestionar seguimientos, soluciones, asignaciones, relaciones y archivos. Usar cuando se necesite localizar identificadores, interpretar href de relaciones o ejecutar una operación GLPI admitida."
---

# Elementos GLPI

Usar `item_list`, `item_get` e `item_delete` para trabajar con elementos genéricos de GLPI. Usar `file_upload`, `file_download`, `file_link` y `file_unlink` para gestionar archivos de tipo `Document`. Indicar siempre el `itemtype` con la capitalización de GLPI, por ejemplo `Ticket`, `Change` o `Document`.

Preferir las herramientas específicas `ticket_*` y `change_*` cuando la operación necesite crear, actualizar, asignar, comentar, solucionar o relacionar elementos. Las herramientas genéricas sirven para descubrir, listar, consultar y eliminar los itemtypes permitidos.

## Descubrir tipos y subtipos

Si no se conoce el `itemtype` aceptado, usar `item_type_list` antes de llamar a las herramientas principales. Elegir el valor de `itemtype` de esa respuesta; no inferirlo ni usar un tipo fuera de la lista devuelta.

Si se necesita conocer los subtipos disponibles para un elemento, usar `item_subtype_list` proporcionando el `itemtype` ya identificado. La respuesta enumera los `subtype` válidos para ese tipo. Usar ese valor para interpretar una ruta `/{itemtype}/{id}/{subitemtype}` o antes de trabajar con un subelemento.

## Localizar elementos: `item_list`

Usar `item_list` para buscar o listar elementos de un tipo:

```json
{"itemtype":"Change","limit":20,"sort_by":"id","order":"DESC"}
```

Aplicar `filters` para acotar los resultados y `fields` para solicitar solo los campos necesarios. Usar `limit` y `offset` para paginar. El resultado de esta operación es la fuente habitual de los identificadores: tomar el valor del campo `id` del elemento que corresponda.

No proporcionar un `id` a `item_list`; para consultar uno concreto, usar `item_get`.

## Consultar un elemento: `item_get`

Usar `item_get` con el `itemtype` y el `id` localizados previamente:

```json
{"itemtype":"Change","id":123}
```

Usar `fields` si solo hacen falta propiedades concretas y `expand_dropdowns` cuando se requieran los valores legibles de desplegables.

Buscar también IDs en los `href` devueltos por la respuesta. Las rutas de relaciones suelen tener esta forma:

```
/{itemtype}/{id}/{subitemtype}
```

Por ejemplo, `/Change/123/Document_Item` identifica el elemento padre `Change` con ID `123` y señala que el subtipo o relación es `Document_Item`. No interpretar `Document_Item` como el ID: el identificador del elemento principal es el segmento numérico entre el itemtype y el subitemtype.

## Eliminar un elemento: `item_delete`

Usar `item_delete` únicamente después de confirmar el `itemtype` y el `id` correctos con `item_list` o `item_get`:

```json
{"itemtype":"Change","id":123}
```

La eliminación normal envía el elemento a la papelera. Incluir `purge: true` solo si se solicita explícitamente una eliminación definitiva. Incluir `keep_history: true` cuando se deba conservar el historial de GLPI.

`item_delete` está disponible en el servidor. Sus parámetros obligatorios son `itemtype` e `id`.

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

## Matriz de rutas y capacidades

Construir las rutas relativas sustituyendo `{id}` por el identificador obtenido. La tabla distingue las rutas que se pueden consultar de las operaciones que no están cubiertas por este conjunto de herramientas.

Las opciones `entity_id` y `profile_id` se pueden incluir en todas las herramientas de esta tabla salvo `item_type_list` e `item_subtype_list`. Usarlas cuando sea necesario operar con una entidad o perfil concretos.

| Nombre | Herramienta | URL relativa | Opciones | Puede hacer | No puede hacer |
| --- | --- | --- | --- | --- | --- |
| Tipos de elemento | `item_type_list` | — | Sin parámetros. | Descubrir los `itemtype` admitidos. | Consultar, crear o eliminar elementos. |
| Subtipos de un tipo | `item_subtype_list` | — | `itemtype` opcional. | Descubrir los `subtype` admitidos para un `itemtype`. | Consultar, crear o eliminar un subelemento. |
| Ticket | `item_list` · `item_get` · `item_delete` | `/Ticket` · `/Ticket/{id}` | `itemtype` obligatorio; `id` para get/delete. Listado: `limit`, `offset`, `sort_by`, `order`, `output`, `fields`, `filters`, `expand_dropdowns`, `include_deleted`. Delete: `purge`, `keep_history`. | Listar, consultar y eliminar tickets. | Crear o actualizar tickets. |
| Change | `item_list` · `item_get` · `item_delete` | `/Change` · `/Change/{id}` | `itemtype` obligatorio; `id` para get/delete. Listado: `limit`, `offset`, `sort_by`, `order`, `output`, `fields`, `filters`, `expand_dropdowns`, `include_deleted`. Delete: `purge`, `keep_history`. | Listar, consultar y eliminar cambios. | Crear o actualizar cambios. |
| Document | `item_list` · `item_get` · `item_delete` | `/Document` · `/Document/{id}` | `itemtype` obligatorio; `id` para get/delete. Listado: `limit`, `offset`, `sort_by`, `order`, `output`, `fields`, `filters`, `expand_dropdowns`, `include_deleted`. Delete: `purge`, `keep_history`. | Listar, consultar y eliminar documentos. | Subir, descargar o modificar archivos. |
| Subir Document | `file_upload` | `/Document` | `file_path` obligatorio; `name`, `file_name`, `additional` opcionales. | Crear un `Document` a partir de un archivo local. | Modificar un documento existente o vincularlo a un ticket/cambio. |
| Descargar Document | `file_download` | `/Document/{document_id}` | `document_id` y `destination_path` obligatorios. | Guardar un `Document` de GLPI en una ruta local. | Consultar documentos sin su ID ni modificar el documento descargado. |
| Vincular Document | `file_link` | `/Document_Item` | `document_id`, `item_type`, `item_id` obligatorios; `additional` opcional. | Vincular un documento a un Ticket o Change. | Crear un documento o modificar su archivo. |
| Desvincular Document | `file_unlink` | `/Document_Item/{link_id}` | `document_id` y `link_id` obligatorios; `purge`, `keep_history` opcionales. | Eliminar una relación `Document_Item`. | Eliminar el documento. |
| Listar Ticket | `ticket_list` | `/Ticket` | `limit`, `offset`, `sort_by`, `order`, `output`, `fields`, `filters`, `expand_dropdowns`, `include_deleted`. | Listar tickets con filtros. | Consultar un ticket puntual; usar `item_get`. |
| Crear Ticket | `ticket_add` | `/Ticket` | `name` obligatorio; `content`, `status`, `impact`, `priority`, `urgency`, `category_id`, `additional`, `pr_links` opcionales. | Crear un ticket. | Actualizar un ticket existente. |
| Actualizar Ticket | `ticket_update` | `/Ticket/{ticket_id}` | `ticket_id` y `fields` obligatorios; `pr_links` opcional. | Actualizar campos del ticket. | Crear o eliminar el ticket. |
| Eliminar Ticket | `ticket_delete` | `/Ticket/{ticket_id}` | `ticket_id` obligatorio; `purge`, `keep_history` opcionales. | Enviar a papelera o purgar el ticket. | Eliminar solo una relación o subelemento. |
| Listar Change | `change_list` | `/Change` | `limit`, `offset`, `sort_by`, `order`, `output`, `fields`, `filters`, `expand_dropdowns`, `include_deleted`. | Listar cambios con filtros. | Consultar un cambio puntual; usar `item_get`. |
| Crear Change | `change_add` | `/Change` | `name` obligatorio; `content`, `status`, `impact`, `priority`, `urgency`, `category_id`, `additional`, `pr_links` opcionales. | Crear un cambio. | Actualizar un cambio existente. |
| Actualizar Change | `change_update` | `/Change/{change_id}` | `change_id` y `fields` obligatorios; `pr_links` opcional. | Actualizar campos del cambio. | Crear o eliminar el cambio. |
| Eliminar Change | `change_delete` | `/Change/{change_id}` | `change_id` obligatorio; `purge`, `keep_history` opcionales. | Enviar a papelera o purgar el cambio. | Eliminar solo una relación o subelemento. |
| Agregar seguimiento a Ticket | `ticket_follow_add` | `/ITILFollowup` | `ticket_id` y `content` obligatorios; `is_private`, `additional` opcionales. | Crear un seguimiento asociado al ticket. | Editar o eliminar un seguimiento existente. |
| Listar seguimientos de Ticket | `ticket_follow_list` | `/Ticket/{ticket_id}/ITILFollowup` | `ticket_id` obligatorio; opciones de listado. | Listar seguimientos del ticket. | Crear seguimientos; usar `ticket_follow_add`. |
| Agregar solución a Ticket | `ticket_solution_add` | `/ITILSolution` | `ticket_id` y `content` obligatorios; `solution_type_id`, `additional` opcionales. | Registrar una solución del ticket. | Editar o eliminar una solución existente. |
| Listar soluciones de Ticket | `ticket_solution_list` | `/Ticket/{ticket_id}/ITILSolution` | `ticket_id` obligatorio; opciones de listado. | Listar soluciones del ticket. | Crear soluciones; usar `ticket_solution_add`. |
| Asignar usuarios a Ticket | `ticket_user_assign` | `/Ticket_User` | `ticket_id` y `users` obligatorios. Cada usuario requiere `users_id`; admite `type`, `use_notification`, `is_dynamic`, `alternative_email`. | Añadir usuarios al ticket. | Quitar o editar asignaciones existentes. |
| Asignar grupos a Ticket | `ticket_group_assign` | `/Group_Ticket` | `ticket_id` y `groups` obligatorios. Cada grupo requiere `groups_id`; admite `type`, `use_notification`, `is_dynamic`, `alternative_email`. | Añadir grupos al ticket. | Quitar o editar asignaciones existentes. |
| Vincular Change a Ticket | `ticket_change_link` | `/Change_Ticket` | `ticket_id` y `change_id` obligatorios; `additional` opcional. | Crear relación Ticket–Change. | Eliminar una relación existente. |
| Desvincular Change de Ticket | `ticket_change_unlink` | `/Change_Ticket/{link_id}` | `ticket_id` y `link_id` obligatorios; `purge`, `keep_history` opcionales. | Eliminar relación Ticket–Change. | Eliminar el ticket o el cambio. |
| Agregar seguimiento a Change | `change_follow_add` | `/ITILFollowup` | `change_id` y `content` obligatorios; `is_private`, `additional` opcionales. | Crear un seguimiento asociado al cambio. | Editar o eliminar un seguimiento existente. |
| Listar seguimientos de Change | `change_follow_list` | `/Change/{change_id}/ITILFollowup` | `change_id` obligatorio; opciones de listado. | Listar seguimientos del cambio. | Crear seguimientos; usar `change_follow_add`. |
| Agregar solución a Change | `change_solution_add` | `/ITILSolution` | `change_id` y `content` obligatorios; `solution_type_id`, `additional` opcionales. | Registrar una solución del cambio. | Editar o eliminar una solución existente. |
| Listar soluciones de Change | `change_solution_list` | `/Change/{change_id}/ITILSolution` | `change_id` obligatorio; opciones de listado. | Listar soluciones del cambio. | Crear soluciones; usar `change_solution_add`. |
| Asignar usuarios a Change | `change_user_assign` | `/Change_User` | `change_id` y `users` obligatorios. Cada usuario requiere `users_id`; admite `type`, `use_notification`, `is_dynamic`, `alternative_email`. | Añadir usuarios al cambio. | Quitar o editar asignaciones existentes. |
| Asignar grupos a Change | `change_group_assign` | `/Change_Group` | `change_id` y `groups` obligatorios. Cada grupo requiere `groups_id`; admite `type`, `use_notification`, `is_dynamic`, `alternative_email`. | Añadir grupos al cambio. | Quitar o editar asignaciones existentes. |
| Vincular Ticket a Change | `change_ticket_link` | `/Change_Ticket` | `change_id` y `ticket_id` obligatorios; `additional` opcional. | Crear relación Change–Ticket. | Eliminar una relación existente. |
| Desvincular Ticket de Change | `change_ticket_unlink` | `/Change_Ticket/{link_id}` | `change_id` y `link_id` obligatorios; `purge`, `keep_history` opcionales. | Eliminar relación Change–Ticket. | Eliminar el cambio o el ticket. |
| Seguimientos de Ticket | `item_subitem_list` | `/Ticket/{id}/ITILFollowup` | `itemtype`, `id`, `subtype` obligatorios; `limit`, `offset`, `sort_by`, `order`, `output`, `fields` opcionales. | Listar seguimientos del ticket. | Obtener, crear, editar o eliminar un seguimiento con estas herramientas. |
| Soluciones de Ticket | `item_subitem_list` | `/Ticket/{id}/ITILSolution` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar soluciones del ticket. | Obtener, crear, editar o eliminar una solución con estas herramientas. |
| Usuarios de Ticket | `item_subitem_list` | `/Ticket/{id}/Ticket_User` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar usuarios relacionados con el ticket. | Añadir, modificar o quitar usuarios. |
| Grupos de Ticket | `item_subitem_list` | `/Ticket/{id}/Group_Ticket` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar grupos relacionados con el ticket. | Añadir, modificar o quitar grupos. |
| Cambios de Ticket | `item_subitem_list` | `/Ticket/{id}/Change_Ticket` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar relaciones entre el ticket y cambios. | Crear o eliminar relaciones. |
| Documentos de Ticket | `item_subitem_list` | `/Ticket/{id}/Document_Item` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar documentos vinculados al ticket. | Subir, vincular o desvincular documentos. |
| Seguimientos de Change | `item_subitem_list` | `/Change/{id}/ITILFollowup` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar seguimientos del cambio. | Obtener, crear, editar o eliminar un seguimiento con estas herramientas. |
| Soluciones de Change | `item_subitem_list` | `/Change/{id}/ITILSolution` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar soluciones del cambio. | Obtener, crear, editar o eliminar una solución con estas herramientas. |
| Usuarios de Change | `item_subitem_list` | `/Change/{id}/Change_User` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar usuarios relacionados con el cambio. | Añadir, modificar o quitar usuarios. |
| Grupos de Change | `item_subitem_list` | `/Change/{id}/Change_Group` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar grupos relacionados con el cambio. | Añadir, modificar o quitar grupos. |
| Tickets de Change | `item_subitem_list` | `/Change/{id}/Change_Ticket` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar relaciones entre el cambio y tickets. | Crear o eliminar relaciones. |
| Documentos de Change | `item_subitem_list` | `/Change/{id}/Document_Item` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar documentos vinculados al cambio. | Subir, vincular o desvincular documentos. |
