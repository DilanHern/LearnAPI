from flask import Blueprint, jsonify, current_app, request
from bson import ObjectId
from datetime import datetime
import re

lessonsStudent_blueprint = Blueprint('lessonsStudent', __name__)
@lessonsStudent_blueprint.route('/list-lessons/<course_id>/<user_id>', methods=['GET'])
def listLessons(course_id, user_id):
    try:
        db = current_app.db
        course_oid = ObjectId(course_id)
        user_oid = ObjectId(user_id)

        # Obtener información del curso
        course = db.courses.find_one({'_id': course_oid})
        if not course:
            return jsonify({'error': 'Curso no encontrado'}), 404

        # Obtener nombre del curso
        course_name = course.get('name')

        # Obtener información del usuario para el streak
        user = db.users.find_one({'_id': user_oid})
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        # Calcular la racha
        streak = get_streak_days(user)

        lessonsList = course.get('lessons', [])
        results = []

        for lesson in lessonsList:
            results.append({
                'id': str(lesson['_id']),
                'name': lesson.get('name', 'Lección sin nombre')
            })

        # Construir respuesta con streak y lessons
        response_data = {
            'streak': streak,
            'courseName': course_name,
            'lessons': results
        }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_streak_days(user):
    info = user.get('information', {})
    streak = info.get('streak', {})
    return streak.get('current', 0)

@lessonsStudent_blueprint.route('/info-lesson/<lesson_id>/<user_id>', methods=['GET'])
def get_infoLesson(lesson_id, user_id):
    try:
        db = current_app.db
        lesson_oid = ObjectId(lesson_id)
        user_oid = ObjectId(user_id)

        # Obtener información del usuario para el streak
        user = db.users.find_one({'_id': user_oid})
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        # Calcular la racha
        streak = get_streak_days(user)

        # Buscar la lección y el nombre del curso
        course = db.courses.find_one(
            {'lessons._id': lesson_oid},
            {'name': 1, 'lessons.$': 1} 
        )
        if not course or 'lessons' not in course or len(course['lessons']) == 0:
            return jsonify({'error': 'Lección no encontrada'}), 404

        lesson = course['lessons'][0]

        # Iterar en theory para obtener text y sign
        theory_list = []
        for theory_item in lesson.get('theory', []):
            theory_list.append({
                'text': theory_item.get('text', ''),
                'sign': str(theory_item.get('sign', '')) 
            })

        # Construir el objeto de la lección con todos los datos solicitados
        lesson_data = {
            'streak': streak,
            'courseName': course.get('name', 'Curso sin nombre'),
            'lessonName': lesson.get('name', 'Lección sin nombre'),
            'theory': theory_list,
            'attempts': lesson.get('attempts', 0),
            'questionCount': lesson.get('questionCount', 0)
        }

        return jsonify(lesson_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500