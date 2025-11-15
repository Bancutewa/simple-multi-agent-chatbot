"""
Intent handler cho general chat
"""
from typing import Dict, Any, Optional
from agno.agent import Agent
from .base_intent import BaseIntent


class GeneralChatIntent(BaseIntent):
    """Intent handler cho trò chuyện thông thường"""

    @property
    def intent_name(self) -> str:
        return "general_chat"

    @property
    def system_prompt(self) -> str:
        return ("Bạn là một chatbot AI thông minh, thân thiện và hữu ích.\n"
                "Luôn trả lời bằng tiếng Việt trừ khi người dùng yêu cầu khác.\n"
                "Trả lời một cách tự nhiên, hấp dẫn và mang tính xây dựng.")

    def get_response(self, data: Dict[str, Any], context: Optional[str] = None) -> str:
        """
        Xử lý response cho general chat

        Args:
            data: Chứa key "message" với nội dung tin nhắn
            context: Lịch sử hội thoại (optional)

        Returns:
            Response từ agent
        """
        message_content = data.get("message", "")

        if not context:
            context = "Không có lịch sử hội thoại."

        conversation_prompt = f"""
        Lịch sử hội thoại (ngữ cảnh):
        {context}

        Câu hỏi mới của người dùng: {message_content}

        Hãy trả lời câu hỏi mới một cách tự nhiên và hữu ích (bằng tiếng Việt).
        """

        response = self.agent.run(conversation_prompt)
        return response.content if hasattr(response, 'content') else str(response)
