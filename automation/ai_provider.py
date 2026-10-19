"""Provider boundary: callers receive plain text or a sanitized failure."""
import os


def generate_text(prompt):
    if os.getenv('AI_PROVIDER', 'gemini') != 'gemini':
        raise ValueError('Unsupported AI_PROVIDER; implement it in ai_provider.py')
    key = os.getenv('GEMINI_API_KEY', '').strip()
    if not key:
        raise ValueError('Set GEMINI_API_KEY in the local .env before API testing')
    from google import genai
    try:
        with genai.Client(api_key=key, http_options={'timeout': 60000}) as client:
            response = client.models.generate_content(
                model=os.getenv('GEMINI_MODEL', 'gemini-flash-latest'),
                contents=prompt,
                config={'temperature': 0.2, 'max_output_tokens': 4096,
                        'response_mime_type': 'application/json'},
            )
            result = response.text
        if not result:
            raise RuntimeError('Empty response')
        # Never expose a credential even if it is accidentally echoed.
        return result.replace(key, '[REDACTED]')
    except Exception:
        raise RuntimeError('Gemini request failed; check model, connectivity, quota and key') from None
