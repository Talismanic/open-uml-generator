import re
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def generate_filename_from_requirement(requirement: str, model_client=None) -> str:
    """
    Uses LLM to generate a short, filename-safe name based on the requirement.
    """
    if model_client is None:
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

    system_message = {
        "role": "system",
        "content": (
            "You're a helpful assistant. Create a short, lowercase, hyphen-separated name "
            "suitable as a file name based on the given software requirement. "
            "Avoid special characters, spaces, or punctuation. Example output: library-system"
        )
    }

    user_message = {
        "role": "user",
        "content": requirement
    }

    result = await model_client.create(messages=[system_message, user_message])

    # ✅ Fix: handle both string and dict responses
    if isinstance(result, dict):
        filename = result["choices"][0]["message"]["content"]
    else:
        filename = result.content

    filename = filename.strip().lower()
    filename = re.sub(r'[^a-z0-9\-]', '', filename)  # Clean for file safety
    return filename
