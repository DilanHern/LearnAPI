# routes/teacherLessons.py
from flask import Blueprint, jsonify, current_app, request
from bson import ObjectId
from datetime import datetime

teacher_lessons_blueprint = Blueprint('teacherLessons', __name__)

# Obtener curso completo por course_id
@teacher_lessons_blueprint.route('/course/<course_id>', methods=['GET'])
def get_course(course_id):
    try:
        db = current_app.db
        course_oid = ObjectId(course_id)

        # Buscar el curso
        course = db.courses.find_one({'_id': course_oid})
        if not course:
            return jsonify({'error': 'Curso no encontrado'}), 404

        # Extraer lecciones
        lessons = course.get('lessons', [])
        lessons_list = []
        for lesson in lessons:
            lessons_list.append({
                'id': str(lesson['_id']),
                'order': lesson.get('order', 0),
                'name': lesson.get('name', 'Lección'),
                'questionCount': lesson.get('questionCount', 0),
                'attempts': lesson.get('attempts', 0),
                'forumEnabled': lesson.get('forumEnabled', True)
            })

        # Construir respuesta completa
        course_data = {
            'id': str(course['_id']),
            'name': course.get('name', 'Curso sin nombre'),
            'description': course.get('description', ''),
            'difficulty': course.get('difficulty', 1),
            'language': course.get('language', False),
            'status': course.get('status', True),
            'studentCount': len(course.get('students', [])),
            'lessonCount': len(lessons),
            'lessons': lessons_list
        }

        return jsonify(course_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# POST: Añadir una lección a un curso
@teacher_lessons_blueprint.route('/course/<course_id>/lesson', methods=['POST'])
def add_lesson(course_id):
    try:
        db = current_app.db
        course_oid = ObjectId(course_id)

        # Obtener datos del body
        data = request.get_json()
        lesson_name = data.get('name')
        if not lesson_name:
            return jsonify({'error': 'El nombre de la lección es requerido'}), 400

        # Buscar el curso
        course = db.courses.find_one({'_id': course_oid})
        if not course:
            return jsonify({'error': 'Curso no encontrado'}), 404

        # Crear nuevo objeto de lección
        new_lesson = {
            '_id': ObjectId(),
            'name': lesson_name,
            'order': len(course.get('lessons', [])) + 1,
            'questionCount': 0,
            'attempts': 0,
            'forumEnabled': True,
            'createdAt': datetime.utcnow()
        }

        # Agregar al array de lecciones del curso
        db.courses.update_one(
            {'_id': course_oid},
            {'$push': {'lessons': new_lesson}}
        )

        # Respuesta
        return jsonify({
            'message': 'Lección agregada correctamente',
            'lesson': {
                'id': str(new_lesson['_id']),
                'name': new_lesson['name'],
                'order': new_lesson['order'],
                'questionCount': new_lesson['questionCount'],
                'attempts': new_lesson['attempts'],
                'forumEnabled': new_lesson['forumEnabled']
            }
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500