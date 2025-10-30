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

# GET: Obtener una lección por su ID
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
            'theory': theory_data,  # Usar la teoría procesada
            'createdAt': lesson.get('createdAt'),
            'course': {
                'id': str(course['_id']),
                'name': course.get('name', 'Curso sin nombre')
            }
        }

        return jsonify(lesson_data), 200

    except Exception as e:
        print(f"Error en get_lesson_by_id: {str(e)}")
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


# PUT: Actualizar el orden de las lecciones de un curso
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
            lesson_id = lesson_data.get('lessonId')  # Usar lessonId que viene del frontend
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

# PUT: Eliminar múltiples lecciones
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
                print(f"🗑️ Marcada para eliminar: {lesson_id} - {lesson.get('name', '')}")  # Debug
            else:
                updated_lessons.append(lesson)

        print(f"Lecciones que permanecen: {len(updated_lessons)}")  # Debug
        print(f"Lecciones a eliminar: {len(deleted_lessons)}")  # Debug

        # Reordenar las lecciones restantes
        for index, lesson in enumerate(updated_lessons, 1):
            lesson['order'] = index
            print(f"🔢 Reordenando: {lesson.get('name', '')} -> orden {index}")  # Debug

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


# PUT: Actualizar una lección (nombre, foro y teoría)
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


# PUT: Actualizar solo el nombre de una lección
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