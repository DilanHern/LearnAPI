from flask import Blueprint, jsonify, current_app, request
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from uuid import uuid4

exercises_bp = Blueprint("exercises", __name__)

# ============================
# Sesiones en memoria
# ============================
SESSIONS = {}     # runId -> estado temporal
USER_ACTIVE = {}  # str(userId) -> runId

# ============================
# Helpers
# ============================
def _to_oid(value, name_for_error="id"):
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str):
        try:
            return ObjectId(value)
        except InvalidId:
            raise ValueError(f"invalid {name_for_error}")
    raise ValueError(f"invalid {name_for_error}")

def _as_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default

def _norm_str(val):
    return (str(val) if val is not None else "").strip().lower()

def _norm_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        v = val.strip().lower()
        return v in ("true", "1", "verdadero", "v", "yes", "y", "sí", "si")
    return False

def _parse_attempts(lesson):
    """(limit:int|None, unlimited:bool). Ilimitado si None/<=0/no existe."""
    att = lesson.get("attempts", None)
    if att is None:
        return (None, True)
    att_i = _as_int(att, 0)
    if att_i <= 0:
        return (None, True)
    return (att_i, False)

def _get_course_and_lesson(course_oid, lesson_oid):
    course = current_app.db.courses.find_one({"_id": course_oid})
    if not course:
        return None, None
    lesson = next((l for l in (course.get("lessons") or []) if l.get("_id") == lesson_oid), None)
    return course, lesson

def _safe_question(db_q):
    """SAFE (sin correctAnswer)."""
    et = _as_int(db_q.get("exerciseType"), 0)
    safe = {
        "_id": str(db_q.get("_id")),
        "exerciseType": et,
        "order": _as_int(db_q.get("order"), 0),
        "question": db_q.get("question"),
        "sign": str(db_q.get("sign")) if db_q.get("sign") else None
    }
    if et in (1, 2):
        safe["possibleAnswers"] = db_q.get("possibleAnswers") or (["Verdadero", "Falso"] if et == 2 else [])
    if et == 3:
        pieces = db_q.get("pieces") or db_q.get("possibleAnswers") or []
        safe["pieces"] = pieces
    return safe

def _evaluate_answer(db_question, user_answer):
    """
    1) selección única: answer índice (0..n-1) o string
    2) V/F: answer booleano o string
    3) ordenar: answer array final
    """
    et = _as_int(db_question.get("exerciseType"), 0)

    if et == 1:
        ca = db_question.get("correctAnswer")
        ca_val = _norm_str(ca[0]) if isinstance(ca, list) and ca else _norm_str(ca)
        if isinstance(user_answer, int):
            poss = db_question.get("possibleAnswers") or []
            chosen = _norm_str(poss[user_answer]) if 0 <= user_answer < len(poss) else ""
            return (chosen == ca_val, user_answer)
        else:
            chosen = _norm_str(user_answer)
            return (chosen == ca_val, user_answer)

    if et == 2:
        ca = db_question.get("correctAnswer") or []
        ca_val = _norm_str(ca[0]) if isinstance(ca, list) and ca else _norm_str(ca)
        user_bool = _norm_bool(user_answer)
        user_val = "verdadero" if user_bool else "falso"
        return (user_val == ca_val, user_bool)

    if et == 3:
        correct = db_question.get("correctAnswer") or []
        ans = user_answer if isinstance(user_answer, list) else []
        norm_c = [_norm_str(x) for x in correct]
        norm_u = [_norm_str(x) for x in ans]
        return (norm_c == norm_u, ans)

    return (False, user_answer)

def _expose_correct_answer(db_question):
    """Devuelve la respuesta correcta en formato amigable para el front."""
    et = _as_int(db_question.get("exerciseType"), 0)
    if et == 1:
        poss = db_question.get("possibleAnswers") or []
        ca = db_question.get("correctAnswer")
        ca_val = _norm_str(ca[0]) if isinstance(ca, list) and ca else _norm_str(ca)
        idx = None; text = None
        for i, opt in enumerate(poss):
            if _norm_str(opt) == ca_val:
                idx, text = i, opt
                break
        return {"type": 1, "text": text}
    if et == 2:
        ca = db_question.get("correctAnswer") or []
        ca_val = _norm_str(ca[0]) if isinstance(ca, list) and ca else _norm_str(ca)
        val = True if ca_val == "verdadero" else False
        label = "Verdadero" if val else "Falso"
        return {"type": 2, "label": label}
    if et == 3:
        order = db_question.get("correctAnswer") or []
        return {"type": 3, "order": order}
    return {"type": et, "value": None}

# ============================
# Persistencia en enrolledCourses (ESQUEMA ESTRICTO)
# ============================
def _ensure_progress(db, user_oid, course_doc, lesson_doc):
    """
    Crea enrolledCourses (si no existe) y el item completedLessons con SOLO:
    _id, lessonId, correctCount, remainingAttempts, (completionDate opcional se agrega en cursos).
    * No se escribe completionDate del curso jamás.
    * completionDate de la lección se escribe en /finish y en /cancel.
    """
    prog = db.enrolledCourses.find_one({"userId": user_oid, "courseId": course_doc["_id"]})
    if not prog:
        db.enrolledCourses.insert_one({
            "userId": user_oid,
            "courseId": course_doc["_id"],
            # NO escribir completionDate del curso (dejarlo ausente)
            "completedLessons": []
        })
        prog = db.enrolledCourses.find_one({"userId": user_oid, "courseId": course_doc["_id"]})

    limit, unlimited = _parse_attempts(lesson_doc)
    lid = lesson_doc["_id"]

    for item in prog.get("completedLessons", []):
        if item.get("lessonId") == lid:
            # backfill _id si faltara
            if "_id" not in item:
                db.enrolledCourses.update_one(
                    {"_id": prog["_id"]},
                    {"$set": {"completedLessons.$[e]._id": ObjectId()}},
                    array_filters=[{"e.lessonId": lid, "e._id": {"$exists": False}}]
                )
            return

    remaining = (limit if not unlimited else -1)  # -1 = ilimitado
    db.enrolledCourses.update_one(
        {"_id": prog["_id"]},
        {"$push": {
            "completedLessons": {
                "_id": ObjectId(),
                "lessonId": lid,
                "correctCount": int(0),
                "remainingAttempts": int(remaining)
                # completionDate se escribe en /finish o /cancel
            }
        }}
    )

def _find_cl_item(db, user_oid, course_doc, lesson_doc):
    prog = db.enrolledCourses.find_one({"userId": user_oid, "courseId": course_doc["_id"]})
    if not prog:
        return None, None
    for item in prog.get("completedLessons", []):
        if item.get("lessonId") == lesson_doc["_id"]:
            return prog, item
    return prog, None

def _get_attempt_state(db, user_oid, course_doc, lesson_doc):
    prog, item = _find_cl_item(db, user_oid, course_doc, lesson_doc)
    if not item:
        return (None, True)
    remaining = _as_int(item.get("remainingAttempts"), 0)
    unlimited = (remaining < 0)
    return (remaining, unlimited)

def _consume_attempt_on_start(db, user_oid, course_doc, lesson_doc):
    """Descuenta 1 intento al iniciar (si remainingAttempts >=1). -1 => ilimitado (no cambia)."""
    remaining, unlimited = _get_attempt_state(db, user_oid, course_doc, lesson_doc)
    if unlimited:
        return (True, -1, True, None)

    res = db.enrolledCourses.update_one(
        {
            "userId": user_oid,
            "courseId": course_doc["_id"],
            "completedLessons": {
                "$elemMatch": {
                    "lessonId": lesson_doc["_id"],
                    "remainingAttempts": {"$gt": 0}
                }
            }
        },
        {"$inc": {"completedLessons.$.remainingAttempts": -1}}
    )
    if res.modified_count == 0:
        return (False, 0, False, "no attempts remaining")

    prog, item = _find_cl_item(db, user_oid, course_doc, lesson_doc)
    return (True, _as_int(item.get("remainingAttempts"), 0), False, None)

def _bump_best_correct_count(db, user_oid, course_doc, lesson_doc, new_correct):
    """Guarda el mejor correctCount histórico para la lección (solo si mejora)."""
    prog, item = _find_cl_item(db, user_oid, course_doc, lesson_doc)
    if not item:
        return
    old = _as_int(item.get("correctCount"), 0)
    if new_correct > old:
        db.enrolledCourses.update_one(
            {"userId": user_oid, "courseId": course_doc["_id"], "completedLessons.lessonId": lesson_doc["_id"]},
            {"$set": {"completedLessons.$.correctCount": int(new_correct)}}
        )

def _set_lesson_completion_date(db, user_oid, course_doc, lesson_doc, when_dt):
    """
    SIEMPRE escribir/actualizar completionDate de la lección (aunque ya exista y aunque tenga 0 correctas).
    * Nunca escribir completionDate del curso.
    """
    db.enrolledCourses.update_one(
        {
            "userId": user_oid,
            "courseId": course_doc["_id"],
            "completedLessons.lessonId": lesson_doc["_id"]
        },
        {"$set": {"completedLessons.$.completionDate": when_dt}}
    )

# ============================
# Endpoints 
# ============================
@exercises_bp.route("/start", methods=["POST"])
def start_exercise():
    """
    Inicia sesión en memoria y DESCUESTA intento al inicio (si aplica).
    Bloqueo global: 1 actividad activa por usuario.
    Body: { userId, courseId, lessonId }
    """
    try:
        data = request.get_json(force=True)
        user_oid   = _to_oid(data["userId"], "userId")
        course_oid = _to_oid(data["courseId"], "courseId")
        lesson_oid = _to_oid(data["lessonId"], "lessonId")
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

    # bloqueo: 1 run activa por usuario
    ukey = str(user_oid)
    if ukey in USER_ACTIVE and USER_ACTIVE[ukey] in SESSIONS and SESSIONS[USER_ACTIVE[ukey]]["state"] == "active":
        run_id = USER_ACTIVE[ukey]
        sess = SESSIONS[run_id]
        return jsonify({
            "error": "active run exists",
            "runId": run_id,
            "resume": True,
            "currentIndex": int(sess.get("currentIndex", 0))
        }), 409

    course, lesson = _get_course_and_lesson(course_oid, lesson_oid)
    if not course:
        return jsonify({"error": "course not found"}), 404
    if not lesson:
        return jsonify({"error": "lesson not found in course"}), 404

    # asegurar progress (sin completionDate aún)
    _ensure_progress(current_app.db, user_oid, course, lesson)

    # descontar intento aquí
    ok, remaining_after, unlimited, reason = _consume_attempt_on_start(current_app.db, user_oid, course, lesson)
    if not ok and not unlimited:
        return jsonify({"error": reason or "no attempts remaining"}), 403

    # preparar preguntas SAFE en orden
    raw = lesson.get("exercises") or []
    safe = [_safe_question(q) for q in raw]
    safe.sort(key=lambda s: (_as_int(s.get("order"), 0), s["_id"]))
    if not safe:
        return jsonify({"error": "no questions in lesson"}), 400

    run_id = str(uuid4())
    SESSIONS[run_id] = {
        "userId": user_oid,
        "courseId": course["_id"],
        "lessonId": lesson["_id"],
        "startedAt": datetime.utcnow(),
        "currentIndex": 0,
        "total": len(safe),
        "answers": {},           # questionId (str) -> {"isCorrect": bool, "skipped": bool}
        "correctCount": 0,
        "order": [str(q["_id"]) for q in safe],
        "state": "active"
    }
    USER_ACTIVE[ukey] = run_id

    return jsonify({
        "runId": run_id,
        "total": len(safe),
        "remainingAttempts": remaining_after,      # -1 si ilimitado
        "unlimited": (remaining_after == -1),
        "questions": safe,
        "currentIndex": 0
    }), 200


@exercises_bp.route("/answer", methods=["POST"])
def answer_question():
    """
    Responde la pregunta actual (o específica).
    Body: { runId, questionId?, answer }
    Si es incorrecta, devuelve correctAnswer.
    """
    data = request.get_json(force=True)
    run_id = data.get("runId")
    if not run_id or run_id not in SESSIONS:
        return jsonify({"error": "run not found"}), 404
    sess = SESSIONS[run_id]
    if sess["state"] != "active":
        return jsonify({"error": "run not active"}), 400

    course = current_app.db.courses.find_one({"_id": sess["courseId"]}, {"lessons": 1})
    if not course:
        return jsonify({"error": "course not found for run"}), 404
    lesson = next((l for l in course.get("lessons", []) if l.get("_id") == sess["lessonId"]), None)
    if not lesson:
        return jsonify({"error": "lesson not found for run"}), 404

    order = sess["order"]
    cur_idx = sess["currentIndex"]
    qid_opt = data.get("questionId")
    if qid_opt is not None:
        try:
            qid_val = str(_to_oid(qid_opt, "questionId"))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        if qid_val not in order:
            return jsonify({"error": "questionId not in run"}), 400
        idx = order.index(qid_val)
    else:
        idx = cur_idx

    qid_str = order[idx]
    qid_oid = ObjectId(qid_str)
    db_q = next((q for q in (lesson.get("exercises") or []) if q.get("_id") == qid_oid), None)
    if not db_q:
        return jsonify({"error": "question not found in course"}), 404

    is_correct, normalized = _evaluate_answer(db_q, data.get("answer"))
    correct_payload = None if is_correct else _expose_correct_answer(db_q)

    sess["answers"][qid_str] = {"isCorrect": bool(is_correct), "skipped": False}
    sess["correctCount"] = sum(1 for v in sess["answers"].values() if v["isCorrect"])

    next_idx = idx + 1
    done = next_idx >= sess["total"]
    if idx == cur_idx:
        sess["currentIndex"] = next_idx if not done else cur_idx

    # construir siguiente SAFE
    next_question_safe = None
    if not done:
        raw = lesson.get("exercises") or []
        safe_all = [_safe_question(q) for q in raw]
        safe_all.sort(key=lambda s: (_as_int(s.get("order"), 0), s["_id"]))
        safe_map = {s["_id"]: s for s in safe_all}
        next_qid = order[next_idx]
        next_question_safe = safe_map.get(next_qid)

    resp = {
        "correct": bool(is_correct),
        "feedback": "¡Correcto!" if is_correct else "Respuesta incorrecta.",
        "currentIndex": idx,
        "nextIndex": (None if done else next_idx),
        "done": done,
        "correctCount": sess["correctCount"],
        "total": sess["total"],
        "nextQuestion": next_question_safe
    }
    if correct_payload is not None:
        resp["correctAnswer"] = correct_payload
    return jsonify(resp), 200


@exercises_bp.route("/skip", methods=["POST"])
def skip_question():
    """
    Marca la pregunta como INCORRECTA, devuelve la respuesta correcta y avanza.
    Body: { runId, questionId? }
    """
    data = request.get_json(force=True)
    run_id = data.get("runId")
    if not run_id or run_id not in SESSIONS:
        return jsonify({"error": "run not found"}), 404
    sess = SESSIONS[run_id]
    if sess["state"] != "active":
        return jsonify({"error": "run not active"}), 400

    course = current_app.db.courses.find_one({"_id": sess["courseId"]}, {"lessons": 1})
    if not course:
        return jsonify({"error": "course not found for run"}), 404
    lesson = next((l for l in course.get("lessons", []) if l.get("_id") == sess["lessonId"]), None)
    if not lesson:
        return jsonify({"error": "lesson not found for run"}), 404

    order = sess["order"]
    cur_idx = sess["currentIndex"]
    qid_opt = data.get("questionId")
    if qid_opt is not None:
        try:
            qid_val = str(_to_oid(qid_opt, "questionId"))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        if qid_val not in order:
            return jsonify({"error": "questionId not in run"}), 400
        idx = order.index(qid_val)
    else:
        idx = cur_idx

    qid_str = order[idx]
    if qid_str in sess["answers"]:
        return jsonify({"error": "question already answered"}), 400

    qid_oid = ObjectId(qid_str)
    db_q = next((q for q in (lesson.get("exercises") or []) if q.get("_id") == qid_oid), None)
    if not db_q:
        return jsonify({"error": "question not found in course"}), 404

    correct_payload = _expose_correct_answer(db_q)

    sess["answers"][qid_str] = {"isCorrect": False, "skipped": True}
    sess["correctCount"] = sum(1 for v in sess["answers"].values() if v["isCorrect"])
    next_idx = idx + 1
    done = next_idx >= sess["total"]
    if idx == cur_idx:
        sess["currentIndex"] = next_idx if not done else cur_idx

    next_question_safe = None
    if not done:
        raw = lesson.get("exercises") or []
        safe_all = [_safe_question(q) for q in raw]
        safe_all.sort(key=lambda s: (_as_int(s.get("order"), 0), s["_id"]))
        safe_map = {s["_id"]: s for s in safe_all}
        next_qid = order[next_idx]
        next_question_safe = safe_map.get(next_qid)

    return jsonify({
        "skipped": True,
        "correct": False,
        "correctAnswer": correct_payload,
        "currentIndex": idx,
        "nextIndex": (None if done else next_idx),
        "done": done,
        "correctCount": sess["correctCount"],
        "total": sess["total"],
        "nextQuestion": next_question_safe
    }), 200


@exercises_bp.route("/finish", methods=["POST"])
def finish_run():
    """
    Finaliza la sesión en memoria.
    - Actualiza correctCount SOLO si mejora (mejor puntaje)
    - Escribe/actualiza completionDate de la lección SIEMPRE (aunque 0 correctas)
    - NUNCA escribe completionDate del curso
    Body: { runId }
    """
    data = request.get_json(force=True)
    run_id = data.get("runId")
    if not run_id or run_id not in SESSIONS:
        return jsonify({"error": "run not found"}), 404
    sess = SESSIONS[run_id]
    if sess["state"] != "active":
        return jsonify({"error": "run not active"}), 400

    now = datetime.utcnow()

    course = current_app.db.courses.find_one({"_id": sess["courseId"]}, {"lessons": 1})
    if not course:
        return jsonify({"error": "course not found for run"}), 404
    lesson = next((l for l in course.get("lessons", []) if l.get("_id") == sess["lessonId"]), None)
    if not lesson:
        return jsonify({"error": "lesson not found for run"}), 404

    # 1) Mejor puntaje
    correct = int(sess["correctCount"])
    total = int(sess["total"])
    _bump_best_correct_count(current_app.db, sess["userId"], course, lesson, correct)

    # 2) CompletionDate SIEMPRE
    _set_lesson_completion_date(current_app.db, sess["userId"], course, lesson, now)

    # limpiar sesión
    sess["state"] = "finished"
    ukey = str(sess["userId"])
    if USER_ACTIVE.get(ukey) == run_id:
        del USER_ACTIVE[ukey]
    del SESSIONS[run_id]

    # estado de intentos (para respuesta)
    remaining, unlimited = _get_attempt_state(current_app.db, sess["userId"], course, lesson)

    return jsonify({
        "summary": {"correctCount": correct, "total": total},
        "remainingAttempts": remaining,          # -1 si ilimitado
        "unlimited": (remaining == -1),
        "finishedAt": (now.isoformat() + "Z")
    }), 200


@exercises_bp.route("/cancel", methods=["POST"])
def cancel_run():
    """
    Cancela la sesión en memoria. (No devuelve intentos; ya se descontó en /start)
    - No actualiza correctCount si mejora
    - Escribe/actualiza completionDate de la lección SIEMPRE (aunque 0 correctas)
    Body: { runId }
    """
    data = request.get_json(force=True)
    run_id = data.get("runId")
    if not run_id or run_id not in SESSIONS:
        return jsonify({"error": "run not found"}), 404
    sess = SESSIONS[run_id]
    if sess["state"] != "active":
        return jsonify({"error": "run not active"}), 400

    now = datetime.utcnow()

    course = current_app.db.courses.find_one({"_id": sess["courseId"]}, {"lessons": 1})
    if not course:
        return jsonify({"error": "course not found for run"}), 404
    lesson = next((l for l in course.get("lessons", []) if l.get("_id") == sess["lessonId"]), None)
    if not lesson:
        return jsonify({"error": "lesson not found for run"}), 404

    # 2) CompletionDate SIEMPRE
    _set_lesson_completion_date(current_app.db, sess["userId"], course, lesson, now)

    # limpiar sesión
    sess["state"] = "canceled"
    ukey = str(sess["userId"])
    if USER_ACTIVE.get(ukey) == run_id:
        del USER_ACTIVE[ukey]
    del SESSIONS[run_id]

    return jsonify({"ok": True, "canceledAt": now.isoformat() + "Z"}), 200


@exercises_bp.route("/status", methods=["GET"])
def run_status():
    """
    Estado actual de la sesión en memoria.
    Query: runId
    """
    run_id = request.args.get("runId")
    if not run_id or run_id not in SESSIONS:
        return jsonify({"error": "run not found"}), 404
    sess = SESSIONS[run_id]

    # intentos actuales
    course = current_app.db.courses.find_one({"_id": sess["courseId"]}, {"lessons": 1})
    lesson = None
    if course:
        lesson = next((l for l in course.get("lessons", []) if l.get("_id") == sess["lessonId"]), None)
    remaining, unlimited = (None, True)
    if course and lesson:
        remaining, unlimited = _get_attempt_state(current_app.db, sess["userId"], course, lesson)

    return jsonify({
        "runId": run_id,
        "userId": str(sess["userId"]),
        "courseId": str(sess["courseId"]),
        "lessonId": str(sess["lessonId"]),
        "currentIndex": int(sess["currentIndex"]),
        "correctCount": int(sess["correctCount"]),
        "total": int(sess["total"]),
        "finishedAt": None,
        "state": sess.get("state", "active"),
        "remainingAttempts": remaining,         # -1 si ilimitado
        "unlimited": (remaining == -1)
    }), 200


@exercises_bp.route("/items", methods=["GET"])
def items_for_lesson():
    """
    Preguntas SAFE para una lección (ordenadas por 'order').
    Query: courseId, lessonId
    """
    course_id = request.args.get("courseId")
    lesson_id = request.args.get("lessonId")

    try:
        course_oid = _to_oid(course_id, "courseId")
        lesson_oid = _to_oid(lesson_id, "lessonId")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    course, lesson = _get_course_and_lesson(course_oid, lesson_oid)
    if not course:
        return jsonify({"error": "course not found"}), 404
    if not lesson:
        return jsonify({"error": "lesson not found in course"}), 404

    raw = lesson.get("exercises") or []
    safe = [_safe_question(q) for q in raw]
    safe.sort(key=lambda s: (_as_int(s.get("order"), 0), s["_id"]))

    return jsonify({
        "lessonId": str(lesson_oid),
        "total": len(safe),
        "questions": safe
    }), 200
