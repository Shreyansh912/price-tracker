from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import json
from groq import Groq
import os

from app.database.session import SessionLocal
from app.agent.custom_agent import agent_registry
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.conversation import Conversation, Message

router = APIRouter(prefix="/api/agent", tags=["Pulse AI Agent"])
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None

@router.post("/chat")
def chat_with_agent(
    payload: ChatRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    user_msg = payload.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # 1. Conversation session handling
    conversation = db.query(Conversation).filter(Conversation.user_id == current_user.id).order_by(Conversation.created_at.desc()).first()
    if not conversation:
        conversation = Conversation(user_id=current_user.id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    db.add(Message(conversation_id=conversation.id, role="user", content=user_msg))
    db.commit()

    try:
        # 2. Call LLM with tool declarations
        messages = [
            {"role": "system", "content": f"You are Pulse AI, a helpful shopping assistant for {current_user.name}. Use tools when users ask about tracked items, searching, history, or pasting URLs."},
            {"role": "user", "content": user_msg}
        ]

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=agent_registry.openai_tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_used = None
        tool_data = None
        response_text = response_message.content or "I have processed your request."

        # 3. Handle LLM Tool Execution Request
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            tool_used = tool_call.function.name
            
            # Safely handle argument parsing if arguments are missing or malformed
            try:
                tool_args = json.loads(tool_call.function.arguments or "{}")
            except Exception:
                tool_args = {}
            
            if tool_used in agent_registry.tools:
                tool_func = agent_registry.tools[tool_used]["function"]
                
                # Inject required context/parameters safely based on signature requirements
                if tool_used == "get_tracked_products":
                    raw_result = tool_func(db=db, user_id=current_user.id)
                elif tool_used == "track_product":
                    raw_result = tool_func(db=db, user_id=current_user.id, **tool_args)
                elif tool_used == "search_products":
                    raw_result = tool_func(db=db, **tool_args)
                elif tool_used == "get_price_history":
                    raw_result = tool_func(db=db, **tool_args)
                else:
                    raw_result = tool_func(db=db, **tool_args)

                try:
                    tool_data = json.loads(raw_result)
                except Exception:
                    tool_data = {"result": raw_result}

                response_text = f"Successfully executed {tool_used} based on your request."

        db.add(Message(conversation_id=conversation.id, role="assistant", content=response_text))
        db.commit()

        return {
            "status": "success",
            "conversation_id": conversation.id,
            "tool_used": tool_used,
            "response": response_text,
            "data": tool_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))