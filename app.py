from flask import Flask, request
from flask_cors import CORS
from pymongo import MongoClient
from routes.user import user_blueprint
from routes.exercises import exercises_bp

from routes.coursesStudent import coursesStudent_blueprint  
from routes.lessonsStudent import lessonsStudent_blueprint
from routes.homeStudent import homeStudent_blueprint
app = Flask(__name__)

#Variable global para definir el lenguaje por defecto
app.config['LESCO'] = True

# conexion a MongoDB, ajustar según sea necesario cada uno localmente
# (luego Jhon lo desplegará en la nube) 
client = MongoClient('mongodb://localhost:27017/')
db = client['LEARN']
app.db = db

# Habilitamos CORS para integrarlo con el frontend
CORS(app)

# Habilitamos las rutas
app.register_blueprint(user_blueprint, url_prefix='/api/profile')
app.register_blueprint(exercises_bp, url_prefix='/api/exercises')
app.register_blueprint(coursesStudent_blueprint, url_prefix='/api')
app.register_blueprint(lessonsStudent_blueprint, url_prefix='/api')
app.register_blueprint(homeStudent_blueprint, url_prefix='/api')

# Endpoint de seguridad
@app.route('/health')   
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    app.run(debug=True)