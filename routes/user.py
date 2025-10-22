from flask import Blueprint, jsonify, current_app, request
from bson import ObjectId
from datetime import datetime

user_blueprint = Blueprint('user', __name__)

# Endpoint de prueba para crear usuario y hacer tests
@user_blueprint.route('/test/create-user', methods=['POST'])
def create_test_user():

    try:
        db = current_app.db
        
        # Obtener datos del request o usar valores por defecto
        data = request.json if request.json else {}
        
        test_user = {
            "type": data.get('type', False),  
            "name": data.get('name', 'Usuario de Prueba'),
            "followers": [],
            "following": [],
            "information": {
                "streak": {
                    "current": data.get('streakDays', 2),
                    "lastConnection": datetime.now()
                },
                "achievements": [],
                "lescoSkills": data.get('lescoSkills', 1),
                "librasSkills": data.get('librasSkills', 1),
                "lescoLevel": data.get('lescoLevel', 1),
                "librasLevel": data.get('librasLevel', 1),
                "myCourses": []
            }
        }
        
        result = db.users.insert_one(test_user)
        user_id = str(result.inserted_id)
        
        return jsonify({
            'message': 'Usuario de prueba creado exitosamente',
            'user_id': user_id,
            'profile_url': f'http://localhost:5000/api/profile/{user_id}',
            'user_data': {
                'name': test_user['name'],
                'type': 'Teacher' if test_user['type'] else 'Student'
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

