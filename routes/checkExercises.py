from flask import Blueprint, jsonify, current_app, request
from bson import ObjectId
from datetime import datetime

check_exercises_bp = Blueprint('check_exercises', __name__)

@check_exercises_bp.route('/courses/<course_id>/lessons/<lesson_id>/exercises/<exercise_id>', methods=['PUT'])
def update_exercise(course_id, lesson_id, exercise_id):
    """
    Actualizar un ejercicio específico dentro de una lección
    
    Espera un JSON con:
    {
        "question": "Nueva pregunta",
        "correctAnswer": ["Verdadero"]  // o ["Falso"]
    }
    """
    try:
        db = current_app.db
        data = request.get_json()
        
        # Validar datos requeridos
        if not data:
            return jsonify({'error': 'No se enviaron datos'}), 400
        
        question = data.get('question')
        correct_answer = data.get('correctAnswer')
        
        if not question or not correct_answer:
            return jsonify({'error': 'Faltan campos requeridos'}), 400
        
        # Validar que correctAnswer sea un array con "Verdadero" o "Falso"
        if not isinstance(correct_answer, list) or correct_answer[0] not in ["Verdadero", "Falso"]:
            return jsonify({'error': 'correctAnswer debe ser ["Verdadero"] o ["Falso"]'}), 400
        
        # Buscar el curso
        course = db.courses.find_one({'_id': ObjectId(course_id)})
        
        if not course:
            return jsonify({'error': 'Curso no encontrado'}), 404
        
        # Buscar la lección dentro del curso
        lesson_found = False
        exercise_found = False
        
        for lesson in course.get('lessons', []):
            if str(lesson['_id']) == lesson_id:
                lesson_found = True
                
                # Buscar el ejercicio dentro de la lección
                for exercise in lesson.get('exercises', []):
                    if str(exercise['_id']) == exercise_id:
                        exercise_found = True
                        
                        # Actualizar el ejercicio usando $set con notación de punto
                        result = db.courses.update_one(
                            {
                                '_id': ObjectId(course_id),
                                'lessons._id': ObjectId(lesson_id),
                                'lessons.exercises._id': ObjectId(exercise_id)
                            },
                            {
                                '$set': {
                                    'lessons.$[lesson].exercises.$[exercise].question': question,
                                    'lessons.$[lesson].exercises.$[exercise].correctAnswer': correct_answer
                                }
                            },
                            array_filters=[
                                {'lesson._id': ObjectId(lesson_id)},
                                {'exercise._id': ObjectId(exercise_id)}
                            ]
                        )
                        
                        if result.modified_count == 0:
                            return jsonify({'error': 'No se pudo actualizar el ejercicio'}), 500
                        
                        return jsonify({
                            'message': 'Ejercicio actualizado exitosamente',
                            'exerciseId': exercise_id,
                            'question': question,
                            'correctAnswer': correct_answer
                        }), 200
        
        if not lesson_found:
            return jsonify({'error': 'Lección no encontrada'}), 404
        
        if not exercise_found:
            return jsonify({'error': 'Ejercicio no encontrado'}), 404
        
    except Exception as e:
        print(f"Error actualizando ejercicio: {e}")
        return jsonify({'error': 'Error interno del servidor', 'details': str(e)}), 500


@check_exercises_bp.route('/courses/<course_id>/lessons/<lesson_id>/exercises/<exercise_id>', methods=['GET'])
def get_exercise(course_id, lesson_id, exercise_id):
    """
    Obtener un ejercicio específico
    """
    try:
        db = current_app.db
        
        course = db.courses.find_one(
            {
                '_id': ObjectId(course_id),
                'lessons._id': ObjectId(lesson_id)
            },
            {
                'lessons.$': 1
            }
        )
        
        if not course:
            return jsonify({'error': 'Curso o lección no encontrada'}), 404
        
        lesson = course['lessons'][0]
        exercise = next(
            (ex for ex in lesson.get('exercises', []) if str(ex['_id']) == exercise_id),
            None
        )
        
        if not exercise:
            return jsonify({'error': 'Ejercicio no encontrado'}), 404
        
        # Convertir ObjectIds a strings para JSON
        exercise['_id'] = str(exercise['_id'])
        if 'sign' in exercise:
            exercise['sign'] = str(exercise['sign'])
        
        return jsonify(exercise), 200
        
    except Exception as e:
        print(f"Error obteniendo ejercicio: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500