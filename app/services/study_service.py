"""
Study Service for generating flashcards and quiz questions.

This service uses RAG to retrieve relevant context from user notes,
then prompts the LLM to generate structured study materials in JSON format.
"""

import json
import re
from typing import List

from app.schemas import Flashcard, FlashcardResponse, MCQOption, QuizQuestion, QuizResponse
from app.services.rag_service import RAGService
from app.core.interfaces import LLMProvider


class StudyService:
    """
    Service for generating study materials (flashcards, quizzes) from notes.

    Uses RAG to retrieve relevant context, then prompts LLM to generate
    structured JSON output that is parsed and validated with Pydantic.
    """

    def __init__(self, rag_service: RAGService, llm_provider: LLMProvider) -> None:
        """
        Initialize the Study Service.

        Args:
            rag_service: RAG service for retrieving relevant context
            llm_provider: LLM provider for generating study materials
        """
        self.rag = rag_service
        self.llm = llm_provider

    async def generate_flashcards(self, topic: str, count: int = 5) -> FlashcardResponse:
        """
        Generate flashcards for a given topic using RAG context.

        Args:
            topic: The topic to generate flashcards for
            count: Number of flashcards to generate (default: 5)

        Returns:
            FlashcardResponse with generated cards and source attribution

        Raises:
            ValueError: If no context found for topic or LLM response invalid
        """
        # Step 1: Retrieve relevant context using RAG
        context_chunks = await self.rag.query_notes(query=topic, k=5)

        if not context_chunks:
            raise ValueError(f"No notes found for topic: {topic}")

        # Step 2: Format context for LLM
        context_text = self._format_context(context_chunks)

        # Step 3: Construct prompt
        prompt = self._construct_flashcard_prompt(topic, count, context_text)

        # Step 4: Call LLM
        print(f"📝 Generating {count} flashcards for topic: {topic}")
        response = await self.llm.generate_response(prompt)

        # Step 5: Parse JSON (robust with fallbacks)
        flashcards = self._parse_flashcard_json(response)

        # Step 6: Extract source titles
        sources = [chunk['metadata'].get('title', 'Unknown') for chunk in context_chunks]

        print(f"✓ Generated {len(flashcards)} flashcards")
        return FlashcardResponse(
            topic=topic,
            count=len(flashcards),
            cards=flashcards,
            context_sources=list(set(sources))  # Deduplicate
        )

    async def generate_quiz(self, topic: str, difficulty: str = "medium") -> QuizResponse:
        """
        Generate a multiple-choice quiz question for a given topic.

        Args:
            topic: The topic for the quiz question
            difficulty: Question difficulty - "easy", "medium", or "hard"

        Returns:
            QuizResponse with question, options, explanation, and sources

        Raises:
            ValueError: If no context found for topic or LLM response invalid
        """
        # Step 1: Retrieve relevant context using RAG
        context_chunks = await self.rag.query_notes(query=topic, k=5)

        if not context_chunks:
            raise ValueError(f"No notes found for topic: {topic}")

        # Step 2: Format context for LLM
        context_text = self._format_context(context_chunks)

        # Step 3: Construct prompt
        prompt = self._construct_quiz_prompt(topic, difficulty, context_text)

        # Step 4: Call LLM
        print(f"📝 Generating {difficulty} quiz question for topic: {topic}")
        response = await self.llm.generate_response(prompt)

        # Step 5: Parse JSON (robust with fallbacks)
        quiz_data = self._parse_quiz_json(response)

        # Step 6: Extract source titles
        sources = [chunk['metadata'].get('title', 'Unknown') for chunk in context_chunks]

        print(f"✓ Generated quiz question")
        return QuizResponse(
            topic=topic,
            difficulty=difficulty,
            question=quiz_data,
            context_sources=list(set(sources))  # Deduplicate
        )

    def _format_context(self, chunks: List[dict]) -> str:
        """
        Format RAG chunks into context text for LLM prompt.

        Args:
            chunks: List of RAG result chunks with text and metadata

        Returns:
            Formatted context string with source attribution
        """
        return "\n\n---\n\n".join([
            f"[Source: {chunk['metadata'].get('title', 'Unknown')}]\n{chunk['text']}"
            for chunk in chunks
        ])

    def _construct_flashcard_prompt(self, topic: str, count: int, context: str) -> str:
        """
        Build the flashcard generation prompt with JSON instructions.

        Args:
            topic: The topic for flashcards
            count: Number of flashcards to generate
            context: Formatted context text from RAG

        Returns:
            Complete prompt string for LLM
        """
        return f"""You are a Flashcard Generator. Your ONLY job is to output valid JSON. Do not include any explanations, markdown formatting, or conversational text.

CONTEXT FROM NOTES:
{context}

TOPIC: {topic}

TASK: Generate exactly {count} flashcards based on the context above.
- Each card has a 'front' (concept/term/question) and 'back' (definition/answer).
- CRITICAL: Keep 'front' under 50 characters and 'back' under 150 characters.
- Base the flashcards ONLY on the context provided.

OUTPUT FORMAT - Your response must be ONLY this valid JSON structure:
{{
  "cards": [
    {{"front": "Term or concept", "back": "Concise definition or explanation"}},
    {{"front": "Another term", "back": "Another concise definition"}}
  ]
}}

CRITICAL RULES:
1. Output ONLY the JSON. No markdown code blocks, no explanations, no extra text.
2. Keep each 'back' field under 150 characters maximum.
3. Ensure the JSON is complete with all closing brackets.
4. Generate all {count} flashcards in a single response."""

    def _construct_quiz_prompt(self, topic: str, difficulty: str, context: str) -> str:
        """
        Build the quiz generation prompt with JSON instructions.

        Args:
            topic: The topic for the quiz question
            difficulty: Question difficulty level
            context: Formatted context text from RAG

        Returns:
            Complete prompt string for LLM
        """
        return f"""You are a Professor creating a rigorous exam.
CONTEXT: {context}

TASK: Create 1 multiple-choice question based on the context.
1. The question should test deep understanding, not just memorization.
2. Difficulty level: {difficulty.upper()}
3. Provide 1 Correct Answer.
4. Provide 3 "Distractors" (wrong answers).
   - Distractors must be PLAUSIBLE. They should represent common student misconceptions.
   - Do NOT make them obviously fake.

OUTPUT FORMAT (JSON ONLY):
{{
  "question": "...",
  "options": [
    {{"text": "Option A text", "is_correct": true}},
    {{"text": "Option B text", "is_correct": false}},
    {{"text": "Option C text", "is_correct": false}},
    {{"text": "Option D text", "is_correct": false}}
  ],
  "explanation": "Briefly explain why the correct answer is right and why the others are wrong."
}}

DO NOT output markdown code blocks or extra text. ONLY the JSON."""

    def _parse_flashcard_json(self, response: str) -> List[Flashcard]:
        """
        Parse and validate flashcard JSON from LLM response.

        Args:
            response: Raw LLM response text

        Returns:
            List of validated Flashcard objects

        Raises:
            ValueError: If JSON parsing fails or validation fails
        """
        # Strategy 1: Try to extract from markdown code block
        json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_block_match:
            try:
                data = json.loads(json_block_match.group(1))
                if 'cards' in data:
                    flashcards = [Flashcard(**card) for card in data['cards']]
                    print(f"✓ Parsed {len(flashcards)} flashcards from markdown block")
                    return flashcards
            except Exception as e:
                print(f"⚠ Failed to parse from markdown block: {e}")

        # Strategy 2: Try to find JSON object anywhere in response
        json_match = re.search(r'\{[^{}]*"cards"[^{}]*\[.*?\]\s*\}', response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                if 'cards' in data:
                    flashcards = [Flashcard(**card) for card in data['cards']]
                    print(f"✓ Parsed {len(flashcards)} flashcards from JSON object")
                    return flashcards
            except Exception as e:
                print(f"⚠ Failed to parse from JSON object: {e}")

        # Strategy 3: Try to find just the outermost JSON object
        cleaned = response.strip()
        # Remove markdown code blocks
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)

        try:
            data = json.loads(cleaned)
            if isinstance(data, dict) and 'cards' in data:
                flashcards = [Flashcard(**card) for card in data['cards']]
                print(f"✓ Parsed {len(flashcards)} flashcards from cleaned response")
                return flashcards
        except Exception as e:
            print(f"⚠ Failed to parse cleaned response: {e}")

        # Strategy 4: Auto-complete truncated JSON (NEW)
        try:
            cleaned = response.strip()
            # Remove markdown code blocks
            cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)

            # Try to auto-complete if it looks like truncated JSON
            if cleaned.startswith('{') and '"cards"' in cleaned:
                # Count opening and closing brackets
                open_braces = cleaned.count('{')
                close_braces = cleaned.count('}')
                open_brackets = cleaned.count('[')
                close_brackets = cleaned.count(']')

                # Add missing closing brackets/braces
                if open_braces > close_braces or open_brackets > close_brackets:
                    print(f"⚠ Detected truncated JSON, attempting auto-completion...")
                    print(f"   Open/Close: {{ {open_braces}/{close_braces} }} [ {open_brackets}/{close_brackets} ]")

                    # Remove incomplete last card if present
                    # Find the last complete card entry
                    last_complete = cleaned.rfind('},')
                    if last_complete != -1:
                        # Truncate at last complete card and add proper closing
                        completed = cleaned[:last_complete+1] + ']}'
                    else:
                        # No complete cards, try to close what we have
                        completed = cleaned
                        # Add missing closing brackets
                        while open_brackets > close_brackets:
                            completed += ']'
                            close_brackets += 1
                        while open_braces > close_braces:
                            completed += '}'
                            close_braces += 1

                    # Try parsing the completed JSON
                    data = json.loads(completed)
                    if isinstance(data, dict) and 'cards' in data and len(data['cards']) > 0:
                        flashcards = [Flashcard(**card) for card in data['cards']]
                        print(f"✓ Auto-completion successful! Recovered {len(flashcards)} flashcards")
                        return flashcards
        except Exception as e:
            print(f"⚠ Auto-completion failed: {e}")

        # Strategy 5: Log failure and provide debug info
        print(f"⚠ All parsing strategies failed")
        print(f"   Response length: {len(response)} chars")
        print(f"   First 300 chars: {response[:300]}")
        print(f"   Last 100 chars: {response[-100:]}")
        raise ValueError(f"Failed to parse LLM response as flashcards: No valid JSON found in response")

    def _parse_quiz_json(self, response: str) -> QuizQuestion:
        """
        Parse and validate quiz JSON from LLM response.

        Args:
            response: Raw LLM response text

        Returns:
            Validated QuizQuestion object

        Raises:
            ValueError: If JSON parsing fails or validation fails
        """
        try:
            # Strip markdown code blocks if present
            response = re.sub(r'^```json\s*|\s*```$', '', response, flags=re.MULTILINE)

            # Extract JSON from response (LLM may add extra text)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")

            json_str = json_match.group(0)
            data = json.loads(json_str)

            # Validate required keys
            required_keys = ['question', 'options', 'explanation']
            for key in required_keys:
                if key not in data:
                    raise ValueError(f"Missing required key '{key}' in JSON")

            # Convert options to Pydantic models
            options = [MCQOption(**opt) for opt in data['options']]

            # Create QuizQuestion (validator will check exactly 1 correct answer)
            quiz_question = QuizQuestion(
                question=data['question'],
                options=options,
                explanation=data['explanation']
            )

            return quiz_question

        except Exception as e:
            print(f"⚠ Failed to parse quiz JSON: {e}")
            print(f"   Raw response: {response[:200]}...")
            raise ValueError(f"Failed to parse LLM response as quiz: {str(e)}")
