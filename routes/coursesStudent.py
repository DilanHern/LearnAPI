from flask import Blueprint, jsonify, current_app, request
from bson import ObjectId
from datetime import datetime
from routes.exercises import _create_news_course_unsubscribe
import re



coursesStudent_blueprint = Blueprint('coursesStudent', __name__)

@coursesStudent_blueprint.route('/my-courses/<user_id>', methods=['GET'])
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

@coursesStudent_blueprint.route('/unenroll-course/<user_id>/<course_id>', methods=['DELETE'])
def unenroll_course(user_id, course_id):
    try:
        db = current_app.db
        user_oid = ObjectId(user_id)
        course_oid = ObjectId(course_id) 
        
        # Verificar que el usuario exista y sea estudiante
        user = db.users.find_one({'_id': user_oid})
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        if user.get('type') != False:
            return jsonify({'error': 'Solo estudiantes pueden desinscribirse de cursos'}), 403
        
        # Verificar que el curso exista
        course = db.courses.find_one({'_id': course_oid})
        if not course:
            return jsonify({'error': 'Curso no encontrado'}), 404
        
        # Verificar que el usuario esté inscrito
        existing_enrollment = db.enrolledCourses.find_one({
            'userId': user_oid,
            'courseId': course_oid
        })
        if not existing_enrollment:
            return jsonify({'error': 'No estás inscrito en este curso'}), 404
        
        # Solo crear noticia si el curso NO estaba terminado
        # (completionDate == None o no existe el campo)
        completion_date = existing_enrollment.get('completionDate', None)
        should_create_news = (completion_date is None)

        # Eliminar el enrolledCourse
        db.enrolledCourses.delete_one({
            'userId': user_oid,
            'courseId': course_oid
        })
        
        # Remover el curso de myCourses del usuario
        db.users.update_one(
            {'_id': user_oid},
            {'$pull': {'information.myCourses': course_oid}}   
        )
        
        # Remover el usuario de la lista de estudiantes del curso
        db.courses.update_one(
            {'_id': course_oid},
            {'$pull': {'students': user_oid}}
        )
        # Crear noticia si NO estaba terminado
        if should_create_news:
            try:
                _create_news_course_unsubscribe(current_app.db, user_oid, course)
            except Exception:
                current_app.logger.exception("Error creando noticia de desuscripción")
        
        return jsonify({'message': 'Desinscripción exitosa'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# ------------------- Cursos disponibles -------------------
@coursesStudent_blueprint.route('/available-courses/<user_id>', methods=['GET'])
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
        
        # Construir respuesta 
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

@coursesStudent_blueprint.route('/enroll-course/<user_id>/<course_id>', methods=['POST'])
def enroll_course(user_id, course_id):
    try:
        db = current_app.db  
        
        user_oid = ObjectId(user_id)
        course_oid = ObjectId(course_id)
        
        # Verificar que el usuario exista y sea estudiante
        user = db.users.find_one({'_id': user_oid})
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        if user.get('type') != False:
            return jsonify({'error': 'Solo estudiantes pueden inscribirse en cursos'}), 403
        
        # Verificar que el curso exista y esté disponible
        course = db.courses.find_one({'_id': course_oid})
        if not course:
            return jsonify({'error': 'Curso no encontrado'}), 404
        if course.get('status') != True:
            return jsonify({'error': 'El curso no está disponible para inscripción'}), 403
        
        # Verificar que el usuario no esté ya inscrito
        existing_enrollment = db.enrolledCourses.find_one({
            'userId': user_oid,
            'courseId': course_oid
        })
        if existing_enrollment:
            return jsonify({'error': 'Ya estás inscrito en este curso'}), 409
        
        # Crear el documento de inscripción (enrolledCourse)
        enrolled_course = {
            'userId': user_oid,
            'courseId': course_oid,
            'completionDate': None,       # Aún no ha completado el curso
            'completedLessons': []        # Lecciones terminadas (vacío al inicio)
        }
        
        # Insertar en la colección y obtener el ID insertado
        enrolled_course_id = db.enrolledCourses.insert_one(enrolled_course).inserted_id
        
        # Agregar el curso a la lista de cursos del usuario
        db.users.update_one(
            {'_id': user_oid},
            {'$addToSet': {'information.myCourses': course_oid}}  # $addToSet evita duplicados
        )
        
        # Agregar el estudiante a la lista de alumnos del curso
        db.courses.update_one(
            {'_id': course_oid},
            {'$addToSet': {'students': user_oid}}
        )
        
        # Devolver respuesta exitosa
        return jsonify({
            'message': 'Inscripción exitosa',
            'enrolledCourseId': str(enrolled_course_id)
        }), 201
        
    except Exception as e:
        # Si ocurre algún error, devuelve el mensaje y código 500
        return jsonify({'error': str(e)}), 500