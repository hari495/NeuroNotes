"""
API routes for Study Mode.

Endpoints for generating flashcards and quiz questions from user notes.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from app.schemas import FlashcardResponse, QuizResponse
from app.services.study_service import StudyService
from app.dependencies import get_study_service


router = APIRouter()
StudyDep = Annotated[StudyService, Depends(get_study_service)]


@router.post("/flashcards", response_model=FlashcardResponse)
async def generate_flashcards(
    topic: str,
    count: int = 5,
    study: StudyDep = None
) -> FlashcardResponse:
    """
    Generate flashcards for a given topic based on user notes.

    This endpoint uses RAG to retrieve relevant context from your uploaded notes,
    then prompts the LLM to generate flashcards in a structured format.

    **Example Request:**
    ```
    POST /api/study/flashcards?topic=linear+algebra+vectors&count=3
    ```

    **Example Response:**
    ```json
    {
      "topic": "linear algebra vectors",
      "count": 3,
      "cards": [
        {
          "front": "Vector Space",
          "back": "A set with vector addition and scalar multiplication operations."
        },
        {
          "front": "Linear Independence",
          "back": "A set of vectors where no vector can be written as a linear combination of others."
        }
      ],
      "context_sources": ["MATH 136 Course Notes"]
    }
    ```

    Args:
        topic: The topic to generate flashcards for (e.g., "Linear Algebra Eigenvectors")
        count: Number of flashcards to generate (1-10, default: 5)
        study: StudyService dependency (injected automatically)

    Returns:
        FlashcardResponse with generated cards and source attribution

    Raises:
        HTTPException 400: Invalid input parameters or no notes found for topic
        HTTPException 500: LLM generation or JSON parsing failed
    """
    try:
        # Validate count
        if count < 1 or count > 10:
            raise HTTPException(
                status_code=400,
                detail="Count must be between 1 and 10"
            )

        # Generate flashcards
        result = await study.generate_flashcards(topic=topic, count=count)
        return result

    except ValueError as e:
        # No context found or parsing error
        error_msg = str(e)

        # Provide specific guidance based on error type
        if "No notes found" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="No relevant notes found for this topic. Try uploading study materials first or use a different topic."
            )
        elif "No valid JSON found" in error_msg or "parse" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Failed to generate flashcards. The AI response was incomplete. Try: (1) Using a simpler topic, (2) Reducing the count, or (3) Trying again."
            )
        else:
            raise HTTPException(status_code=400, detail=error_msg)

    except Exception as e:
        # Unexpected error
        print(f"✗ Flashcard generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating flashcards. Please try again."
        )


@router.post("/quiz", response_model=QuizResponse)
async def generate_quiz(
    topic: str,
    difficulty: str = "medium",
    study: StudyDep = None
) -> QuizResponse:
    """
    Generate a multiple-choice quiz question for a given topic.

    This endpoint uses RAG to retrieve relevant context from your uploaded notes,
    then prompts the LLM to generate a rigorous MCQ with plausible distractors.

    **Example Request:**
    ```
    POST /api/study/quiz?topic=eigenvectors&difficulty=hard
    ```

    **Example Response:**
    ```json
    {
      "topic": "eigenvectors",
      "difficulty": "hard",
      "question": {
        "question": "Which statement about eigenvectors is correct?",
        "options": [
          {"text": "They form a basis for the vector space", "is_correct": false},
          {"text": "They change only by a scalar multiple", "is_correct": true},
          {"text": "They are unchanged by the transformation", "is_correct": false},
          {"text": "They must be orthogonal to each other", "is_correct": false}
        ],
        "explanation": "Eigenvectors change by a scalar factor (eigenvalue) when a transformation is applied..."
      },
      "context_sources": ["Linear Algebra Textbook.pdf"]
    }
    ```

    Args:
        topic: The topic for the quiz question (e.g., "Vector Spaces in Linear Algebra")
        difficulty: Question difficulty - "easy", "medium", or "hard" (default: "medium")
        study: StudyService dependency (injected automatically)

    Returns:
        QuizResponse with question, 4 options, explanation, and source attribution

    Raises:
        HTTPException 400: Invalid difficulty or no notes found for topic
        HTTPException 500: LLM generation or JSON parsing failed
    """
    try:
        # Validate difficulty
        if difficulty not in ["easy", "medium", "hard"]:
            raise HTTPException(
                status_code=400,
                detail="Difficulty must be 'easy', 'medium', or 'hard'"
            )

        # Generate quiz
        result = await study.generate_quiz(topic=topic, difficulty=difficulty)
        return result

    except ValueError as e:
        # No context found or parsing error
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected error
        print(f"✗ Quiz generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Failed to generate quiz. Please try again."
        )
