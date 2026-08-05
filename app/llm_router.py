import os
import asyncio
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from app.cost_tracker import log_llm_cost

load_dotenv()

def get_llm_with_fallback():
    groq_key = os.getenv("GROQ_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    models = []
    if groq_key and groq_key != "your_groq_api_key_here":
        models.append((
            "Groq",
            "llama-3.1-8b-instant",
            ChatGroq(
                model="llama-3.1-8b-instant",
                api_key=groq_key,
                temperature=0.1,
                request_timeout=15.0
            )
        ))
        
    if openrouter_key and openrouter_key != "your_openrouter_api_key_here":
        models.append((
            "OpenRouter",
            "meta-llama/llama-3.1-8b-instruct:free",
            ChatOpenAI(
                model_name="meta-llama/llama-3.1-8b-instruct:free",
                openai_api_key=openrouter_key,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.1,
                request_timeout=15.0
            )
        ))

    return models

async def invoke_llm_with_retry_and_fallback(prompt: str, incident_id: str = "INC-UNKNOWN", max_retries: int = 2) -> str:
    models = get_llm_with_fallback()
    
    if not models:
        return "ROOT CAUSE: Unable to contact LLM service. No valid API keys found.\nCONFIDENCE: 0.0\nRECOMMENDED ACTION: Verify API keys in .env file."

    for provider_name, model_name, model in models:
        for attempt in range(1, max_retries + 1):
            try:
                start_time = time.time()
                response = await asyncio.wait_for(
                    asyncio.to_thread(model.invoke, prompt),
                    timeout=15.0
                )
                latency_ms = (time.time() - start_time) * 1000
                
                # Extract Token Usage Metadata
                usage = getattr(response, "usage_metadata", {}) or {}
                input_tokens = usage.get("input_tokens", len(prompt) // 4)
                output_tokens = usage.get("output_tokens", len(response.content) // 4)
                
                # Log Token Usage & Estimated Cost
                log_llm_cost(
                    incident_id=incident_id,
                    provider=provider_name,
                    model_name=model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms
                )
                
                return response.content
            except asyncio.TimeoutError:
                print(f"⚠️ [{provider_name}] Attempt {attempt} Timed out (>15s). Retry after backoff...")
            except Exception as e:
                err_str = str(e)
                print(f"⚠️ [{provider_name}] Attempt {attempt} Error: {err_str[:100]}...")
                if "401" in err_str or "Invalid API Key" in err_str:
                    break
                    
            await asyncio.sleep(attempt * 1.5)

        print(f"❌ Provider [{provider_name}] Failed completely. Switching to Fallback Provider...")

    return (
        "ROOT CAUSE: RCA could not be completed automatically because AI analysis services are temporarily unavailable.\n"
        "CONFIDENCE: 0.0\n"
        "RECOMMENDED ACTION: Manually inspect collected logs and system_telemetry.db metrics."
    )