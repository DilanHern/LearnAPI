from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from routes.exercises import _create_news_activity_result

news_bp = Blueprint("news", __name__)

# ============================
# Como realizar peticiones CURL / pruebas
# ============================
# curl -X POST http://localhost:5000/api/news/activity \
#  -H "Content-Type: application/json" \
#  -d '{
#    "userId":"<USER_ID>",
#    "courseId":"<COURSE_ID>",
#    "lessonId":"<LESSON_ID>",
#    "correct": 8,
#    "total": 10
#  }'

# FEED
# curl "http://localhost:5000/api/news/feed?userId=<USER_ID>" &limit=10 <- se puede poner un limite
# paginación hacia atrás (más antiguas):
# curl "http://localhost:5000/api/news/feed?userId=<USER_ID>&limit=10&before=<NEWS_ID>"

# Like (+1)
# curl -X POST http://localhost:5000/api/news/like \
#  -H "Content-Type: application/json" \
#  -d '{"newsId":"<NEWS_ID>","action":"like"}'

# Unlike (-1 hasta 0)
# curl -X POST http://localhost:5000/api/news/like \
#  -H "Content-Type: application/json" \
#  -d '{"newsId":"<NEWS_ID>","action":"unlike"}'

# curl -X POST http://localhost:5000/api/news/comment \
#  -H "Content-Type: application/json" \
#  -d '{"newsId":"<NEWS_ID>","userId":"<USER_ID>","comment":"¡Excelente trabajo!"}'

#COMMENTS
#curl "http://localhost:5000/api/news/comments?newsId=<NEWS_ID>" &limit=10 <- se puede poner un limite
# Paginación:
#curl "http://localhost:5000/api/news/comments?newsId=<NEWS_ID>&limit=10&before=<COMMENT_ID>"

# ============================
# Helpers
# ============================
def _to_oid(v, name="id"):
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str):
        try:
            return ObjectId(v)
        except InvalidId:
            raise ValueError(f"invalid {name}")
    raise ValueError(f"invalid {name}")

def _user_public_info(db, user_id):
    u = db.users.find_one(
        {"_id": user_id},
        {"name": 1, "firstName": 1, "lastName": 1, "email": 1}
    ) or {}

    # 1) name raíz
    nm = u.get("name")
    if isinstance(nm, str) and nm.strip():
        display = nm.strip()
    else:
        # 2) first + last
        fn = u.get("firstName") or ""
        ln = u.get("lastName") or ""
        full = f"{fn} {ln}".strip()
        if full:
            display = full
        else:
            # 4) email
            em = u.get("email")
            display = em.strip() if isinstance(em, str) and em.strip() else "Usuario"

    return {"userId": str(user_id), "displayName": display}

def _get_following_ids(db, user_oid: ObjectId):
    u = db.users.find_one({"_id": user_oid}, {
        "information.following": 1,
        "following": 1,
        "follows": 1
    }) or {}
    ids = []
    info = (u or {}).get("information", {}) or {}
    for arr in (info.get("following"), u.get("following"), u.get("follows")):
        if isinstance(arr, list):
            for x in arr:
                try:
                    ids.append(_to_oid(x))
                except Exception:
                    continue
            break  # usa el primer campo válido que exista
    return list({i for i in ids})  # únicos

# ============================
# Endpoints
# ============================
@news_bp.route("/feed", methods=["GET"])
def feed_following():
    """
    GET /api/news/feed?userId=<id>&limit=20&before=<newsId>
    Devuelve noticias de seguidos + las propias del usuario.
    """
    db = current_app.db
    try:
        user_id = _to_oid(request.args.get("userId"), "userId")
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    limit = min(int(request.args.get("limit", 20)), 50)

    # IDs de seguidos
    following = _get_following_ids(db, user_id) or []

    # Incluye sus propias noticias
    if user_id not in following:
        following.append(user_id)

    q = {"userId": {"$in": following}}
    before = request.args.get("before")
    if before:
        try:
            before_id = _to_oid(before, "before")
            q["_id"] = {"$lt": before_id}
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    cursor = db.news.find(q).sort([("date", -1), ("_id", -1)]).limit(limit)

    items = []
    for doc in cursor:
        items.append({
            "_id": str(doc["_id"]),
            "userId": str(doc["userId"]),
            "title": doc.get("title"),
            "description": doc.get("description"),
            "likes": int(doc.get("likes", 0)),
            "date": doc.get("date").isoformat() + "Z" if doc.get("date") else None,
            "comments": [
                {
                    "_id": str(c.get("_id")),
                    "comment": c.get("comment"),
                    "userId": str(c.get("userId")) if c.get("userId") else None,
                    "date": c.get("date").isoformat() + "Z" if c.get("date") else None
                } for c in (doc.get("comments") or [])
            ]
        })

    return jsonify({"items": items}), 200

@news_bp.route("/like", methods=["POST"])
def like_news():
    """
    POST /api/news/like
    Body: { newsId, action: "like" | "unlike" }
    Nota: 'likes' es un contador entero en tu esquema. No se deduplica por usuario.
    """
    db = current_app.db
    data = request.get_json(force=True)
    try:
        news_id = _to_oid(data["newsId"], "newsId")
        action = (data.get("action") or "like").strip().lower()
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

    if action not in ("like", "unlike"):
        return jsonify({"error": "action must be 'like' or 'unlike'"}), 400

    if action == "like":
        db.news.update_one({"_id": news_id}, {"$inc": {"likes": 1}})
    else:
        # evita negativos
        doc = db.news.find_one({"_id": news_id}, {"likes": 1})
        cur = int(doc.get("likes", 0)) if doc else 0
        if cur > 0:
            db.news.update_one({"_id": news_id}, {"$inc": {"likes": -1}})

    doc = db.news.find_one({"_id": news_id}, {"likes": 1})
    if not doc:
        return jsonify({"error": "news not found"}), 404
    return jsonify({"likes": int(doc.get("likes", 0))}), 200

@news_bp.route("/comment", methods=["POST"])
def comment_news():
    """
    POST /api/news/comment
    Body: { newsId, userId, comment }
    """
    db = current_app.db
    data = request.get_json(force=True)
    try:
        news_id = _to_oid(data["newsId"], "newsId")
        user_id = _to_oid(data["userId"], "userId")
        text = (data.get("comment") or "").strip()
        if not text:
            return jsonify({"error": "comment required"}), 400
        if len(text) > 500:
            return jsonify({"error": "comment too long (max 500)"}), 400
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

    newc = {
        "_id": ObjectId(),
        "comment": text,
        "userId": user_id,
        "date": datetime.utcnow()
    }
    res = db.news.update_one({"_id": news_id}, {"$push": {"comments": newc}})
    if res.matched_count == 0:
        return jsonify({"error": "news not found"}), 404

    return jsonify({
        "comment": {
            "_id": str(newc["_id"]),
            "comment": newc["comment"],
            "userId": str(newc["userId"]),
            "date": newc["date"].isoformat() + "Z"
        }
    }), 200

@news_bp.route("/comments", methods=["GET"])
def get_news_comments():
    """
    GET /api/news/comments?newsId=<id>&limit=20&before=<commentId>
    Devuelve los comentarios de una noticia (paginados, más recientes primero).
    """
    db = current_app.db
    try:
        news_id = _to_oid(request.args.get("newsId"), "newsId")
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    limit = min(int(request.args.get("limit", 20)), 50)
    before = request.args.get("before")

    # Usamos aggregate para ordenar/paginar dentro del array de comments
    pipeline = [
        {"$match": {"_id": news_id}},
        {"$unwind": "$comments"},
    ]

    # Paginación por commentId (trae los más recientes "antes" de cierto id)
    if before:
        try:
            before_id = _to_oid(before, "before")
            pipeline.append({"$match": {"comments._id": {"$lt": before_id}}})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    pipeline.extend([
        {"$sort": {"comments.date": -1, "comments._id": -1}},
        {"$limit": limit},
        {"$project": {
            "_id": 0,
            "commentId": "$comments._id",
            "userId": "$comments.userId",
            "comment": "$comments.comment",
            "date": "$comments.date"
        }}
    ])

    rows = list(db.news.aggregate(pipeline))
    items = []
    for r in rows:
        uid = r.get("userId")
        items.append({
            "_id": str(r.get("commentId")),
            "comment": r.get("comment"),
            "user": _user_public_info(db, uid) if isinstance(uid, ObjectId) else None,
            "date": r.get("date").isoformat() + "Z" if r.get("date") else None
        })

    return jsonify({"items": items}), 200

@news_bp.route("/activity", methods=["POST"])
def create_activity_news():
    """
    Crea una noticia con el resultado de una lección.
    Body: { userId, courseId, lessonId, correct, total }
    """
    db = current_app.db
    data = request.get_json(force=True)
    try:
        user_oid   = _to_oid(data["userId"], "userId")
        course_oid = _to_oid(data["courseId"], "courseId")
        lesson_oid = _to_oid(data["lessonId"], "lessonId")
        correct    = int(data.get("correct", 0))
        total      = int(data.get("total", 0))
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

    course_doc = db.courses.find_one(
        {"_id": course_oid},
        {"name": 1, "lessons._id": 1, "lessons.name": 1}
    )
    if not course_doc:
        return jsonify({"error": "course or lesson not found"}), 404

    lessons = course_doc.get("lessons") or []
    lesson_doc = next(
        (l for l in lessons if str(l.get("_id")) == str(lesson_oid)),
        None
    )
    if not lesson_doc:
        return jsonify({"error": "course or lesson not found"}), 404

    try:
        print(course_doc, "asd",lesson_doc)
        _create_news_activity_result(db, user_oid, course_doc, lesson_doc, correct, total)
    except Exception:
        current_app.logger.exception("Error creando noticia de resultado de actividad")

    return jsonify({"ok": True}), 200