from flask import Flask, request, current_app, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from routes.user import user_blueprint
from routes.auth import auth_blueprint
from routes.exercises import exercises_bp
from routes.news import news_bp
from routes.coursesStudent import coursesStudent_blueprint  
from routes.lessonsStudent import lessonsStudent_blueprint
from routes.homeStudent import homeStudent_blueprint

app = Flask(__name__)

#Variable global para definir el lenguaje por defecto
app.config['LESCO'] = False

# conexion a MongoDB, ajustar según sea necesario cada uno localmente
# (luego Jhon lo desplegará en la nube) 
client = MongoClient('mongodb://localhost:27017/')
db = client['LEARN']
app.db = db

# Habilitamos CORS para integrarlo con el frontend
CORS(app)

# Habilitamos las rutas
app.register_blueprint(auth_blueprint, url_prefix='/api/auth')
app.register_blueprint(user_blueprint, url_prefix='/api/profile')
app.register_blueprint(exercises_bp, url_prefix='/api/exercises')
app.register_blueprint(news_bp, url_prefix="/api/news")
app.register_blueprint(coursesStudent_blueprint, url_prefix='/api')
app.register_blueprint(lessonsStudent_blueprint, url_prefix='/api')
app.register_blueprint(homeStudent_blueprint, url_prefix='/api')

# Endpoint de seguridad
@app.route('/health')   
def health():
    return {'status': 'ok'}, 200

# Endpoint para alternar el valor de LESCO dependiendo del valor que se le de
@app.route('/api/language', methods=['POST'])
def set_lesco():
    try:
        data = request.get_json()
        value = data.get('value')
        
        if value not in [0, 1]:
            return jsonify({'error': 'Value must be 0 or 1'}), 400
        
        # Establecer el valor de LESCO basado en el número
        current_app.config['LESCO'] = bool(value)  # 1 → True, 0 → False
        
        return jsonify({
            'message': 'LESCO set successfully',
            'newValue': current_app.config['LESCO']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    




if __name__ == '__main__':
    app.run(debug=True)