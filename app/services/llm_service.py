"""
Service for LLM integration via Groq API (FREE).
"""
import json
import re
from typing import Dict, Any, Tuple

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.config import settings
from app.core.exceptions import LLMServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """
    Service for interacting with Groq LLM API (FREE).
    
    Handles document analysis with structured output parsing
    and automatic retry logic.
    """
    
    def __init__(self):
        """Initialize LLM service with API configuration."""
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.base_url = settings.GROQ_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def _create_analysis_prompt(self, text: str) -> str:
        """
        Create structured prompt for document analysis.
        
        Args:
            text: Extracted document text (will be truncated if too long).
            
        Returns:
            Formatted prompt string.
        """
        
        truncated_text = text[:6000] if len(text) > 6000 else text
        
        prompt = f"""Analyze the following document and provide a structured analysis.

DOCUMENT TEXT:
{truncated_text}

{"[Text truncated for length...]" if len(text) > 6000 else ""}

INSTRUCTIONS:
Provide your analysis in the following JSON format. Be precise and extract actual information from the document.

{{
    "summary": "A concise 2-3 sentence summary of the document's main content and purpose",
    "document_type": "one of: invoice, cv, resume, report, letter, contract, agreement, memo, proposal, other",
    "metadata": {{
        "date": "any date found in the document (format: YYYY-MM-DD if possible, or as written)",
        "sender": "sender name or organization if found",
        "recipient": "recipient name or organization if found",
        "amount": "any monetary amount mentioned (with currency if specified)",
        "key_entities": ["list of important names, organizations, or entities mentioned"],
        "language": "primary language of the document",
        "topics": ["main topics or subjects covered"]
    }}
}}

IMPORTANT:
- Only include metadata fields if the information is explicitly present in the document
- Use null for missing fields
- Be accurate and don't hallucinate information
- Return ONLY the JSON object, no additional text or markdown"""
        
        return prompt
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response, handling markdown code blocks.
        
        Args:
            response_text: Raw response text from LLM.
            
        Returns:
            Parsed JSON dictionary.
            
        Raises:
            LLMServiceError: If JSON parsing fails.
        """
        
        text = response_text.strip()
        
       
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        
        
        if text.startswith('```'):
           
            text = re.sub(r'```[a-z]*\n?', '', text)
        
       
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse JSON from LLM response",
                extra={"response": response_text[:500], "error": str(e)}
            )
            raise LLMServiceError(
                f"Failed to parse JSON response: {str(e)}",
                provider="Groq"
            )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPError)),
        reraise=True
    )
    async def _make_api_call(self, prompt: str) -> str:
        """
        Make API call to Groq with retry logic.
        
        Args:
            prompt: Formatted prompt for the LLM.
            
        Returns:
            Raw response text from LLM.
            
        Raises:
            LLMServiceError: If API call fails after retries.
        """
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that analyzes documents and returns structured JSON responses. Always return valid JSON without markdown formatting."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  
            "max_tokens": 2000,
            "response_format": {"type": "json_object"}  
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.debug(
                    "Making Groq API call",
                    extra={"model": self.model}
                )
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                
                content = data["choices"][0]["message"]["content"]
                
                
                if "usage" in data:
                    usage = data["usage"]
                    logger.info(
                        "Groq API call successful",
                        extra={
                            "model": self.model,
                            "prompt_tokens": usage.get("prompt_tokens"),
                            "completion_tokens": usage.get("completion_tokens"),
                            "total_tokens": usage.get("total_tokens")
                        }
                    )
                
                return content
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(
                "Groq API error",
                extra={"error": error_msg, "model": self.model},
                exc_info=True
            )
            raise LLMServiceError(error_msg, provider="Groq")
        except httpx.TimeoutException:
            logger.warning("Groq API timeout, will retry")
            raise
        except Exception as e:
            logger.error(
                "Unexpected error calling Groq API",
                extra={"error": str(e), "model": self.model},
                exc_info=True
            )
            raise LLMServiceError(str(e), provider="Groq")
    
    async def analyze_document(
        self,
        extracted_text: str
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Analyze document text using LLM and return structured results.
        
        Args:
            extracted_text: Full text extracted from document.
            
        Returns:
            Tuple of (summary, document_type, metadata_dict).
            
        Raises:
            LLMServiceError: If analysis fails.
        """
        
        prompt = self._create_analysis_prompt(extracted_text)
        
       
        response_text = await self._make_api_call(prompt)
        
        
        analysis = self._parse_json_response(response_text)
        
        
        try:
            summary = analysis.get("summary", "")
            document_type = analysis.get("document_type", "other")
            metadata = analysis.get("metadata", {})
            
            if not summary:
                raise ValueError("Summary is empty")
            
           
            metadata = {k: v for k, v in metadata.items() if v is not None}
            
            logger.info(
                "Document analysis completed",
                extra={
                    "document_type": document_type,
                    "summary_length": len(summary),
                    "metadata_keys": list(metadata.keys())
                }
            )
            
            return summary, document_type, metadata
            
        except (KeyError, ValueError) as e:
            logger.error(
                "Invalid analysis response structure",
                extra={"error": str(e), "response": analysis}
            )
            raise LLMServiceError(
                f"Invalid response structure: {str(e)}",
                provider="Groq"
            )