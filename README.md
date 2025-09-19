# Servidor MCP de Pruebas

Un servidor Model Context Protocol (MCP) de pruebas implementado en Python, diseñado para testing y desarrollo de integraciones MCP.

## 🚀 Características

- **6 Herramientas de prueba** para diferentes casos de uso
- **2 Prompts dinámicos** para testing interactivo  
- **2 Recursos de información** sobre el servidor
- **Operaciones de archivo seguras** limitadas al directorio del proyecto
- **Cálculos matemáticos** con funciones básicas
- **Logging configurable** para debugging

## 📋 Herramientas Disponibles

### 🔧 Herramientas Básicas

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `echo` | Devuelve el mensaje enviado | `message: string` |
| `get_time` | Obtiene fecha/hora actual | `format?: string` |
| `calculate` | Evalúa expresiones matemáticas | `expression: string` |

### 📁 Herramientas de Archivo

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `write_file` | Escribe contenido a un archivo | `filename: string, content: string` |
| `read_file` | Lee el contenido de un archivo | `filename: string` |
| `list_files` | Lista archivos en un directorio | `directory?: string, pattern?: string` |

## 💬 Prompts Disponibles

- **`test_prompt`** - Prompt de prueba configurable con parámetro `topic`
- **`help_prompt`** - Ayuda completa sobre el servidor y sus funcionalidades

## 📊 Recursos Disponibles

- **`test://info`** - Información detallada del servidor (JSON)
- **`test://config`** - Configuración actual del servidor (JSON)

## 🛠️ Instalación

### Usando pip (recomendado)

```bash
# Clonar o descargar el proyecto
cd mcp-glpi

# Instalar el paquete en modo desarrollo
pip install -e .
```

### Instalación manual

```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# Windows:
.venv\Scripts\activate
# Unix/macOS:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🚀 Uso

### Ejecutar el servidor

```bash
# Usando el comando instalado
mcp-glpi

# O directamente con Python
python -m mcp_test.server

# Con logging detallado
mcp-glpi --verbose
```

### Configuración en Claude Desktop

Añade esta configuración a tu archivo `claude_desktop_config.json`:

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

### Configuración en otros clientes MCP

El servidor usa stdio para comunicación, por lo que es compatible con cualquier cliente MCP que soporte este método.

## 📝 Ejemplos de Uso

### Ejemplo 1: Testing Básico
```
Usuario: "Usa la herramienta echo para decir 'Hola MCP!'"
Servidor: "Echo: Hola MCP!"
```

### Ejemplo 2: Cálculos
```
Usuario: "Calcula 2 + 2 * 3"
Servidor: "Resultado: 2 + 2 * 3 = 8"

Usuario: "¿Cuánto es sqrt(16) + sin(pi/2)?"
Servidor: "Resultado: sqrt(16) + sin(pi/2) = 5.0"
```

### Ejemplo 3: Operaciones de Archivo
```
Usuario: "Crea un archivo llamado 'test.txt' con contenido 'Hola mundo'"
Servidor: "Archivo 'test.txt' escrito exitosamente (10 caracteres)"

Usuario: "Lee el archivo test.txt"
Servidor: "Contenido de 'test.txt': Hola mundo"
```

### Ejemplo 4: Fecha y Hora
```
Usuario: "¿Qué hora es?"
Servidor: "Fecha y hora actual: 2025-09-17T10:30:00.123456"

Usuario: "Dame la fecha en formato legible"
Servidor: "Fecha y hora actual: 2025-09-17 10:30:00"
```

## 🔧 Desarrollo

### Estructura del Proyecto

```
mcp-glpi/
├── src/mcp_test/
│   ├── __init__.py
│   └── server.py          # Servidor MCP principal
├── pyproject.toml         # Configuración del proyecto
├── requirements.txt       # Dependencias
├── README.md             # Este archivo
└── .gitignore           # Archivos a ignorar
```

### Añadir Nuevas Herramientas

1. Añade la definición de la herramienta en `list_tools()`
2. Implementa la lógica en `call_tool()`
3. Añade tests si es necesario

### Configuración de Seguridad

El servidor incluye medidas de seguridad básicas:
- Restricción de operaciones de archivo al directorio actual y subdirectorios
- Evaluación segura de expresiones matemáticas
- Validación de entrada en todas las herramientas

## 🧪 Testing

Para probar el servidor:

```bash
# Ejecutar el servidor en modo verbose para debugging
python -m mcp_test.server --verbose

# En otro terminal, usar un cliente MCP o testing manual
# El servidor mostrará logs detallados de todas las operaciones
```

## 📚 Dependencias

- **mcp** - Implementación del protocolo MCP
- **click** - Interface de línea de comandos
- **pydantic** - Validación de datos

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-herramienta`)
3. Commit tus cambios (`git commit -am 'Añadir nueva herramienta'`)
4. Push a la rama (`git push origin feature/nueva-herramienta`)
5. Crea un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Si tienes problemas o preguntas:

1. Revisa los logs del servidor con `--verbose`
2. Verifica que todas las dependencias estén instaladas
3. Asegúrate de que el cliente MCP esté configurado correctamente
4. Crea un issue en el repositorio del proyecto

---

¡Feliz testing con MCP! 🎉