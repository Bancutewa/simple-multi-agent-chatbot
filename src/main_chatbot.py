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
import uuid

# Load environment variables
load_dotenv()

# Constants
CHAT_SESSIONS_FILE = "chat_sessions.json"

class ChatSessionManager:
    """Quản lý multiple chat sessions"""

    def __init__(self):
        self.sessions = self._load_sessions()
        self.current_session_id = None

    def _load_sessions(self) -> Dict[str, Dict]:
        """Load sessions from file"""
        try:
            if os.path.exists(CHAT_SESSIONS_FILE):
                with open(CHAT_SESSIONS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            st.warning(f"Không thể tải sessions: {e}")
        return {}

    def _save_sessions(self):
        """Save sessions to file"""
        try:
            with open(CHAT_SESSIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"Lỗi lưu sessions: {e}")

    def create_session(self, title: str = None) -> str:
        """Tạo session mới"""
        session_id = str(uuid.uuid4())
        if not title:
            title = f"Chat {len(self.sessions) + 1}"

        self.sessions[session_id] = {
            "id": session_id,
            "title": title,
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        self._save_sessions()
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Lấy session theo ID"""
        return self.sessions.get(session_id)

    def update_session_title(self, session_id: str, title: str):
        """Cập nhật title của session"""
        if session_id in self.sessions:
            self.sessions[session_id]["title"] = title
            self.sessions[session_id]["updated_at"] = datetime.now().isoformat()
            self._save_sessions()

    def add_message_to_session(self, session_id: str, role: str, content: str):
        """Thêm message vào session"""
        if session_id in self.sessions:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            self.sessions[session_id]["messages"].append(message)
            self.sessions[session_id]["updated_at"] = datetime.now().isoformat()
            self._save_sessions()

    def delete_session(self, session_id: str):
        """Xóa session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()

    def get_all_sessions(self) -> List[Dict]:
        """Lấy tất cả sessions, sắp xếp theo updated_at"""
        sessions_list = list(self.sessions.values())
        sessions_list.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions_list

    def generate_session_title(self, session_id: str) -> str:
        """Tự động tạo title từ tin nhắn đầu tiên"""
        session = self.get_session(session_id)
        if session and session["messages"]:
            first_message = session["messages"][0]
            if first_message["role"] == "user":
                content = first_message["content"][:50]
                return content if len(content) < 50 else content + "..."
        return f"Chat {session_id[:8]}"

# System prompt for intent analysis
SYSTEM_INTENT_PROMPT = """
Bạn là một AI phân tích ý định.
Nhiệm vụ: Phân tích câu hỏi của người dùng và trả về 1 trong 3 intent.
Luôn trả về JSON hợp lệ, không gì khác.

1. general_chat: Người dùng muốn trò chuyện, hỏi đáp, chào hỏi, hỏi thông tin.
2. generate_image: Người dùng muốn tạo ảnh, vẽ, generate image, tạo hình ảnh. Từ khóa: vẽ, tạo ảnh, generate image, hình ảnh, bức ảnh.
3. generate_audio: Người dùng muốn tạo audio, podcast, đọc văn bản, tạo âm thanh, phát âm. Từ khóa: đọc, phát, audio, âm thanh, podcast.

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

Ví dụ 6:
Người dùng: "Vẽ cho tôi một con chó"
Bạn: {"intent": "generate_image", "description": "một con chó"}

Ví dụ 7:
Người dùng: "Tạo ảnh phong cảnh núi rừng"
Bạn: {"intent": "generate_image", "description": "phong cảnh núi rừng"}

Ví dụ 8:
Người dùng: "Đọc bài viết này cho tôi nghe"
Bạn: {"intent": "generate_audio", "description": "Đọc bài viết này cho tôi nghe"}
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

        # Khởi tạo session manager
        self.session_manager = ChatSessionManager()

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

    def analyze_user_intent(self, message: str, session_id: str = None) -> Dict:
        """Phân tích ý định của người dùng (dùng agent đã khởi tạo)"""
        if not self.intent_agent:
            return {"intent": "general_chat", "message": "Lỗi intent agent."}

        try:
            # Nếu không có session_id, sử dụng context mặc định
            if session_id:
                context_str = self._format_conversation_context(session_id)
            else:
                context_str = "Không có lịch sử hội thoại."
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

    def _format_conversation_context(self, session_id: str) -> str:
        """Format conversation context từ session hiện tại"""
        session = self.session_manager.get_session(session_id)
        if not session or not session["messages"]:
            return "Không có lịch sử hội thoại."

        context_parts = []
        # Lấy 5 tin nhắn gần nhất
        recent_messages = session["messages"][-5:]
        for msg in recent_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"][:100]  # Giới hạn độ dài
            context_parts.append(f"{role}: {content}")
        return "\n".join(context_parts)


    def get_greeting(self) -> str:
        return "👋 **Xin chào! Tôi là AI Chatbot Assistant**\n\nTôi có thể trò chuyện, tạo ảnh và tạo audio cho bạn. Bạn muốn thử gì nào?"

    def get_help(self) -> str:
        return "🆘 **Hướng dẫn sử dụng**\n\n- **Trò chuyện:** Gửi tin nhắn bất kỳ.\n- **Tạo ảnh:** Gửi yêu cầu như 'vẽ một con mèo' hoặc 'tạo ảnh'.\n- **Tạo audio:** Gửi yêu cầu như 'đọc văn bản này' hoặc 'tạo podcast từ URL'."

    def _get_api_key(self) -> str:
        """Lấy API key từ environment variable GEMINI_API_KEY"""
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            st.error("❌ **Thiếu API Key!**\n\nVui lòng thiết lập biến môi trường `GEMINI_API_KEY`:\n\n```bash\nexport GEMINI_API_KEY=your_api_key_here\n```\n\nLấy API key tại: https://aistudio.google.com/")
            st.stop()  # Dừng app nếu không có API key
        return api_key

    def add_message_to_session(self, session_id: str, role: str, content: str):
        """Thêm message vào session cụ thể"""
        self.session_manager.add_message_to_session(session_id, role, content)

    def get_current_session_messages(self, session_id: str) -> List[Dict]:
        """Lấy messages của session hiện tại"""
        session = self.session_manager.get_session(session_id)
        return session["messages"] if session else []

    def get_response(self, user_input: str, session_id: str = None) -> str:
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
            intent_analysis = self.analyze_user_intent(user_input, session_id)
            intent = intent_analysis.get("intent", "general_chat")

            # --- BƯỚC 2: ĐIỀU HƯỚNG TỚI INTENT HANDLER TƯƠNG ỨNG ---
            if intent in self.intent_agents:
                agent = self.intent_agents[intent]
                intent_handler = intent_registry.get_intent_instance(intent, agent)

                if intent_handler:
                    # Lấy context cho conversation intents
                    context = None
                    if intent == "general_chat" and session_id:
                        context = self._format_conversation_context(session_id)

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
        layout="wide"
    )

    # Khởi tạo chatbot
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = MainChatbot()

    chatbot = st.session_state.chatbot

    # Khởi tạo current session nếu chưa có
    if "current_session_id" not in st.session_state:
        # Tạo session mới hoặc lấy session gần nhất
        sessions = chatbot.session_manager.get_all_sessions()
        if sessions:
            st.session_state.current_session_id = sessions[0]["id"]
        else:
            st.session_state.current_session_id = chatbot.session_manager.create_session()

    current_session_id = st.session_state.current_session_id

    # --- SIDEBAR: Chat History ---
    with st.sidebar:
        st.header("💬 Chat Sessions")

        # Hiển thị thông tin API key
        st.caption(f"🔑 API: {'✅ Connected' if chatbot.api_key else '❌ Missing'}")

        # Nút tạo chat mới
        if st.button("➕ New Chat", use_container_width=True):
            new_session_id = chatbot.session_manager.create_session()
            st.session_state.current_session_id = new_session_id
            st.rerun()

        st.divider()

        # Hiển thị danh sách sessions
        sessions = chatbot.session_manager.get_all_sessions()

        for session in sessions:
            session_id = session["id"]
            title = session["title"]
            message_count = len(session["messages"])

            # Highlight session hiện tại
            if session_id == current_session_id:
                st.markdown(f"**🟢 {title}** ({message_count} msgs)")
            else:
                if st.button(f"💬 {title} ({message_count})", key=f"session_{session_id}", use_container_width=True):
                    st.session_state.current_session_id = session_id
                    st.rerun()

            # Menu cho mỗi session (rename, delete)
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("⋮", key=f"menu_{session_id}", help="Options"):
                    st.session_state[f"show_menu_{session_id}"] = not st.session_state.get(f"show_menu_{session_id}", False)

            # Menu options
            if st.session_state.get(f"show_menu_{session_id}", False):
                with st.container():
                    if st.button("✏️ Rename", key=f"rename_{session_id}"):
                        st.session_state[f"renaming_{session_id}"] = True

                    if st.button("🗑️ Delete", key=f"delete_{session_id}"):
                        chatbot.session_manager.delete_session(session_id)
                        if current_session_id == session_id:
                            # Chuyển sang session khác
                            remaining_sessions = chatbot.session_manager.get_all_sessions()
                            if remaining_sessions:
                                st.session_state.current_session_id = remaining_sessions[0]["id"]
                            else:
                                st.session_state.current_session_id = chatbot.session_manager.create_session()
                        st.rerun()

            # Rename input
            if st.session_state.get(f"renaming_{session_id}", False):
                new_title = st.text_input(
                    "New title:",
                    value=title,
                    key=f"title_input_{session_id}"
                )
                if st.button("💾 Save", key=f"save_rename_{session_id}"):
                    rename_session(session_id, new_title)

    # --- MAIN CONTENT: Current Chat ---
    current_session = chatbot.session_manager.get_session(current_session_id)

    if current_session:
        st.title(f"🤖 {current_session['title']}")

        # Hiển thị messages của session hiện tại
        messages = current_session["messages"]

        if messages:
            for message in messages:
                with st.chat_message(message["role"]):
                    content = message["content"]

                    # Kiểm tra xem có audio display response trong session state không
                    if message["role"] == "assistant" and st.session_state.get('audio_display_response'):
                        display_content = st.session_state.audio_display_response
                        del st.session_state.audio_display_response
                        st.markdown(display_content, unsafe_allow_html=True)
                    else:
                        st.markdown(content, unsafe_allow_html=True)
        else:
            st.info("👋 Bắt đầu cuộc trò chuyện mới!")

        # Chat input (API key đã được kiểm tra ở init)
        if user_input := st.chat_input("Hỏi tôi hoặc yêu cầu 'vẽ một con chó'...", disabled=not chatbot.api_key):

                # Thêm tin nhắn người dùng vào session
                chatbot.add_message_to_session(current_session_id, "user", user_input)

                # Hiển thị message của user
                with st.chat_message("user"):
                    st.markdown(user_input)

                # Lấy phản hồi của bot
                with st.chat_message("assistant"):
                    with st.spinner("🤖 Đang suy nghĩ..."):
                        bot_response = chatbot.get_response(user_input, current_session_id)

                        # Kiểm tra xem có display response đặc biệt không (cho audio)
                        display_response = st.session_state.get('audio_display_response', bot_response)
                        if 'audio_display_response' in st.session_state:
                            del st.session_state.audio_display_response  # Xóa sau khi sử dụng

                        if display_response.strip():  # Chỉ hiển thị nếu có nội dung
                            st.markdown(display_response, unsafe_allow_html=True)

                # Thêm tin nhắn của bot vào session
                chatbot.add_message_to_session(current_session_id, "assistant", bot_response)

                # Tự động cập nhật title nếu là tin nhắn đầu tiên
                if len(current_session["messages"]) == 2:  # user + assistant
                    auto_title = chatbot.session_manager.generate_session_title(current_session_id)
                    if auto_title != current_session["title"]:
                        chatbot.session_manager.update_session_title(current_session_id, auto_title)

    else:
        st.error("Session không tồn tại!")


def rename_session(session_id: str, new_title: str):
    """Helper function để rename session"""
    if "chatbot" in st.session_state:
        st.session_state.chatbot.session_manager.update_session_title(session_id, new_title)
        if f"renaming_{session_id}" in st.session_state:
            del st.session_state[f"renaming_{session_id}"]
        st.rerun()

if __name__ == "__main__":
    main()