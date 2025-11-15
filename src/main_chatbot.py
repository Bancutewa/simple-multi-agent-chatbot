import os
import streamlit as st
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from agno.agent import Agent
from agno.models.google import Gemini
from dotenv import load_dotenv
from intents.intent_registry import intent_registry

# Load environment variables
load_dotenv()

# Constants
CHAT_HISTORY_FILE = "chat_history.json"

# System prompt for intent analysis
SYSTEM_INTENT_PROMPT = """
Bạn là một AI phân tích ý định.
Nhiệm vụ: Phân tích câu hỏi của người dùng và trả về 1 trong 3 intent.
Luôn trả về JSON hợp lệ, không gì khác.

1. general_chat: Người dùng muốn trò chuyện, hỏi đáp, chào hỏi.
2. generate_image: Người dùng muốn tạo ảnh, vẽ, generate image.
3. generate_audio: Người dùng muốn tạo audio, podcast, đọc văn bản, tạo âm thanh.

{"intent": "general_chat", "message": "Nội dung chat"}
HOẶC
{"intent": "generate_image", "description": "Mô tả ảnh"}
HOẶC
{"intent": "generate_audio", "description": "Nội dung text hoặc URL"}

---
Ví dụ 1:
Người dùng: "Xin chào"
Bạn: {"intent": "general_chat", "message": "Xin chào"}

Ví dụ 2:
Người dùng: "Vẽ cho tôi một con mèo"
Bạn: {"intent": "generate_image", "description": "một con mèo"}

Ví dụ 3:
Người dùng: "Đọc văn bản này cho tôi"
Bạn: {"intent": "generate_audio", "description": "Đọc văn bản này cho tôi"}

Ví dụ 4:
Người dùng: "Tạo podcast từ bài viết này https://example.com/blog"
Bạn: {"intent": "generate_audio", "description": "https://example.com/blog"}

Ví dụ 5:
Người dùng: "Thời tiết hôm nay thế nào?"
Bạn: {"intent": "general_chat", "message": "Thời tiết hôm nay thế nào?"}
"""

# System prompt for image generation
IMAGE_SYSTEM_PROMPT = """
You are an AI image prompt generator.
Your job is to take a simple description and turn it into a detailed, rich, English prompt for an AI image generator like Stable Diffusion.
Respond ONLY with the <prompt: ...> tag. Do not add any other text.

Example 1:
User: "một con mèo"
Response: <prompt: a photorealistic image of a small orange tabby cat sleeping peacefully on a soft blue cushion>

Example 2:
User: "xe ô tô"
Response: <prompt: a sleek, futuristic red sports car driving on a wet city road at night, neon lights reflecting on its surface, cinematic style>
"""


class MainChatbot:
    def __init__(self):
        self.api_key = self._get_api_key()

        self.model_id = "gemini-2.5-flash"
        self.model = Gemini(id=self.model_id, api_key=self.api_key) if self.api_key else None

        # Khởi tạo các intent agents thông qua registry
        self.intent_agents = {}
        self.intent_agent = None

        if self.api_key:
            self._initialize_intent_agents()

        # Khởi tạo Intent Analyzer Agent riêng biệt
        self.intent_agent = self._initialize_agent("Intent Analyzer", [
            SYSTEM_INTENT_PROMPT,
            "Luôn trả về JSON hợp lệ."
        ], markdown=False)

        self.chat_history = self._load_chat_history()

    def _initialize_intent_agents(self):
        """Khởi tạo các intent agents thông qua registry"""
        if not self.model:
            return

        for intent_name in intent_registry.get_intent_names():
            agent = intent_registry.create_agent_for_intent(intent_name, self.model, self.api_key)
            if agent:
                self.intent_agents[intent_name] = agent


    def _initialize_agent(self, name: str, instructions: List[str], markdown: bool = True) -> Optional[Agent]:
        if not self.api_key:
            return None
        try:
            return Agent(
                name=name,
                model=Gemini(id=self.model_id, api_key=self.api_key),
                description=f"Agent cho nhiệm vụ: {name}",
                instructions=instructions,
                markdown=markdown,
                debug_mode=False
            )
        except Exception as e:
            st.error(f"Lỗi khởi tạo agent '{name}': {e}")
            return None

    def analyze_user_intent(self, message: str) -> Dict:
        """Phân tích ý định của người dùng (dùng agent đã khởi tạo)"""
        if not self.intent_agent:
            return {"intent": "general_chat", "message": "Lỗi intent agent."}

        try:
            context_str = self._format_conversation_context()
            intent_prompt = f"""
            # Lịch sử hội thoại (để tham khảo):
            {context_str}

            # Câu hỏi MỚI của người dùng:
            "{message}"

            Trả về JSON phân tích câu hỏi MỚI.
            """

            response = self.intent_agent.run(intent_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            cleaned = re.sub(r"^```json|```$", "", response_text, flags=re.MULTILINE).strip()
            
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                print(f"Lỗi JSONDecodeError khi phân tích intent. Trả về: {response_text}")
                # Fallback an toàn
                if "generate_image" in response_text.lower():
                    return {"intent": "generate_image", "description": message}
                else:
                    return {"intent": "general_chat", "message": message}

        except Exception as e:
            print(f"Intent analysis error: {e}")
            return {"intent": "general_chat", "message": message}

    def _format_conversation_context(self) -> str:
        if not self.chat_history:
            return "Không có lịch sử hội thoại."
        context_parts = []
        for msg in self.chat_history[-5:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"][:100]
            context_parts.append(f"{role}: {content}")
        return "\n".join(context_parts)


    def get_greeting(self) -> str:
        return "👋 **Xin chào! Tôi là AI Chatbot Assistant**\n\nTôi có thể trò chuyện, tạo ảnh và tạo audio cho bạn. Bạn muốn thử gì nào?"

    def get_help(self) -> str:
        return "🆘 **Hướng dẫn sử dụng**\n\n- **Trò chuyện:** Gửi tin nhắn bất kỳ.\n- **Tạo ảnh:** Gửi yêu cầu như 'vẽ một con mèo' hoặc 'tạo ảnh'.\n- **Tạo audio:** Gửi yêu cầu như 'đọc văn bản này' hoặc 'tạo podcast từ URL'."

    def _get_api_key(self) -> str:
        api_key = os.getenv("GEMINI_API_KEY") or st.session_state.get("gemini_api_key", "")
        if not api_key:
            with st.sidebar:
                st.header("🔑 API Configuration")
                api_key_input = st.text_input("Gemini API Key", type="password", help="Nhập API key của Google Gemini")
                if api_key_input:
                    st.session_state.gemini_api_key = api_key_input
                    st.success("✅ API key đã được lưu!")
                    st.rerun() # Rerun để app khởi tạo agent với key mới
                else:
                    st.warning("⚠️ Vui lòng nhập API key để sử dụng")
        return api_key

    def _load_chat_history(self) -> List[Dict]:
        try:
            if os.path.exists(CHAT_HISTORY_FILE):
                with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            st.warning(f"Không thể tải lịch sử chat: {e}")
        return []

    def _save_chat_history(self):
        try:
            with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history[-50:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"Lỗi lưu lịch sử chat: {e}")

    def add_message(self, role: str, content: str):
        message = {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        self.chat_history.append(message)
        self._save_chat_history()

    def get_response(self, user_input: str) -> str:
        """Hàm logic chính: 1. Phân tích intent -> 2. Gọi intent handler tương ứng"""
        if not self.api_key:
             return "❌ Vui lòng nhập API key ở thanh bên trái."
        if not self.intent_agent or not self.intent_agents:
            return "❌ Lỗi khởi tạo agent. Vui lòng kiểm tra API key hoặc khởi động lại."

        try:
            user_input_lower = user_input.lower().strip()

            # Xử lý lệnh đặc biệt (không tốn API)
            if user_input_lower in ["hello", "hi", "xin chào", "chào"]:
                return self.get_greeting()
            if user_input_lower in ["help", "giúp đỡ", "hướng dẫn", "?"]:
                return self.get_help()
            if user_input_lower in ["clear", "xóa lịch sử", "reset"]:
                return "🗑️ Để xóa lịch sử chat, hãy sử dụng nút 'Xóa lịch sử chat' ở cuối trang."

            # --- BƯỚC 1: PHÂN TÍCH INTENT ---
            intent_analysis = self.analyze_user_intent(user_input)
            intent = intent_analysis.get("intent", "general_chat")

            # --- BƯỚC 2: ĐIỀU HƯỚNG TỚI INTENT HANDLER TƯƠNG ỨNG ---
            if intent in self.intent_agents:
                agent = self.intent_agents[intent]
                intent_handler = intent_registry.get_intent_instance(intent, agent)

                if intent_handler:
                    # Lấy context cho conversation intents
                    context = None
                    if intent == "general_chat":
                        context = self._format_conversation_context()

                    response = intent_handler.get_response(intent_analysis, context)

                    # Xử lý đặc biệt cho audio intent: sử dụng display response thay vì history response
                    if intent == "generate_audio" and hasattr(intent_handler, 'get_display_response'):
                        display_response = intent_handler.get_display_response()
                        if display_response:
                            # Lưu display response vào session state để sử dụng trong UI
                            st.session_state.audio_display_response = display_response
                            # Trả về history response để lưu vào chat history
                            return response

                    return response

            # Fallback: general chat nếu không tìm thấy intent handler
            return "❌ Không thể xử lý yêu cầu này. Vui lòng thử lại."

        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "resource_exhausted" in error_str or "quota" in error_str:
                return "❌ **Đã hết quota Gemini API miễn phí!**\n\nVui lòng kiểm tra tài khoản Google AI Studio hoặc đợi (thường là 1 phút) để thử lại."
            print(f"Lỗi nghiêm trọng trong get_response: {e}")
            return f"❌ Đã xảy ra lỗi: {e}"

def main():
    st.set_page_config(
        page_title="🤖 AI Chatbot Assistant",
        page_icon="🤖",
        layout="centered"
    )

    st.title("🤖 AI Chatbot Assistant")
    st.markdown("### Chatbot AI đa năng (Chat, Tạo ảnh & Audio)")

    if "chatbot" not in st.session_state:
        st.session_state.chatbot = MainChatbot()
    
    chatbot = st.session_state.chatbot

    # --- Sidebar ---
    with st.sidebar:
        st.header("ℹ️ Thông tin")
        st.markdown("Một chatbot AI sử dụng Gemini, Pollinations.ai và ElevenLabs, được xây dựng với kiến trúc Multi-Agent (Intent -> Skill).")
        st.divider()
        st.header("🎯 Intent Handlers")
        for intent_name in intent_registry.get_intent_names():
            emoji_map = {
                "general_chat": "💬",
                "generate_image": "🖼️",
                "generate_audio": "🎵"
            }
            emoji = emoji_map.get(intent_name, "🤖")
            display_name = intent_name.replace("_", " ").title()
            st.metric(display_name, emoji)
        st.metric("Intent Analyzer", "🧠")
        st.divider()
        st.header("📊 Thống kê")
        st.metric("Tin nhắn đã chat", len(chatbot.chat_history))

    # 🎯 TỐI ƯU 3: Sử dụng st.chat_message để hiển thị lịch sử
    # Giao diện đẹp và hiện đại hơn
    if chatbot.api_key:
        for message in chatbot.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    else:
        st.info("👋 Vui lòng nhập Gemini API Key ở thanh bên (sidebar) để bắt đầu.")

    # 🎯 TỐI ƯU 4: Sử dụng st.chat_input cho ô nhập liệu
    # Tự động xử lý việc gửi tin nhắn, không cần st.form hay st.button
    if user_input := st.chat_input("Hỏi tôi hoặc yêu cầu 'vẽ một con chó'...", disabled=not chatbot.api_key):
        
        # Thêm tin nhắn người dùng vào lịch sử và hiển thị
        chatbot.add_message("user", user_input)
        with st.chat_message("user"):
            st.markdown(user_input)

        # Lấy phản hồi của bot và hiển thị
        with st.chat_message("assistant"):
            with st.spinner("🤖 Đang suy nghĩ..."):
                bot_response = chatbot.get_response(user_input)

                # Kiểm tra xem có display response đặc biệt không (cho audio)
                display_response = st.session_state.get('audio_display_response', bot_response)
                if 'audio_display_response' in st.session_state:
                    del st.session_state.audio_display_response  # Xóa sau khi sử dụng

                if display_response.strip():  # Chỉ hiển thị nếu có nội dung
                    st.markdown(display_response, unsafe_allow_html=True)
        
        # Thêm tin nhắn của bot vào lịch sử
        chatbot.add_message("assistant", bot_response)
        
        # Không cần st.rerun() nữa, st.chat_input xử lý việc này

    # Nút xóa lịch sử (đặt ở cuối)
    if chatbot.api_key and len(chatbot.chat_history) > 0:
        if st.button("🗑️ Xóa lịch sử chat"):
            chatbot.chat_history = []
            chatbot._save_chat_history()
            st.success("✅ Đã xóa lịch sử chat!")
            st.rerun()

if __name__ == "__main__":
    main()