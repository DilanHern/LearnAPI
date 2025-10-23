from flask import Blueprint, jsonify, current_app, request
from bson import ObjectId
from datetime import datetime
import re


user_blueprint = Blueprint('user', __name__)

@user_blueprint.route('/<user_id>', methods=['GET'])
def get_user_profile(user_id):

    try:
        db = current_app.db
        user_oid = ObjectId(user_id)
        
        # Obtener información del usuario
        user = db.users.find_one({'_id': user_oid})
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Calcular estadísticas generales
        summary = calculate_summary(db, user_oid, user)
        
        # Obtener logros
        achievements = get_user_achievements(db, user)
        
        # Obtener estadísticas por idioma
        lesco_stats = get_language_stats(db, user_oid, language=False)  # 0 = LESCO
        libras_stats = get_language_stats(db, user_oid, language=True)  # 1 = LIBRAS
        
        # Construir respuesta
        profile_data = {
            'user': {
                'name': user.get('name', 'Usuario'),
                'initials': get_initials(user.get('name', 'U')),
                'followers': len(user.get('followers', [])),
                'following': len(user.get('following', [])),
                'level': calculate_actual_level(user),
                'skillsProgress': calculate_current_skills(user),
                'totalSkills': calculate_next_level_skills(user)
            },
            'achievements': achievements,
            'summary': summary,
            'lesco': lesco_stats,
            'libras': libras_stats
        }
        
        return jsonify(profile_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def calculate_summary(db, user_id, user):
    info = user.get('information', {})
    streak = info.get('streak', {})
    
    # Calcular nivel total 
    lesco_level = info.get('lescoLevel', 0)
    libras_level = info.get('librasLevel', 0)
    total_level = lesco_level + libras_level
    
    # Calcular habilidades totales
    lesco_skills = info.get('lescoSkills', 0)
    libras_skills = info.get('librasSkills', 0)
    total_skills = lesco_skills + libras_skills
    
    # Contar logros totales
    achievements_count = len(info.get('achievements', []))
    
    return {
        'streakDays': streak.get('current', 0),
        'totalLevel': total_level,
        'totalSkills': total_skills,
        'achievementsEarned': achievements_count
    }


def get_user_achievements(db, user):
    info = user.get('information', {})
    achievement_ids = info.get('achievements', [])
    lesco = current_app.config['LESCO']
    
    # Si no hay logros, retornar lista vacía
    if not achievement_ids:
        return []
    
    # Determinar qué tipo de logros buscar
    achievement_type = False if lesco else True 
    
    # Buscar logros que coincidan con el idioma
    achievements = list(db.achievements.find({
        '_id': {'$in': achievement_ids},
        'type': achievement_type
    }).sort('date', -1))
    
    achievements_list = []
    for achievement in achievements:
        achievements_list.append({
            'id': str(achievement['_id']),
            'title': achievement.get('name', 'Logro'),
            'value': get_achievement_value(achievement),
            'type': 'LESCO' if achievement.get('type') == False else 'LIBRAS'
        })
    
    return achievements_list

# Extraer valor numérico del contenido del logro
def get_achievement_value(achievement):
    content = achievement.get('content', '')
    numbers = re.findall(r'\d+', content)
    return int(numbers[0]) if numbers else 0


def get_language_stats(db, user_id, language):

    # Obtener cursos completados del idioma
    completed = db.completedCourses.find({'userId': user_id})
    
    courses_completed = 0
    lessons_completed = 0
    activities_completed = 0
    total_attempts = 0
    attempt_count = 0
    
    for comp_course in completed:
        # Verificar el idioma del curso
        course = db.courses.find_one({'_id': comp_course['courseId']})
        if course and course.get('language') == language:
            courses_completed += 1
            
            # Contar lecciones y actividades
            completed_lessons = comp_course.get('completedLessons', [])
            lessons_completed += len(completed_lessons)
            
            for lesson in completed_lessons:
                # Obtener información de la lección original
                original_lesson = next(
                    (l for l in course.get('lessons', []) if l['_id'] == lesson['lessonId']),
                    None
                )
                if original_lesson:
                    activities_completed += original_lesson.get('questionCount', 0)
                    
                    # Calcular intentos
                    max_attempts = original_lesson.get('attempts', 0)
                    remaining = lesson.get('remainingAttempts', 0)
                    used_attempts = max_attempts - remaining
                    total_attempts += used_attempts
                    attempt_count += 1
    
    # Calcular promedio de intentos
    average_attempts = round(total_attempts / attempt_count, 1) if attempt_count > 0 else 0
    
    # Obtener nivel y habilidades del usuario
    user = db.users.find_one({'_id': user_id})
    info = user.get('information', {}) if user else {}
    
    level = info.get('lescoLevel', 0) if not language else info.get('librasLevel', 0)
    skills = info.get('lescoSkills', 0) if not language else info.get('librasSkills', 0)
    
    return {
        'coursesCompleted': courses_completed,
        'lessonsCompleted': lessons_completed,
        'activitiesCompleted': activities_completed,
        'averageAttempts': average_attempts,
        'level': level,
        'skills': skills
    }

# Iniciales para el avatar
def get_initials(name):
    # Se divide el nombre por espacios
    parts = name.split()
    if len(parts) >= 2:
        # Obtiene la primera letra de las dos primeras palabras
        return f"{parts[0][0]}{parts[1][0]}".upper()
    elif len(parts) == 1:
        # Obtiene las dos primeras letras de la primera palabra
        return parts[0][:2].upper()

# Nivel total del usuario
def calculate_total_level(user):
    # Desde information vamos a obtener los niveles
    info = user.get('information', {})
    lesco_level = info.get('lescoLevel', 0)
    libras_level = info.get('librasLevel', 0)
    return lesco_level + libras_level  


def calculate_current_skills(user):
    lesco=current_app.config['LESCO']
    info = user.get('information', {})
    if lesco:
        lesco_skills = info.get('lescoSkills', 0)
        return lesco_skills
    else:
        libras_skills = info.get('librasSkills', 0)
        return libras_skills


# Habilidades necesarias para el siguiente nivel
def calculate_next_level_skills(user):
    # Obtenemos la variable global
    lesco=current_app.config['LESCO']
    if lesco:
        info = user.get('information', {})
        lesco_level = info.get('lescoLevel', 0)
        next_level_skills = lesco_level + 1
        return next_level_skills
    else:
        info = user.get('information', {})
        libras_level = info.get('librasLevel', 0)
        next_level_skills = libras_level + 1
        return next_level_skills

def calculate_actual_level(user):
    # Obtenemos la variable global
    lesco=current_app.config['LESCO']
    if lesco:
        info = user.get('information', {})
        lesco_level = info.get('lescoLevel', 0)
        return lesco_level
    else:
        info = user.get('information', {})
        libras_level = info.get('librasLevel', 0)
        return libras_level


# Endpoint de prueba para crear usuario y hacer tests
@user_blueprint.route('/test/create-user', methods=['POST'])
def create_test_user():

    try:
        db = current_app.db
        
        # Obtener datos del request o usar valores por defecto
        data = request.json
        
        test_user = {
            "type": data.get('type'),  
            "name": data.get('name'),
            "followers": [],
            "following": [],
            "information": {
                "streak": {
                    "current": data.get('streakDays'),
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
            'name': test_user['name'],
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

