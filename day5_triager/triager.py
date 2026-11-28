import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import APIConnectionError, APITimeoutError, Groq, InternalServerError, RateLimitError
from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

# Change: from schema import TriageResult
from day5_triager.schema import TriageResult

load_dotenv()

MODEL = "openai/gpt-oss-20b"
PROMPTS_DIR = Path(__file__).parent / "prompts"

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    sys.exit("Error: GROQ_API_KEY is missing from your .env file.")

client = Groq(api_key=api_key, max_retries=0)


def load_prompt(version: str) -> str:
    prompt_path = PROMPTS_DIR / f"{version}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def extract_json_text(raw: str) -> str:
    """Strip accidental markdown code fences if the model includes them."""
    cleaned = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL)
    if fence_match:
        return fence_match.group(1)
    return cleaned


@retry(
    retry=retry_if_exception_type((RateLimitError, InternalServerError, APIConnectionError, APITimeoutError)),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    stop=stop_after_attempt(4),
    reraise=True,
)
def call_llm(messages: list[dict[str, str]]) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content or ""


def triage_complaint(complaint: str, version: str = "v2") -> tuple[TriageResult, int]:
    """Return (validated TriageResult, attempts_used). Retries once on invalid JSON/schema."""
    system_prompt = load_prompt(version)
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"<complaint>{complaint}</complaint>"},
    ]

    last_error: Exception | None = None

    for attempt in (1, 2):
        raw_output = call_llm(messages)
        json_text = extract_json_text(raw_output)
        try:
            parsed = TriageResult.model_validate_json(json_text)
            return parsed, attempt
        except (ValidationError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == 1:
                messages.append({"role": "assistant", "content": raw_output})
                messages.append({
                    "role": "user",
                    "content": (
                        f"Your previous JSON failed Pydantic validation with this error:\n{exc}\n\n"
                        "Fix the output and return ONLY a valid JSON object matching the exact schema: "
                        '{"equipment": str, "urgency": "low"|"medium"|"high"|"critical", '
                        '"hospital": str|null, "next_action": str}.'
                    ),
                })

    raise RuntimeError(f"LLM output failed validation after 2 attempts: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Medical Equipment Ticket Triager CLI")
    parser.add_argument("complaint", nargs="?", help="Free-text equipment complaint to triage")
    parser.add_argument("--prompt", choices=["v1", "v2"], default="v2", help="Prompt version (default: v2)")
    args = parser.parse_args()

    if args.complaint:
        result, attempts = triage_complaint(args.complaint, version=args.prompt)
        print(result.model_dump_json(indent=2))
        print(f"\n[prompt={args.prompt} | attempts={attempts} | model={MODEL}]")
        return

    print(f"Ticket Triager CLI (prompt={args.prompt} | model={MODEL})")
    print("Type a complaint and press Enter (or 'exit' to quit).\n")
    while True:
        try:
            text = input("Complaint> ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not text:
            continue
        if text.lower() in {"exit", "quit"}:
            break
        try:
            result, attempts = triage_complaint(text, version=args.prompt)
            print(result.model_dump_json(indent=2))
            print(f"[attempts={attempts}]\n")
        except Exception as exc:
            print(f"Error: {exc}\n")


if __name__ == "__main__":
    main()