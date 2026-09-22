# AI English Tutor — Grammar MVP Specification

> Visione estesa del progetto. Per la prima implementazione, il perimetro di riferimento è [MVP-SPEC.md](MVP-SPEC.md); in caso di differenze prevale quella specifica minimale.

## 1. Project Overview

**AI English Tutor** is a web application for beginner English learners. The first MVP focuses only on grammar study for CEFR levels **A1** and **A2**.

The core experience is:

> The user selects their level and chooses a 15- or 30-minute session. The system selects an appropriate grammar topic, generates a structured lesson with exercises, evaluates the submitted answers, explains mistakes, stores the result, and recommends what to study next.

The MVP should be intentionally small, reliable, and easy to evolve.

---

## 2. Product Goal

The application should reduce the effort required to decide what to study.

A typical user flow:

```text
Login
  ↓
Choose level: A1 / A2
  ↓
Home
  ↓
Recommended lesson
  ↓
Choose duration: 15 / 30 minutes
  ↓
Generated grammar lesson
  ↓
Exercises
  ↓
Submit answers
  ↓
Correction + explanations
  ↓
Score + progress update
  ↓
Recommended next lesson
```

Example:

```text
Level: A1
Duration: 15 minutes

Today's lesson:
Present Simple — Affirmative

1. Explanation
2. Examples
3. 6 exercises
4. Correction
5. Final feedback
```

---

## 3. MVP Scope

The MVP includes:

- User registration and login
- User-selected CEFR level: A1 or A2
- 15-minute sessions
- 30-minute sessions
- Deterministic A1/A2 grammar curriculum
- Automatic next-topic selection
- AI-generated grammar explanations
- AI-generated examples
- AI-generated structured exercises
- Multiple-choice exercises
- Fill-in-the-blank exercises
- Sentence-correction exercises
- Deterministic correction where possible
- Score calculation
- AI explanations for mistakes
- Lesson result persistence
- Basic progress tracking
- Weak-topic detection
- Recommended next lesson

---

## 4. Explicitly Out of Scope

Do **not** implement in the MVP:

- B1, B2, C1 or C2
- Speaking
- Speech-to-text
- Text-to-speech
- Pronunciation scoring
- Free-form writing
- Essay evaluation
- Vocabulary trainer
- Flashcards
- Spaced repetition
- Listening
- Reading comprehension
- RAG
- Vector databases
- Knowledge bases
- Web search
- MCP
- Multi-agent systems
- Specialized grammar agents
- Social features
- Teacher dashboards
- Classrooms
- Organizations
- Gamification
- XP, badges or leaderboards
- Payments or subscriptions
- Mobile apps
- Push notifications
- Complex recommendation ML
- Kubernetes
- Microservices

These can be explored in later versions.

---

# 5. Target User

The first target user is:

- A beginner English learner
- CEFR A1 or A2
- Wants short guided study sessions
- Wants immediate correction
- Wants simple explanations
- Does not want to manually choose every grammar topic

The product should require very few decisions before starting a study session.

---

# 6. Main User Journey

## 6.1 First access

The user:

1. Registers or logs in.
2. Selects:
   - A1
   - A2
3. The selected level is stored.
4. The system determines the first recommended grammar topic.

Example:

```text
Your level
A1

Recommended lesson
Verb "to be" — Affirmative

Choose session length

[ 15 minutes ]
[ 30 minutes ]

[ Start lesson ]
```

---

## 6.2 Starting a session

The user chooses either:

```text
15 minutes
```

or:

```text
30 minutes
```

The system:

1. Loads the user's level.
2. Loads lesson history.
3. Checks weak topics.
4. Reads the deterministic curriculum.
5. Selects the next suitable topic.
6. Generates a lesson for that topic and duration.
7. Validates the generated lesson.
8. Persists the generated lesson.
9. Returns the safe lesson content to the client.

---

## 6.3 Completing a lesson

The user:

1. Reads the explanation.
2. Reads the examples.
3. Completes the exercises.
4. Submits all answers.

The backend then:

1. Loads the original stored lesson.
2. Evaluates the answers.
3. Calculates the score.
4. Identifies error categories.
5. Requests short AI explanations for relevant mistakes.
6. Saves the lesson result.
7. Updates progress.
8. Determines the next lesson.
9. Returns the final feedback.

---

# 7. Supported CEFR Levels

Only:

```text
A1
A2
```

The data model should make adding future levels straightforward, but no additional levels should be implemented now.

---

# 8. Curriculum Strategy

The curriculum is **deterministic**.

The LLM must not decide:

- Which topics belong to A1
- Which topics belong to A2
- The canonical order of topics
- Topic prerequisites

Suggested storage:

```text
curriculum/
├── a1.json
└── a2.json
```

The curriculum may initially live inside the backend repository.

---

# 9. Suggested A1 Curriculum

```text
1. Subject pronouns
2. Verb "to be" — affirmative
3. Verb "to be" — negative
4. Verb "to be" — questions
5. Articles — a / an
6. Definite article — the
7. Singular and plural nouns
8. Possessive adjectives
9. Have got / has got
10. There is / there are
11. Present Simple — affirmative
12. Present Simple — negative
13. Present Simple — questions
14. Adverbs of frequency
15. Can / can't
16. Basic prepositions of place
17. Basic prepositions of time
18. This / that / these / those
19. Basic question words
20. Imperatives
```

The exact list can be refined before implementation, but once defined it should remain explicit and version-controlled.

---

# 10. Suggested A2 Curriculum

```text
1. Present Continuous
2. Present Simple vs Present Continuous
3. Past Simple — regular verbs
4. Past Simple — irregular verbs
5. Past Simple — negatives and questions
6. Countable and uncountable nouns
7. Some / any
8. Much / many / a lot of
9. Comparative adjectives
10. Superlative adjectives
11. Going to
12. Will
13. Should / shouldn't
14. Must / mustn't
15. Have to
16. Adverbs of manner
17. Object pronouns
18. Basic Present Perfect
19. Present Perfect with ever / never
20. Basic First Conditional
```

---

# 11. Curriculum Data Model

Suggested topic model:

```json
{
  "id": "present-simple-affirmative",
  "level": "A1",
  "title": "Present Simple — Affirmative",
  "order": 11,
  "prerequisites": [
    "subject-pronouns"
  ],
  "learning_objectives": [
    "Understand the basic Present Simple structure",
    "Use the base verb with I/you/we/they",
    "Use third-person singular -s"
  ]
}
```

Minimum useful fields:

```text
id
level
title
order
prerequisites
learning_objectives
```

Avoid adding unnecessary curriculum metadata in the MVP.

---

# 12. Lesson Duration

The user can select:

```text
15 minutes
30 minutes
```

This is an approximate instructional duration, not an enforced timer.

The selected duration affects:

- Explanation length
- Number of examples
- Number of exercises
- Exercise variety
- Amount of review

---

# 13. 15-Minute Lesson

Suggested structure:

```text
2 min   Explanation
2 min   Examples
8 min   Exercises
3 min   Correction and review
```

Suggested exercise count:

```text
5–7 exercises
```

Possible distribution:

```text
2 multiple choice
3 fill in the blank
1 sentence correction
```

The exact distribution may vary slightly.

---

# 14. 30-Minute Lesson

Suggested structure:

```text
5 min   Explanation
5 min   Examples
15 min  Exercises
5 min   Correction and review
```

Suggested exercise count:

```text
10–15 exercises
```

Possible distribution:

```text
4 multiple choice
5 fill in the blank
3 sentence correction
```

The exercises may gradually increase in difficulty while staying within the requested CEFR level and grammar topic.

---

# 15. Lesson Generation

Lesson content is generated by an LLM.

Generation context should contain controlled information such as:

```json
{
  "level": "A1",
  "topic_id": "present-simple-affirmative",
  "title": "Present Simple — Affirmative",
  "duration_minutes": 15,
  "learning_objectives": [
    "Use Present Simple affirmative forms",
    "Use third-person singular -s"
  ]
}
```

The model generates:

- Title
- Explanation
- Examples
- Exercises
- Correct answers
- Accepted answers if needed
- Error categories

The internal representation must be structured.

Do not use free-form Markdown as the source of truth for a lesson.

---

# 16. Lesson Structured Output

Example:

```json
{
  "level": "A1",
  "topic_id": "present-simple-affirmative",
  "title": "Present Simple — Affirmative",
  "duration_minutes": 15,
  "explanation": "We use the Present Simple to talk about habits and routines...",
  "examples": [
    {
      "sentence": "I work in Rome.",
      "note": "Use the base form with I."
    },
    {
      "sentence": "She works in Rome.",
      "note": "Use -s with she."
    }
  ],
  "exercises": [
    {
      "id": "exercise-1",
      "type": "multiple_choice",
      "question": "She ___ in London.",
      "options": [
        "live",
        "lives",
        "living"
      ],
      "correct_answer": "lives",
      "accepted_answers": [
        "lives"
      ],
      "error_category": "third_person_s"
    }
  ]
}
```

---

# 17. Supported Exercise Types

Only three exercise types are required.

## 17.1 Multiple Choice

Example:

```text
She ___ English every day.

A. study
B. studies
C. studying
```

Internal example:

```json
{
  "type": "multiple_choice",
  "question": "She ___ English every day.",
  "options": [
    "study",
    "studies",
    "studying"
  ],
  "correct_answer": "studies"
}
```

---

## 17.2 Fill in the Blank

Example:

```text
I ___ in Italy. (live)
```

Internal example:

```json
{
  "type": "fill_blank",
  "question": "I ___ in Italy. (live)",
  "correct_answer": "live",
  "accepted_answers": [
    "live"
  ]
}
```

Exercises should avoid ambiguity.

---

## 17.3 Sentence Correction

Example:

```text
Correct the sentence:

He work in London.
```

Expected answer:

```text
He works in London.
```

Example:

```json
{
  "type": "sentence_correction",
  "question": "He work in London.",
  "correct_answer": "He works in London.",
  "accepted_answers": [
    "He works in London."
  ]
}
```

Sentence correction can use controlled normalization before comparison.

---

# 18. Exercise Evaluation

Core principle:

> If correctness can be evaluated deterministically, do not ask the LLM to judge it.

For:

- Multiple choice
- Fill in the blank
- Controlled sentence correction

use backend logic.

Flow:

```text
User answer
    ↓
Normalize
    ↓
Compare to accepted answers
    ↓
Correct / Incorrect
```

The LLM is used for explanation, not basic scoring.

---

# 19. Answer Normalization

Possible normalization:

- Trim leading/trailing spaces
- Collapse repeated spaces
- Case normalization where appropriate
- Ignore irrelevant final punctuation where appropriate

Example accepted variants:

```text
Lives
lives
lives.
```

The rules should remain conservative.

Do not introduce fuzzy matching unless a concrete need appears.

---

# 20. Mistake Explanation

For incorrect answers, use the LLM to generate a short learner-friendly explanation.

Input:

```json
{
  "level": "A1",
  "topic": "present_simple",
  "question": "She ___ in London.",
  "user_answer": "live",
  "correct_answer": "lives",
  "error_category": "third_person_s"
}
```

Expected style:

```text
Correct answer:
She lives in London.

Why:
With he, she and it in the Present Simple, the verb normally takes -s.
```

The explanation should:

- Match A1/A2 language complexity
- Be concise
- Explain the concrete mistake
- Avoid unnecessary linguistic terminology
- Never introduce unsupported corrections

---

# 21. Error Categories

Exercises should include machine-readable error categories where practical.

Examples:

```text
third_person_s
verb_to_be
article_usage
plural_nouns
word_order
present_simple_negative
present_simple_question
past_simple_regular
past_simple_irregular
some_any
countable_uncountable
comparative_form
superlative_form
```

These support progress analysis without relying on the LLM to infer everything retrospectively.

---

# 22. Score Calculation

Use a simple score:

```text
score = correct_answers / total_exercises
```

Example:

```text
8 / 10 = 80%
```

No weighted scoring is required in the MVP.

---

# 23. Final Feedback

Example:

```text
Lesson completed

Present Simple — Affirmative

Score
8 / 10 — 80%

Strong areas
✓ Basic sentence structure
✓ I / you / we / they forms

Needs review
• Third-person singular -s

Mistakes
2

Recommended next lesson
Present Simple — Negative Forms
```

Feedback should be concise and actionable.

---

# 24. Progress Tracking

Minimum data to persist:

- Current user level
- Completed lessons
- Topic scores
- Error categories
- Completion timestamps
- Weak topics

Example lesson result:

```json
{
  "user_id": "user-123",
  "topic_id": "present-simple-affirmative",
  "level": "A1",
  "score": 0.8,
  "correct_answers": 8,
  "total_exercises": 10,
  "duration_minutes": 15,
  "mistakes": [
    {
      "error_category": "third_person_s",
      "count": 2
    }
  ],
  "completed_at": "2026-09-18T12:00:00Z"
}
```

---

# 25. Student Profile

Keep the learner model minimal.

Example:

```json
{
  "user_id": "user-123",
  "level": "A1",
  "completed_topics": [
    "subject-pronouns",
    "verb-to-be-affirmative"
  ],
  "weak_topics": [
    "present-simple-affirmative"
  ]
}
```

A sophisticated memory system is not necessary.

---

# 26. Weak Topic Detection

Use transparent deterministic rules.

Initial suggestion:

```text
If latest topic score < 70%
→ mark topic as needs_review
```

Optional:

```text
If the same error category occurs in at least 2 different lessons
→ increase its review priority
```

Do not build a machine-learning recommendation system in the MVP.

---

# 27. Next-Lesson Selection

Next-topic selection should be deterministic.

Suggested priority:

```text
1. Weak topic requiring review
2. Next incomplete topic whose prerequisites are satisfied
3. Older completed topic eligible for review
```

Example:

```text
Level:
A1

Completed:
Subject pronouns
Verb to be — affirmative
Verb to be — negative

Weak:
Verb to be — negative

Recommendation:
Verb to be — negative review
```

The LLM must not override curriculum order or prerequisites.

---

# 28. Basic Personalization

Personalization may use only:

- Current CEFR level
- Completed topics
- Previous scores
- Weak topics
- Repeated error categories

Examples:

```text
Low score
→ review same topic

Repeated third_person_s errors
→ include extra third-person exercises

High score
→ continue to next topic
```

Do not implement complex adaptive-learning algorithms yet.

---

# 29. Agentic Architecture

Use **one Tutor Agent**.

No multi-agent system.

High-level concept:

```text
                    Tutor Agent
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
   Student Progress   Curriculum    Lesson Results
          |              |              |
          +--------------+--------------+
                         |
                         v
                  Lesson Generator
```

The agent coordinates the learning session but should not own deterministic business rules.

---

# 30. Initial Agent Tools

Use three tools.

## Tool 1 — `get_student_progress`

Purpose:

Retrieve the learner's current state.

Suggested interface:

```python
get_student_progress(
    user_id: str
)
```

Example output:

```json
{
  "level": "A1",
  "completed_topics": [],
  "weak_topics": [],
  "recent_scores": []
}
```

---

## Tool 2 — `get_next_lesson`

Purpose:

Select the next grammar topic using curriculum and progress rules.

Suggested interface:

```python
get_next_lesson(
    user_id: str,
    duration_minutes: int
)
```

Responsibilities:

- Read curriculum
- Read progress
- Check prerequisites
- Prioritize required reviews
- Return the generation context

Example output:

```json
{
  "level": "A1",
  "topic_id": "present-simple-affirmative",
  "title": "Present Simple — Affirmative",
  "duration_minutes": 15,
  "learning_objectives": [
    "Use Present Simple affirmative forms",
    "Use third-person singular -s"
  ]
}
```

---

## Tool 3 — `save_lesson_result`

Purpose:

Persist completed lesson results.

Suggested interface:

```python
save_lesson_result(
    user_id: str,
    lesson_result: LessonResult
)
```

Responsibilities:

- Save score
- Save error categories
- Mark completion
- Update weak-topic state

---

# 31. Tutor Agent Responsibilities

The Tutor Agent may:

- Read learner progress
- Request the next lesson
- Coordinate lesson generation
- Use saved results to produce final feedback
- Present the recommended next step

The Tutor Agent must not:

- Invent curriculum topics
- Reclassify CEFR levels
- Calculate scores itself
- Judge deterministic answers itself
- Modify persistence directly without tools
- Override prerequisite rules

---

# 32. Suggested LangGraph Flow

Minimal conceptual flow:

```text
START
  ↓
Load Student Context
  ↓
Select Lesson
  ↓
Generate Lesson
  ↓
Validate Lesson
  ↓
Persist Lesson
  ↓
Present Lesson
  ↓
USER COMPLETES EXERCISES
  ↓
Evaluate Answers
  ↓
Save Result
  ↓
Generate Feedback
  ↓
Recommend Next Lesson
  ↓
END
```

The implementation can be simpler if some steps are normal backend services instead of graph nodes.

Do not force every operation into LangGraph.

---

# 33. Responsibility Separation

Keep three major domains separate:

```text
                  Tutor Agent
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
    Curriculum     Lesson      Progress
      Engine      Generator     Tracker
```

## Curriculum Engine

Deterministic.

Responsible for:

- Topic definitions
- Ordering
- Prerequisites
- Next-topic rules

## Lesson Generator

LLM-driven.

Responsible for:

- Explanation
- Examples
- Exercise creation
- Error metadata

## Progress Tracker

Deterministic.

Responsible for:

- Scores
- History
- Weak topics
- Repeated error categories

---

# 34. Backend Stack

Recommended:

```text
Python
FastAPI
LangGraph
Pydantic
PostgreSQL
SQLAlchemy
Alembic
```

Suggested structure:

```text
src/
├── api/
├── agent/
├── curriculum/
├── lesson_generation/
├── evaluation/
├── progress/
├── models/
├── repositories/
└── services/
```

Avoid architectural layers that do not provide immediate value.

---

# 35. API Responsibilities

The backend should expose operations for:

- Registration
- Login
- Current profile
- Updating selected level
- Starting a lesson
- Retrieving an active lesson
- Submitting answers
- Retrieving progress
- Retrieving curriculum overview

---

# 36. Suggested API Endpoints

Possible minimal design:

```text
POST  /auth/register
POST  /auth/login

GET   /me
PATCH /me/level

POST  /lessons/start
GET   /lessons/{lesson_id}
POST  /lessons/{lesson_id}/submit

GET   /progress
GET   /curriculum
```

Lesson start request:

```json
{
  "duration_minutes": 15
}
```

Possible response:

```json
{
  "lesson_id": "lesson-123",
  "level": "A1",
  "topic_id": "present-simple-affirmative",
  "title": "Present Simple — Affirmative",
  "content": {}
}
```

---

# 37. Authentication

Keep authentication minimal.

Requirements:

- Registration
- Login
- User identity
- Protected personal progress

Do not implement:

- Social login
- Complex roles
- Organizations
- Multi-tenant authorization

The concrete authentication mechanism can be chosen based on the final deployment environment.

---

# 38. Database

Use PostgreSQL.

Suggested MVP entities:

```text
users
lesson_sessions
lesson_results
```

Optional:

```text
user_topic_progress
```

The curriculum can remain in JSON files.

---

# 39. Suggested User Model

```text
id
email
password_hash OR external_auth_id
level
created_at
updated_at
```

---

# 40. Suggested Lesson Session Model

```text
id
user_id
topic_id
level
duration_minutes
generated_content_json
status
created_at
completed_at
```

Possible status values:

```text
started
completed
abandoned
```

---

# 41. Suggested Lesson Result Model

```text
id
lesson_session_id
user_id
score
correct_answers
total_exercises
mistakes_json
created_at
```

---

# 42. Lesson Persistence

Every generated lesson should be persisted before presentation.

Reasons:

- Refreshing the page must not regenerate the lesson
- Correct answers must remain stable
- Evaluation must use the exact original lesson
- Debugging becomes easier
- Lesson history can be inspected

---

# 43. Correct Answers Security

Correct answers must never be sent to the client before submission.

Backend stores:

```text
question
options
correct answer
accepted answers
error category
```

Frontend receives only safe fields:

```text
question
options
exercise type
exercise id
```

Submission flow:

```text
Frontend answers
      ↓
Backend loads original lesson
      ↓
Backend evaluates
      ↓
Backend returns corrections
```

---

# 44. Frontend

Keep the frontend minimal.

Suggested pages:

```text
Login / Register
Onboarding
Home
Lesson
Results
Progress
```

---

# 45. Home Page

Example:

```text
Welcome back

Your level
A1

Progress
34%

Recommended lesson
Present Simple — Negative Forms

Choose session length

[ 15 minutes ]
[ 30 minutes ]

[ Start lesson ]
```

---

# 46. Lesson Page

Example:

```text
Present Simple — Affirmative
A1 · 15 min

Explanation
--------------------------------

Examples
--------------------------------

Exercises

1 / 6

She ___ in Rome.

( ) live
( ) lives
( ) living

[ Next ]
```

Exercises may initially be shown:

- One at a time, or
- All on one page

Choose whichever is simpler to implement.

---

# 47. Results Page

Example:

```text
Lesson completed

8 / 10
80%

Strong areas
✓ Basic Present Simple structure

Needs review
• Third-person singular -s

Mistakes

1.
Your answer:
She live in London.

Correct:
She lives in London.

Why:
With she, the verb normally takes -s.

Next lesson
Present Simple — Negative Forms

[ Continue ]
```

---

# 48. Progress Page

Keep progress simple.

Possible information:

```text
Current level
A1

Completed topics
7 / 20

Recent results
Present Simple        80%
Verb to be            90%
Articles              65%

Needs review
Articles
```

No complex analytics dashboard is required.

---

# 49. LLM Responsibilities

Use the LLM for:

- Grammar explanations
- Examples
- Exercise generation
- Mistake explanations
- Concise final feedback

Do not use the LLM for:

- Curriculum definition
- Topic ordering
- Prerequisite checks
- Score calculation
- Basic answer validation
- Progress calculations

---

# 50. Structured Output Validation

All generated lessons should pass through Pydantic models.

Conceptual example:

```python
class Lesson(BaseModel):
    level: Literal["A1", "A2"]
    topic_id: str
    title: str
    duration_minutes: Literal[15, 30]
    explanation: str
    examples: list[LessonExample]
    exercises: list[Exercise]
```

Invalid generations should be rejected and retried with a small retry limit.

Never trust arbitrary free-form model output as application data.

---

# 51. Prompt Requirements

Generation prompts should include:

- CEFR level
- Grammar topic
- Learning objectives
- Session duration
- Allowed exercise types
- Target number of exercises
- Language complexity requirements
- Structured output schema

The model should be instructed to:

- Stay within the requested grammar topic
- Use vocabulary appropriate for A1/A2
- Avoid unnecessary advanced grammar
- Generate unambiguous exercises
- Ensure every exercise has a correct answer
- Avoid duplicate exercises
- Keep explanations concise
- Return only the requested schema

---

# 52. Lesson Validation

Before exposing a lesson, validate:

```text
Requested level matches output
Requested topic matches output
Duration is valid
Exercise count is within expected range
Only supported exercise types are present
Every exercise has a correct answer
Every multiple-choice correct answer is in its options
Every exercise has an error category where applicable
Exercise IDs are unique
```

If validation fails:

```text
Retry generation
```

Use a limited retry count.

No infinite retry loops.

---

# 53. Suggested Technology Stack

```text
Frontend
Vue or React

Backend
Python + FastAPI

Agent
LangGraph

LLM
Amazon Bedrock or OpenAI

Structured AI output
Pydantic

Database
PostgreSQL

ORM
SQLAlchemy

Migrations
Alembic

Local development
Docker Compose
```

Prefer established libraries over custom infrastructure.

---

# 54. Deployment Strategy

Deployment is not the first milestone.

Recommended order:

```text
1. Curriculum works locally
2. Lesson generation works
3. Structured validation works
4. Exercise correction works
5. Progress persists
6. Agent flow works
7. Frontend works
8. Automated tests pass
9. Deploy
```

Potential later deployment:

```text
Frontend
S3 + CloudFront or managed frontend hosting

Backend
ECS / App Runner / Lambda

Database
RDS PostgreSQL
```

Do not introduce complex AWS infrastructure before the local MVP is complete.

---

# 55. Testing Strategy

## Curriculum Tests

Test:

- A1 order
- A2 order
- Prerequisite resolution
- Invalid topic detection
- Next-topic selection

## Evaluation Tests

Test:

- Multiple-choice correction
- Fill-in-the-blank normalization
- Sentence-correction normalization
- Score calculation
- Accepted-answer handling

## Progress Tests

Test:

- Lesson result persistence
- Weak-topic detection
- Review priority
- Next-lesson recommendation

## Lesson Generation Tests

Test:

- Schema validation
- Requested level
- Requested topic
- Supported exercise types
- Exercise count
- Unique exercise IDs
- Valid multiple-choice answers

## Agent Tool Tests

Test:

- `get_student_progress`
- `get_next_lesson`
- `save_lesson_result`

Do not rely only on end-to-end LLM tests.

---

# 56. Observability

Keep observability basic.

Useful logs:

```text
lesson_generation_started
lesson_generation_completed
lesson_generation_failed

level
topic_id
duration_minutes

LLM latency
token usage if available

lesson_submitted
score
exercise_count
```

Avoid logging sensitive account data or unnecessary raw user content.

---

# 57. Design Principles

## Keep the MVP small

Implement only the complete grammar-learning loop.

## Deterministic where possible

Use normal application logic for:

- Scores
- Answers
- Curriculum
- Prerequisites
- Topic progression

## Use AI where it adds value

Use the LLM for:

- Natural explanations
- Content generation
- Personalized feedback

## Structured AI

Prefer typed structured outputs over unstructured model responses.

## Grounded correction

All feedback must refer to the real exercise and stored correct answer.

## Persistent progress

The user should be able to return later and continue from their previous progress.

## Simple personalization

Use previous scores and errors without introducing complex memory architecture.

## Avoid premature architecture

No multi-agent system, microservices, vector database or RAG unless a later requirement clearly needs them.

---

# 58. MVP Definition of Done

The MVP is complete when:

1. A user can register.
2. A user can log in.
3. A user can select A1 or A2.
4. The selected level persists.
5. The A1 curriculum exists as structured data.
6. The A2 curriculum exists as structured data.
7. The system can determine the next grammar topic.
8. The user can choose 15 minutes.
9. The user can choose 30 minutes.
10. The backend can generate a structured lesson with an LLM.
11. Generated lessons are validated.
12. Generated lessons are persisted.
13. Lessons contain explanations.
14. Lessons contain examples.
15. Multiple-choice exercises work.
16. Fill-in-the-blank exercises work.
17. Sentence-correction exercises work.
18. Correct answers remain server-side before submission.
19. The backend can evaluate submitted answers.
20. The backend calculates a score.
21. Incorrect answers receive clear explanations.
22. Lesson results are persisted.
23. Weak topics can be identified.
24. The next lesson is selected automatically.
25. The user can view basic progress.
26. The full learning loop works locally.
27. Core deterministic logic has automated tests.

---

# 59. Reference User Story

> As an A1 or A2 English learner, I want to choose how much time I have available so that the system can automatically create an appropriate grammar lesson, let me practice, correct my answers, explain my mistakes, and tell me what I should study next.

---

# 60. Example Full Flow

```text
User logs in
      ↓
Level = A1
      ↓
Home
      ↓
Recommended:
Present Simple — Affirmative
      ↓
User selects:
15 minutes
      ↓
Tutor Agent
      ↓
get_student_progress()
      ↓
get_next_lesson()
      ↓
LLM generates structured lesson
      ↓
Backend validates lesson
      ↓
Backend persists lesson
      ↓
Frontend receives safe lesson
      ↓
User studies explanation
      ↓
User completes 6 exercises
      ↓
POST answers
      ↓
Backend evaluates deterministically
      ↓
Score = 67%
      ↓
Detected errors:
third_person_s × 2
      ↓
save_lesson_result()
      ↓
Topic marked needs_review
      ↓
LLM generates concise explanation
      ↓
Results page
      ↓
Recommended:
Present Simple — Affirmative Review
```

---

# 61. Suggested Implementation Milestones

## Milestone 1 — Curriculum

Implement:

- A1 JSON
- A2 JSON
- Topic model
- Ordering
- Prerequisites
- Next-topic selection tests

No LLM yet.

## Milestone 2 — Lesson Generation

Implement:

- Pydantic lesson schema
- LLM provider abstraction
- Lesson generation prompt
- Output validation
- Retry handling

## Milestone 3 — Evaluation

Implement:

- Answer normalization
- Multiple choice
- Fill in the blank
- Sentence correction
- Score calculation
- Error collection

## Milestone 4 — Persistence

Implement:

- PostgreSQL
- User
- Lesson session
- Lesson result
- Progress retrieval
- Weak-topic rules

## Milestone 5 — Tutor Agent

Implement:

- LangGraph
- `get_student_progress`
- `get_next_lesson`
- `save_lesson_result`
- Minimal orchestration

## Milestone 6 — API

Implement:

- Auth
- User level
- Start lesson
- Get lesson
- Submit lesson
- Progress

## Milestone 7 — Frontend

Implement:

- Login
- Onboarding
- Home
- Lesson
- Results
- Progress

## Milestone 8 — Hardening

Implement:

- Tests
- Error handling
- Logging
- Prompt refinements
- Documentation
- Local Docker Compose

Only after these milestones should deployment be considered.

---

# 62. Future Evolution

Possible later versions:

## V2 — Vocabulary

- Thematic vocabulary
- Vocabulary exercises
- Basic review

## V3 — Writing

- Guided writing
- Structured corrections
- Grammar/vocabulary/coherence feedback

## V4 — Text Conversation

- Conversation scenarios
- Tutor chat
- End-of-session correction

## V5 — Voice

- Speech-to-text
- Text-to-speech
- Voice conversation

## V6 — Adaptive Tutor

- Richer learner profile
- Long-term weakness detection
- Dynamic difficulty
- Personalized study plans

These are not MVP requirements.

---

# 63. Guidelines for Coding Agents

When implementing this project:

- Treat this specification as the MVP source of truth.
- Prefer the smallest solution that satisfies the requirements.
- Do not add features listed as out of scope.
- Do not introduce multi-agent architecture.
- Keep curriculum rules deterministic.
- Keep answer evaluation deterministic wherever possible.
- Use the LLM only where generation or explanation provides real value.
- Use Pydantic for model-generated structured data.
- Keep correct answers on the backend until submission.
- Persist generated lessons before presenting them.
- Add automated tests around curriculum, evaluation and progression.
- Do not force every backend operation into LangGraph.
- Prefer established Python libraries.
- Avoid premature abstractions.
- Avoid microservices.
- Avoid unnecessary cloud infrastructure.
- Document assumptions.
- Make small, reviewable changes.
- If a design choice conflicts with this document, prefer the simpler MVP solution unless there is a concrete technical requirement.

---

# 64. Short Product Definition

**AI English Tutor** is a personalized grammar-learning application for A1 and A2 learners. The user selects a 15- or 30-minute study session, receives an AI-generated grammar lesson with structured exercises, submits answers for deterministic correction, receives clear explanations for mistakes, and follows a predefined curriculum adapted through basic progress tracking.
