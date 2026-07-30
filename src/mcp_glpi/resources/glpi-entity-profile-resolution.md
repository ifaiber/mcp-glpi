# Resolución de `entity_id` / `profile_id` por nombre

Cualquier herramienta que acepte `entity_id` y/o `profile_id` (todas las `ticket_*`, `change_*`, `file_*`, y las genéricas `item_list`/`item_get`/`item_delete`/`item_subitem_list`) acepta, ademas de un id numérico, el **nombre** de la entidad o del perfil como texto. Cuando el valor no es numérico, el servidor lo busca entre las entidades/perfiles del usuario logueado y lo resuelve automáticamente a su id antes de ejecutar la operación.

No enviar un `entity_id`/`profile_id` (u omitirlo/vacío) sigue significando "usar el activo por defecto de la sesión", igual que antes. Un id numérico sigue funcionando exactamente igual que antes: esta resolución solo se activa cuando el valor recibido no es un número.

## Solo se da el nombre del perfil

Si se indica `profile_id` con un nombre y **no** se indica `entity_id`:

1. Se busca ese nombre entre los perfiles del usuario (los mismos que devuelve `profile_list`).
2. Se cambia al perfil encontrado.
3. Como no se indicó ninguna entidad, se toma automáticamente la **primera** entidad de ese perfil y se opera en ella.

```json
{"itemtype":"Ticket","limit":5,"profile_id":"Desarrollador"}
```

La respuesta exitosa incluye un campo `resolution_notes` (lista de strings) explicando qué se resolvió, por ejemplo:

```json
{
  "ok": true,
  "command": "item_list",
  "data": {"...": "..."},
  "resolution_notes": [
    "profile_id: nombre de perfil 'Desarrollador' resuelto a id 6.",
    "entity_id: no se indico; se selecciono automaticamente la primera entidad del perfil 'Desarrollador': 'Desarrollo' (id 6)."
  ]
}
```

Leer siempre `resolution_notes` cuando esté presente para saber en qué entidad terminó operando la llamada: la elección de "primera entidad" es automática y puede no ser la que se esperaba si el perfil tiene varias.

## Solo se da el nombre de la entidad

Si se indica `entity_id` con un nombre y **no** se indica `profile_id`:

1. Se listan los perfiles del usuario y se busca ese nombre de entidad entre las entidades de **todos** ellos.
2. Si aparece en un solo perfil, se resuelven `profile_id` y `entity_id` a partir de ese match (perfil primero, entidad despues).
3. Si aparece en más de un perfil (nombre ambiguo), la llamada falla con un error de validación en vez de adivinar — ver más abajo.

```json
{"itemtype":"Ticket","limit":5,"entity_id":"Desarrollo"}
```

Si además se indica `profile_id` (numérico o por nombre) junto con un `entity_id` por nombre, la búsqueda de la entidad se acota a las entidades de **ese** perfil unicamente, no a todos los perfiles del usuario.

## Ambigüedad: pedir más contexto, no adivinar

Cuando un nombre de perfil coincide con más de un perfil, o un nombre de entidad coincide con entidades de más de un perfil, la herramienta responde con `"ok": false` y `"error": {"type": "validation_error", ...}`, listando las coincidencias encontradas (perfil y/o entidad con sus ids). No se elige ninguna de forma arbitraria.

Ante ese error, dar más contexto en el siguiente intento: indicar el id numérico directamente, o combinar `profile_id` (para acotar a un perfil concreto) con el nombre de la entidad.

Lo mismo aplica si el nombre no coincide con ningún perfil/entidad: error de validación explícito remitiendo a `profile_list`/`entity_list` para ver los valores disponibles, en vez de continuar con un valor por defecto silencioso.

## Notas de implementación relevantes para interpretar los resultados

- La búsqueda de nombre es exacta e insensible a mayúsculas/minúsculas; no hace coincidencia parcial ni difusa.
- El perfil siempre se resuelve/cambia antes que la entidad (igual que el resto de las herramientas): el perfil activo determina los permisos con los que luego se valida/aplica el cambio de entidad.
- `resolution_notes` solo aparece en la respuesta cuando realmente hubo una resolución por nombre; si `entity_id`/`profile_id` eran numéricos, estaban vacíos, o no se indicaron, la respuesta no incluye ese campo.
