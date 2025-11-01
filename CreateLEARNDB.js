// INSTRUCTIONS:
// 1. Open MongoDB Compass
// 2. Connect to your server
// 3. Open MONGOSH tab
// 4. Execute: use LEARN
// 5. Copy and paste all this code in the mongosh console

// 1. Create users collection with validation
db.createCollection("users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["firebaseUid", "type"],
      properties: {
        firebaseUid: {
          bsonType: "string",
          description: "UID del usuario proveniente de Firebase Authentication"
        },
        type: {
          bsonType: "bool",
          description: "false = Student, true = Teacher"
        },
        followers: {
          bsonType: "array",
          items: { bsonType: "objectId" }
        },
        following: {
          bsonType: "array",
          items: { bsonType: "objectId" }
        },
        information: {
          bsonType: "object",
          required: ["streak"],
          properties: {
            streak: {
              bsonType: "object",
              required: ["current", "lastConnection"],
              properties: {
                current: { bsonType: "int" },
                lastConnection: { bsonType: "date" }
              }
            },
            achievements: {
              bsonType: "array",
              items: { bsonType: "objectId" }
            },
            lescoSkills: { bsonType: "int" },
            librasSkills: { bsonType: "int" },
            lescoLevel: { bsonType: "int" },
            librasLevel: { bsonType: "int" },
            myCourses: {
              bsonType: "array",
              items: { bsonType: "objectId" }
            }
          }
        }
      }
    }
  }
});

// 2. Create achievements collection
db.createCollection("achievements", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "type", "content", "date"],
      properties: {
        name: { bsonType: "string" },
        type: { 
          bsonType: "bool",
          description: "false = LESCO, true = LIBRAS"
        },
        content: { bsonType: "string" },
        date: { bsonType: "date" },
        premadeId: { bsonType: "objectId" }
      }
    }
  }
});

// 3. Create news collection (modificado: title en lugar de premadeId)
db.createCollection("news", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["userId", "date"],
      properties: {
        userId: { bsonType: "objectId" },
        title: { bsonType: "string" },  // Cambiado de premadeId a title
        description: { bsonType: "string" },
        likes: { bsonType: "int" },
        date: { bsonType: "date" },
        comments: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["_id", "comment", "userId", "date"],
            properties: {
              _id: { bsonType: "objectId" },
              comment: { bsonType: "string" },
              userId: { bsonType: "objectId" },
              date: { bsonType: "date" }
            }
          }
        }
      }
    }
  }
});

// 4. Create courses collection
db.createCollection("courses", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["userId", "name", "difficulty", "language", "status"],
      properties: {
        userId: { bsonType: "objectId" },
        name: { bsonType: "string" },
        description: { bsonType: "string" },
        difficulty: { bsonType: "int" },
        language: { 
          bsonType: "bool",
          description: "false = LESCO, true = LIBRAS"
        },
        status: { 
          bsonType: "bool",
          description: "false = private, true = public"
        },
        students: {
          bsonType: "array",
          items: { bsonType: "objectId" }
        },
        lessons: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["_id", "order", "name", "questionCount", "attempts", "forumEnabled"],
            properties: {
              _id: { bsonType: "objectId" },
              order: { bsonType: "int" },
              name: { bsonType: "string" },
              questionCount: { bsonType: "int" },
              attempts: { bsonType: "int" },
              forumEnabled: { bsonType: "bool" },
              theory: {
                bsonType: "array",
                items: {
                  bsonType: "object",
                  properties: {
                    text: { bsonType: "string" },
                    sign: { bsonType: "objectId" }
                  }
                }
              },
              exercises: {
                bsonType: "array",
                items: {
                  bsonType: "object",
                  required: ["_id", "exerciseType", "order"],
                  properties: {
                    _id: { bsonType: "objectId" },
                    exerciseType: { bsonType: "int" },
                    order: { bsonType: "int" },
                    sign: { bsonType: "objectId" },
                    question: { bsonType: "string" },
                    possibleAnswers: {
                      bsonType: "array",
                      items: { bsonType: "string" }
                    },
                    correctAnswer: {
                      bsonType: "array",
                      items: { bsonType: "string" }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
});

// 5. Create enrolled courses collection (modificado: agregados totalQuestions y correctAnswers)
db.createCollection("enrolledCourses", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["userId", "courseId"],
      properties: {
        userId: { bsonType: "objectId" },
        courseId: { bsonType: "objectId" },
        completionDate: { bsonType: ["date", "null"] },
        totalQuestions: { bsonType: ["int", "null"] },  // Nuevo: preguntas totales
        correctAnswers: { bsonType: ["int", "null"] },  // Nuevo: cantidad de correctas
        completedLessons: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["_id", "lessonId"],
            properties: {
              _id: { bsonType: "objectId" },
              lessonId: { bsonType: "objectId" },
              correctCount: { bsonType: "int" },
              remainingAttempts: { bsonType: "int" },
              completionDate: { bsonType: "date" }
            }
          }
        }
      }
    }
  }
});

// 6. Create forums collection
db.createCollection("forums", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["lessonId", "userId", "content", "creationDate"],
      properties: {
        lessonId: { bsonType: "objectId" },
        userId: { bsonType: "objectId" },
        content: { bsonType: "string" },
        videoURL: { 
          bsonType: ["string", "null"],
          description: "URL del video (opcional)"
        },
        creationDate: { bsonType: "date" },
        comments: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["_id", "userId", "content", "date"],
            properties: {
              _id: { bsonType: "objectId" },
              userId: { bsonType: "objectId" },
              content: { bsonType: "string" },
              videoURL: { 
                bsonType: ["string", "null"],
                description: "URL del video (opcional)"
              },
              date: { bsonType: "date" }
            }
          }
        }
      }
    }
  }
});

// 7. Create teacher statistics collection (modificado: campos directos sin generalStatistics)
db.createCollection("teacherStatistics", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["userId"],
      properties: {
        userId: { bsonType: "objectId" },
        coursesCreated: { bsonType: "int" },
        lessonsCreated: { bsonType: "int" },
        totalStudents: { bsonType: "int" }
      }
    }
  }
});

db.users.createIndex({ firebaseUid: 1 }, { unique: true });

print("\nCollections created successfully!");