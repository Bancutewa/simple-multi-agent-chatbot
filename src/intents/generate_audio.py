"""
Intent handler cho generate audio
"""
import os
import re
import time
from uuid import uuid4
from typing import Dict, Any, Optional
from agno.agent import Agent
from .base_intent import BaseIntent

# Import optional dependencies with fallback
try:
    from agno.tools.eleven_labs import ElevenLabsTools
    from agno.tools.firecrawl import FirecrawlTools
    from agno.utils.audio import write_audio_to_file
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    ElevenLabsTools = None
    FirecrawlTools = None
    write_audio_to_file = None


class GenerateAudioIntent(BaseIntent):
    """Intent handler cho việc tạo audio"""

    # Voice options cho ElevenLabs
    VOICE_OPTIONS = {
        "Nguyễn Ngân (Female, Vietnamese)": "DvG3I1kDzdBY3u4EzYh6",
        "Nhật Phong (Male, Vietnamese)": "RxhjHDfpO54FYotYtKpw",
        "Rachel (Female, American)": "21m00Tcm4TlvDq8ikWAM",
        "Drew (Male, American)": "29vD33N1CtxCmqQRPOHJ",
    }

    def __init__(self, agent: Agent):
        super().__init__(agent)
        # Tạo audio agent riêng với ElevenLabs tools
        self.audio_agent = None
        self._audio_display_response = None  # Response đầy đủ cho display
        self._audio_history_response = None  # Response rút gọn cho history
        self._initialize_audio_agent()

    def _initialize_audio_agent(self):
        """Khởi tạo audio agent với ElevenLabs tools"""
        if not ELEVENLABS_AVAILABLE:
            print("Warning: ElevenLabs dependencies not available. Audio generation will be disabled.")
            return

        try:
            elevenlabs_api_key = os.getenv("ELEVEN_LABS_API_KEY")
            firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")

            if elevenlabs_api_key:
                tools = [
                    ElevenLabsTools(
                        voice_id=self.VOICE_OPTIONS["Nguyễn Ngân (Female, Vietnamese)"],  # Default voice
                        model_id="eleven_turbo_v2_5",
                        target_directory="audio_generations",
                        api_key=elevenlabs_api_key,
                    )
                ]

                if firecrawl_api_key and FirecrawlTools:
                    tools.append(FirecrawlTools(api_key=firecrawl_api_key))

                self.audio_agent = Agent(
                    name="Audio Generation Agent",
                    model=self.agent.model,  # Sử dụng cùng model
                    tools=tools,
                    description="You are an AI agent that can generate audio using the ElevenLabs API.",
                    instructions=[
                        "When the user provides text or a URL:",
                        "1. If it's a URL, use FirecrawlTools to scrape the content first",
                        "2. Create a concise summary of the content that is NO MORE than 3000 characters long",
                        "3. The summary should capture the main points while being engaging and conversational",
                        "4. Use the ElevenLabsTools to convert the text/summary to audio",
                        "5. Ensure the text is within the 3000 character limit to avoid ElevenLabs API limits",
                    ],
                    markdown=True,
                    debug_mode=False,
                )
        except Exception as e:
            print(f"Warning: Could not initialize audio agent: {e}")

    @property
    def intent_name(self) -> str:
        return "generate_audio"

    @property
    def system_prompt(self) -> str:
        return """You are an AI audio content generator.
Your job is to take user requests and prepare content for text-to-speech generation.
If the user provides a URL, help scrape and summarize it.
If the user provides text, format it for better audio narration.

Respond with the content to be converted to audio."""

    def get_response(self, data: Dict[str, Any], context: Optional[str] = None) -> str:
        """
        Xử lý response cho generate audio

        Args:
            data: Chứa key "description" với text hoặc URL
            context: Không sử dụng cho intent này

        Returns:
            HTML audio player hoặc thông báo lỗi
        """
        description = data.get("description", "").strip()

        if not description:
            return "❌ Vui lòng cung cấp text hoặc URL để tạo audio."

        if not ELEVENLABS_AVAILABLE:
            return "❌ Tính năng tạo audio chưa được cài đặt. Vui lòng cài đặt elevenlabs package: `pip install elevenlabs`"

        if not self.audio_agent:
            # Fallback: tạo demo audio player với sample audio (for testing UI)
            if description.lower().strip() == "demo" or description.lower().strip() == "test":
                return self._create_demo_audio_player()
            return "❌ Không thể khởi tạo audio agent. Vui lòng kiểm tra ELEVEN_LABS_API_KEY."

        try:
            # Tạo thư mục lưu audio nếu chưa có
            save_dir = "audio_generations"
            os.makedirs(save_dir, exist_ok=True)

            # Lấy danh sách file hiện tại trước khi tạo audio
            import time
            existing_files = set(os.listdir(save_dir)) if os.path.exists(save_dir) else set()

            # Chạy audio agent để generate audio
            print(f"🎵 Đang tạo audio cho: {description[:50]}...")
            audio_response = self.audio_agent.run(
                f"Convert this content to audio: {description}"
            )

            # Chờ file được ghi xong (thay vì sleep cứng)
            latest_file = self._wait_for_new_audio_file(save_dir, existing_files)

            if not latest_file:
                return "❌ Audio được tạo nhưng không tìm thấy file. Vui lòng thử lại."

            print(f"✅ Audio file đã tạo: {latest_file}")

            # Đọc file và tạo audio player
            try:
                with open(latest_file, "rb") as f:
                    audio_bytes = f.read()

                # Lấy tên file để hiển thị
                filename = os.path.basename(latest_file)
                
                # Kiểm tra kích thước file
                file_size = len(audio_bytes) / 1024  # KB
                print(f"📦 Audio file size: {file_size:.2f} KB")

                # Sử dụng Streamlit audio player
                try:
                    import streamlit as st

                    # Hiển thị audio player với st.audio
                    st.audio(latest_file, format='audio/mp3')

                    # Hiển thị thông tin và nút download
                    st.success("🎵 **Audio được tạo thành công!**")
                    st.write(f"**📝 Nội dung:** {description[:100]}{'...' if len(description) > 100 else ''}")
                    st.write(f"**📁 File:** `{filename}` ({file_size:.1f} KB)")
                    st.write(f"**🎤 Voice:** Nguyễn Ngân (Female, Vietnamese)")

                    # Nút download
                    with open(latest_file, "rb") as f:
                        st.download_button(
                            label="⬇️ Tải xuống Audio",
                            data=f,
                            file_name=filename,
                            mime="audio/mpeg"
                        )

                    return ""  # Không trả về gì vì đã render trực tiếp

                except ImportError:
                    # Fallback nếu không thể import streamlit (không nên xảy ra trong context này)
                    import base64
                    audio_b64 = base64.b64encode(audio_bytes).decode()
                    return f"""🎵 **Audio được tạo thành công!**

<audio controls style="width: 100%; max-width: 400px;">
    <source src="data:audio/mpeg;base64,{audio_b64}" type="audio/mpeg">
    Trình duyệt của bạn không hỗ trợ audio player.
</audio>

<a href="data:audio/mpeg;base64,{audio_b64}" download="{filename}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">⬇️ Tải xuống Audio</a>

**📝 Nội dung:** {description[:100]}{'...' if len(description) > 100 else ''}  
**📁 File:** `{filename}` ({file_size:.1f} KB)  
**🎤 Voice:** Nguyễn Ngân (Female, Vietnamese)"""

            except Exception as e:
                print(f"❌ Error reading audio file: {e}")
                import traceback
                traceback.print_exc()
                return f"❌ Audio được tạo nhưng không thể hiển thị: {e}"

        except Exception as e:
            error_msg = str(e).lower()
            if "eleven" in error_msg and ("api" in error_msg or "key" in error_msg):
                return "❌ Lỗi API ElevenLabs. Vui lòng kiểm tra ELEVEN_LABS_API_KEY."
            elif "quota" in error_msg or "limit" in error_msg:
                return "❌ Đã hết quota ElevenLabs API."
            else:
                return f"❌ Lỗi tạo audio: {e}"

    def _wait_for_new_audio_file(self, save_dir: str, existing_files: set) -> Optional[str]:
        """Chờ file audio mới được tạo và trả về đường dẫn đến file"""
        max_wait_time = 15  # Tối đa 15 giây
        check_interval = 0.5  # Kiểm tra mỗi 0.5 giây

        for _ in range(int(max_wait_time / check_interval)):
            time.sleep(check_interval)

            # Tìm file mới được tạo
            current_files = set(os.listdir(save_dir)) if os.path.exists(save_dir) else set()
            new_files = [f for f in (current_files - existing_files) if f.endswith('.mp3')]

            if new_files:
                # Lấy file mới nhất
                latest_file = os.path.join(save_dir, sorted(new_files)[-1])
                print(f"📁 New audio file detected: {latest_file}")

                # Đợi file được ghi hoàn toàn (check size ổn định)
                if self._wait_for_file_stable(latest_file):
                    return latest_file

        # Fallback: lấy file mới nhất theo thời gian tạo
        print("⚠️ No new file detected, using fallback...")
        audio_files = [f for f in os.listdir(save_dir) if f.endswith('.mp3')]
        if audio_files:
            audio_files.sort(key=lambda x: os.path.getctime(os.path.join(save_dir, x)),
                          reverse=True)
            latest_file = os.path.join(save_dir, audio_files[0])
            print(f"📁 Using latest file as fallback: {latest_file}")
            return latest_file

        return None

    def _wait_for_file_stable(self, file_path: str, timeout: int = 5) -> bool:
        """Chờ file không thay đổi size (đã được ghi hoàn toàn)"""
        if not os.path.exists(file_path):
            return False

        initial_size = os.path.getsize(file_path)
        time.sleep(0.5)  # Chờ 0.5 giây

        for _ in range(timeout * 2):  # Kiểm tra mỗi 0.5 giây
            if not os.path.exists(file_path):
                return False

            current_size = os.path.getsize(file_path)
            if current_size == initial_size:
                return True  # File không thay đổi size

            initial_size = current_size
            time.sleep(0.5)

        return True  # Timeout nhưng file vẫn ổn định

    def get_display_response(self) -> str:
        """Lấy response đầy đủ cho display (với HTML player)"""
        return self._audio_display_response or ""

    def get_history_response(self) -> str:
        """Lấy response rút gọn cho chat history"""
        return self._audio_history_response or ""

    def _create_demo_audio_player(self) -> str:
        """Tạo demo audio player để test UI"""
        # Sử dụng một sample audio từ URL public (có sẵn trên web)
        # Đây là một beep sound rất ngắn để test audio player

        return f"""🎵 **Demo Audio Player (Test UI)**

<audio controls style="width: 100%; max-width: 400px;">
    <source src="data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmUdBzmL0/LNfTEFIHnA8N2SRgoURrTp66hYFwZBn+DyvmYdBjmL0/LNfTEFIHnA8N2SRgoURrTp66hYFwZBn+DyvmYdBjmL0/LNfTEF" type="audio/wav">
    Trình duyệt của bạn không hỗ trợ audio player.
</audio>

**🎤 Test thành công!** Audio player hoạt động.

**Để tạo audio thật với ElevenLabs:**
1. Cài đặt: `pip install elevenlabs`
2. Thêm API key: `ELEVEN_LABS_API_KEY` trong .env
3. Thử với prompt: "xin chào các bạn"

*Demo audio player sẽ hiển thị và có thể phát được.*"""

