from flask import Flask, request
from flask_cors import CORS
from pymongo import MongoClient
from routes.user import user_blueprint

app = Flask(__name__)

# conexion a MongoDB, ajustar según sea necesario cada uno localmente
# (luego Jhon lo desplegará en la nube) 
client = MongoClient('mongodb://localhost:27017/')
db = client['LEARN']
app.db = db

# Habilitamos CORS para integrarlo con el frontend
CORS(app)

# Habilitamos las rutas
app.register_blueprint(user_blueprint, url_prefix='/api/profile')

# Endpoint de seguridad
@app.route('/health')   
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    app.run(debug=True)