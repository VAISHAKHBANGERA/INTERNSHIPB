import csv
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from groq import (
    APIConnectionError,
    APITimeoutError,
    Groq,
    InternalServerError,
    RateLimitError,
)
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# --- Configuration ---
load_dotenv()
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MODEL = "openai/gpt-oss-20b"
TEMPERATURE = 0.5
MAX_TURNS = 20  # Spend-cap guard: stops runaway loops
USD_TO_INR = 93.0
LOG_FILE = Path("day4_llm/cost_log.csv")

# Verified Groq USD price per 1,000,000 tokens (input, output)
PRICING_PER_1M: dict[str, tuple[float, float]] = {
    "openai/gpt-oss-20b": (0.075, 0.30),
    "openai/gpt-oss-120b": (0.15, 0.60),
    "qwen/qwen3.8-27b": (0.80, 4.00),
}

SYSTEM_PROMPT = (
    "You are a concise, helpful engineering assistant. "
    "Give clear, accurate answers."
)

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    sys.exit("Error: GROQ_API_KEY is missing from your .env file.")

# max_retries=0 lets tenacity control retries and exponential backoff directly
client = Groq(api_key=api_key, max_retries=0)


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> tuple[float, float]:
    """Return estimated (cost_usd, cost_inr) for a single API call."""
    in_rate, out_rate = PRICING_PER_1M.get(model, (0.075, 0.30))
    cost_usd = (input_tokens / 1_000_000) * in_rate + (output_tokens / 1_000_000) * out_rate
    cost_inr = cost_usd * USD_TO_INR
    return cost_usd, cost_inr


def log_call(model: str, input_tokens: int, output_tokens: int, cost_usd: float, cost_inr: float) -> None:
    """Append one call's token counts and cost estimates to cost_log.csv."""
    file_exists = LOG_FILE.exists() and LOG_FILE.stat().st_size > 0
    with LOG_FILE.open(mode="a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                ["timestamp", "model", "input_tokens", "output_tokens", "cost_usd", "cost_inr"]
            )
        writer.writerow([
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            model,
            input_tokens,
            output_tokens,
            f"{cost_usd:.6f}",
            f"{cost_inr:.4f}",
        ])


@retry(
    retry=retry_if_exception_type(
        (RateLimitError, InternalServerError, APIConnectionError, APITimeoutError)
    ),
    wait=wait_exponential(multiplier=1, min=1, max=16),
    stop=stop_after_attempt(4),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def stream_reply(messages: list[dict[str, str]]) -> tuple[str, int, int]:
    """Stream tokens to terminal and return (full_text, input_tokens, output_tokens)."""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        stream=True,
    )

    chunks: list[str] = []
    input_tokens = 0
    output_tokens = 0

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            token = chunk.choices[0].delta.content
            print(token, end="", flush=True)
            chunks.append(token)

        # Groq reports final stream usage in chunk.x_groq.usage (or chunk.usage)
        usage = getattr(chunk, "usage", None) or getattr(
            getattr(chunk, "x_groq", None), "usage", None
        )
        if usage:
            input_tokens = getattr(usage, "prompt_tokens", 0) or 0
            output_tokens = getattr(usage, "completion_tokens", 0) or 0

    print()  # Newline after streamed reply finishes
    return "".join(chunks), input_tokens, output_tokens


def main() -> None:
    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    total_usd = 0.0
    total_inr = 0.0

    print(f"Groq CLI Chat ({MODEL} | temp={TEMPERATURE} | max_turns={MAX_TURNS})")
    print("Type 'exit' or 'quit' to stop.\n")

    for turn in range(1, MAX_TURNS + 1):
        try:
            user_input = input(f"You ({turn}/{MAX_TURNS}): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break

        messages.append({"role": "user", "content": user_input})
        print("AI: ", end="", flush=True)

        try:
            reply, in_tok, out_tok = stream_reply(messages)
        except Exception as exc:
            print(f"\n[API call failed after retries: {exc}]")
            messages.pop()  # Remove failed user turn so history stays clean
            continue

        messages.append({"role": "assistant", "content": reply})

        cost_usd, cost_inr = estimate_cost(MODEL, in_tok, out_tok)
        total_usd += cost_usd
        total_inr += cost_inr
        log_call(MODEL, in_tok, out_tok, cost_usd, cost_inr)

        print(
            f"[in: {in_tok} | out: {out_tok} | "
            f"turn: ${cost_usd:.6f} (₹{cost_inr:.4f}) | "
            f"session: ${total_usd:.6f} (₹{total_inr:.4f})]\n"
        )
    else:
        print(f"Reached MAX_TURNS ({MAX_TURNS}) spend cap. Exiting.")

    print(f"Saved call log to {LOG_FILE}")


if __name__ == "__main__":
    main()