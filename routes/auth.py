from flask import Blueprint, jsonify, current_app, request
from bson import ObjectId
from datetime import datetime

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/sync-user', methods=['POST'])
def sync_firebase_user():
    """
    Endpoint para crear o sincronizar un usuario de Firebase en MongoDB
    
    Espera un JSON con la siguiente estructura:
    {
        "uid": "firebase_user_id"
    }
    """
    try:
        db = current_app.db
        data = request.get_json()
        
        # Validar datos requeridos
        if not data:
            return jsonify({'error': 'No se enviaron datos'}), 400
        
        firebase_uid = data.get('uid')
        
        if not firebase_uid:
            return jsonify({'error': 'Se requiere uid'}), 400
        
        # Buscar si el usuario ya existe por firebaseUid
        existing_user = db.users.find_one({'firebaseUid': firebase_uid})
        
        if existing_user:
            # Usuario existe - actualizar lastConnection en el streak
            db.users.update_one(
                {'_id': existing_user['_id']},
                {'$set': {'information.streak.lastConnection': datetime.now()}}
            )
            
            return jsonify({
                'message': 'Usuario sincronizado exitosamente',
                'userId': str(existing_user['_id']),
                'isNewUser': False,
                'user': {
                    'id': str(existing_user['_id']),
                    'firebaseUid': firebase_uid,
                    'type': existing_user.get('type', False)
                }
            }), 200
        
        else:
            # Usuario no existe - crear nuevo con type automáticamente en false
            new_user = {
                'firebaseUid': firebase_uid,
                'type': False,  # false = estudiante (por defecto)
                'followers': [],
                'following': [],
                'information': {
                    'streak': {
                        'current': 0,
                        'lastConnection': datetime.now()
                    },
                    'achievements': [],
                    'lescoSkills': 0,
                    'librasSkills': 0,
                    'lescoLevel': 0,
                    'librasLevel': 0,
                    'myCourses': []
                }
            }
            
            result = db.users.insert_one(new_user)
            
            return jsonify({
                'message': 'Usuario creado exitosamente',
                'userId': str(result.inserted_id),
                'isNewUser': True,
                'user': {
                    'id': str(result.inserted_id),
                    'firebaseUid': firebase_uid,
                    'type': False
                }
            }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_blueprint.route('/user-by-firebase/<firebase_uid>', methods=['GET'])
def get_user_by_firebase_uid(firebase_uid):
    """
    Obtener usuario de MongoDB usando su Firebase UID
    """
    try:
        db = current_app.db
        
        user = db.users.find_one({'firebaseUid': firebase_uid})
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify({
            'userId': str(user['_id']),
            'firebaseUid': user.get('firebaseUid'),
            'type': user.get('type', False)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

