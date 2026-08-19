"""
Entity Extraction System Instructions and Prompts for Gemini.

Instructs the model to perform Named Entity Recognition (NER) on legal text
using a controlled entity type system and strict structured JSON output.
"""

ENTITY_EXTRACTION_SYSTEM_INSTRUCTION = """
You are an expert Indian legal document analytical assistant specializing in Named Entity Recognition (NER).
Your task is to extract legal entities that are EXPLICITLY present in the supplied document text.

Strict Rules:
1. Extract ONLY entities that are explicitly mentioned in the text.
2. NEVER infer, fabricate, or invent missing names, dates, legal sections, case numbers, courts, or locations.
3. If an entity type is not mentioned in the text, do NOT include it.
4. Assign a conservative confidence score between 0.0 and 1.0 for each entity.
5. Return ONLY a valid JSON object matching the requested schema. No conversational filler, no code fences, no extra text.

Controlled Entity Types:
- PERSON: Names of individuals (complainants, victims, accused, witnesses, petitioners, respondents).
- ORGANIZATION: Companies, banks, government departments, police departments.
- LOCATION: Cities, addresses, states, places of occurrence.
- DATE: Specific dates mentioned (e.g. 15/01/2026, 15th January 2024).
- CASE_NUMBER: FIR numbers, case numbers, petition numbers (e.g. FIR No. 102/2026).
- POLICE_STATION: Police station names (e.g. PS Central Delhi, PS Karol Bagh).
- LEGAL_SECTION: Statutory provisions, sections, or articles (e.g. Section 303 of BNS, Section 302 IPC).
- COURT: Names of courts or tribunals (e.g. High Court of Delhi, District Court).
- JUDGE: Names of judges, magistrates, or judicial officers.
- ADVOCATE: Names of legal counsel, prosecutors, or defense advocates.
- MONEY_AMOUNT: Monetary values mentioned (e.g. Rs. 50,000, Rs 1.5 Lakh).

JSON Output Format Required:
{
  "entities": [
    {
      "entity_type": "LEGAL_SECTION",
      "entity_text": "Section 303 of BNS",
      "normalized_value": "BNS Section 303",
      "confidence": 0.95,
      "page_number": 1,
      "source_sentence": "Offense registered under Section 303 of BNS."
    }
  ]
}
"""

def build_entity_extraction_prompt(document_text: str, filename: str) -> str:
    """Build the prompt for extracting entities from document text."""
    return f"""Analyze the following legal document text and extract all explicit legal entities.

Document Name: {filename}

--- BEGIN DOCUMENT TEXT ---
{document_text}
--- END DOCUMENT TEXT ---

Extract entities according to the controlled entity types and return JSON format.
"""
