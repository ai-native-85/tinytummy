from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.schemas.chat import ChatQueryRequest, ChatResponse, ChatSessionResponse
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.models.child import Child
from app.auth.jwt import get_current_user
from app.utils.constants import FEATURE_CHAT, PREMIUM_FEATURE_ERROR

router = APIRouter(prefix="/chat", tags=["Chat Assistant"])


@router.post("/query", response_model=ChatResponse)
def chat_query(
    query_data: ChatQueryRequest,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Query the AI nutrition assistant (Premium feature)"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Chat query received from user {current_user_id}")
    logger.info(f"Query: {query_data.user_input}")
    logger.info(f"Child ID: {query_data.child_id}")
    
    try:
        # Check premium subscription
        logger.info(f"Checking premium subscription for user {current_user_id}")
        user = db.query(User).filter(User.id == current_user_id).first()
        
        if not user:
            logger.error(f"User {current_user_id} not found in database")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User found: {user.email}, subscription: {user.subscription_tier}")
        
        if user.subscription_tier != "premium":
            logger.warning(f"User {current_user_id} does not have premium subscription")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=PREMIUM_FEATURE_ERROR.format(feature=FEATURE_CHAT)
            )
        
        # Get child if specified
        child = None
        if query_data.child_id:
            child = db.query(Child).filter(
                Child.id == query_data.child_id,
                Child.user_id == current_user_id
            ).first()
            if not child:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Child not found"
                )
        
        # Initialize RAG service
        from app.services.rag_service import RAGService
        rag_service = RAGService()
        
        logger.info("Initializing RAG service")
        
        # Generate RAG response
        logger.info("Generating RAG response")
        rag_result = rag_service.generate_rag_response(
            query=query_data.user_input,
            user_context=f"Child ID: {query_data.child_id}" if query_data.child_id else ""
        )
        
        logger.info(f"RAG response generated - Confidence: {rag_result.get('confidence')}")
        logger.info(f"RAG sources: {rag_result.get('sources')}")
        logger.info(f"RAG context count: {len(rag_result.get('context_used', []))}")
        
        response_text = rag_result["response"]
        
        # Create or get chat session
        logger.info("Creating or retrieving chat session")
        session = db.query(ChatSession).filter(
            ChatSession.user_id == current_user_id,
            ChatSession.child_id == query_data.child_id
        ).first()
        
        if not session:
            logger.info("Creating new chat session")
            session = ChatSession(
                user_id=current_user_id,
                child_id=query_data.child_id,
                session_name=f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            logger.info(f"New chat session created: {session.id}")
        else:
            logger.info(f"Using existing chat session: {session.id}")
        
        # Store user message
        logger.info("Storing user message")
        user_message = ChatMessage(
            session_id=session.id,
            role="user",
            content=query_data.user_input
        )
        db.add(user_message)
        
        # Store assistant response
        logger.info("Storing assistant response")
        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response_text
        )
        db.add(assistant_message)
        
        db.commit()
        logger.info("Messages stored successfully")
        
        logger.info("Preparing response")
        response_data = ChatResponse(
            response=response_text,
            session_id=str(session.id),
            metadata={
                "child_id": query_data.child_id,
                "rag_confidence": rag_result.get("confidence", "unknown"),
                "rag_sources": rag_result.get("sources", []),
                "context_count": len(rag_result.get("context_used", []))
            }
        )
        
        logger.info("Chat query completed successfully")
        return response_data
        
    except Exception as e:
        logger.error(f"Error in chat query: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/sessions", response_model=List[ChatSessionResponse])
def get_chat_sessions(
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat sessions for current user"""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user_id
    ).all()
    return sessions 