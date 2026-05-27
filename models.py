import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from connection import Base

class ConversationModel(Base):
    __tablename__ = "conversations"

    conversation_uuid = Column(String(36), primary_key=True, index=True)
    conversation_title = Column(String(255), nullable=False)
    created_at_timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Kétirányú reláció kaszkádolt törléssel (biztonságos takarítás)
    messages = relationship(
        "MessageModel", 
        back_populates="conversation", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )

class MessageModel(Base):
    __tablename__ = "messages"

    message_uuid = Column(String(36), primary_key=True, index=True)
    conversation_uuid = Column(String(36), ForeignKey("conversations.conversation_uuid", ondelete="CASCADE"), nullable=False)
    sender_role = Column(String(20), nullable=False)  # 'user', 'model', 'system'
    message_content = Column(Text, nullable=False)
    
    # Token elszámolási mérőszámok
    prompt_token_count = Column(Integer, default=0)
    response_token_count = Column(Integer, default=0)
    total_token_count = Column(Integer, default=0)
    created_at_timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("ConversationModel", back_populates="messages")