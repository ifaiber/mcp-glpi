# Elementos genéricos de GLPI

Usar `item_list`, `item_get`, `item_delete` e `item_subitem_list` para trabajar con elementos y sub-elementos genéricos de GLPI. Indicar siempre el `itemtype` con la capitalización de GLPI, por ejemplo `Ticket`, `Change`, `Document`, `Computer`, `Monitor` o `Software`.

Estas herramientas son de **descubrimiento, consulta y eliminación genérica**. Cuando la operación necesite crear, actualizar, asignar, comentar, solucionar, relacionar o transferir archivos, usar las herramientas específicas `ticket_*`, `change_*` y `file_*` — ver el recurso `mcp-glpi://docs/glpi-tools`.

## Descubrir tipos y subtipos

`item_type_list`/`item_subtype_list` devuelven una lista de **referencia** (itemtypes/subtypes ya probados), no una lista cerrada de valores permitidos: `item_list`/`item_get`/`item_delete`/`item_subitem_list` aceptan **cualquier** itemtype o subtype de GLPI, esté o no en esa lista. Usar `item_type_list` cuando no se conozca de antemano qué itemtype usar, para partir de un valor conocido en vez de adivinar; si ya se sabe el itemtype/subtype exacto (por ejemplo por un `href` de otra respuesta), se puede usar directamente sin pasar por `item_type_list` primero.

Un itemtype/subtype que no existe en GLPI, o uno que existe pero para el que el perfil activo no tiene permiso, no falla con un error de validación previo: falla con el error real que devuelve GLPI (por ejemplo `404`, `400 ERROR_RESOURCE_NOT_FOUND_NOR_COMMONDBTM`, o `403 ERROR_RIGHT_MISSING`), reportado como `runtime_error`. Si eso ocurre, revisar el nombre exacto (capitalización de GLPI) o intentar con otro `profile_id` (ver `mcp-glpi://docs/glpi-entity-profile-resolution`) antes de asumir que el itemtype no existe.

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

## Listar sub-elementos: `item_subitem_list`

Usar `item_subitem_list` para listar los sub-elementos relacionados con un elemento puntual — seguimientos, soluciones, usuarios/grupos asignados, relaciones con otros tickets/cambios, documentos vinculados — una vez identificados el `itemtype`, el `id` y el `subtype` (este último con `item_subtype_list`):

```json
{"itemtype":"Ticket","id":123,"subtype":"Document_Item"}
```

Acepta las mismas opciones de listado que `item_list` (`limit`, `offset`, `sort_by`, `order`, `output`, `fields`), pero no `filters`, `expand_dropdowns` ni `include_deleted`: la API de sub-items de GLPI no los expone.

`item_subitem_list` es de solo lectura: para crear o eliminar seguimientos, soluciones, asignaciones o relaciones, usar las herramientas específicas correspondientes (ver `mcp-glpi://docs/glpi-tools`).

## Eliminar un elemento: `item_delete`

Usar `item_delete` únicamente después de confirmar el `itemtype` y el `id` correctos con `item_list` o `item_get`:

```json
{"itemtype":"Change","id":123}
```

La eliminación normal envía el elemento a la papelera. Incluir `purge: true` solo si se solicita explícitamente una eliminación definitiva. Incluir `keep_history: true` cuando se deba conservar el historial de GLPI.

`item_delete` está disponible en el servidor. Sus parámetros obligatorios son `itemtype` e `id`.

## Activos y gestión (`Computer`, `Monitor`, `Software`, ...)

Además de `Ticket`/`Change`/`Document`, el catálogo soporta itemtypes de activos y gestión, verificados contra una instancia GLPI real: `Computer`, `Monitor`, `Software`, `SoftwareVersion`, `Project`, `ProjectTask`, `KnowbaseItem`, `Reminder`, `ContractType`, `Manufacturer`, `DeviceSimcard`. Se usan igual que `Ticket`/`Change` — mismo `item_list`/`item_get`/`item_delete`/`item_subitem_list`, mismo flujo de descubrimiento con `item_type_list`/`item_subtype_list`.

`Computer` y `Monitor` en particular suelen requerir un perfil GLPI con derechos de inventario/activos, distinto del perfil de soporte que usa la sesión por defecto. Si `item_list`/`item_get` devuelven un error `403`/`ERROR_RIGHT_MISSING` para uno de estos itemtypes, volver a intentar pasando `profile_id` con un perfil que sí tenga esos derechos (por id o por nombre — ver el recurso `mcp-glpi://docs/glpi-entity-profile-resolution`); consultar `entityprofile_list` para ver qué perfiles (y entidades asociadas) tiene el usuario.

Esta no es la lista completa de itemtypes de GLPI: es la que ya se probó en esta instancia. Otros itemtypes (`NetworkEquipment`, `Peripheral`, `Printer`, `Contract`, `User`, etc.) también se pueden intentar con `item_list`/`item_get`/`item_delete`/`item_subitem_list` aunque no aparezcan en `item_type_list`; simplemente no hay garantía de que el perfil activo tenga permiso — si falla, el error lo devuelve GLPI (`403`/`400`/`404`), no el servidor.

## Matriz de rutas y capacidades

Construir las rutas relativas sustituyendo `{id}` por el identificador obtenido. Las opciones `entity_id` y `profile_id` se pueden incluir en todas las herramientas de esta tabla salvo `item_type_list` e `item_subtype_list`. Las filas que siguen cubren los itemtypes ya verificados; cualquier otro itemtype de GLPI (no listado aquí) también funciona con `item_list`/`item_get`/`item_delete`/`item_subitem_list` — simplemente no hay fila de referencia porque no se probó en esta instancia.

| Nombre | Herramienta | URL relativa | Opciones | Puede hacer | No puede hacer |
| --- | --- | --- | --- | --- | --- |
| Tipos de elemento | `item_type_list` | — | Sin parámetros. | Listar itemtypes conocidos/verificados (referencia, no una lista cerrada). | Consultar, crear o eliminar elementos. |
| Subtipos de un tipo | `item_subtype_list` | — | `itemtype` opcional. | Listar subtypes conocidos/verificados para un `itemtype` (referencia, no una lista cerrada). | Consultar, crear o eliminar un subelemento. |
| Ticket | `item_list` · `item_get` · `item_delete` | `/Ticket` · `/Ticket/{id}` | `itemtype` obligatorio; `id` para get/delete. Listado: `limit`, `offset`, `sort_by`, `order`, `output`, `fields`, `filters`, `expand_dropdowns`, `include_deleted`. Delete: `purge`, `keep_history`. | Listar, consultar y eliminar tickets. | Crear o actualizar tickets. |
| Change | `item_list` · `item_get` · `item_delete` | `/Change` · `/Change/{id}` | `itemtype` obligatorio; `id` para get/delete. Listado: `limit`, `offset`, `sort_by`, `order`, `output`, `fields`, `filters`, `expand_dropdowns`, `include_deleted`. Delete: `purge`, `keep_history`. | Listar, consultar y eliminar cambios. | Crear o actualizar cambios. |
| Document | `item_list` · `item_get` · `item_delete` | `/Document` · `/Document/{id}` | `itemtype` obligatorio; `id` para get/delete. Listado: `limit`, `offset`, `sort_by`, `order`, `output`, `fields`, `filters`, `expand_dropdowns`, `include_deleted`. Delete: `purge`, `keep_history`. | Listar, consultar y eliminar documentos. | Subir, descargar o modificar archivos. |
| Computer | `item_list` · `item_get` · `item_delete` | `/Computer` · `/Computer/{id}` | Igual que Ticket/Change/Document. Puede requerir `profile_id` con derechos de activos. | Listar, consultar y eliminar equipos. | Crear o actualizar equipos. |
| Monitor | `item_list` · `item_get` · `item_delete` | `/Monitor` · `/Monitor/{id}` | Igual que Computer. Puede requerir `profile_id` con derechos de activos. | Listar, consultar y eliminar monitores. | Crear o actualizar monitores. |
| Software | `item_list` · `item_get` · `item_delete` | `/Software` · `/Software/{id}` | Igual que Ticket/Change/Document. | Listar, consultar y eliminar software (catálogo). | Crear o actualizar software. |
| SoftwareVersion | `item_list` · `item_get` · `item_delete` | `/SoftwareVersion` · `/SoftwareVersion/{id}` | Igual que Ticket/Change/Document. | Listar, consultar y eliminar versiones de software. | Crear o actualizar versiones. |
| Project | `item_list` · `item_get` · `item_delete` | `/Project` · `/Project/{id}` | Igual que Ticket/Change/Document. | Listar, consultar y eliminar proyectos. | Crear o actualizar proyectos. |
| ProjectTask | `item_list` · `item_get` · `item_delete` | `/ProjectTask` · `/ProjectTask/{id}` | Igual que Ticket/Change/Document. | Listar, consultar y eliminar tareas de proyecto. | Crear o actualizar tareas. |
| KnowbaseItem | `item_list` · `item_get` · `item_delete` | `/KnowbaseItem` · `/KnowbaseItem/{id}` | Igual que Ticket/Change/Document. | Listar, consultar y eliminar artículos de la base de conocimiento. | Crear o actualizar artículos. |
| Reminder | `item_list` · `item_get` · `item_delete` | `/Reminder` · `/Reminder/{id}` | Igual que Ticket/Change/Document. | Listar, consultar y eliminar recordatorios. | Crear o actualizar recordatorios. |
| ContractType | `item_list` · `item_get` · `item_delete` | `/ContractType` · `/ContractType/{id}` | Igual que Ticket/Change/Document. Puede requerir `profile_id` con derechos de activos. | Listar, consultar y eliminar tipos de contrato. | Crear o actualizar tipos de contrato. |
| Manufacturer | `item_list` · `item_get` · `item_delete` | `/Manufacturer` · `/Manufacturer/{id}` | Igual que Ticket/Change/Document. Puede requerir `profile_id` con derechos de activos. | Listar, consultar y eliminar fabricantes. | Crear o actualizar fabricantes. |
| DeviceSimcard | `item_list` · `item_get` · `item_delete` | `/DeviceSimcard` · `/DeviceSimcard/{id}` | Igual que Ticket/Change/Document. Puede requerir `profile_id` con derechos de activos. | Listar, consultar y eliminar tarjetas SIM. | Crear o actualizar tarjetas SIM. |
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
| Documentos de Computer | `item_subitem_list` | `/Computer/{id}/Document_Item` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar documentos vinculados al equipo. | Subir, vincular o desvincular documentos. |
| Tickets de Computer | `item_subitem_list` | `/Computer/{id}/Ticket` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar tickets relacionados con el equipo. | Crear tickets. |
| Software instalado en Computer | `item_subitem_list` | `/Computer/{id}/Item_SoftwareVersion` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar versiones de software instaladas en el equipo. | Instalar o desinstalar software. |
| Antivirus de Computer | `item_subitem_list` | `/Computer/{id}/ComputerAntivirus` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar antivirus instalados en el equipo. | Agregar o quitar antivirus. |
| Maquinas virtuales de Computer | `item_subitem_list` | `/Computer/{id}/ComputerVirtualMachine` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar maquinas virtuales alojadas en el equipo. | Crear o eliminar maquinas virtuales. |
| Documentos de Monitor | `item_subitem_list` | `/Monitor/{id}/Document_Item` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar documentos vinculados al monitor. | Subir, vincular o desvincular documentos. |
| Tickets de Monitor | `item_subitem_list` | `/Monitor/{id}/Ticket` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar tickets relacionados con el monitor. | Crear tickets. |
| Documentos de Software | `item_subitem_list` | `/Software/{id}/Document_Item` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar documentos vinculados al software. | Subir, vincular o desvincular documentos. |
| Versiones de Software | `item_subitem_list` | `/Software/{id}/SoftwareVersion` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar versiones registradas del software. | Crear o eliminar versiones. |
| Documentos de Project | `item_subitem_list` | `/Project/{id}/Document_Item` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar documentos vinculados al proyecto. | Subir, vincular o desvincular documentos. |
| Tickets de Project | `item_subitem_list` | `/Project/{id}/Ticket` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar tickets relacionados con el proyecto. | Crear tickets. |
| Tareas de Project | `item_subitem_list` | `/Project/{id}/ProjectTask` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar tareas del proyecto. | Crear o eliminar tareas. |
| Documentos de ProjectTask | `item_subitem_list` | `/ProjectTask/{id}/Document_Item` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar documentos vinculados a la tarea. | Subir, vincular o desvincular documentos. |
| Tickets de ProjectTask | `item_subitem_list` | `/ProjectTask/{id}/Ticket` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar tickets relacionados con la tarea. | Crear tickets. |
| Documentos de KnowbaseItem | `item_subitem_list` | `/KnowbaseItem/{id}/Document_Item` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar documentos vinculados al articulo. | Subir, vincular o desvincular documentos. |
| Tickets de KnowbaseItem | `item_subitem_list` | `/KnowbaseItem/{id}/Ticket` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar tickets relacionados con el articulo. | Crear tickets. |
| Documentos de Reminder | `item_subitem_list` | `/Reminder/{id}/Document_Item` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar documentos vinculados al recordatorio. | Subir, vincular o desvincular documentos. |
| Documentos de Manufacturer | `item_subitem_list` | `/Manufacturer/{id}/Document_Item` | `itemtype`, `id`, `subtype` obligatorios; opciones de listado. | Listar documentos vinculados al fabricante. | Subir, vincular o desvincular documentos. |
