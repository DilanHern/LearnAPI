// INSTRUCTIONS:
// 1. First execute CreateLEARNDB.js to create collections
// 2. Open MongoDB Compass
// 3. Connect to your server
// 4. Open MONGOSH tab
// 5. Copy and paste all this code in the mongosh console


print("Iniciando seed de la base de datos LEARN...\n");

// ========================================
// 1. CREAR COMENTARIOS PREDEFINIDOS
// ========================================
print("Creando comentario predefinido...");

const premadeComment = {
  content: "¡Felicitaciones por tu increíble progreso!"
};

const premadeId = db.premadeComments.insertOne(premadeComment).insertedId;
print(`Comentario predefinido creado: ${premadeId}\n`);

// ========================================
// 2. CREAR USUARIOS (1 Estudiante y 1 Profesor)
// ========================================
print("Creando usuarios...");

// Crear el estudiante primero
const student = {
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
// 3. CREAR LOGROS
// ========================================
print("Creando logros...");

const achievements = [
  // LESCO
  {
    name: "Nivel 3 LESCO Alcanzado",
    type: false, // LESCO
    content: "¡Alcanzaste el nivel 3 en LESCO!",
    date: new Date("2025-10-10"),
    premadeId: premadeId
  },
  {
    name: "Nivel 4 LESCO Alcanzado",
    type: false,
    content: "¡Alcanzaste el nivel 4 en LESCO!",
    date: new Date("2025-10-15"),
    premadeId: premadeId
  },
  {
    name: "Nivel 5 LESCO Alcanzado",
    type: false,
    content: "¡Alcanzaste el nivel 5 en LESCO!",
    date: new Date("2025-10-18"),
    premadeId: premadeId
  },
  // LIBRAS
  {
    name: "Nivel 3 LIBRAS Alcanzado",
    type: true, // LIBRAS
    content: "¡Alcanzaste el nivel 3 en LIBRAS!",
    date: new Date("2025-10-12"),
    premadeId: premadeId
  },
  {
    name: "Nivel 4 LIBRAS Alcanzado",
    type: true,
    content: "¡Alcanzaste el nivel 4 en LIBRAS!",
    date: new Date("2025-10-16"),
    premadeId: premadeId
  }
];

const achievementIds = db.achievements.insertMany(achievements).insertedIds;
print(`${Object.keys(achievementIds).length} logros creados (3 LESCO + 2 LIBRAS)\n`);

// Asignar todos al estudiante
const achievementIdArray = Object.values(achievementIds);
db.users.updateOne(
  { _id: studentId },
  { $set: { "information.achievements": achievementIdArray } }
);
print("Todos los logros asignados al estudiante\n");

// ========================================
// 4. CREAR CURSO CON LECCIÓN
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
// 5. CREAR CURSO INSCRITO (ANTES: COMPLETADO)
// ========================================
print("Creando registro de curso inscrito...");

const enrolledCourse = {
  userId: studentId,
  courseId: courseId,
  completionDate: new Date("2025-10-15"),
  completedLessons: [
    {
      _id: new ObjectId(),
      lessonId: lessonId,
      correctCount: NumberInt(2),
      remainingAttempts: NumberInt(2),
      completionDate: new Date("2025-10-15")
      // timeSeconds eliminado
    }
  ]
};

const enrolledCourseId = db.enrolledCourses.insertOne(enrolledCourse).insertedId;
print(`Curso inscrito registrado: ${enrolledCourseId}\n`);

// ========================================
// 6. CREAR POST EN NEWS
// ========================================
print("Creando publicación...");

const newsPost = {
  userId: studentId,
  premadeId: premadeId,
  description: "¡Completé mi primera lección de LESCO!",
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
// 7. CREAR POST EN FORO
// ========================================
print("Creando post en foro...");

const forumPost = {
  lessonId: lessonId,
  userId: studentId,
  content: "¿Alguien puede explicarme mejor la diferencia entre los saludos formales e informales?",
  creationDate: new Date("2025-10-13"),
  comments: [
    {
      _id: new ObjectId(),
      userId: teacherId,
      content: "Claro María. Los saludos formales se usan en contextos profesionales, mientras que los informales son para amigos y familia.",
      date: new Date("2025-10-13")
    }
  ]
};

const forumId = db.forums.insertOne(forumPost).insertedId;
print(`Post de foro creado: ${forumId}\n`);
// ========================================
// 8. CREAR ESTADÍSTICAS DE ESTUDIANTE
// ========================================
print("Creando estadísticas de estudiante...");

const studentStatsId = new ObjectId();

const studentStats = {
  _id: studentStatsId,
  userId: studentId,
  enrolledCourseId: enrolledCourseId, // Cambiado de completedCourseId
  totalSigns: NumberInt(25),
  averageSuccess: 0.85
};

db.studentStatistics.insertOne(studentStats);
print(`Estadísticas de estudiante creadas: ${studentStatsId}\n`);


// ========================================
// 9. CREAR ESTADÍSTICAS DE PROFESOR
// ========================================
print("Creando estadísticas de profesor...");

const teacherStats = {
  userId: teacherId,
  generalStatistics: {
    totalSigns: NumberInt(50),
    averageSuccess: 0.82,
    coursesCreated: NumberInt(1),
    lessonsCreated: NumberInt(1),
    totalStudents: NumberInt(1)
  },
  courseStatistics: [
    {
      courseId: courseId,
      averageSuccess: 0.85,
      studentStatistics: [studentStatsId]
    }
  ],
  lessonStatistics: [
    {
      lessonId: lessonId,
      averageAttempts: 1.5,
      successPercentage: 0.9
    }
  ]
};

const teacherStatsId = db.teacherStatistics.insertOne(teacherStats).insertedId;
print(`Estadísticas de profesor creadas: ${teacherStatsId}\n`);
