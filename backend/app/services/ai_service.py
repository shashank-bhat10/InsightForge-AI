from typing import Optional

from google import genai

from app.config.settings import settings

from app.services.analytics_service import (
    get_dataset_summary,
    get_dataset_statistics,
    get_dataset_insights,
    get_grouped_analysis
)

from app.services.dataset_service import get_dataset_preview


client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)


def generate_ai_response(
    prompt: str,
    conversation_history: Optional[list] = None
):
    try:
        history_context = ""

        if conversation_history:
            history_lines = []

            for message in conversation_history:
                history_lines.append(
                    f"User: {message['prompt']}"
                )
                history_lines.append(
                    f"InsightForge AI: {message['response']}"
                )

            history_context = f"""
PREVIOUS CONVERSATION:
{chr(10).join(history_lines)}

Use this previous conversation to understand references such as:
"that", "this", "it", "the above", "previous result", etc.
"""

        context = f"""
You are InsightForge AI, an AI data analysis assistant.

{history_context}

CURRENT USER QUESTION:
{prompt}

Answer the current question clearly and naturally.

If the user refers to something from the previous conversation,
use the previous conversation to understand what they mean.

Do not invent information.
"""

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=context
        )

        return {
            "success": True,
            "response": response.text
        }

    except Exception as e:
        return {
            "success": False,
            "response": str(e)
        }


def generate_dataset_ai_response(
    prompt: str,
    file_path: str,
    conversation_history: Optional[list] = None
):
    try:
        summary = get_dataset_summary(file_path)

        statistics = get_dataset_statistics(file_path)

        insights = get_dataset_insights(file_path)

        grouped_analysis = get_grouped_analysis(file_path)

        preview = get_dataset_preview(
            file_path,
            rows=20
        )

        history_context = ""

        if conversation_history:
            history_lines = []

            for message in conversation_history:
                history_lines.append(
                    f"User: {message['prompt']}"
                )
                history_lines.append(
                    f"InsightForge AI: {message['response']}"
                )

            history_context = f"""
PREVIOUS CONVERSATION:
{chr(10).join(history_lines)}

Use the previous conversation to understand follow-up
questions and references such as:
"that", "this", "it", "the above", "previous result", etc.
"""

        dataset_context = f"""
You are InsightForge AI, an AI data analysis assistant.

The user has uploaded a dataset and is asking questions about it.

DATASET SUMMARY:
{summary}

NUMERIC STATISTICS:
{statistics}

DATASET INSIGHTS:
{insights}

GROUPED ANALYSIS:
{grouped_analysis}

FIRST 20 ROWS:
{preview}

{history_context}

CURRENT USER QUESTION:
{prompt}

INSTRUCTIONS:

1. Answer the user's current question using the dataset information
   provided above.

2. Use GROUPED ANALYSIS when the question asks about:

   - highest or lowest sales by category
   - average values by category
   - total values by category
   - comparisons between categories
   - best or worst performing groups
   - relationships between categorical and numeric columns

3. Use NUMERIC STATISTICS for general statistical questions.

4. Use DATASET SUMMARY for questions about:

   - number of rows
   - number of columns
   - column names
   - missing values
   - data types

5. Use FIRST 20 ROWS only when the question specifically requires
   looking at individual records or examples.

6. Do NOT calculate results from only the first 20 rows when
   GROUPED ANALYSIS contains the required information.

7. If the user asks a follow-up question referring to a previous
   answer, use PREVIOUS CONVERSATION to understand the reference.

8. Do not invent values that are not present in the dataset.

9. If the dataset does not contain enough information to answer
   the question, clearly say so.

10. Give a clear and concise answer.

11. When useful, include the relevant value and category in the answer.
"""

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=dataset_context
        )

        return {
            "success": True,
            "response": response.text
        }

    except Exception as e:
        return {
            "success": False,
            "response": str(e)
        }