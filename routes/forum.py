from flask import Blueprint, jsonify, current_app, request
from bson import ObjectId
from datetime import datetime
import re

forum_blueprint = Blueprint('forum', __name__)

# Iniciales para el avatar
def get_initials(name):
    # Se divide el nombre por espacios
    parts = name.split()
    if len(parts) >= 2:
        # Obtiene la primera letra de las dos primeras palabras
        return f"{parts[0][0]}{parts[1][0]}".upper()
    elif len(parts) == 1:
        # Obtiene las dos primeras letras de la primera palabra
        return parts[0][:2].upper()

def time_ago(date):
    now = datetime.utcnow()
    diff = now - date
    total_seconds = diff.total_seconds()
    
    if total_seconds < 60:
        return "ahora"
    
    minutes = total_seconds // 60
    if minutes < 60:
        return f"{int(minutes)} minutos"
    
    hours = minutes // 60
    if hours < 24:
        return f"{int(hours)} horas"
    
    days = hours // 24
    if days < 7:
        return f"{int(days)} días"
    
    weeks = days // 7
    if weeks < 4:
        return f"{int(weeks)} semanas"
    
    months = days // 30
    if months < 12:
        return f"{int(months)} meses"
    
    years = days // 365
    return f"{int(years)} años"

@forum_blueprint.route('/create-post/<lesson_id>/<user_id>', methods=['POST'])
def create_forum_post(lesson_id, user_id):
    try:
        db = current_app.db
        lesson_oid = ObjectId(lesson_id)
        user_oid = ObjectId(user_id)
        
        # Obtener datos del body
        data = request.get_json()
        content = data.get('content')
        video_url = data.get('videoURL', None)  
        
        # Validar campos requeridos
        if not content:
            return jsonify({'error': 'El contenido es requerido'}), 400
        
        # Verificar que el usuario existe
        user = db.users.find_one({'_id': user_oid})
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
    
        # Verificar que la lección existe (buscar en cursos)
        course = db.courses.find_one({'lessons._id': lesson_oid})
        if not course:
            return jsonify({'error': 'Lección no encontrada'}), 404
        
        # Crear el post en el foro
        forum_post = {
            'lessonId': lesson_oid,
            'userId': user_oid,
            'content': content,
            'videoURL': video_url,  
            'creationDate': datetime.utcnow(),
            'comments': []  
        }
        
        forum_id = db.forums.insert_one(forum_post).inserted_id
        
        return jsonify({
            'message': 'Post creado exitosamente',
            'forumId': str(forum_id)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@forum_blueprint.route('/comment/<forum_id>/<user_id>', methods=['POST'])
def add_comment(forum_id, user_id):
    try:
        db = current_app.db
        forum_oid = ObjectId(forum_id)
        user_oid = ObjectId(user_id)
        
        # Obtener datos del body
        data = request.get_json()
        content = data.get('content')
        video_url = data.get('videoURL', None)  
        
        # Validar campos requeridos
        if not content:
            return jsonify({'error': 'El contenido del comentario es requerido'}), 400
        
        # Verificar que el usuario existe
        user = db.users.find_one({'_id': user_oid})
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Verificar que el post del foro existe
        forum_post = db.forums.find_one({'_id': forum_oid})
        if not forum_post:
            return jsonify({'error': 'Post del foro no encontrado'}), 404
        
        # Crear el comentario
        comment = {
            '_id': ObjectId(),  
            'userId': user_oid,
            'content': content,
            'videoURL': video_url,  
            'date': datetime.utcnow()
        }
        
        # Agregar el comentario al array del post
        db.forums.update_one(
            {'_id': forum_oid},
            {'$push': {'comments': comment}}
        )
        
        return jsonify({
            'message': 'Comentario agregado exitosamente',
            'commentId': str(comment['_id'])
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@forum_blueprint.route('/get-forums/<lesson_id>', methods=['GET'])
def get_forum(lesson_id):
    try:
        db = current_app.db
        lesson_oid = ObjectId(lesson_id)
        
        # Buscar la lección en courses para obtener nombre y profesor
        course = db.courses.find_one({'lessons._id': lesson_oid}, {'lessons.$': 1, 'userId': 1})
        if not course:
            return jsonify({'error': 'Lección no encontrada'}), 404
        
        lesson = course['lessons'][0]
        lesson_name = lesson['name']
        
        # Obtener nombre del profesor
        teacher = db.users.find_one({'_id': course['userId']}, {'name': 1})
        teacher_name = teacher['name'] if teacher else 'Profesor desconocido'
        
        # Buscar todos los foros de la lección
        forums = list(db.forums.find({'lessonId': lesson_oid}))
        
        forum_data = []
        for forum in forums:
            # Obtener nombre del usuario que creó el post
            user = db.users.find_one({'_id': forum['userId']}, {'name': 1})
            user_name = user['name'] if user else 'Usuario desconocido'
            
            # Contar comentarios
            comment_count = len(forum.get('comments', []))
            
            # Obtener el comentario más reciente (si hay)
            latest_comment = None
            if comment_count > 0:
                comments = sorted(forum['comments'], key=lambda x: x['date'], reverse=True)
                latest = comments[0]
                latest_user = db.users.find_one({'_id': latest['userId']}, {'name': 1})
                latest_comment = {
                    'userName': latest_user['name'],
                    'content': latest['content'],
                    'videoURL': latest.get('videoURL'),
                    'date': time_ago(latest['date'])  
                }
            
            forum_data.append({
                'id': str(forum['_id']),
                'userName': user_name,
                'initials': get_initials(user_name),
                'content': forum['content'],
                'videoURL': forum.get('videoURL'),
                'date': time_ago(forum['creationDate']), 
                'commentCount': comment_count,
                'latestComment': latest_comment
            })
        
        return jsonify({
            'lessonName': lesson_name,
            'teacherName': teacher_name,
            'forums': forum_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@forum_blueprint.route('/get-comments/<forum_id>', methods=['GET'])
def get_comments(forum_id):
    try:
        db = current_app.db
        forum_oid = ObjectId(forum_id)
        
        # Buscar el post del foro
        forum = db.forums.find_one({'_id': forum_oid})
        if not forum:
            return jsonify({'error': 'Post del foro no encontrado'}), 404
        
        comments_data = []
        for comment in forum.get('comments', []):
            user = db.users.find_one({'_id': comment['userId']}, {'name': 1})
            user_name = user['name'] if user else 'Usuario desconocido'
            
            comments_data.append({
                'id': str(comment['_id']),
                'userName': user_name,
                'initials': get_initials(user_name),
                'date': time_ago(comment['date']),
                'content': comment['content'],
                'videoURL': comment.get('videoURL')
            })
        
        return jsonify({
            'comments': comments_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@forum_blueprint.route('/forum-teacher-courses/<teacher_id>', methods=['GET'])
def get_teacher_courses(teacher_id):
    try:
        db = current_app.db
        teacher_oid = ObjectId(teacher_id)
        
        # Obtener configuración LESCO
        lesco = current_app.config.get('LESCO', True)  
        
        # Verificar que el profesor existe
        teacher = db.users.find_one({'_id': teacher_oid})
        if not teacher:
            return jsonify({'error': 'Profesor no encontrado'}), 404
        
        # Buscar cursos del profesor filtrados por idioma
        if lesco:
            language_filter = True  # Buscar cursos LESCO
        else:
            language_filter = False  # Buscar cursos LIBRAS
        
        courses = list(db.courses.find({'userId': teacher_oid, 'language': language_filter}))
        
        courses_data = []
        for course in courses:
            courses_data.append({
                'id': str(course['_id']),
                'name': course.get('name', 'Sin nombre'),
                'difficulty': course.get('difficulty', 1),
                'language': 'LESCO' if course.get('language') == False else 'LIBRAS',
                'description': course.get('description', 'Sin descripción')
            })
        print("Cursos obtenidos para el foro del profesor:", lesco) # DEBUG
        
        return jsonify({
            'courses': courses_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@forum_blueprint.route('/lessons-with-forum/<course_id>', methods=['GET'])
def get_lessons_with_forum(course_id):
    try:
        db = current_app.db
        course_oid = ObjectId(course_id)
        
        # Buscar el curso
        course = db.courses.find_one({'_id': course_oid})
        if not course:
            return jsonify({'error': 'Curso no encontrado'}), 404
        
        # Filtrar lecciones con forumEnabled: true
        lessons_with_forum = []
        for lesson in course.get('lessons', []):
            if lesson.get('forumEnabled', False):
                lessons_with_forum.append({
                    'id': str(lesson['_id']),
                    'name': lesson['name']
                })
        
        return jsonify({
            'lessons': lessons_with_forum
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500