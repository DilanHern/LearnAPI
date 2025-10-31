# routes/teacherLessons.py
from flask import Blueprint, jsonify, current_app, request
from bson import ObjectId
from datetime import datetime

teacher_lessons_blueprint = Blueprint('teacherLessons', __name__)

# Obtener curso completo por course_id =======================================
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

# GET: Obtener una lección por su ID ===========================================
@teacher_lessons_blueprint.route('/lesson/<lesson_id>', methods=['GET'])
def get_lesson(lesson_id):
    try:
        db = current_app.db
        lesson_oid = ObjectId(lesson_id)

        # Buscar curso que contenga la lección
        course = db.courses.find_one({'lessons._id': lesson_oid})
        if not course:
            return jsonify({'error': 'Lección no encontrada'}), 404

        # Buscar la lección dentro del curso
        lesson = next((l for l in course['lessons'] if l['_id'] == lesson_oid), None)
        if not lesson:
            return jsonify({'error': 'Lección no encontrada en el curso'}), 404

        # Procesar la teoría para convertir ObjectIds a strings
        theory_data = []
        if lesson.get('theory'):
            for theory_item in lesson['theory']:
                processed_item = {}
                if 'text' in theory_item:
                    processed_item['text'] = theory_item['text']
                if 'sign' in theory_item:
                    # Convertir ObjectId a string
                    if isinstance(theory_item['sign'], ObjectId):
                        processed_item['sign'] = str(theory_item['sign'])
                    else:
                        processed_item['sign'] = theory_item['sign']
                theory_data.append(processed_item)

        # Construir datos de respuesta
        lesson_data = {
            'id': str(lesson['_id']),
            'name': lesson.get('name', 'Lección sin nombre'),
            'order': lesson.get('order', 0),
            'questionCount': lesson.get('questionCount', 0),
            'attempts': lesson.get('attempts', 0),
            'forumEnabled': lesson.get('forumEnabled', True),
            'theory': theory_data,
            'course': {
                'id': str(course['_id']),
                'name': course.get('name', 'Curso sin nombre')
            }
        }

        return jsonify(lesson_data), 200

    except Exception as e:
        print(f"Error en get_lesson_by_id: {str(e)}")
        return jsonify({'error': str(e)}), 500


# POST: Añadir una lección a un curso =======================================
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


# PUT: Actualizar el orden de las lecciones de un curso =======================================
@teacher_lessons_blueprint.route('/course/<course_id>/lessons/reorder', methods=['PUT'])
def reorder_lessons(course_id):
    try:
        db = current_app.db
        course_oid = ObjectId(course_id)

        data = request.get_json()
        lessons_data = data.get('lessons')

        if not lessons_data or not isinstance(lessons_data, list):
            return jsonify({'error': 'Se requiere una lista válida de lecciones'}), 400

        # Buscar curso
        course = db.courses.find_one({'_id': course_oid})
        if not course:
            return jsonify({'error': 'Curso no encontrado'}), 404

        lessons = course.get('lessons', [])
        
        # Crear un diccionario con los nuevos órdenes usando lessonId del frontend
        order_map = {}
        for lesson_data in lessons_data:
            lesson_id = lesson_data.get('id')
            new_order = lesson_data.get('order')
            if lesson_id and new_order is not None:
                order_map[lesson_id] = new_order

        print(f"Order map recibido: {order_map}")  # Debug

        # Actualizar los órdenes en el arreglo
        updated_count = 0
        for lesson in lessons:
            lesson_id = str(lesson['_id'])
            if lesson_id in order_map:
                lesson['order'] = order_map[lesson_id]
                updated_count += 1

        print(f"Lecciones actualizadas: {updated_count}")  # Debug

        # Guardar el curso actualizado
        db.courses.update_one({'_id': course_oid}, {'$set': {'lessons': lessons}})

        return jsonify({
            'message': 'Orden actualizado correctamente',
            'updated_count': updated_count
        }), 200

    except Exception as e:
        print(f"Error en reorder_lessons: {str(e)}")  # Debug
        return jsonify({'error': str(e)}), 500

# PUT: Eliminar múltiples lecciones =======================================
@teacher_lessons_blueprint.route('/course/<course_id>/lessons/delete', methods=['PUT'])
def delete_multiple_lessons(course_id):
    try:
        db = current_app.db
        course_oid = ObjectId(course_id)

        data = request.get_json()
        lessons_to_delete = data.get('lessonsToDelete', [])
        
        print(f"Lecciones a eliminar recibidas: {lessons_to_delete}")  # Debug

        if not lessons_to_delete or not isinstance(lessons_to_delete, list):
            return jsonify({'error': 'Se requiere una lista válida de lecciones a eliminar'}), 400

        # Buscar el curso
        course = db.courses.find_one({'_id': course_oid})
        if not course:
            return jsonify({'error': 'Curso no encontrado'}), 404

        print(f"Curso encontrado: {course['name']}")  # Debug
        print(f"Lecciones antes: {len(course.get('lessons', []))}")  # Debug

        # Filtrar lecciones, removiendo las que están en la lista de eliminación
        lessons = course.get('lessons', [])
        updated_lessons = []
        deleted_lessons = []
        
        for lesson in lessons:
            lesson_id = str(lesson['_id'])
            if lesson_id in lessons_to_delete:
                deleted_lessons.append({
                    'id': lesson_id,
                    'name': lesson.get('name', '')
                })
                print(f"Marcada para eliminar: {lesson_id} - {lesson.get('name', '')}")  # Debug
            else:
                updated_lessons.append(lesson)

        print(f"Lecciones que permanecen: {len(updated_lessons)}")  # Debug
        print(f"Lecciones a eliminar: {len(deleted_lessons)}")  # Debug

        # Reordenar las lecciones restantes
        for index, lesson in enumerate(updated_lessons, 1):
            lesson['order'] = index
            print(f"Reordenando: {lesson.get('name', '')} -> orden {index}")  # Debug

        # Actualizar el curso en la base de datos
        db.courses.update_one(
            {'_id': course_oid},
            {'$set': {'lessons': updated_lessons}}
        )

        return jsonify({
            'message': 'Lecciones eliminadas correctamente',
            'deleted_count': len(deleted_lessons),
            'deleted_lessons': deleted_lessons,
            'remaining_lessons': len(updated_lessons)
        }), 200

    except Exception as e:
        print(f"Error en delete_multiple_lessons: {str(e)}")
        return jsonify({'error': str(e)}), 500


# PUT: Actualizar una lección (nombre, foro y teoría) =======================================
@teacher_lessons_blueprint.route('/lesson/<lesson_id>', methods=['PUT'])
def update_lesson(lesson_id):
    try:
        db = current_app.db
        lesson_oid = ObjectId(lesson_id)

        # Obtener datos del body
        data = request.get_json()
        
        # Buscar curso que contenga la lección
        course = db.courses.find_one({'lessons._id': lesson_oid})
        if not course:
            return jsonify({'error': 'Lección no encontrada'}), 404

        # Preparar campos a actualizar
        update_fields = {}
        
        # Actualizar nombre si viene en el request
        if 'name' in data:
            update_fields['lessons.$.name'] = data['name']
        
        # Actualizar forumEnabled si viene en el request
        if 'forumEnabled' in data:
            update_fields['lessons.$.forumEnabled'] = data['forumEnabled']
        
        # Actualizar teoría si viene en el request
        if 'theory' in data:
            # Procesar la teoría para convertir strings a ObjectIds si es necesario
            processed_theory = []
            for theory_item in data['theory']:
                processed_item = {}
                if 'text' in theory_item:
                    processed_item['text'] = theory_item['text']
                if 'sign' in theory_item:
                    # Si es un ObjectId válido, convertirlo, sino dejarlo como string
                    if theory_item['sign'] and ObjectId.is_valid(theory_item['sign']):
                        processed_item['sign'] = ObjectId(theory_item['sign'])
                    else:
                        processed_item['sign'] = theory_item['sign']
                processed_theory.append(processed_item)
            
            update_fields['lessons.$.theory'] = processed_theory

        # Si no hay campos para actualizar
        if not update_fields:
            return jsonify({'error': 'No se proporcionaron campos para actualizar'}), 400

        # Actualizar la lección en la base de datos
        result = db.courses.update_one(
            {'lessons._id': lesson_oid},
            {'$set': update_fields}
        )

        if result.modified_count == 0:
            return jsonify({'error': 'No se realizaron cambios en la lección'}), 400

        return jsonify({
            'message': 'Lección actualizada correctamente',
            'updated_fields': list(update_fields.keys())
        }), 200

    except Exception as e:
        print(f"Error en update_lesson: {str(e)}")
        return jsonify({'error': str(e)}), 500


# PUT: Actualizar solo el nombre de una lección =======================================
@teacher_lessons_blueprint.route('/lesson/<lesson_id>/name', methods=['PUT'])
def update_lesson_name(lesson_id):
    try:
        db = current_app.db
        lesson_oid = ObjectId(lesson_id)

        # Obtener datos del body
        data = request.get_json()
        
        # Validar que venga el nombre
        if 'name' not in data:
            return jsonify({'error': 'El campo "name" es requerido'}), 400
        
        new_name = data['name'].strip()
        if not new_name:
            return jsonify({'error': 'El nombre no puede estar vacío'}), 400

        # Buscar curso que contenga la lección y actualizar solo el nombre
        result = db.courses.update_one(
            {'lessons._id': lesson_oid},
            {'$set': {'lessons.$.name': new_name}}
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Lección no encontrada'}), 404

        if result.modified_count == 0:
            return jsonify({'message': 'El nombre ya estaba actualizado', 'name': new_name}), 200

        return jsonify({
            'message': 'Nombre de lección actualizado correctamente',
            'name': new_name
        }), 200

    except Exception as e:
        print(f"Error en update_lesson_name: {str(e)}")
        return jsonify({'error': str(e)}), 500


# GET: Obtener todas las actividades de una lección =======================================
@teacher_lessons_blueprint.route('/lesson/<lesson_id>/activities', methods=['GET'])
def get_lesson_activities(lesson_id):
    try:
        db = current_app.db
        lesson_oid = ObjectId(lesson_id)

        # Buscar curso que contenga la lección
        course = db.courses.find_one({'lessons._id': lesson_oid})
        if not course:
            return jsonify({'error': 'Lección no encontrada'}), 404

        # Buscar la lección específica
        lesson = next((l for l in course['lessons'] if l['_id'] == lesson_oid), None)
        if not lesson:
            return jsonify({'error': 'Lección no encontrada en el curso'}), 404

        # Obtener las actividades (exercises) de la lección
        exercises = lesson.get('exercises', [])
        
        # Mapear los tipos de ejercicio a nombres más descriptivos
        exercise_type_map = {
            1: "Selección única",
            2: "Verdadero o falso", 
            3: "Ordenar frase",
            # Puedes agregar más tipos según necesites
        }

        # Formatear las actividades para la respuesta
        exercises_list = []
        for exercise in exercises:
            exercise_type = exercise.get('exerciseType', 0)
            exercise_data = {
                'id': str(exercise['_id']),
                'type': exercise_type,
                'typeName': exercise_type_map.get(exercise_type, f"Tipo {exercise_type}"),
                'order': exercise.get('order', 0),
            }
            exercises_list.append(exercise_data)

        # Ordenar por orden
        exercises_list.sort(key=lambda x: x['order'])

        # Incluir información básica de la lección en la respuesta
        response_data = {
            'lesson': {
                'id': str(lesson['_id']),
                'name': lesson.get('name', 'Lección sin nombre'),
                'questionCount': lesson.get('questionCount', 0),
                'attempts': lesson.get('attempts', 0),
                'forumEnabled': lesson.get('forumEnabled', True),
                'course': {
                    'id': str(course['_id']),
                    'name': course.get('name', 'Curso sin nombre')
                }
            },
            'activities': exercises_list,
            'totalActivities': len(exercises_list)
        }

        return jsonify(response_data), 200

    except Exception as e:
        print(f"Error en get_lesson_activities: {str(e)}")
        return jsonify({'error': str(e)}), 500


# POST: Crear una nueva actividad/ejercicio en una lección ======================================= 
@teacher_lessons_blueprint.route('/lesson/<lesson_id>/activity', methods=['POST'])
def create_activity(lesson_id):
    try:
        db = current_app.db
        lesson_oid = ObjectId(lesson_id)

        # Obtener datos del body
        data = request.get_json()
        
        # Validar campos requeridos
        if 'exerciseType' not in data:
            return jsonify({'error': 'El tipo de ejercicio es requerido'}), 400
        
        exercise_type = data['exerciseType']
        
        # Buscar curso que contenga la lección
        course = db.courses.find_one({'lessons._id': lesson_oid})
        if not course:
            return jsonify({'error': 'Lección no encontrada'}), 404

        # Buscar la lección específica
        lesson = next((l for l in course['lessons'] if l['_id'] == lesson_oid), None)
        if not lesson:
            return jsonify({'error': 'Lección no encontrada en el curso'}), 404

        # Obtener las actividades existentes para determinar el siguiente orden
        exercises = lesson.get('exercises', [])
        next_order = len(exercises) + 1

        # Crear el nuevo objeto de ejercicio (solo con campos básicos)
        new_exercise = {
            '_id': ObjectId(),
            'exerciseType': exercise_type,
            'order': next_order
        }

        # Actualizar la lección agregando el nuevo ejercicio
        result = db.courses.update_one(
            {'lessons._id': lesson_oid},
            {'$push': {'lessons.$.exercises': new_exercise}}
        )

        if result.modified_count == 0:
            return jsonify({'error': 'No se pudo agregar la actividad a la lección'}), 400

        # Incrementar el contador de preguntas de la lección
        db.courses.update_one(
            {'lessons._id': lesson_oid},
            {'$inc': {'lessons.$.questionCount': 1}}
        )

        # Mapear tipos de ejercicio a nombres descriptivos
        exercise_type_map = {
            1: "Selección única",
            2: "Verdadero o falso", 
            3: "Ordenar frase",
        }

        return jsonify({
            'message': 'Actividad creada correctamente',
            'activity': {
                'id': str(new_exercise['_id']),
                'type': new_exercise['exerciseType'],
                'typeName': exercise_type_map.get(new_exercise['exerciseType'], f"Tipo {new_exercise['exerciseType']}"),
                'order': new_exercise['order']
            }
        }), 201

    except Exception as e:
        print(f"Error en create_activity: {str(e)}")
        return jsonify({'error': str(e)}), 500


# PUT: Actualizar actividades - intentos, orden y eliminar actividades
@teacher_lessons_blueprint.route('/lesson/<lesson_id>/update-activities', methods=['PUT'])
def update_activities(lesson_id):
    try:
        db = current_app.db
        lesson_oid = ObjectId(lesson_id)

        # Obtener datos del body
        data = request.get_json()
        
        # Buscar curso que contenga la lección
        course = db.courses.find_one({'lessons._id': lesson_oid})
        if not course:
            return jsonify({'error': 'Lección no encontrada'}), 404

        # Buscar la lección específica
        lesson_index = None
        lesson = None
        for i, l in enumerate(course['lessons']):
            if l['_id'] == lesson_oid:
                lesson_index = i
                lesson = l
                break

        if not lesson:
            return jsonify({'error': 'Lección no encontrada en el curso'}), 404

        # Preparar actualizaciones
        update_fields = {}
        activities_to_delete = data.get('activitiesToDelete', [])
        activities_order = data.get('activitiesOrder', [])
        attempts = data.get('attempts')

        # 1. Actualizar intentos si viene en el request
        if attempts is not None:
            update_fields[f'lessons.{lesson_index}.attempts'] = attempts

        # 2. Procesar eliminación de actividades
        current_exercises = lesson.get('exercises', [])
        if activities_to_delete and isinstance(activities_to_delete, list):
            # Convertir a ObjectIds para comparar
            activities_to_delete_oids = [ObjectId(activity_id) for activity_id in activities_to_delete]
            
            # Filtrar ejercicios, removiendo los que están en la lista de eliminación
            updated_exercises = [ex for ex in current_exercises if ex['_id'] not in activities_to_delete_oids]
            
            # Actualizar el campo de ejercises
            update_fields[f'lessons.{lesson_index}.exercises'] = updated_exercises
            
            # Actualizar el contador de preguntas
            deleted_count = len(current_exercises) - len(updated_exercises)
            update_fields[f'lessons.{lesson_index}.questionCount'] = lesson.get('questionCount', 0) - deleted_count
            
            print(f"Eliminando {deleted_count} actividades: {activities_to_delete}")
        else:
            updated_exercises = current_exercises

        # 3. Procesar reordenamiento de actividades
        if activities_order and isinstance(activities_order, list):
            # Crear un mapa de nuevos órdenes
            order_map = {}
            for activity_data in activities_order:
                activity_id = activity_data.get('id')
                new_order = activity_data.get('order')
                if activity_id and new_order is not None:
                    order_map[activity_id] = new_order

            # Actualizar los órdenes en los ejercicios
            for exercise in updated_exercises:
                exercise_id = str(exercise['_id'])
                if exercise_id in order_map:
                    exercise['order'] = order_map[exercise_id]
                    print(f"Reordenando actividad {exercise_id} -> orden {order_map[exercise_id]}")

            # Asegurarse de que los ejercicios estén ordenados
            updated_exercises.sort(key=lambda x: x.get('order', 0))
            
            # Actualizar el campo de ejercises con el nuevo orden
            update_fields[f'lessons.{lesson_index}.exercises'] = updated_exercises

        # Si no hay campos para actualizar
        if not update_fields:
            # En lugar de error, retornar éxito indicando que no había cambios
            return jsonify({
                'message': 'No se realizaron cambios (los datos ya estaban actualizados)',
                'deleted_count': 0,
                'reordered_count': 0,
                'attempts_updated': False,
                'no_changes': True
            }), 200

        # Actualizar en la base de datos
        result = db.courses.update_one(
            {'_id': course['_id']},
            {'$set': update_fields}
        )

        if result.modified_count == 0:
            # Si no se modificó nada, también es éxito (datos ya estaban actualizados)
            return jsonify({
                'message': 'No se realizaron cambios (los datos ya estaban actualizados)',
                'deleted_count': 0,
                'reordered_count': 0,
                'attempts_updated': False,
                'no_changes': True
            }), 200

        return jsonify({
            'message': 'Actividades actualizadas correctamente',
            'deleted_count': len(activities_to_delete) if activities_to_delete else 0,
            'reordered_count': len(activities_order) if activities_order else 0,
            'attempts_updated': attempts is not None,
            'no_changes': False
        }), 200

    except Exception as e:
        print(f"Error en update_activities: {str(e)}")
        return jsonify({'error': str(e)}), 500