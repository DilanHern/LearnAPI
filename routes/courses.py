from flask import Blueprint, jsonify, current_app, request
from bson import ObjectId
from datetime import datetime
import re


courses_blueprint = Blueprint('courses', __name__)

@courses_blueprint.route('/my-courses/<user_id>', methods=['GET'])
def get_my_courses(user_id):
    try:
        db = current_app.db
        user_oid = ObjectId(user_id)
        
        # Obtener información del usuario
        user = db.users.find_one({'_id': user_oid})
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Obtener la racha actual
        streak = get_streak_days(user)
        
        # Determinar idioma basado en configuración global
        language = not current_app.config['LESCO']  # True = LIBRAS, False = LESCO
        
        # Obtener cursos inscritos filtrados por idioma
        enrolled_courses = get_info_enrolled_courses(db, user_oid, language)
        
        # Construir respuesta
        response_data = {
            'streak': streak,
            'enrolledCourses': enrolled_courses
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_info_enrolled_courses(db, user_id, language):
    # Obtener todos los cursos inscritos del usuario
    enrolled_courses = db.enrolledCourses.find({'userId': user_id})
    
    courses_list = []
    
    for enrolled in enrolled_courses:
        # Buscar el curso en la colección courses usando courseId
        course = db.courses.find_one({'_id': enrolled['courseId']})
        
        if course and course.get('language') == language:  # Filtrar por idioma
            # Obtener el nombre del profesor usando userId del curso
            teacher = db.users.find_one({'_id': course['userId']})
            teacher_name = teacher.get('name', 'Profesor desconocido') if teacher else 'Profesor desconocido'
            
            # Construir el objeto del curso
            course_data = {
                'id': str(course['_id']),
                'name': course.get('name', 'Curso sin nombre'),
                'difficulty': course.get('difficulty', 1),
                'lessonsCount': len(course.get('lessons', [])),
                'teacherName': teacher_name,
                'description': course.get('description', 'Sin descripción')
            }
            
            courses_list.append(course_data)
    
    return courses_list


# Obtiene la racha
def get_streak_days(user):
    info = user.get('information', {})
    streak = info.get('streak', {})
    return streak.get('current', 0)

@courses_blueprint.route('/available-courses/<user_id>', methods=['GET'])
def get_available_courses(user_id):
    try:
        db = current_app.db
        user_oid = ObjectId(user_id)
        
        # Obtener información del usuario
        user = db.users.find_one({'_id': user_oid})
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Obtener la racha actual
        streak = get_streak_days(user)
        

        # Determinar idioma basado en configuración global
        language = not current_app.config['LESCO']  # True = LIBRAS, False = LESCO
        
        # Obtener cursos disponibles filtrados por idioma
        available_courses = get_info_available_courses(db, user_oid, language)
        
        # Construir respuesta (sin streak, ya que no aplica)
        response_data = {
            'streak': streak,
            'availableCourses': available_courses
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_info_available_courses(db, user_id, language):
    # Obtener IDs de cursos inscritos por el usuario
    enrolled_course_ids = set()
    enrolled_courses = db.enrolledCourses.find({'userId': user_id})
    for enrolled in enrolled_courses:
        enrolled_course_ids.add(enrolled['courseId'])
    
    # Obtener cursos públicos del idioma que NO están inscritos
    available_courses = db.courses.find({
        'status': True,  # Solo públicos
        'language': language,  # Filtrar por idioma
        '_id': {'$nin': list(enrolled_course_ids)}  # Excluir inscritos
    })
    
    courses_list = []
    
    for course in available_courses:
        # Obtener el nombre del profesor usando userId del curso
        teacher = db.users.find_one({'_id': course['userId']})
        teacher_name = teacher.get('name', 'Profesor desconocido') if teacher else 'Profesor desconocido'
        
        # Construir el objeto del curso
        course_data = {
            'id': str(course['_id']),
            'name': course.get('name', 'Curso sin nombre'),
            'difficulty': course.get('difficulty', 1),
            'lessonsCount': len(course.get('lessons', [])),
            'teacherName': teacher_name,
            'description': course.get('description', 'Sin descripción')
        }
        
        courses_list.append(course_data)
    
    return courses_list