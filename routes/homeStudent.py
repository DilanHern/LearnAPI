from flask import Blueprint, app, jsonify, current_app, request
from bson import ObjectId
from datetime import datetime
import re

homeStudent_blueprint = Blueprint('homeStudent', __name__)

# Función para obtener la racha
def get_streak_days(user):
    info = user.get('information', {})
    streak = info.get('streak', {})
    return streak.get('current', 0)

# Función para extraer valor numérico del logro 
def get_achievement_value(achievement):
    content = achievement.get('content', '')
    numbers = re.findall(r'\d+', content)
    return int(numbers[0]) if numbers else 0

# Habilidades actuales del usuario
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

# Obtener el último logro del usuario (solo el más reciente)
def get_last_achievement(db, user):
    info = user.get('information', {})
    achievement_ids = info.get('achievements', [])
    lesco = current_app.config['LESCO']
    
    # Si no hay logros, retornar None
    if not achievement_ids:
        return None
    
    # Determinar qué tipo de logros buscar
    achievement_type = False if lesco else True
    
    # Buscar el logro más reciente que coincida con la lengua (ordenado por fecha descendente, limitado a 1)
    achievement = db.achievements.find({
        '_id': {'$in': achievement_ids},
        'type': achievement_type
    }).sort('date', -1).limit(1)
    
    # Si hay resultado, construir el diccionario
    for ach in achievement:
        return {
            'id': str(ach['_id']),
            'title': ach.get('name', 'Logro'),
            'value': get_achievement_value(ach),
            'type': 'LESCO' if ach.get('type') == False else 'LIBRAS'
        }
    
    # Si no se encontró ninguno, retornar None
    return None

# Obtener el curso más reciente completado por el usuario
def get_recent_course(db, user_oid):
    enrolled_courses = db.enrolledCourses.find({'userId': user_oid})
    latest_completion_date = None
    latest_course_id = None
    
    # Iterar sobre enrolledCourses para encontrar la lección más reciente
    for enrolled in enrolled_courses:
        for lesson in enrolled.get('completedLessons', []):
            completion_date = lesson.get('completionDate')
            if completion_date:
                if latest_completion_date is None or completion_date > latest_completion_date:
                    latest_completion_date = completion_date
                    latest_course_id = enrolled['courseId']
    
    # Si encontró un curso, obtener sus detalles
    if latest_course_id:
        course = db.courses.find_one({'_id': latest_course_id})
        if course:
            teacher = db.users.find_one({'_id': course['userId']})
            teacher_name = teacher.get('name', 'Profesor desconocido') if teacher else 'Profesor desconocido'
            return {
                'courseName': course.get('name', 'Curso sin nombre'),
                'difficulty': course.get('difficulty', 1),
                'lessonsCount': len(course.get('lessons', [])),
                'teacherName': teacher_name,
                'description': course.get('description', 'Sin descripción')
            }
    
    # Si no hay cursos completados, retornar None
    return None

@homeStudent_blueprint.route('/studentHome-info/<user_id>', methods=['GET'])
def get_home_info(user_id):
    try:
        db = current_app.db
        user_oid = ObjectId(user_id)

        # Obtener información del usuario
        user = db.users.find_one({'_id': user_oid})
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        # Calcular la racha
        streak = get_streak_days(user)

        # Obtener último logro
        last_achievement = get_last_achievement(db, user)

        # Obtener curso más reciente
        recent_course = get_recent_course(db, user_oid)

        response_data = {
            'streak': streak,
            'level': calculate_actual_level(user),
            'skillsProgress': calculate_current_skills(user),
            'totalSkills': calculate_next_level_skills(user),
            'lastAchievement': last_achievement,
            'recentCourse': recent_course  # Cambié a recentCourse
        }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@homeStudent_blueprint.route('/api/language/status', methods=['GET'])
def get_lesco():
    try:
        # Devolver el valor actual de LESCO
        return jsonify({
            'lesco': current_app.config['LESCO']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500