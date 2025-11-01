# routes/teacherActivities.py
from flask import Blueprint, jsonify, current_app, request
from bson import ObjectId
from datetime import datetime

teacher_activities_blueprint = Blueprint('teacherActivities', __name__)

# GET: Obtener una actividad por su ID =======================================
@teacher_activities_blueprint.route('/activity/<activity_id>', methods=['GET'])
def get_activity(activity_id):
    try:
        db = current_app.db
        
        # Validar que el ID sea válido
        if not ObjectId.is_valid(activity_id):
            return jsonify({'error': 'ID de actividad no válido'}), 400
            
        activity_oid = ObjectId(activity_id)

        # Buscar curso que contenga la actividad en sus lecciones
        course = db.courses.find_one({'lessons.exercises._id': activity_oid})
        if not course:
            return jsonify({'error': 'Actividad no encontrada'}), 404

        # Buscar la lección y actividad específica
        lesson = None
        activity = None
        
        for l in course['lessons']:
            for ex in l.get('exercises', []):
                if ex['_id'] == activity_oid:
                    lesson = l
                    activity = ex
                    break
            if activity:
                break

        if not activity:
            return jsonify({'error': 'Actividad no encontrada en la lección'}), 404

        # Construir respuesta
        activity_data = {
            'id': str(activity['_id']),
            'exerciseType': activity.get('exerciseType', 0),
            'order': activity.get('order', 0),
            'question': activity.get('question', ''),
            'possibleAnswers': activity.get('possibleAnswers', []),
            'correctAnswer': activity.get('correctAnswer', []),
            'sign': str(activity.get('sign', '')) if activity.get('sign') else None,
            'lesson': {
                'id': str(lesson['_id']),
                'name': lesson.get('name', 'Lección sin nombre')
            },
            'course': {
                'id': str(course['_id']),
                'name': course.get('name', 'Curso sin nombre')
            }
        }

        return jsonify(activity_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# PUT: Actualizar una actividad =======================================
@teacher_activities_blueprint.route('/activity/<activity_id>', methods=['PUT'])
def update_activity(activity_id):
    try:
        db = current_app.db
        
        # Validar que el ID sea válido
        if not ObjectId.is_valid(activity_id):
            return jsonify({'error': 'ID de actividad no válido'}), 400
            
        activity_oid = ObjectId(activity_id)
        data = request.get_json()

        # Validaciones básicas
        if not data:
            return jsonify({'error': 'No se proporcionaron datos para actualizar'}), 400

        # Buscar curso que contenga la actividad
        course = db.courses.find_one({'lessons.exercises._id': activity_oid})
        if not course:
            return jsonify({'error': 'Actividad no encontrada'}), 404

        # Validar según el tipo de ejercicio
        exercise_type = data.get('exerciseType')
        
        if exercise_type == 1:  # Selección única
            errors = validate_single_selection(data)
            if errors:
                return jsonify({'error': errors}), 400
                
        elif exercise_type == 3:  # Ordenar frase
            errors = validate_order_phrase(data)
            if errors:
                return jsonify({'error': errors}), 400
        else:
            return jsonify({'error': 'Tipo de ejercicio no soportado'}), 400

        # Preparar campos a actualizar
        update_fields = {}
        
        if 'question' in data:
            update_fields['lessons.$[lesson].exercises.$[exercise].question'] = data['question']
        
        if 'possibleAnswers' in data:
            update_fields['lessons.$[lesson].exercises.$[exercise].possibleAnswers'] = data['possibleAnswers']
        
        if 'correctAnswer' in data:
            update_fields['lessons.$[lesson].exercises.$[exercise].correctAnswer'] = data['correctAnswer']
        
        if 'sign' in data:
            # Convertir string a ObjectId si es válido, sino dejarlo como string
            if data['sign'] and ObjectId.is_valid(data['sign']):
                update_fields['lessons.$[lesson].exercises.$[exercise].sign'] = ObjectId(data['sign'])
            else:
                update_fields['lessons.$[lesson].exercises.$[exercise].sign'] = data['sign']

        # Si no hay campos para actualizar
        if not update_fields:
            return jsonify({'error': 'No se proporcionaron campos válidos para actualizar'}), 400

        # Actualizar en la base de datos usando arrayFilters
        result = db.courses.update_one(
            {'lessons.exercises._id': activity_oid},
            {'$set': update_fields},
            array_filters=[
                {'lesson.exercises._id': activity_oid},
                {'exercise._id': activity_oid}
            ]
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Actividad no encontrada'}), 404

        if result.modified_count == 0:
            return jsonify({'message': 'No se realizaron cambios (los datos ya estaban actualizados)'}), 200

        return jsonify({
            'message': 'Actividad actualizada correctamente',
            'updated_fields': list(update_fields.keys())
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Validaciones para Selección Única =======================================
def validate_single_selection(data):
    errors = []
    
    # Validar pregunta
    question = data.get('question', '').strip()
    if not question:
        errors.append('La pregunta es requerida')
    
    # Validar opciones (deben ser exactamente 4)
    possible_answers = data.get('possibleAnswers', [])
    if len(possible_answers) != 4:
        errors.append('Debe haber exactamente 4 opciones')
    else:
        for i, answer in enumerate(possible_answers):
            if not answer or not answer.strip():
                errors.append(f'La opción {i+1} no puede estar vacía')
    
    # Validar respuesta correcta
    correct_answer = data.get('correctAnswer', [])
    if len(correct_answer) != 1:
        errors.append('Debe haber exactamente una respuesta correcta')
    elif correct_answer[0] not in possible_answers:
        errors.append('La respuesta correcta debe estar entre las opciones posibles')
    
    return ', '.join(errors) if errors else None

# Validaciones para Ordenar Frase =======================================
def validate_order_phrase(data):
    errors = []
    
    # Validar pregunta
    question = data.get('question', '').strip()
    if not question:
        errors.append('La pregunta es requerida')
    
    # Validar palabras (mínimo 2)
    possible_answers = data.get('possibleAnswers', [])
    if len(possible_answers) < 2:
        errors.append('Debe haber al menos 2 palabras para ordenar')
    else:
        for i, word in enumerate(possible_answers):
            if not word or not word.strip():
                errors.append(f'La palabra {i+1} no puede estar vacía')
    
    # Validar respuesta correcta
    correct_answer = data.get('correctAnswer', [])
    if len(correct_answer) != len(possible_answers):
        errors.append('El orden correcto debe tener la misma cantidad de palabras que las opciones')
    else:
        # Verificar que todas las palabras de possibleAnswers estén en correctAnswer
        for word in possible_answers:
            if word not in correct_answer:
                errors.append(f'La palabra "{word}" debe estar en el orden correcto')
        # Verificar que no haya palabras extrañas en correctAnswer
        for word in correct_answer:
            if word not in possible_answers:
                errors.append(f'La palabra "{word}" no existe en las opciones')
    
    return ', '.join(errors) if errors else None