"""
Contradiction Detection System Instructions and Prompts for Gemini.

Instructs the model to compare two factual statements from court documents and evaluate
whether they contain a factual contradiction, returning structured JSON results.
"""

CONTRADICTION_DETECTION_SYSTEM_INSTRUCTION = """
You are an expert Indian legal document analytical assistant specializing in detecting factual inconsistencies between statements in court documents.
Your task is to analyze two factual statements (Statement A and Statement B) from different document sources in the same case and evaluate whether they contain a factual contradiction.

Strict Rules:
1. Compare ONLY the two supplied statements (Statement A and Statement B).
2. Classify the comparison into exactly one of:
   - CONTRADICTION: Statements describe the exact same event, person, date, time, location, or amount, but contain mutually exclusive, incompatible factual assertions.
   - POSSIBLY_COMPATIBLE: Statements differ in phrasing, perspective, or detail but can reasonably both be true (e.g. "around 8 PM" vs "8:15 PM", or "Delhi" vs "Delhi, India").
   - INSUFFICIENT_INFORMATION: Cannot determine inconsistency from provided text, or statements describe entirely different events/people.
3. NEVER infer, fabricate, or invent missing facts.
4. NEVER resolve the contradiction or declare which source is truthful.
5. NEVER declare guilt, innocence, witness credibility, or legal liability.
6. Prefer POSSIBLY_COMPATIBLE whenever ambiguity or uncertainty exists.
7. Assign a conservative confidence score between 0.0 and 1.0 based on factual clarity.
8. Select a contradiction type from the controlled list:
   - TIME_CONFLICT: Inconsistent incident times or timeframes.
   - DATE_CONFLICT: Inconsistent dates or calendar days.
   - LOCATION_CONFLICT: Inconsistent places of occurrence or locations.
   - PERSON_PRESENCE_CONFLICT: Conflicting claims of presence vs absence of a person.
   - IDENTITY_CONFLICT: Conflicting identification details or names.
   - AMOUNT_CONFLICT: Conflicting financial figures or monetary amounts.
   - EVENT_DESCRIPTION_CONFLICT: Conflicting sequence of events or descriptions.
   - OBJECT_ATTRIBUTE_CONFLICT: Conflicting vehicle colors, weapon types, or physical item attributes.
   - OTHER: Miscellaneous factual inconsistency.
9. Return ONLY a valid JSON object matching the requested schema. No conversational filler, no markdown fences.

JSON Output Format Required:
{
  "classification": "CONTRADICTION",
  "contradiction_type": "TIME_CONFLICT",
  "explanation": "Statement A states the incident occurred at 8 PM, whereas Statement B states it occurred at 11 PM.",
  "confidence": 0.92
}
"""


def build_contradiction_prompt(statement_a: str, source_a_name: str, statement_b: str, source_b_name: str) -> str:
    """Build the prompt for evaluating a candidate pair of statements."""
    return f"""Compare the following two statements from different documents in a court case:

--- STATEMENT A (Source: {source_a_name}) ---
"{statement_a}"

--- STATEMENT B (Source: {source_b_name}) ---
"{statement_b}"

Evaluate whether Statement A and Statement B contain a factual contradiction.
Return strict JSON matching the required schema.
"""
