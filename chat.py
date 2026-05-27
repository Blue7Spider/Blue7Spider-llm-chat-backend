import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from connection import get_database_session
from models import MessageModel
from moderation import ContentModerationService
from llm_client import ExternalLanguageModelClient
from self_correction import OutputSelfCorrectionService
from app import settings

router = APIRouter(prefix="/chat", tags=["Chat Műveletek"])

# --- PYDANTIC VALIDÁCIÓS MODELLEK ---
class GenerationConfigSchema(BaseModel):
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    max_output_tokens: int = Field(default=1024, ge=1, le=4096)

class ChatRequestSchema(BaseModel):
    conversation_uuid: str = Field(..., min_length=36, max_length=36)
    user_prompt: str = Field(..., min_length=1, max_length=4000)
    config: GenerationConfigSchema = Field(default_factory=GenerationConfigSchema)

# --- ASZINKRON HÁTTÉRFELADAT A TOKENELSZÁMOLÁSHOZ ---
async def async_persist_message_logs(
    conversation_uuid: str, 
    user_text: str, 
    bot_text: str,
    db_session_factory
):
    async with db_session_factory() as session:
        # User üzenet mentése
        user_msg = MessageModel(
            message_uuid=str(uuid.uuid4()),
            conversation_uuid=conversation_uuid,
            sender_role="user",
            message_content=user_text,
            prompt_token_count=len(user_text) // 4, # Egyszerűsített token becslés
            total_token_count=len(user_text) // 4
        )
        # Model üzenet mentése
        model_msg = MessageModel(
            message_uuid=str(uuid.uuid4()),
            conversation_uuid=conversation_uuid,
            sender_role="model",
            message_content=bot_text,
            response_token_count=len(bot_text) // 4,
            total_token_count=len(bot_text) // 4
        )
        session.add_all([user_msg, model_msg])
        await session.commit()

# --- CHAT STREAMING VÉGPONT ---
@router.post("/stream")
async def process_chat_message_stream(
    payload: ChatRequestSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session)
):
    # 1. Bemenet moderáció (Prompt-Injection védelem)
    moderator = ContentModerationService()
    if not await moderator.is_prompt_safe(payload.user_prompt):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="A megadott prompt biztonsági kockázatot jelent."
        )

    # 2. Kontextus betöltése adatbázisból (Utolsó N üzenet - Elkerüli a Context Overflow támadást)
    query = select(MessageModel).where(
        MessageModel.conversation_uuid == payload.conversation_uuid
    ).order_by(MessageModel.created_at_timestamp.desc()).limit(settings.max_context_message_limit)
    
    result = await db.execute(query)
    db_messages = result.scalars().all()
    
    context_history = []
    for msg in reversed(db_messages):
        context_history.append({"role": msg.sender_role, "content": msg.message_content})

    # 3. Stream generátor függvény
    async def sse_payload_generator():
        llm_client = ExternalLanguageModelClient()
        system_instruction = "Te egy biztonságos, segítőkész AI asszisztens vagy."
        
        # Ideiglenes puffer a válasz teljes validációjához
        full_captured_response = []
        
        # Új prompt hozzáadása a futó kontextushoz
        context_history.append({"role": "user", "content": payload.user_prompt})
        
        async for token in llm_client.stream_chat_completion(
            system_instruction, context_history, payload.config.model_dump()
        ):
            full_captured_response.append(token)
            yield f"data: {json.dumps({'chunk': token})}\n\n"

        # 4. Önjavítás és Szanitálás a generálás végén
        complete_text = "".join(full_captured_response)
        validated_text = await OutputSelfCorrectionService.sanitize_and_validate_output(complete_text)
        
        # 5. Aszinkron perzisztencia háttérfolyamatként (Nem blokkolja a klienst)
        from connection import async_session_factory
        background_tasks.add_task(
            async_persist_message_logs,
            payload.conversation_uuid,
            payload.user_prompt,
            validated_text,
            async_session_factory
        )

    return StreamingResponse(sse_payload_generator(), media_type="text/event-stream")