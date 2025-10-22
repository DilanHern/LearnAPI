# LearnAPI

API REST desarrollada con Flask y MongoDB para la plataforma de aprendizaje de lenguaje de señas (LESCO y LIBRAS).

## Estructura del Proyecto

```
LearnAPI/
├── app.py                  # Archivo principal de la aplicación Flask
├── CreateLEARNDB.js        # Script para crear la estructura de la base de datos
├── requirements.txt        # Dependencias de Python
├── README.md              # Documentación del proyecto
└── routes/                # Módulos de rutas de la API
    └── user.py            # Endpoints relacionados con usuarios y perfiles
```

### Descripción de Archivos

#### `app.py`
Archivo principal que configura y ejecuta la aplicación Flask.

**Funciones principales:**
- Inicializa la aplicación Flask
- Configura la conexión a MongoDB (base de datos `LEARN`), por el momento utilizarlo **local**, luego Jhon la desplegará en la nube una vez esté lista
- Habilita CORS para permitir peticiones desde el frontend
- Registra los blueprints 

**Endpoints globales:**
- `GET /health` - Verificación del estado del servidor

#### `CreateLEARNDB.js`
Script de MongoDB Shell para crear la estructura completa de la base de datos con validaciones.

**Colecciones creadas:**
1. **users** - Información de usuarios (estudiantes y profesores)
2. **achievements** - Logros obtenidos por usuarios
3. **premadeComments** - Comentarios predefinidos del sistema
4. **news** - Publicaciones en el feed social
5. **courses** - Cursos creados por profesores
6. **completedCourses** - Historial de cursos completados
7. **forums** - Foros de discusión por lección
8. **teacherStatistics** - Estadísticas de profesores
9. **studentStatistics** - Estadísticas de estudiantes

**Uso:**
```bash
# 1. Abrir MongoDB Compass
# 2. Conectarse al servidor local
# 3. Abrir la pestaña MONGOSH
# 4. Ejecutar: use LEARN
# 5. Copiar y pegar todo el código del archivo
```

#### `routes/user.py`
Módulo que contiene todos los endpoints relacionados con perfiles de usuario.


#### `requirements.txt`
Lista de dependencias de Python necesarias para el proyecto.

```txt
Flask==3.0.0           # Framework web
flask-cors==4.0.0      # Manejo de CORS para integración con frontend
pymongo==4.6.1         # Driver de MongoDB para Python
```

## Tecnologías Utilizadas

- **Flask 3.0.0** - Framework web de Python
- **MongoDB** - Base de datos NoSQL
- **PyMongo 4.6.1** - Driver oficial de MongoDB para Python
- **Flask-CORS 4.0.0** - Extensión para habilitar CORS
