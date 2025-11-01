from flask import Flask, request
from flask_cors import CORS
from pymongo import MongoClient
from routes.user import user_blueprint
from routes.teacherLessons import teacher_lessons_blueprint
from routes.teacherActivities import teacher_activities_blueprint

app = Flask(__name__)

# Variable global para definir el lenguaje por defecto
app.config['LESCO'] = True

# Conexion a MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['LEARN']
app.db = db

# Configuración CORS
CORS(app)

# Habilitamos las rutas
app.register_blueprint(user_blueprint, url_prefix='/api/profile')
app.register_blueprint(teacher_lessons_blueprint, url_prefix='/api/teacher')
app.register_blueprint(teacher_activities_blueprint, url_prefix='/api/teacher')

# ✅ FUNCIÓN PARA MOSTRAR RUTAS (sin before_first_request)
def print_routes():
    print("🚀 Rutas registradas:")
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        print(f"  {rule.rule} -> {methods}")

# Endpoint de seguridad
@app.route('/health')   
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    print("🚀 Servidor Flask iniciado en http://localhost:5000")
    # Mostrar rutas al iniciar
    print_routes()
    app.run(debug=True)