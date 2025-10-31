// INSTRUCTIONS:
// 1. First execute CreateLEARNDB.js to create collections
// 2. Open MongoDB Compass
// 3. Connect to your server
// 4. Open MONGOSH tab
// 5. Copy and paste all this code in the mongosh console

print("Iniciando seed de la base de datos LEARN...\n");

// ========================================
// 1. CREAR USUARIOS (1 Estudiante y 1 Profesor)
// ========================================
print("Creando usuarios...");

// Crear el estudiante primero
const student = {
  firebaseUid: "firebase_uid_student_maria_001",
  type: false, // Estudiante
  name: "María Badilla Castro",
  followers: [], // Se llenará después
  following: [], // Se llenará después
  information: {
    streak: {
      current: NumberInt(7),
      lastConnection: new Date()
    },
    achievements: [], // Se llenará después
    lescoSkills: NumberInt(2),
    librasSkills: NumberInt(3),
    lescoLevel: NumberInt(6),
    librasLevel: NumberInt(5),
    myCourses: [] // Se llenará después
  }
};

const studentId = db.users.insertOne(student).insertedId;
print(`Estudiante creado: ${studentId}`);

// Crear el profesor
const teacher = {
  firebaseUid: "firebase_uid_teacher_sofia_002",
  type: true, // Profesor
  name: "Sofia Castro Álvarez",
  followers: [studentId], // El estudiante sigue al profesor
  following: [studentId], // El profesor sigue al estudiante
  information: {
    streak: {
      current: NumberInt(30),
      lastConnection: new Date()
    },
    achievements: [], // Se llenará después
    lescoSkills: NumberInt(50),
    librasSkills: NumberInt(45),
    lescoLevel: NumberInt(10),
    librasLevel: NumberInt(9),
    myCourses: [] // Se llenará después
  }
};

const teacherId = db.users.insertOne(teacher).insertedId;
print(`Profesor creado: ${teacherId}\n`);

print("Creando usuario nuevo sin seguidores...");
const newUser = {
  firebaseUid: "firebase_uid_student_carlos_003",
  type: false, // Estudiante
  name: "Carlos Rodríguez Pérez",
  followers: [], // Array vacío - sin seguidores
  following: [], // Array vacío - no sigue a nadie
  information: {
    streak: {
      current: NumberInt(0), // Nueva racha
      lastConnection: new Date()
    },
    achievements: [], // Sin logros inicialmente
    lescoSkills: NumberInt(0), // Habilidades iniciales en 0
    librasSkills: NumberInt(0),
    lescoLevel: NumberInt(1), // Nivel inicial 1
    librasLevel: NumberInt(1),
    myCourses: [] // Sin cursos inicialmente
  }
};
const newUserId = db.users.insertOne(newUser).insertedId;
print(`Usuario nuevo creado: ${newUserId}\n`);

// Actualizar followers/following del estudiante
db.users.updateOne(
  { _id: studentId },
  { 
    $set: { 
      followers: [teacherId],
      following: [teacherId]
    }
  }
);
print("Relaciones followers/following establecidas\n");

// ========================================
// 2. CREAR LOGROS
// ========================================
print("Creando logros...");

const achievements = [
  // LESCO
  {
    name: "¡Nivel 10!",
    type: false,
    content: "Subiste a nivel 10.",
    date: new Date("2025-10-28")
  },
  {
    name: "¡Nivel 25!",
    type: false,
    content: "Subiste a nivel 25.",
    date: new Date("2025-10-28")
  },
  {
    name: "¡Nivel 50!",
    type: false,
    content: "Subiste a nivel 50.",
    date: new Date("2025-10-28")
  },
  {
    name: "¡Nivel 100!",
    type: false,
    content: "Subiste a nivel 100.",
    date: new Date("2025-10-28")
  },
  {
    name: "10 cursos completados",
    type: false,
    content: "Completaste 10 cursos.",
    date: new Date("2025-10-28")
  },
  {
    name: "25 cursos completados",
    type: false,
    content: "Completaste 25 cursos.",
    date: new Date("2025-10-28")
  },
  {
    name: "50 cursos completados",
    type: false,
    content: "Completaste 50 cursos.",
    date: new Date("2025-10-28")
  },
  {
    name: "100 cursos completados",
    type: false,
    content: "Completaste 100 cursos.",
    date: new Date("2025-10-28")
  },
  {
    name: "5 logros conseguidos",
    type: false,
    content: "Conseguiste 5 logros.",
    date: new Date("2025-10-28")
  },
  {
    name: "10 logros conseguidos",
    type: false,
    content: "Conseguiste 10 logros.",
    date: new Date("2025-10-28")
  },
  {
    name: "15 logros conseguidos",
    type: false,
    content: "Conseguiste 15 logros.",
    date: new Date("2025-10-28")
  },
  {
    name: "20 logros conseguidos",
    type: false,
    content: "Conseguiste 20 logros.",
    date: new Date("2025-10-28")
  },
  {
    name: "25 logros conseguidos",
    type: false,
    content: "Conseguiste 25 logros.",
    date: new Date("2025-10-28")
  },
  //LIBRAS
  {
    name: "¡Nivel 10!",
    type: true,
    content: "Subiste a nivel 10.",
    date: new Date("2025-10-28")
  },
  {
    name: "¡Nivel 25!",
    type: true,
    content: "Subiste a nivel 25.",
    date: new Date("2025-10-28")
  },
  {
    name: "¡Nivel 50!",
    type: true,
    content: "Subiste a nivel 50.",
    date: new Date("2025-10-28")
  },
  {
    name: "¡Nivel 100!",
    type: true,
    content: "Subiste a nivel 100.",
    date: new Date("2025-10-28")
  },
  {
    name: "10 cursos completados",
    type: true,
    content: "Completaste 10 cursos.",
    date: new Date("2025-10-28")
  },
  {
    name: "25 cursos completados",
    type: true,
    content: "Completaste 25 cursos.",
    date: new Date("2025-10-28")
  },
  {
    name: "50 cursos completados",
    type: true,
    content: "Completaste 50 cursos.",
    date: new Date("2025-10-28")
  },
  {
    name: "100 cursos completados",
    type: true,
    content: "Completaste 100 cursos.",
    date: new Date("2025-10-28")
  },
  {
    name: "5 logros conseguidos",
    type: true,
    content: "Conseguiste 5 logros.",
    date: new Date("2025-10-28")
  },
  {
    name: "10 logros conseguidos",
    type: true,
    content: "Conseguiste 10 logros.",
    date: new Date("2025-10-28")
  },
  {
    name: "15 logros conseguidos",
    type: true,
    content: "Conseguiste 15 logros.",
    date: new Date("2025-10-28")
  },
  {
    name: "20 logros conseguidos",
    type: true,
    content: "Conseguiste 20 logros.",
    date: new Date("2025-10-28")
  },
  {
    name: "25 logros conseguidos",
    type: true,
    content: "Conseguiste 25 logros.",
    date: new Date("2025-10-28")
  }
];

const achievementIds = db.achievements.insertMany(achievements).insertedIds;
print(`${Object.keys(achievementIds).length} logros creados (13 LESCO + 13 LIBRAS)\n`);

// Asignar todos al estudiante
const achievementIdArray = Object.values(achievementIds);
db.users.updateOne(
  { _id: studentId },
  { $set: { "information.achievements": achievementIdArray } }
);
print("Todos los logros asignados al estudiante\n");

// ========================================
// 3. CREAR CURSO CON LECCIÓN
// ========================================
print("Creando curso...");

const lessonId = new ObjectId();
const exercise1Id = new ObjectId();
const exercise2Id = new ObjectId();
const signId1 = new ObjectId(); // Mock sign ID
const signId2 = new ObjectId();

const course = {
  userId: teacherId,
  name: "LESCO Básico - Saludos",
  description: "Aprende los saludos básicos en LESCO",
  difficulty: NumberInt(1),
  language: false, // LESCO
  status: true, // Público
  students: [studentId],
  lessons: [
    {
      _id: lessonId,
      order: NumberInt(1),
      name: "Saludos Básicos",
      questionCount: NumberInt(2),
      attempts: NumberInt(3),
      forumEnabled: true,
      theory: [
        {
          text: "La seña de 'Hola' se realiza moviendo la mano derecha hacia adelante.",
          sign: signId1
        }
      ],
      exercises: [
        {
          _id: exercise1Id,
          exerciseType: NumberInt(1),
          order: NumberInt(1),
          sign: signId1,
          question: "¿Qué significa esta seña?",
          possibleAnswers: ["Hola", "Adiós", "Gracias", "Por favor"],
          correctAnswer: ["Hola"]
        },
        {
          _id: exercise2Id,
          exerciseType: NumberInt(1),
          order: NumberInt(2),
          sign: signId2,
          question: "¿Cuál es la seña correcta para 'Buenos días'?",
          possibleAnswers: ["Opción A", "Opción B", "Opción C"],
          correctAnswer: ["Opción B"]
        }
      ]
    }
  ]
};

const courseId = db.courses.insertOne(course).insertedId;
print(`Curso creado: ${courseId}\n`);

// Asignar curso a ambos usuarios
db.users.updateOne(
  { _id: studentId },
  { $set: { "information.myCourses": [courseId] } }
);

db.users.updateOne(
  { _id: teacherId },
  { $set: { "information.myCourses": [courseId] } }
);
print("Curso asignado a estudiante y profesor\n");

// ========================================
// 4. CREAR CURSO INSCRITO (ANTES: COMPLETADO)
// ========================================
print("Creando registro de curso inscrito...");

const enrolledCourse = {
  userId: studentId,
  courseId: courseId,
  completionDate: null,
  totalQuestions: NumberInt(10),  // Nuevo: preguntas totales
  correctAnswers: NumberInt(5),  // Nuevo: cantidad de correctas
  completedLessons: [
    {
      _id: new ObjectId(),
      lessonId: lessonId,
      correctCount: NumberInt(2),
      remainingAttempts: NumberInt(2),
      completionDate: new Date("2025-10-15")
    }
  ]
};

const enrolledCourseId = db.enrolledCourses.insertOne(enrolledCourse).insertedId;
print(`Curso inscrito registrado: ${enrolledCourseId}\n`);

// ========================================
// 5. CREAR POST EN NEWS
// ========================================
print("Creando publicación...");

const newsPost = {
  userId: studentId,
  title: "¡Completé mi primera lección de LESCO!",  // Cambiado de premadeId a title
  description: "¡Estoy emocionada por aprender más!",
  likes: NumberInt(5),
  date: new Date("2025-10-15"),
  comments: [
    {
      _id: new ObjectId(),
      comment: "¡Excelente trabajo María!",
      userId: teacherId,
      date: new Date("2025-10-15")
    }
  ]
};

const newsId = db.news.insertOne(newsPost).insertedId;
print(`Publicación creada: ${newsId}\n`);

// ========================================
// 6. CREAR POST EN FORO
// ========================================
print("Creando post en foro...");

const forumPost = {
  lessonId: lessonId,
  userId: studentId,
  content: "¿Alguien puede explicarme mejor la diferencia entre los saludos formales e informales?",
  videoURL: "https://example.com/video-tutorial.mp4",  // Agregado
  creationDate: new Date("2025-10-13"),
  comments: [
    {
      _id: new ObjectId(),
      userId: teacherId,
      content: "Claro María. Los saludos formales se usan en contextos profesionales, mientras que los informales son para amigos y familia.",
      videoURL: "https://example.com/respuesta-video.mp4",  // Agregado
      date: new Date("2025-10-13")
    }
  ]
};

const forumId = db.forums.insertOne(forumPost).insertedId;
print(`Post de foro creado: ${forumId}\n`);

// ========================================
// 7. CREAR ESTADÍSTICAS DE PROFESOR
// ========================================
print("Creando estadísticas de profesor...");

const teacherStats = {
  userId: teacherId,
  coursesCreated: NumberInt(1),
  lessonsCreated: NumberInt(1),
  totalStudents: NumberInt(1)
  // Eliminados: generalStatistics, courseStatistics y lessonStatistics
};

const teacherStatsId = db.teacherStatistics.insertOne(teacherStats).insertedId;
print(`Estadísticas de profesor creadas: ${teacherStatsId}\n`);

// ========================================
// 8. CREAR NUEVO CURSO LIBRAS Y ENROLLED COURSE PARA MARÍA
// ========================================
print("Creando nuevo curso LIBRAS y enrolled course para María Badilla Castro...");

// Crear IDs únicos para el nuevo curso
const newLessonId = new ObjectId();
const newExercise1Id = new ObjectId();
const newExercise2Id = new ObjectId();
const newSignId1 = new ObjectId();
const newSignId2 = new ObjectId();

// Crear el nuevo curso LIBRAS
const newCourse = {
  userId: teacherId,
  name: "LIBRAS Básico - Números",
  description: "Aprende los números básicos en LIBRAS",
  difficulty: NumberInt(1),
  language: true,  // LIBRAS
  status: true,  // Público
  students: [studentId],
  lessons: [
    {
      _id: newLessonId,
      order: NumberInt(1),
      name: "Números del 1 al 5",
      questionCount: NumberInt(2),
      attempts: NumberInt(3),
      forumEnabled: true,
      theory: [
        {
          text: "El número 1 se representa con el dedo índice extendido.",
          sign: newSignId1
        }
      ],
      exercises: [
        {
          _id: newExercise1Id,
          exerciseType: NumberInt(1),
          order: NumberInt(1),
          sign: newSignId1,
          question: "¿Qué número representa esta seña?",
          possibleAnswers: ["1", "2", "3", "4"],
          correctAnswer: ["1"]
        },
        {
          _id: newExercise2Id,
          exerciseType: NumberInt(1),
          order: NumberInt(2),
          sign: newSignId2,
          question: "¿Cuál es la seña para el número 2?",
          possibleAnswers: ["Opción A", "Opción B", "Opción C"],
          correctAnswer: ["Opción B"]
        }
      ]
    }
  ]
};

const newCourseId = db.courses.insertOne(newCourse).insertedId;
print(`Nuevo curso LIBRAS creado: ${newCourseId}`);

// Crear enrolledCourse para María (sin completar)
const newEnrolledCourse = {
  userId: studentId,
  courseId: newCourseId,
  completionDate: null,
  totalQuestions: null,  // Nuevo: preguntas totales
  correctAnswers: null,  // Nuevo: cantidad de correctas
  completedLessons: []
};

const newEnrolledCourseId = db.enrolledCourses.insertOne(newEnrolledCourse).insertedId;
print(`Enrolled course creado para María: ${newEnrolledCourseId}`);

// Agregar el nuevo curso a myCourses de María
db.users.updateOne(
  { _id: studentId },
  { $push: { "information.myCourses": newCourseId } }
);
print("Nuevo curso agregado a myCourses de María\n");

// ========================================
// 9. AGREGAR SEGUNDA LECCIÓN AL CURSO LESCO
// ========================================
print("Agregando segunda lección al curso LESCO...");

// Crear IDs únicos para la nueva lección
const lessonId2 = new ObjectId();
const exercise3Id = new ObjectId();
const exercise4Id = new ObjectId();
const signId3 = new ObjectId();
const signId4 = new ObjectId();

const newLesson = {
  _id: lessonId2,
  order: NumberInt(2),
  name: "Despedidas Básicas",
  questionCount: NumberInt(2),
  attempts: NumberInt(3),
  forumEnabled: true,
  theory: [
    {
      text: "La seña de 'Adiós' se realiza moviendo la mano de lado a lado.",
      sign: signId3
    },
    {
      text: "La seña de 'Hasta luego' se hace con la mano derecha en forma de 'L' moviéndose hacia adelante.",
      sign: signId4
    }
  ],
  exercises: [
    {
      _id: exercise3Id,
      exerciseType: NumberInt(1),
      order: NumberInt(1),
      sign: signId3,
      question: "¿Qué significa esta seña?",
      possibleAnswers: ["Hola", "Adiós", "Gracias", "Por favor"],
      correctAnswer: ["Adiós"]
    },
    {
      _id: exercise4Id,
      exerciseType: NumberInt(1),
      order: NumberInt(2),
      sign: signId4,
      question: "¿Cuál es la seña correcta para 'Hasta luego'?",
      possibleAnswers: ["Opción A", "Opción B", "Opción C"],
      correctAnswer: ["Opción C"]
    }
  ]
};

// Agregar la nueva lección al curso existente
db.courses.updateOne(
  { _id: courseId },
  { $push: { lessons: newLesson } }
);
print(`Segunda lección agregada al curso LESCO: ${lessonId2}\n`);

