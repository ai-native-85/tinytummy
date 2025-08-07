"""Chat service for managing chat sessions and messages"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import ChatSessionCreate, ChatMessageCreate


class ChatService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, session_data: ChatSessionCreate, user_id: str) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(
            user_id=user_id,
            child_id=session_data.child_id,
            session_name=session_data.session_name or f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_user_sessions(self, user_id: str) -> List[ChatSession]:
        """Get all chat sessions for a user"""
        return self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.created_at.desc()).all()

    def get_session_messages(self, session_id: str, user_id: str) -> List[ChatMessage]:
        """Get all messages for a chat session"""
        # Verify session ownership
        session = self.db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()

    def add_message(self, message_data: ChatMessageCreate, session_id: str, user_id: str) -> ChatMessage:
        """Add a message to a chat session"""
        # Verify session ownership
        session = self.db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        message = ChatMessage(
            session_id=session_id,
            role=message_data.role,
            content=message_data.content
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session and all its messages"""
        session = self.db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Delete all messages first
        self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).delete()
        
        # Delete session
        self.db.delete(session)
        self.db.commit()
        return True 