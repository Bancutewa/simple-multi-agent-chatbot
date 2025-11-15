"""
Intent handler cho generate image
"""
import re
from typing import Dict, Any, Optional
from urllib.parse import quote
from agno.agent import Agent
from .base_intent import BaseIntent


class GenerateImageIntent(BaseIntent):
    """Intent handler cho việc tạo ảnh"""

    @property
    def intent_name(self) -> str:
        return "generate_image"

    @property
    def system_prompt(self) -> str:
        return """You are an AI image prompt generator.
Your job is to take a simple description and turn it into a detailed, rich, English prompt for an AI image generator like Stable Diffusion.
Respond ONLY with the <prompt: ...> tag. Do not add any other text.

Example 1:
User: "một con mèo"
Response: <prompt: a photorealistic image of a small orange tabby cat sleeping peacefully on a soft blue cushion>

Example 2:
User: "xe ô tô"
Response: <prompt: a sleek, futuristic red sports car driving on a wet city road at night, neon lights reflecting on its surface, cinematic style>"""

    def get_response(self, data: Dict[str, Any], context: Optional[str] = None) -> str:
        """
        Xử lý response cho generate image

        Args:
            data: Chứa key "description" với mô tả ảnh
            context: Không sử dụng cho intent này

        Returns:
            Markdown với link ảnh
        """
        description = data.get("description", "")

        # Gọi Image Agent để tạo prompt chi tiết
        image_response = self.agent.run(description)
        response_text = image_response.content if hasattr(image_response, 'content') else str(image_response)

        detailed_prompt = self._extract_image_prompt(response_text)

        if not detailed_prompt:
            # Fallback nếu image_agent không trả về tag <prompt>
            detailed_prompt = description  # Dùng tạm mô tả gốc

        return self._generate_image_url(detailed_prompt)

    def _extract_image_prompt(self, message: str) -> str:
        """Trích xuất prompt tiếng Anh từ tag <prompt:...>"""
        match = re.search(r"<prompt:(.*?)>", message, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""  # Trả về rỗng nếu không tìm thấy

    def _generate_image_url(self, detailed_prompt: str) -> str:
        """
        Tạo URL cho image generation
        """
        try:
            # Sử dụng quote để mã hóa URL đúng cách (an toàn hơn replace)
            prompt_encoded = quote(detailed_prompt)
            image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}"

            # Trả về Markdown hoàn chỉnh
            return f"🖼️ **Hình ảnh của bạn:**\n\n![{detailed_prompt[:50]}...]({image_url})"

        except Exception as e:
            return f"❌ Lỗi tạo hình ảnh: {e}"
