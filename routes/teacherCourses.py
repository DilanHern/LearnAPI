from flask import Blueprint, jsonify, current_app, request
from bson import ObjectId
from datetime import datetime
import re

teacher_courses_blueprint = Blueprint('teacher_courses', __name__)

@teacher_courses_blueprint.route('/teacher-courses', methods=['GET'])
def get_teacher_courses():
    try:
        db = current_app.db
        
        # Obtener parámetros de la query string
        user_id = request.args.get('user_id')
        language_param = request.args.get('language', 'false').lower()
        
        if not user_id:
            return jsonify({'error': 'Se requiere user_id en los parámetros'}), 400
        
        try:
            user_oid = ObjectId(user_id)
        except:
            return jsonify({'error': 'ID de usuario inválido'}), 400
        
        language = language_param == 'true'  # Default lesco (false)
        
        # Verificar que el usuario existe y es profesor
        #luego se puede quitar porque este endpoint es para profes nad más
        user = db.users.find_one({'_id': user_oid})
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        if not user.get('type', False):  # false es estudiante, true es profesor
            return jsonify({'error': 'El usuario no es un profesor'}), 403
        
        # Obtener cursos del profesor filtrados por idioma
        teacher_courses = get_teacher_courses_info(db, user_oid, language)
        
        response_data = {
            'courses': teacher_courses
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Error en get_teacher_courses: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@teacher_courses_blueprint.route('/course-students/<course_id>', methods=['DELETE'])
def remove_student_from_course(course_id):
    try:
        db = current_app.db
        data = request.get_json()
        
        if not data or 'student_id' not in data:
            return jsonify({'error': 'Se requiere student_id en el body'}), 400
        
        course_oid = ObjectId(course_id)
        student_oid = ObjectId(data['student_id'])
        
        # Verificar que el curso existe
        course = db.courses.find_one({'_id': course_oid})
        if not course:
            return jsonify({'error': 'Curso no encontrado'}), 404
        
        # Verificar que el estudiante existe
        student = db.users.find_one({'_id': student_oid})
        if not student:
            return jsonify({'error': 'Estudiante no encontrado'}), 404
        
        # Eliminar la inscripción
        result = db.enrolledCourses.delete_one({
            'courseId': course_oid,
            'userId': student_oid
        })
        
        if result.deleted_count == 0:
            return jsonify({'error': 'El estudiante no estaba inscrito en este curso'}), 404
        
        return jsonify({'message': 'Estudiante eliminado del curso exitosamente'}), 200
        
    except Exception as e:
        print(f"Error en remove_student_from_course: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

def get_teacher_courses_info(db, teacher_id, language):
    try:
        # Buscar todos los cursos creados por el profesor en el idioma específico
        courses = db.courses.find({
            'userId': teacher_id,
            'language': language
        })
        
        courses_list = []
        
        for course in courses:
            # Contar estudiantes inscritos
            enrolled_count = db.enrolledCourses.count_documents({'courseId': course['_id']})
            
            # Convertir ObjectId a string 
            course_data = {
                '_id': str(course['_id']),
                'userId': str(course['userId']),
                'name': course.get('name', 'Curso sin nombre'),
                'description': course.get('description', ''),
                'difficulty': course.get('difficulty', 0),
                'language': course.get('language', False),
                'status': course.get('status', False),
                'students': enrolled_count,
                'lessons': process_lessons(course.get('lessons', []))
            }
            
            courses_list.append(course_data)
        
        return courses_list
    except Exception as e:
        print(f"Error en get_teacher_courses_info: {str(e)}")
        return []

def process_lessons(lessons):
    try:
        processed_lessons = []
        for lesson in lessons:
            processed_lesson = {
                '_id': str(lesson['_id']),
                'order': lesson.get('order', 0),
                'name': lesson.get('name', ''),
                'questionCount': lesson.get('questionCount', 0),
                'attempts': lesson.get('attempts', 0),
                'time': lesson.get('time', 0),
                'forumEnabled': lesson.get('forumEnabled', False)
            }
            
            # Procesar teoría si existe
            if 'theory' in lesson:
                processed_lesson['theory'] = []
                for theory_item in lesson['theory']:
                    processed_theory = theory_item.copy()
                    if 'sign' in processed_theory and processed_theory['sign']:
                        processed_theory['sign'] = str(processed_theory['sign'])
                    processed_lesson['theory'].append(processed_theory)
            
            # Procesar ejercicios si existen
            if 'exercises' in lesson:
                processed_lesson['exercises'] = []
                for exercise in lesson['exercises']:
                    processed_exercise = exercise.copy()
                    processed_exercise['_id'] = str(exercise['_id'])
                    if 'sign' in processed_exercise and processed_exercise['sign']:
                        processed_exercise['sign'] = str(processed_exercise['sign'])
                    processed_lesson['exercises'].append(processed_exercise)
            
            processed_lessons.append(processed_lesson)
        
        return processed_lessons
    except Exception as e:
        print(f"Error en process_lessons: {str(e)}")
        return []

@teacher_courses_blueprint.route('/teacher-courses', methods=['POST'])
def create_teacher_course():
    try:
        db = current_app.db
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({'error': 'Se requiere user_id en el body'}), 400
        
        user_oid = ObjectId(data['user_id'])
        
        # Verificar que el usuario existe y es profesor
        user = db.users.find_one({'_id': user_oid})
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        if not user.get('type', False):
            return jsonify({'error': 'El usuario no es un profesor'}), 403
        
        # Validar datos requeridos
        required_fields = ['name', 'difficulty', 'language', 'status']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido faltante: {field}'}), 400
        
        # Crear nuevo curso
        new_course = {
            'userId': user_oid,
            'name': data['name'],
            'description': data.get('description', ''),
            'difficulty': data['difficulty'],
            'language': data['language'],
            'status': data['status'],
            'students': [],
            'lessons': data.get('lessons', [])
        }
        
        result = db.courses.insert_one(new_course)
        
        # ACTUALIZAR ESTADÍSTICAS - Incrementar cursos creados
        update_teacher_statistics(db, user_oid, courses_created=1)
        
        return jsonify({
            'message': 'Curso creado exitosamente',
            'courseId': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        print(f"Error en create_teacher_course: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@teacher_courses_blueprint.route('/teacher-courses', methods=['PUT'])
def update_teacher_course():
    try:
        db = current_app.db
        data = request.get_json()

        if not data or 'course_id' not in data:
            return jsonify({'error': 'Se requiere course_id en el body'}), 400
        
        course_oid = ObjectId(data['course_id'])
        
        # Verificar que el curso existe
        existing_course = db.courses.find_one({'_id': course_oid})
        if not existing_course:
            return jsonify({'error': 'Curso no encontrado'}), 404
        
        # Campos permitidos para actualización
        update_fields = {}
        allowed_fields = ['name', 'description', 'difficulty', 'language', 'status']
        
        for field in allowed_fields:
            if field in data:
                update_fields[field] = data[field]
        
        # Procesar lecciones - CONVIRTIENDO STRINGS A ObjectId
        if 'lessons' in data and isinstance(data['lessons'], list):
            try:
                validated_lessons = []
                for lesson in data['lessons']:
                    # Convertir _id de lección a ObjectId
                    lesson_id = ObjectId(lesson['_id']) if lesson.get('_id') else ObjectId()
                    
                    validated_lesson = {
                        '_id': lesson_id,
                        'order': int(lesson.get('order', 0)),
                        'name': str(lesson.get('name', '')),
                        'questionCount': int(lesson.get('questionCount', 0)),
                        'attempts': int(lesson.get('attempts', 0)),
                        'time': int(lesson.get('time', 0)),
                        'forumEnabled': bool(lesson.get('forumEnabled', False))
                    }
                    
                    # Procesar teoría 
                    if 'theory' in lesson and isinstance(lesson['theory'], list):
                        validated_lesson['theory'] = []
                        for theory_item in lesson['theory']:
                            processed_theory = theory_item.copy()
                            if 'sign' in processed_theory and processed_theory['sign']:
                                processed_theory['sign'] = ObjectId(processed_theory['sign'])
                            validated_lesson['theory'].append(processed_theory)
                    
                    # Procesar ejercicios convertir _id y sign a ObjectId
                    if 'exercises' in lesson and isinstance(lesson['exercises'], list):
                        validated_lesson['exercises'] = []
                        for exercise in lesson['exercises']:
                            processed_exercise = exercise.copy()
                            # Convertir _id del ejercicio
                            if '_id' in processed_exercise and processed_exercise['_id']:
                                processed_exercise['_id'] = ObjectId(processed_exercise['_id'])
                            # Convertir sign del ejercicio  
                            if 'sign' in processed_exercise and processed_exercise['sign']:
                                processed_exercise['sign'] = ObjectId(processed_exercise['sign'])
                            validated_lesson['exercises'].append(processed_exercise)
                    
                    validated_lessons.append(validated_lesson)
                
                update_fields['lessons'] = validated_lessons
                print(f"Lecciones procesadas: {len(validated_lessons)} lecciones")
                
            except Exception as e:
                print(f"Error procesando lecciones: {str(e)}")
                return jsonify({'error': f'Error en estructura de lecciones: {str(e)}'}), 400
        
        if update_fields:
            print(f"Campos a actualizar: {update_fields}")
            result = db.courses.update_one(
                {'_id': course_oid},
                {'$set': update_fields}
            )
            
            print(f"Resultado actualización: {result.modified_count} modificados")
            
            if result.modified_count == 0:
                return jsonify({'message': 'No se realizaron cambios en el curso'}), 200
        
        return jsonify({'message': 'Curso actualizado exitosamente'}), 200
        
    except Exception as e:
        print(f"Error en update_teacher_course: {str(e)}")
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@teacher_courses_blueprint.route('/teacher-courses', methods=['DELETE'])
def delete_teacher_course():
    try:
        db = current_app.db
        data = request.get_json()
        
        if not data or 'course_id' not in data:
            return jsonify({'error': 'Se requiere course_id en el body'}), 400
        
        course_oid = ObjectId(data['course_id'])
        
        # Verificar que el curso existe
        existing_course = db.courses.find_one({'_id': course_oid})
        if not existing_course:
            return jsonify({'error': 'Curso no encontrado'}), 404
        
        # Obtener el ID del profesor para actualizar estadísticas
        teacher_id = existing_course['userId']
        
        # Contar lecciones que se eliminarán
        lessons_to_remove = len(existing_course.get('lessons', []))
        
        # Eliminar el curso
        db.courses.delete_one({'_id': course_oid})
        
        # También eliminar inscripciones relacionadas
        db.enrolledCourses.delete_many({'courseId': course_oid})
        
        # ACTUALIZAR ESTADÍSTICAS - Decrementar cursos y lecciones
        update_teacher_statistics(db, teacher_id, courses_created=-1, lessons_created=-lessons_to_remove)
        
        return jsonify({'message': 'Curso eliminado exitosamente'}), 200
        
    except Exception as e:
        print(f"Error en delete_teacher_course: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500



@teacher_courses_blueprint.route('/course-students/<course_id>', methods=['GET'])
def get_course_students(course_id):
    try:
        db = current_app.db
        
        course_oid = ObjectId(course_id)
        
        # Verificar que el curso existe
        course = db.courses.find_one({'_id': course_oid})
        if not course:
            return jsonify({'error': 'Curso no encontrado'}), 404
        
        # Obtener estudiantes inscritos en el curso
        enrolled_students = db.enrolledCourses.find({'courseId': course_oid})
        
        students_list = []
        for enrollment in enrolled_students:
            student = db.users.find_one({'_id': enrollment['userId']})
            if student:
                student_data = {
                    'id': str(student['_id']),
                    'name': student.get('name', 'Estudiante sin nombre'),
                    'email': student.get('email', 'Sin email'),
                    'initials': get_initials(student.get('name', '')),
                    'enrollmentDate': enrollment.get('enrollmentDate', '')
                }
                students_list.append(student_data)
        
        response_data = {
            'courseName': course.get('name', ''),
            'students': students_list
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Error en get_course_students: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500


def update_teacher_statistics(db, teacher_id, courses_created=0, lessons_created=0, students_added=0):
    
    #Actualiza las estadísticas del profesor en la colección teacherStatistics

    try:
        # Buscar si existe un documento de estadísticas para este profesor
        existing_stats = db.teacherStatistics.find_one({'userId': teacher_id})
        
        if existing_stats:
            # Actualizar documento existente
            update_data = {}
            if courses_created != 0:
                update_data['coursesCreated'] = max(0, existing_stats.get('coursesCreated', 0) + courses_created)
            if lessons_created != 0:
                update_data['lessonsCreated'] = max(0, existing_stats.get('lessonsCreated', 0) + lessons_created)
            if students_added != 0:
                update_data['totalStudents'] = max(0, existing_stats.get('totalStudents', 0) + students_added)
            
            if update_data:
                db.teacherStatistics.update_one(
                    {'userId': teacher_id},
                    {'$set': update_data}
                )
        else:
            # Crear nuevo documento de estadísticas si no existe
            # Solo crear si se agrega valores positivos, es decir no eliminar
            if courses_created > 0 or lessons_created > 0 or students_added > 0:
                new_stats = {
                    'userId': teacher_id,
                    'coursesCreated': max(0, courses_created),
                    'lessonsCreated': max(0, lessons_created),
                    'totalStudents': max(0, students_added)
                }
                db.teacherStatistics.insert_one(new_stats)
                
    except Exception as e:
        print(f"Error en update_teacher_statistics: {str(e)}")

def get_initials(name):
    if not name:
        return "?"
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    elif len(parts) == 1:
        return parts[0][0].upper()
    return "?"