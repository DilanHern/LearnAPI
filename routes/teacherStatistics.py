from flask import Blueprint, jsonify, current_app, request
from bson import ObjectId

teacher_statistics_blueprint = Blueprint('teacher_statistics', __name__)

# estadísticas generales y por curso
@teacher_statistics_blueprint.route('/teacher-statistics/<teacher_id>', methods=['GET'])
def get_teacher_statistics(teacher_id):
    try:
        db = current_app.db
        
        # Validar id
        try:
            teacher_oid = ObjectId(teacher_id)
        except:
            return jsonify({'error': 'ID de profesor inválido'}), 400
        
        # usuario existe y es profesor
        teacher = db.users.find_one({'_id': teacher_oid})
        if not teacher:
            return jsonify({'error': 'Profesor no encontrado'}), 404
        
        if not teacher.get('type', False):
            return jsonify({'error': 'El usuario no es un profesor'}), 403
        
        statistics = calculate_teacher_statistics(db, teacher_oid)
        
        return jsonify(statistics), 200
        
    except Exception as e:
        print(f"Error en get_teacher_statistics: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@teacher_statistics_blueprint.route('/course-statistics/<teacher_id>/<course_id>', methods=['GET'])
def get_course_statistics(teacher_id, course_id):
    try:
        db = current_app.db
        
        # Validar ids 
        try:
            teacher_oid = ObjectId(teacher_id)
            course_oid = ObjectId(course_id)
        except:
            return jsonify({'error': 'ID de profesor o curso inválido'}), 400
        
        # usuario existe y es profesor
        teacher = db.users.find_one({'_id': teacher_oid})
        if not teacher:
            return jsonify({'error': 'Profesor no encontrado'}), 404
        
        if not teacher.get('type', False):
            return jsonify({'error': 'El usuario no es un profesor'}), 403
        
        # curso existe y pertenece al profesor
        course = db.courses.find_one({'_id': course_oid, 'userId': teacher_oid})
        if not course:
            return jsonify({'error': 'Curso no encontrado o no pertenece al profesor'}), 404
        
        # estadísticas del curso
        course_statistics = calculate_course_statistics(db, course_oid)
        
        return jsonify(course_statistics), 200
        
    except Exception as e:
        print(f"Error en get_course_statistics: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

def calculate_teacher_statistics(db, teacher_id):

    #Calcula las estadísticas generales del profesor
    
    try:
        # contar cursos creados por el profesor
        total_courses = db.courses.count_documents({'userId': teacher_id})
        
        # contar cursos publicados y no publicados
        published_courses = db.courses.count_documents({
            'userId': teacher_id, 
            'status': True  # true = publicados
        })
        private_courses = db.courses.count_documents({
            'userId': teacher_id, 
            'status': False  # false = privados
        })
        
        # contar lecciones creadas por el profesor
        teacher_courses = db.courses.find({'userId': teacher_id})
        total_lessons = 0
        
        for course in teacher_courses:
            lessons = course.get('lessons', [])
            total_lessons += len(lessons)
        
        # contar estudiantes totales en la plataforma
        total_students = db.users.count_documents({'type': False})  # false = estudiantes
        
        #todos los cursos del profesor
        teacher_course_ids = [course['_id'] for course in db.courses.find(
            {'userId': teacher_id}, 
            {'_id': 1}
        )]
        
        # Contar estudiantes que están en cursos del profesor
        enrolled_students = db.enrolledCourses.distinct('userId', {
            'courseId': {'$in': teacher_course_ids}
        })
        teacher_students_count = len(enrolled_students)
        
        # calcular porcentaje de éxito 
        success_percentage = calculate_success_percentage(db, teacher_course_ids)
        
        # info adicional de los cursos
        courses_info = []
        teacher_courses = db.courses.find({'userId': teacher_id})
        
        for course in teacher_courses:
            # Contar estudiantes en este curso específico
            course_enrolled_count = db.enrolledCourses.count_documents({
                'courseId': course['_id']
            })
            
            # calcular porcentaje de éxito para este curso específico
            course_success_percentage = calculate_course_success_percentage(db, course['_id'])
            
            course_info = {
                'courseId': str(course['_id']),
                'name': course.get('name', 'Curso sin nombre'),
                'language': 'LIBRAS' if course.get('language') else 'LESCO',
                'status': 'Publicado' if course.get('status') else 'Privado',
                'lessonCount': len(course.get('lessons', [])),
                'enrolledStudents': course_enrolled_count,
                'successPercentage': course_success_percentage
            }
            courses_info.append(course_info)
        
        # respuesta
        statistics = {
            'teacherId': str(teacher_id),
            'generalStatistics': {
                'totalCourses': total_courses,
                'publishedCourses': published_courses,
                'privateCourses': private_courses,
                'totalLessons': total_lessons,
                'totalStudentsPlatform': total_students,
                'teacherStudents': teacher_students_count,  # Estudiantes únicos del profesor
                'overallSuccessPercentage': success_percentage
            },
            'coursesDetail': courses_info
        }
        
        return statistics
        
    except Exception as e:
        print(f"Error en calculate_teacher_statistics: {str(e)}")
        return {
            'teacherId': str(teacher_id),
            'generalStatistics': {
                'totalCourses': 0,
                'publishedCourses': 0,
                'privateCourses': 0,
                'totalLessons': 0,
                'totalStudentsPlatform': 0,
                'teacherStudents': 0,
                'overallSuccessPercentage': 0
            },
            'coursesDetail': []
        }

def calculate_course_statistics(db, course_id): 
    #Calcula las estadísticas de un curso específico

    try:
        # información del curso
        course = db.courses.find_one({'_id': course_id})
        if not course:
            return {'error': 'Curso no encontrado'}
        
        # todas las personas del curso en enrolledcourses
        enrollments = db.enrolledCourses.find({'courseId': course_id})
        
        students_list = []
        total_percentage = 0
        valid_enrollments = 0
        
        for enrollment in enrollments:
            # Obtener información del estudiante
            student = db.users.find_one({'_id': enrollment['userId']})
            if not student:
                continue
            
            # porcentaje de éxito del estudiante
            total_questions = enrollment.get('totalQuestions', 0)
            correct_answers = enrollment.get('correctAnswers', 0)
            student_percentage = 0
            
            if total_questions and total_questions > 0 and correct_answers is not None:
                student_percentage = (correct_answers / total_questions) * 100
                total_percentage += student_percentage
                valid_enrollments += 1
            
            # Info del estudiante 
            student_info = {
                'studentId': str(student['_id']),
                'name': student.get('name', 'Estudiante sin nombre'),
                'successPercentage': round(student_percentage, 2)
            }
            students_list.append(student_info)
        
        # Calcular promedio del curso
        course_success_percentage = 0
        if valid_enrollments > 0:
            course_success_percentage = total_percentage / valid_enrollments
        
        # Info del curso
        course_info = {
            'courseId': str(course['_id']),
            'name': course.get('name', 'Curso sin nombre'),
            'totalEnrolledStudents': len(students_list),
            'courseSuccessPercentage': round(course_success_percentage, 2)
        }
        
        # respuesta
        statistics = {
            'courseInfo': course_info,
            'students': students_list
        }
        
        return statistics
        
    except Exception as e:
        print(f"Error en calculate_course_statistics: {str(e)}")
        return {
            'courseInfo': {
                'courseId': str(course_id),
                'name': 'Error al cargar información',
                'totalEnrolledStudents': 0,
                'courseSuccessPercentage': 0
            },
            'students': []
        }

def calculate_success_percentage(db, teacher_course_ids):
    
    #Calcula el porcentaje de éxito general para todos los cursos del profesor
    
    try:
        # estudiantes inscritos en los cursos, que estén en enrolled con ids de curso del profe
        enrollments = db.enrolledCourses.find({
            'courseId': {'$in': teacher_course_ids},
            'totalQuestions': {'$ne': None, '$gt': 0},
            'correctAnswers': {'$ne': None}
        })
        
        total_percentage = 0
        valid_enrollments = 0
        
        for enrollment in enrollments:
            total_questions = enrollment.get('totalQuestions', 0)
            correct_answers = enrollment.get('correctAnswers', 0)
            
            if total_questions > 0:
                percentage = (correct_answers / total_questions) * 100
                total_percentage += percentage
                valid_enrollments += 1
        
        if valid_enrollments > 0:
            overall_percentage = total_percentage / valid_enrollments
            return round(overall_percentage, 2)
        else:
            return 0
            
    except Exception as e:
        print(f"Error en calculate_success_percentage: {str(e)}")
        return 0

def calculate_course_success_percentage(db, course_id):
    
    #Calcula el porcentaje de éxito para un curso específico
    
    try:
        # estudiantes inscritos en el curso, que estén en enrolled con ese curso específico
        enrollments = db.enrolledCourses.find({
            'courseId': course_id,
            'totalQuestions': {'$ne': None, '$gt': 0},
            'correctAnswers': {'$ne': None}
        })
        
        total_percentage = 0
        valid_enrollments = 0
        
        for enrollment in enrollments:
            total_questions = enrollment.get('totalQuestions', 0)
            correct_answers = enrollment.get('correctAnswers', 0)
            
            if total_questions > 0:
                percentage = (correct_answers / total_questions) * 100
                total_percentage += percentage
                valid_enrollments += 1
        
        if valid_enrollments > 0:
            course_percentage = total_percentage / valid_enrollments
            return round(course_percentage, 2)
        else:
            return 0
            
    except Exception as e:
        print(f"Error en calculate_course_success_percentage: {str(e)}")
        return 0



# Estadísticas del estudiante en un curso específico


@teacher_statistics_blueprint.route('/student-course-stadistics/<course_id>/<student_id>', methods=['GET'])

def get_student_course_stadistics(course_id, student_id):
    try:
        db = current_app.db
        
        # Validar ids
        try:
            course_oid = ObjectId(course_id)
            student_oid = ObjectId(student_id)
        except:
            return jsonify({'error': 'ID de curso o estudiante inválido'}), 400
        
        # curso existe
        course = db.courses.find_one({'_id': course_oid})
        if not course:
            return jsonify({'error': 'Curso no encontrado'}), 404
        
        # estudiante existe
        student = db.users.find_one({'_id': student_oid})
        if not student:
            return jsonify({'error': 'Estudiante no encontrado'}), 404
        
        # estudiante está en el curso
        enrollment = db.enrolledCourses.find_one({
            'courseId': course_oid,
            'userId': student_oid
        })
        
        if not enrollment:
            return jsonify({'error': 'El estudiante no está inscrito en este curso'}), 404
        
        # progreso del estudiante
        progress = calculate_student_course_stadistics(db, course_oid, student_oid, enrollment)
        
        return jsonify(progress), 200
        
    except Exception as e:
        print(f"Error en get_student_course_progress: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

def calculate_student_course_stadistics(db, course_id, student_id, enrollment):
    try:
        # info del curso
        course = db.courses.find_one({'_id': course_id})
        if not course:
            return {'error': 'Curso no encontrado'}
        
        #info del estudiante
        student = db.users.find_one({'_id': student_id})
        if not student:
            return {'error': 'Estudiante no encontrado'}
        
        #porcentaje de éxito del curso del estudiante
        total_questions = enrollment.get('totalQuestions', 0)
        correct_answers = enrollment.get('correctAnswers', 0)
        overall_percentage = 0
        
        if total_questions and total_questions > 0 and correct_answers is not None:
            overall_percentage = (correct_answers / total_questions) * 100
        
        #Calcular lecciones completadas vs totales
        course_lessons = course.get('lessons', [])
        total_lessons = len(course_lessons)
        
        enrollment_completed_lessons = enrollment.get('completedLessons', [])
        completed_lessons_count = len(enrollment_completed_lessons)
        
        # Mapa de lecciones completadas por lessonId para más rápido
        completed_lessons_map = {}
        for completed_lesson in enrollment_completed_lessons:
            lesson_id = completed_lesson.get('lessonId')
            if lesson_id:
                completed_lessons_map[str(lesson_id)] = completed_lesson
        
        # Solo las lecciones completadas
        lessons_progress = []
        for lesson in course_lessons:
            lesson_id = str(lesson['_id'])
            completed_lesson = completed_lessons_map.get(lesson_id)
            
            #lecciones que están en completedLessons
            if completed_lesson:
                total_exercises = lesson.get('questionCount', 0)
                correct_count = completed_lesson.get('correctCount', 0)
                
                lesson_data = {
                    'lessonId': lesson_id,
                    'name': lesson.get('name', 'Lección sin nombre'),
                    'correctCount': correct_count,
                    'questionCount': total_exercises
                }
                lessons_progress.append(lesson_data)
        

        progress_data = {
            'studentName': student.get('name', 'Estudiante sin nombre'),
            'successPercentage': round(overall_percentage, 2),
            'lessonsProgress': lessons_progress,
            'lessonsSummary': {
                'completed': completed_lessons_count,
                'total': total_lessons,
                'completionPercentage': round((completed_lessons_count / total_lessons * 100) if total_lessons > 0 else 0, 2)
            }
        }
        
        return progress_data
        
    except Exception as e:
        print(f"Error en calculate_student_course_progress: {str(e)}")
        return {
            'studentName': 'Error al cargar nombre',
            'successPercentage': 0,
            'lessonsProgress': [],
            'lessonsSummary': {
                'completed': 0,
                'total': 0,
                'completionPercentage': 0
            }
        }
    except Exception as e:
        print(f"Error en calculate_student_course_progress: {str(e)}")
        return {
            'studentName': 'Error al cargar nombre',
            'successPercentage': 0,
            'lessonsProgress': []
        }

#estadísticas para app por curso
@teacher_statistics_blueprint.route('/course-lessons-statistics/<course_id>', methods=['GET'])
def get_course_lessons_statistics(course_id):
    try:
        db = current_app.db
        
        # Validar id
        try:
            course_oid = ObjectId(course_id)
        except:
            return jsonify({'error': 'ID de curso inválido'}), 400
        
        # curso existe
        course = db.courses.find_one({'_id': course_oid})
        if not course:
            return jsonify({'error': 'Curso no encontrado'}), 404
        
        #estadísticas del curso
        course_statistics = calculate_course_lessons_statistics(db, course_oid)
        
        return jsonify(course_statistics), 200
        
    except Exception as e:
        print(f"Error en get_course_lessons_statistics: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

def calculate_course_lessons_statistics(db, course_id):
    
    #Calcula las estadísticas detalladas de un curso con porcentaje por lección
    
    try:
        #info del curso
        course = db.courses.find_one({'_id': course_id})
        if not course:
            return {'error': 'Curso no encontrado'}
        
        # Calcular porcentaje de éxito del curso
        course_success_percentage = calculate_course_success_percentage(db, course_id)
        
        #inscripciones del curso
        enrollments = db.enrolledCourses.find({'courseId': course_id})
        
        # Procesar lecciones 
        lessons_statistics = []
        course_lessons = course.get('lessons', [])
        
        for lesson in course_lessons:
            lesson_id = str(lesson['_id'])
            lesson_name = lesson.get('name', 'Lección sin nombre')
            total_exercises = lesson.get('questionCount', 0)
            
            # calcular porcentaje de éxito para la lección
            lesson_success_percentage = calculate_lesson_success_percentage(db, course_id, lesson_id, total_exercises)
            
            lesson_data = {
                'lessonId': lesson_id,
                'name': lesson_name,
                'successPercentage': lesson_success_percentage,
                'totalExercises': total_exercises
            }
            lessons_statistics.append(lesson_data)
        
        
        statistics = {
            'courseInfo': {
                'courseId': str(course['_id']),
                'name': course.get('name', 'Curso sin nombre'),
                'successPercentage': course_success_percentage
            },
            'lessonsStatistics': lessons_statistics
        }
        
        return statistics
        
    except Exception as e:
        print(f"Error en calculate_course_lessons_statistics: {str(e)}")
        return {
            'courseInfo': {
                'courseId': str(course_id),
                'name': 'Error al cargar información',
                'successPercentage': 0
            },
            'lessonsStatistics': []
        }

def calculate_lesson_success_percentage(db, course_id, lesson_id, total_exercises):
    
    #Calcula el porcentaje de éxito para una lección específica
    
    try:
        # Obtener todas las inscripciones(en enrolled coursess) del curso que tienen esta lección completada
        enrollments = db.enrolledCourses.find({
            'courseId': course_id,
            'completedLessons.lessonId': ObjectId(lesson_id)
        })
        
        total_lesson_percentage = 0
        valid_students = 0
        
        for enrollment in enrollments:
            # Buscar la lección completada específica
            completed_lesson = None
            for comp_lesson in enrollment.get('completedLessons', []):
                if str(comp_lesson.get('lessonId')) == lesson_id:
                    completed_lesson = comp_lesson
                    break
            
            if completed_lesson:
                correct_count = completed_lesson.get('correctCount', 0)
                
                # calcular porcentaje del estudiante para esta lección
                if total_exercises > 0:
                    student_lesson_percentage = (correct_count / total_exercises) * 100
                    total_lesson_percentage += student_lesson_percentage
                    valid_students += 1
        
        # Si nadie ha completado la lección retorna mensaje 
        if valid_students == 0:
            return "No completada"
        
        #calcular promedio del porcentaje de la lección
        lesson_percentage = total_lesson_percentage / valid_students
        return round(lesson_percentage, 2)
            
    except Exception as e:
        print(f"Error en calculate_lesson_success_percentage: {str(e)}")
        return "Error en cálculo"