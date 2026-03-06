# Documentación del Proyecto Sésamo Backend

## 📌 Descripción General

**Sésamo Backend** es una API RESTful desarrollada con **FastAPI** y **Python 3.12+**, diseñada para gestionar una plataforma educativa. Permite la administración de usuarios, roles, escuelas, cuestionarios y respuestas de los estudiantes.

La arquitectura sigue el patrón **Repository**, separando claramente la lógica de negocio, el acceso a datos y la definición de la API.

---

## 🛠️ Stack Tecnológico

- **Lenguaje**: Python 3.12+
- **Framework Web**: FastAPI (Alto rendimiento, validación automática con Pydantic)
- **ORM**: SQLAlchemy (Mapeo Objeto-Relacional para MySQL/MariaDB)
- **Base de Datos**: MySQL (Driver `pymysql`)
- **Validación de Datos**: Pydantic v2
- **Gestión de Paquetes**: `uv` (Reemplazo moderno y rápido para pip/poetry)
- **Autenticación**: JWT (JSON Web Tokens) con `pyjwt` y `bcrypt` para hashing de contraseñas.
- **Servidor ASGI**: Uvicorn

---

## 📂 Estructura del Proyecto

La estructura del proyecto está organizada para facilitar la escalabilidad y el mantenimiento:

```
sesamoBack/
├── app/
│   ├── main.py                 # Punto de entrada de la aplicación (FastAPI instance)
│   ├── config.py               # Configuración global y variables de entorno (Settings)
│   ├── models/                 # Modelos de Base de Datos (SQLAlchemy)
│   │   ├── user.py             # Usuarios (Admin, Estudiante)
│   │   ├── role.py             # Roles del sistema
│   │   ├── school.py           # Escuelas registradas
│   │   ├── category.py         # Categorías de cuestionarios (Matemáticas, Ciencias, etc.)
│   │   ├── questionnaire.py    # Cuestionarios
│   │   ├── question.py         # Preguntas individuales
│   │   ├── answer_option.py    # Opciones de respuesta (A, B, C, D)
│   │   └── user_response.py    # Respuestas enviadas por los estudiantes
│   ├── schemas/                # Schemas Pydantic (DTOs para Request/Response)
│   │   ├── auth.py             # Login, Token
│   │   └── [entity].py         # Schemas CRUD para cada entidad
│   ├── repositories/           # Capa de Acceso a Datos (Lógica de DB)
│   │   └── [entity]_repository.py
│   ├── routers/                # Endpoints de la API (Controladores)
│   │   ├── auth.py             # Login y Registro
│   │   └── [entity].py         # CRUD endpoints
│   └── utilities/              # Utilidades transversales
│       ├── db.py               # Configuración de conexión a DB y Seeding inicial
│       ├── jwt.py              # Generación y validación de tokens, dependencias de seguridad
│       └── encription.py       # Utilidades de cifrado (Fernet, Bcrypt)
├── .env                        # Variables de entorno (No incluido en control de versiones)
├── pyproject.toml              # Definición de dependencias del proyecto (uv/pip)
└── DOCUMENTATION.md            # Este archivo
```

---

## 🗄️ Modelo de Datos (Base de Datos)

El sistema gestiona las siguientes entidades principales y sus relaciones:

1.  **Users (`users`)**:
    - Almacena la información de todos los usuarios del sistema.
    - Relaciones: `Role` (Muchos a Uno), `School` (Muchos a Uno).
    - Campos clave: `email` (único), `password` (hash bcrypt), `role_id`, `school_id`.

2.  **Roles (`roles`)**:
    - Define los niveles de acceso.
    - Roles por defecto: `Admin` (ID 1), `Estudiante` (ID 2).

3.  **Schools (`schools`)**:
    - Instituciones educativas registradas en la plataforma.

4.  **Content (Cuestionarios)**:
    - **Categories (`categories`)**: Agrupan los cuestionarios (ej. "Matemáticas").
    - **Questionnaires (`questionnaires`)**: Conjunto de preguntas. Relación con `Category`.
    - **Questions (`questions`)**: Preguntas individuales. Relación con `Questionnaire`.
    - **AnswerOptions (`answer_options`)**: Opciones de respuesta para una pregunta.
      - Campo `is_correct`: Indica si es la respuesta correcta (Visible solo para Admins).

5.  **UserResponses (`user_responses`)**:
    - Registro de las respuestas enviadas por los estudiantes a los cuestionarios.

---

## 🔐 Autenticación y Seguridad

### Sistema JWT

- **Login (`POST /auth/login`)**:
  - Recibe `email` y `password`.
  - Devuelve un `access_token` (JWT).
  - **Payload del Token**: Incluye `sub` (email), `id`, `name`, `last_name`, `role_id`, `school_id`.
- **Protección de Rutas**:
  - `HTTPBearer`: Esquema de seguridad estándar. En Swagger UI solo se requiere pegar el token.

### Roles y Permisos

- **Admin (`role_id=1`)**:
  - Acceso total (Lectura/Escritura) a todos los recursos.
  - Gestión de Usuarios, Escuelas y Roles.
  - Creación y edición de Cuestionarios y Respuestas Correctas.
- **Estudiante (`role_id=2`)**:
  - Lectura de Cuestionarios y Preguntas.
  - Envío de sus propias respuestas (`UserResponses`).
  - **Restricción**: No pueden ver el campo `is_correct` de las opciones de respuesta ni acceder a endpoints administrativos.

---

## 🚀 Instalación y Ejecución

### Prerrequisitos

- Python 3.12 o superior.
- Gestor de paquetes `uv` (recomendado) o `pip`.
- Servidor de Base de Datos MySQL/MariaDB en ejecución.

### 1. Configuración de Entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```ini
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=3306
DB_NAME=sesamo
ENCRYPTION_KEY=clave_generada_con_fernet
SECRET_KEY=clave_secreta_jwt_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 2. Instalación de Dependencias

Usando `uv` (Recomendado):

Este comando creará automáticamente un entorno virtual (`.venv`) e instalará todas las dependencias definidas en el proyecto.

```bash
uv sync
```

O usando `pip`:

Si prefieres usar `pip`, es **altamente recomendable** crear primero un entorno virtual para evitar conflictos entre versiones de librerías locales y las del sistema.

1.  **Crear el entorno virtual** (puedes usar `venv` o `virtualenv`):

    ```bash
    python -m venv venv
    # O si tienes virtualenv instalado:
    # python -m virtualenv venv
    ```

2.  **Activar el entorno virtual**:
    - En macOS/Linux:
      ```bash
      source venv/bin/activate
      ```
    - En Windows:
      ```bash
      venv\Scripts\activate
      ```

3.  **Instalar las dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Crear Base de Datos (Opcional)

Si la base de datos aún no existe en tu servidor MySQL, puedes ejecutar el script de creación automática:

```bash
# Usando uv
uv run python create_db.py

# Usando python (con entorno virtual activo)
python create_db.py
```

### 4. Ejecutar la Aplicación

Modo desarrollo (con recarga automática):

```bash
# Usando uv
uv run uvicorn app.main:app --reload

# Usando uvicorn directamente (con entorno virtual activo)
uvicorn app.main:app --reload
```

La aplicación estará disponible en `http://127.0.0.1:8000/api/v1`.

---

## 📖 Documentación de la API

FastAPI genera automáticamente documentación interactiva:

- **Swagger UI**: [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs) - Interfaz gráfica para probar endpoints.
- **ReDoc**: [http://127.0.0.1:8000/api/v1/redoc](http://127.0.0.1:8000/api/v1/redoc) - Documentación alternativa más limpia.

### Principales Endpoints

| Método | Endpoint           | Descripción                    | Acceso                            |
| :----- | :----------------- | :----------------------------- | :-------------------------------- |
| `POST` | `/auth/login`      | Iniciar sesión y obtener token | Público                           |
| `POST` | `/auth/register`   | Registrar nuevo estudiante     | Público                           |
| `GET`  | `/users/`          | Listar todos los usuarios      | **Admin**                         |
| `GET`  | `/questionnaires/` | Listar cuestionarios           | Auth (Todos)                      |
| `POST` | `/questionnaires/` | Crear cuestionario             | **Admin**                         |
| `GET`  | `/answer-options/` | Ver opciones de respuesta      | Auth (Sin `is_correct`)           |
| `POST` | `/answer-options/` | Crear opción de respuesta      | **Admin** (Devuelve `is_correct`) |

---

## 🌱 Datos Iniciales (Seeding)

Al iniciar la aplicación, el sistema verifica y crea automáticamente datos esenciales si no existen:

- Roles (Admin, Estudiante, etc.)
- Escuelas de ejemplo.
- Categorías de ejemplo.
- Usuarios de prueba (`admin@sesamo.com`, `student@sesamo.com`).
- Un cuestionario de prueba con preguntas y respuestas.

---

## 🤝 Flujo de Desarrollo (Cómo agregar una nueva funcionalidad)

1.  **Modelo (`app/models/`)**: Definir la clase SQLAlchemy y la tabla en la DB.
2.  **Schema (`app/schemas/`)**: Definir los modelos Pydantic para `Create`, `Update` y `Response`.
3.  **Repositorio (`app/repositories/`)**: Implementar la lógica CRUD usando SQLAlchemy.
4.  **Router (`app/routers/`)**: Crear los endpoints HTTP y conectar con el repositorio.
5.  **Main (`app/main.py`)**: Registrar el nuevo router.
