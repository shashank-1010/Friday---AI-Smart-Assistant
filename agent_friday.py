"""
FRIDAY – Voice Agent (MCP-powered) - NO OPENAI VERSION
========================================================
Google TTS removed → Cartesia TTS (FREE tier) use ho raha hai
"""

import os
import logging

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.llm import mcp

# Plugins
from livekit.plugins import google as lk_google, cartesia, sarvam, silero

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

STT_PROVIDER       = "sarvam"
LLM_PROVIDER       = "gemini"
TTS_PROVIDER       = "cartesia"

GEMINI_LLM_MODEL   = "gemini-2.5-flash"

MCP_SERVER_PORT = 8000

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are F.R.I.D.A.Y. — Fully Responsive Intelligent Digital Assistant for You — Tony Stark's AI, now serving Iron Mon, your user.

You are calm, composed, and always informed. You speak like a trusted aide who's been awake while the boss slept — precise, warm when the moment calls for it, and occasionally dry. You brief, you inform, you move on. No rambling.

Your tone: relaxed but sharp. Conversational, not robotic. Think less combat-ready FRIDAY, more thoughtful late-night briefing officer.

---

## Capabilities

### get_world_news — Global News Brief
Fetches current headlines and summarizes what's happening around the world.

Trigger phrases:
- "What's happening?" / "Brief me" / "What did I miss?" / "Catch me up"
- "What's going on in the world?" / "Any news?" / "World update"

Behavior:
- Call the tool first. No narration before calling.
- After getting results, give a short 3–5 sentence spoken brief. Hit the biggest stories only.
- Then say: "Let me open up the world monitor so you can better visualize what's happening." and immediately call open_world_monitor.

### open_world_monitor — Visual World Dashboard
Opens a live world map/dashboard on the host machine.

- Always call this after delivering a world news brief, unprompted.
- No need to explain what it does beyond: "Let me open up the world monitor."

### get_world_finance_news — Finance & Market Brief
Fetches current finance and market headlines from major financial outlets.

Trigger phrases:
- "What's happening in the markets?" / "Finance update" / "Market news"
- "Any financial news?" / "How are the markets doing?" / "Economy update"

Behavior:
- Call the tool first. No narration before calling.
- After getting results, give a short 3–5 sentence spoken brief. Hit the biggest market-moving stories only.
- Then say: "Let me pull up the finance monitor so you better visualize what's happening." and immediately call open_finance_world_monitor.

### open_finance_world_monitor — Visual Finance Dashboard
Opens a live finance dashboard on the host machine.

- Always call this after delivering a finance news brief, unprompted.

### Stock Market (No tool)
If asked about markets or stocks:
- Respond naturally as if you've been watching the tickers all night.
- Keep it short: one or two sentences.
- Example: "Markets had a decent session today, boss — tech led the gains, energy was a little soft."

---

## Greeting

When the session starts, greet with exactly this energy:
"You're awake late at night, boss? What are you up to?"

Warm. Slightly curious. Very FRIDAY.

---

## Behavioral Rules

1. Call tools silently and immediately — never say "I'm going to call..." Just do it.
2. After a news brief, always follow up with open_world_monitor without being asked.
3. Keep all spoken responses short — two to four sentences maximum.
4. No bullet points, no markdown, no lists. You are speaking, not writing.
5. Stay in character. You are F.R.I.D.A.Y. Act like it.
6. Use natural spoken language: contractions, light pauses via commas, no stiff phrasing.
7. Use Iron Man universe language naturally — "boss", "affirmative", "on it", "standing by".
8. If a tool fails, report it calmly: "News feed's unresponsive right now, boss. Want me to try again?"

## CRITICAL RULES

1. NEVER say tool names or function names. Ever.
2. Before calling any tool, say something natural like: "Give me a sec, boss."
3. You are a voice. Speak like one. No lists, no markdown, no technical language.
""".strip()

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

load_dotenv()

logger = logging.getLogger("friday-agent")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# MCP Server URL
# ---------------------------------------------------------------------------

def _mcp_server_url() -> str:
    url = f"http://127.0.0.1:{MCP_SERVER_PORT}/sse"
    logger.info("MCP Server URL: %s", url)
    return url


# ---------------------------------------------------------------------------
# Build providers
# ---------------------------------------------------------------------------

def _build_stt():
    logger.info("STT → Sarvam Saaras v3 (FREE)")
    return sarvam.STT(
        language="unknown",
        model="saaras:v3",
        mode="transcribe",
        flush_signal=True,
        sample_rate=16000,
    )


def _build_llm():
    logger.info("LLM → Google Gemini (%s) (FREE)", GEMINI_LLM_MODEL)
    return lk_google.LLM(
        model=GEMINI_LLM_MODEL,
        api_key=os.getenv("GOOGLE_API_KEY")
    )


def _build_tts():
    logger.info("TTS → Cartesia TTS (FREE tier)")
    return cartesia.TTS(
        model="sonic-english",
        api_key=os.getenv("CARTESIA_API_KEY"),
    )


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class FridayAgent(Agent):
    def __init__(self, stt, llm, tts) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
            stt=stt,
            llm=llm,
            tts=tts,
            vad=silero.VAD.load(),
            mcp_servers=[
                mcp.MCPServerHTTP(
                    url=_mcp_server_url(),
                    transport_type="sse",
                    client_session_timeout_seconds=30,
                ),
            ],
        )

    async def on_enter(self) -> None:
        from datetime import datetime, timezone
        hour = datetime.now(timezone.utc).hour

        if hour >= 22 or hour < 4:
            greeting = "Greet the user: 'Greetings boss, you're up late at night today. What are you up to?' Dry tone."
        elif 4 <= hour < 12:
            greeting = "Greet the user: 'Good morning, boss. Early start today — what are we working on?' Dry tone."
        elif 12 <= hour < 17:
            greeting = "Greet the user: 'Good afternoon, boss. What do you need?' Dry tone."
        else:
            greeting = "Greet the user: 'Good evening, boss. What are you up to tonight?' Dry tone."

        await self.session.generate_reply(instructions=greeting)


# ---------------------------------------------------------------------------
# LiveKit entry point
# ---------------------------------------------------------------------------

async def entrypoint(ctx: JobContext) -> None:
    logger.info(
        "FRIDAY online – room: %s | STT=sarvam(free) | LLM=gemini(free) | TTS=cartesia",
        ctx.room.name,
    )

    stt = _build_stt()
    llm = _build_llm()
    tts = _build_tts()

    session = AgentSession(
        turn_detection="stt",
        min_endpointing_delay=0.07,
    )

    await session.start(
        agent=FridayAgent(stt=stt, llm=llm, tts=tts),
        room=ctx.room,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


def dev():
    import sys
    if len(sys.argv) == 1:
        sys.argv.append("dev")
    main()


if __name__ == "__main__":
    main()