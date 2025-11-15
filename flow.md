# 🔄 Flow Code - AI Chatbot Assistant

## 📋 Tổng quan kiến trúc

Chatbot sử dụng **kiến trúc Intent-based Multi-Agent** với các thành phần chính:

```
User Input → Intent Analyzer → Intent Handler → Response
                                   ├─ General Chat
                                   ├─ Generate Image
                                   └─ Generate Audio
```

---

## 📁 Cấu trúc thư mục

```
chatbot/
├── app.py                          # Entry point chính
├── src/
│   ├── main_chatbot.py            # Main chatbot logic
│   └── intents/                   # Intent handlers
│       ├── __init__.py
│       ├── base_intent.py         # Base class cho intents
│       ├── intent_registry.py     # Registry quản lý intents
│       ├── general_chat.py        # Handler trò chuyện
│       ├── generate_image.py      # Handler tạo ảnh
│       └── generate_audio.py      # Handler tạo audio
└── audio_generations/             # Thư mục lưu audio files
```

---

## 🚀 Flow chi tiết

### **1. Entry Point - `app.py`**

```python
# Chức năng: Khởi động ứng dụng Streamlit
1. Import sys, os
2. Thêm 'src' vào Python path → Cho phép import intents
3. Import main() từ src.main_chatbot
4. Chạy main()
```

**Vai trò:**

- Thiết lập environment để import các module
- Khởi động Streamlit app

---

### **2. Main Logic - `src/main_chatbot.py`**

#### **2.1 Khởi tạo MainChatbot class**

```python
class MainChatbot:
    def __init__(self):
        1. Lấy GEMINI_API_KEY từ .env hoặc Streamlit session
        2. Khởi tạo Gemini model
        3. Khởi tạo intent agents qua intent_registry
           - general_chat agent
           - generate_image agent
           - generate_audio agent
        4. Khởi tạo Intent Analyzer agent (phân tích ý định)
        5. Load chat history từ chat_history.json
```

#### **2.2 Xử lý User Input - `get_response()`**

```python
def get_response(user_input: str) -> str:
    # BƯỚC 1: Xử lý lệnh đặc biệt (không tốn API)
    if user_input in ["hello", "hi", "xin chào"]:
        return get_greeting()
    if user_input in ["help", "giúp đỡ"]:
        return get_help()

    # BƯỚC 2: Phân tích Intent
    intent_analysis = analyze_user_intent(user_input)
    # Trả về: {"intent": "general_chat|generate_image|generate_audio",
    #          "message|description": "..."}

    # BƯỚC 3: Route đến Intent Handler
    intent = intent_analysis.get("intent")

    if intent in self.intent_agents:
        agent = self.intent_agents[intent]  # Lấy agent tương ứng
        intent_handler = intent_registry.get_intent_instance(intent, agent)

        # Lấy context nếu là general_chat
        context = self._format_conversation_context() if intent == "general_chat" else None

        # Gọi handler xử lý
        return intent_handler.get_response(intent_analysis, context)
```

#### **2.3 Intent Analysis - `analyze_user_intent()`**

```python
def analyze_user_intent(message: str) -> Dict:
    # Sử dụng Intent Analyzer Agent (Gemini)
    1. Format context từ lịch sử chat (5 tin nhắn gần nhất)
    2. Tạo prompt với context + message mới
    3. Gọi intent_agent.run(prompt)
    4. Parse JSON response
       {
         "intent": "general_chat" | "generate_image" | "generate_audio",
         "message": "..." | "description": "..."
       }
    5. Fallback nếu lỗi JSON → detect keyword "generate_image" hoặc mặc định "general_chat"
```

**System Prompt cho Intent Analyzer:**

```
Phân tích câu hỏi và trả về 1 trong 3 intent:
1. general_chat: Trò chuyện, hỏi đáp
2. generate_image: Tạo ảnh, vẽ
3. generate_audio: Tạo audio, podcast, đọc văn bản

Ví dụ:
- "Xin chào" → {"intent": "general_chat", "message": "Xin chào"}
- "Vẽ con mèo" → {"intent": "generate_image", "description": "một con mèo"}
- "Đọc văn bản này" → {"intent": "generate_audio", "description": "..."}
```

#### **2.4 Streamlit UI - `main()`**

```python
def main():
    1. Setup page config (title, icon, layout)
    2. Khởi tạo MainChatbot trong session_state (tái sử dụng)

    # Sidebar
    3. Hiển thị thông tin:
       - Intent handlers có sẵn (💬 💖 🎵)
       - Intent Analyzer (🧠)
       - Số tin nhắn đã chat

    # Main Chat Interface
    4. Hiển thị lịch sử chat (st.chat_message)
    5. Chat input (st.chat_input)
    6. Khi user gửi tin nhắn:
       a. Thêm message vào lịch sử
       b. Hiển thị message của user
       c. Gọi chatbot.get_response(user_input)
       d. Hiển thị response với st.markdown(unsafe_allow_html=True)
       e. Lưu response vào lịch sử

    # Clear History Button
    7. Nút xóa lịch sử chat
```

---

### **3. Intent System - `intents/`**

#### **3.1 Base Intent - `base_intent.py`**

```python
class BaseIntent(ABC):
    """Abstract base class cho tất cả intent handlers"""

    @abstractmethod
    def intent_name(self) -> str:
        # Tên intent: "general_chat", "generate_image", etc.
        pass

    @abstractmethod
    def system_prompt(self) -> str:
        # System prompt cho agent của intent này
        pass

    @abstractmethod
    def get_response(data: Dict, context: Optional[str]) -> str:
        # Logic xử lý response
        pass
```

**Vai trò:**

- Định nghĩa interface chung cho tất cả intent handlers
- Đảm bảo consistency

---

#### **3.2 Intent Registry - `intent_registry.py`**

```python
class IntentRegistry:
    def __init__(self):
        self._intents = {}  # Mapping: intent_name → intent_class
        self._instances = {}  # Cached instances
        self._register_builtin_intents()

    def _register_builtin_intents(self):
        # Đăng ký các intent có sẵn
        self.register_intent("general_chat", GeneralChatIntent)
        self.register_intent("generate_image", GenerateImageIntent)
        self.register_intent("generate_audio", GenerateAudioIntent)

    def get_intent_instance(intent_name: str, agent: Agent):
        # Lấy hoặc tạo instance của intent handler
        # Sử dụng cache để tối ưu hiệu suất
        if key not in self._instances:
            self._instances[key] = intent_class(agent)
        return self._instances[key]
```

**Vai trò:**

- Quản lý tập trung các intent handlers
- Factory pattern để tạo instances
- Caching để tối ưu performance

---

#### **3.3 General Chat Intent - `general_chat.py`**

```python
class GeneralChatIntent(BaseIntent):
    intent_name = "general_chat"

    system_prompt = """
    Bạn là chatbot AI thông minh, thân thiện
    Luôn trả lời bằng tiếng Việt
    Trả lời tự nhiên, hấp dẫn, xây dựng
    """

    def get_response(data, context):
        message = data.get("message")

        # Tạo prompt với context
        prompt = f"""
        Lịch sử hội thoại:
        {context}

        Câu hỏi mới: {message}

        Trả lời tự nhiên và hữu ích (tiếng Việt)
        """

        # Gọi agent
        response = self.agent.run(prompt)
        return response.content
```

**Flow:**

```
User message → Format với context → Gemini Agent → Response
```

---

#### **3.4 Generate Image Intent - `generate_image.py`**

```python
class GenerateImageIntent(BaseIntent):
    intent_name = "generate_image"

    system_prompt = """
    AI image prompt generator
    Chuyển mô tả đơn giản → prompt chi tiết tiếng Anh
    Trả về format: <prompt: ...>
    """

    def get_response(data, context):
        description = data.get("description")  # VD: "một con mèo"

        # BƯỚC 1: Tạo prompt chi tiết
        response = self.agent.run(description)
        # Response: "<prompt: a photorealistic orange tabby cat...>"

        # BƯỚC 2: Extract prompt từ tag
        detailed_prompt = self._extract_image_prompt(response)

        # BƯỚC 3: Tạo URL Pollinations.ai
        return self._generate_image_url(detailed_prompt)

    def _generate_image_url(detailed_prompt):
        from urllib.parse import quote
        prompt_encoded = quote(detailed_prompt)
        url = f"https://image.pollinations.ai/prompt/{prompt_encoded}"

        return f"""
        🖼️ **Hình ảnh của bạn:**
        ![{detailed_prompt[:50]}]({url})
        """
```

**Flow:**

```
"Vẽ con mèo"
  → Agent: "<prompt: a cute orange cat...>"
  → Extract: "a cute orange cat..."
  → URL: https://image.pollinations.ai/prompt/a%20cute%20orange%20cat...
  → Markdown ![...](url)
  → Streamlit hiển thị ảnh
```

---

#### **3.5 Generate Audio Intent - `generate_audio.py`**

```python
class GenerateAudioIntent(BaseIntent):
    intent_name = "generate_audio"

    # Voice options
    VOICE_OPTIONS = {
        "Nguyễn Ngân (Female, Vietnamese)": "DvG3I1kDzdBY3u4EzYh6",
        "Nhật Phong (Male, Vietnamese)": "RxhjHDfpO54FYotYtKpw",
        ...
    }

    def __init__(agent):
        self.audio_agent = None
        self._initialize_audio_agent()

    def _initialize_audio_agent(self):
        # Kiểm tra elevenlabs có sẵn không
        if not ELEVENLABS_AVAILABLE:
            return

        # Lấy API keys
        elevenlabs_api_key = os.getenv("ELEVEN_LABS_API_KEY")
        firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")

        # Tạo audio agent với tools
        self.audio_agent = Agent(
            name="Audio Generation Agent",
            model=self.agent.model,
            tools=[
                ElevenLabsTools(
                    voice_id="...",
                    model_id="eleven_turbo_v2_5",
                    target_directory="audio_generations",
                    api_key=elevenlabs_api_key
                ),
                FirecrawlTools(api_key=firecrawl_api_key)  # Optional
            ],
            instructions=[
                "If URL → scrape content",
                "Summarize under 3000 chars",
                "Convert to audio using ElevenLabs"
            ]
        )

    def get_response(data, context):
        description = data.get("description")

        # Check dependencies
        if not ELEVENLABS_AVAILABLE:
            return "❌ Cần cài: pip install elevenlabs"

        if not self.audio_agent:
            # Fallback: demo mode
            if description.lower() in ["demo", "test"]:
                return self._create_demo_audio_player()
            return "❌ Cần ELEVEN_LABS_API_KEY"

        # BƯỚC 1: Tạo thư mục
        save_dir = "audio_generations"
        os.makedirs(save_dir, exist_ok=True)

        # BƯỚC 2: Lưu danh sách file hiện tại (để detect file mới)
        existing_files = set(os.listdir(save_dir))

        # BƯỚC 3: Gọi audio agent
        print("🎵 Đang tạo audio...")
        audio_response = self.audio_agent.run(
            f"Convert this content to audio: {description}"
        )
        # ElevenLabsTools tự động lưu file MP3 vào audio_generations/

        # BƯỚC 4: Chờ file được ghi xong (smart waiting)
        # _wait_for_new_audio_file() tự động detect file mới và chờ stable

        # BƯỚC 5: Tìm file MỚI được tạo
        current_files = set(os.listdir(save_dir))
        new_files = [f for f in (current_files - existing_files)
                     if f.endswith('.mp3')]

        if new_files:
            latest_file = os.path.join(save_dir, sorted(new_files)[-1])
        else:
            # Fallback: lấy file mới nhất theo thời gian
            all_files = [f for f in os.listdir(save_dir) if f.endswith('.mp3')]
            all_files.sort(key=lambda x: os.path.getctime(os.path.join(save_dir, x)),
                          reverse=True)
            latest_file = os.path.join(save_dir, all_files[0])

        print(f"✅ Audio file: {latest_file}")

        # BƯỚC 6: Đọc file và encode base64
        with open(latest_file, "rb") as f:
            audio_bytes = f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode()

        filename = os.path.basename(latest_file)
        file_size = len(audio_bytes) / 1024  # KB

        # BƯỚC 7: Hiển thị audio player với Streamlit components
        st.audio(latest_file, format='audio/mp3')
        st.success("🎵 **Audio được tạo thành công!**")
        st.write(f"**📝 Nội dung:** {description[:100]}...")
        st.write(f"**📁 File:** {filename} ({file_size:.1f} KB)")
        st.write(f"**🎤 Voice:** Nguyễn Ngân (Female, Vietnamese)")

        # Nút download
        with open(latest_file, "rb") as f:
            st.download_button(
                label="⬇️ Tải xuống Audio",
                data=f,
                file_name=filename,
                mime="audio/mpeg"
            )

        return ""  # Đã render trực tiếp, không cần trả về text
```

**Flow chi tiết:**

```
"Xin chào các bạn"
  ↓
1. Save existing files list: existing_files = set(os.listdir("audio_generations"))
  ↓
2. Audio Agent with ElevenLabsTools
  ↓
3. Call ElevenLabs TTS API
  ↓
4. ElevenLabsTools auto save: audio_generations/c5324429-3382-446f-98fe-ea95cde57453.mp3
  ↓
5. Smart wait for file creation (_wait_for_new_audio_file)
     - Poll every 0.5s for up to 15s
     - Detect new files: current_files - existing_files
     - Wait for file size to stabilize (_wait_for_file_stable)
  ↓
6. File ready: path/to/audio.mp3
  ↓
7. Read file: audio_bytes
  ↓
8. Encode base64: audio_b64
  ↓
9. Create HTML <audio> player with data:audio/mpeg;base64,{audio_b64}
  ↓
10. Streamlit render with unsafe_allow_html=True
  ↓
11. User can:
    - ▶️ Play audio inline
    - ⬇️ Download MP3 file
    - 👀 See file info (name, size, voice)
```

**Key points:**

- ✅ **No dependency on response.audio object** (bỏ lỗi base64_audio)
- ✅ **File detection by diff** (existing vs current files)
- ✅ **Fallback logic** (nếu không detect được, lấy file mới nhất)
- ✅ **Time.sleep(1)** để đảm bảo file được flush hoàn toàn
- ✅ **Full metadata** trong response (filename, size, voice)

---

## 🔄 Flow tổng thể (End-to-End)

### **Ví dụ 1: Trò chuyện**

```
User: "Xin chào"
  ↓
app.py → main()
  ↓
MainChatbot.get_response("Xin chào")
  ↓
analyze_user_intent("Xin chào")
  ↓ Intent Analyzer Agent
{"intent": "general_chat", "message": "Xin chào"}
  ↓
intent_agents["general_chat"].get_response(...)
  ↓ GeneralChatIntent
"👋 Xin chào! Tôi là AI Chatbot Assistant..."
  ↓
Streamlit display
```

### **Ví dụ 2: Tạo ảnh**

```
User: "Vẽ một con mèo"
  ↓
MainChatbot.get_response("Vẽ một con mèo")
  ↓
analyze_user_intent("Vẽ một con mèo")
  ↓
{"intent": "generate_image", "description": "một con mèo"}
  ↓
GenerateImageIntent.get_response(...)
  ↓ Image Agent
"<prompt: a photorealistic orange tabby cat...>"
  ↓ Extract + Encode URL
![...](https://image.pollinations.ai/prompt/...)
  ↓
Streamlit display image
```

### **Ví dụ 3: Tạo audio**

```
User: "Đọc văn bản: xin chào các bạn"
  ↓
MainChatbot.get_response(...)
  ↓
analyze_user_intent(...)
  ↓
{"intent": "generate_audio", "description": "xin chào các bạn"}
  ↓
GenerateAudioIntent.get_response(...)
  ↓ Audio Agent + ElevenLabsTools
Call ElevenLabs API
  ↓
Save: audio_generations/uuid.mp3
  ↓
Read file → base64
  ↓
HTML <audio controls>...</audio>
  ↓
Streamlit display audio player
```

---

## 🎯 Điểm mạnh của kiến trúc

### **1. Separation of Concerns**

- Mỗi intent có file riêng
- Logic tách biệt, dễ maintain

### **2. Extensibility**

- Thêm intent mới: Tạo file → Implement BaseIntent → Register
- Không cần sửa main logic

### **3. Registry Pattern**

- Quản lý tập trung
- Dynamic loading
- Caching instances

### **4. Context Awareness**

- Lịch sử chat làm context
- Intent analyzer xem xét context
- General chat sử dụng context

### **5. Error Handling**

- Graceful fallback
- Informative error messages
- Debug logging

### **6. Scalability**

- Session state caching
- Agent reuse
- File-based audio storage

---

## 📦 Dependencies

### **Core:**

- `streamlit`: UI framework
- `agno`: Agent framework (Gemini)
- `python-dotenv`: Environment variables

### **Optional (cho audio):**

- `elevenlabs`: TTS API
- `firecrawl`: Web scraping

### **External APIs:**

- **Gemini AI**: Chat, Intent analysis, Image prompts
- **Pollinations.ai**: Image generation (free, no key)
- **ElevenLabs**: Text-to-Speech (requires API key)

---

## 🚀 Cách mở rộng

### **Thêm intent mới:**

1. **Tạo file** `intents/new_intent.py`:

```python
class NewIntent(BaseIntent):
    intent_name = "new_intent"
    system_prompt = "..."

    def get_response(data, context):
        # Logic của bạn
        return "Response"
```

2. **Register** trong `intent_registry.py`:

```python
self.register_intent("new_intent", NewIntent)
```

3. **Update** Intent Analyzer prompt trong `main_chatbot.py`:

```python
SYSTEM_INTENT_PROMPT = """
...
4. new_intent: Mô tả khi nào dùng
...
"""
```

4. **Done!** Intent tự động xuất hiện trong sidebar và hoạt động

---

## 🎨 UI Components

### **Streamlit Features Used:**

- `st.chat_message()`: Hiển thị tin nhắn (user/assistant)
- `st.chat_input()`: Ô nhập liệu tự động xử lý submit
- `st.markdown(unsafe_allow_html=True)`: Render HTML (audio player, images)
- `st.sidebar`: Thông tin và metrics
- `st.session_state`: Cache chatbot instance
- `st.spinner()`: Loading indicator

### **HTML Components:**

- `<audio controls>`: Audio player
- `<a download>`: Download button
- `![...]()`: Markdown images
- Base64 data URLs: Embed audio/images

---

## 📝 Configuration

### **Environment Variables (.env):**

```env
GEMINI_API_KEY=your_gemini_key
ELEVEN_LABS_API_KEY=your_elevenlabs_key  # Optional
FIRECRAWL_API_KEY=your_firecrawl_key     # Optional
```

### **File Storage:**

- `chat_history.json`: Lịch sử chat (JSON)
- `audio_generations/`: Audio files (MP3)

---

## 🔍 Debug & Logging

### **Debug outputs trong console:**

- Intent analysis results
- Audio object structure
- File paths
- API responses

### **Streamlit error display:**

- API key missing
- Quota exceeded
- Dependencies not installed

---

## 🎯 Performance Optimizations

1. **Session State Caching**: Tránh reinit MainChatbot
2. **Agent Reuse**: Intent agents được reuse
3. **Intent Instance Caching**: Registry cache instances
4. **File-based Audio**: Không load toàn bộ vào memory

---

## 📊 Metrics & Monitoring

**Sidebar hiển thị:**

- Số tin nhắn đã chat
- Intent handlers có sẵn
- Status của từng intent

---

**End of Flow Documentation** 🎉
