# 🤖 AI Chatbot Assistant

Chatbot AI thông minh với khả năng trò chuyện và tạo hình ảnh sử dụng Google Gemini.

## ✨ Tính năng chính

- **💬 Chatbot thông minh**: Trò chuyện tự nhiên về cuộc sống, công nghệ, học tập
- **🖼️ Tạo hình ảnh**: Tạo hình ảnh từ mô tả văn bản (sử dụng pollinations.ai)
- **🎯 Phân tích ý định**: Tự động nhận diện ý định người dùng (chat hoặc tạo ảnh)
- **❓ Trả lời câu hỏi**: Đưa ra câu trả lời hữu ích và chính xác
- **💾 Lịch sử chat**: Lưu trữ và hiển thị lịch sử cuộc trò chuyện
- **🎯 Lệnh đặc biệt**: Hỗ trợ các lệnh như hello, help, clear
- **🌐 Tiếng Việt**: Hỗ trợ đầy đủ tiếng Việt
- **🔧 Dễ sử dụng**: Giao diện đơn giản với Streamlit

## 🚀 Cài đặt và Chạy

### 1. Cài đặt Dependencies

```bash
cd chatbot
pip install -r requirements.txt
```

### 2. Cấu hình API Key

```bash
# Copy file cấu hình mẫu
cp env.example .env

# Chỉnh sửa file .env với API key của bạn
GEMINI_API_KEY=your_gemini_api_key_here
```

**Lấy API Key:**

- **Gemini API Key**: Đăng ký tại [Google AI Studio](https://aistudio.google.com/)
- Hoàn toàn miễn phí với 1,500 requests/ngày

### 3. Chạy Chatbot

```bash
# Từ thư mục chatbot
streamlit run app.py

# Hoặc chạy trực tiếp
python -m src.main_chatbot
```

## 🎯 Cách sử dụng

### Chat thông thường

- Gửi tin nhắn bất kỳ để trò chuyện
- Chatbot sẽ trả lời một cách thân thiện và hữu ích

### Lệnh đặc biệt

```
hello, hi, xin chào  → Hiển thị lời chào và giới thiệu
help, giúp đỡ        → Hiển thị hướng dẫn sử dụng
clear, xóa lịch sử   → Hướng dẫn xóa lịch sử chat
```

### Tạo hình ảnh

Chatbot có khả năng **phân tích ý định** và tự động nhận diện khi bạn muốn tạo hình ảnh:

**Cách tạo hình ảnh:**

- Nói "vẽ", "tạo hình", "generate image", "vẽ cho tôi"
- Mô tả chi tiết hình ảnh bạn muốn
- Chatbot sẽ phân tích và tạo hình ảnh sử dụng AI

**Ví dụ tạo hình ảnh:**

```
👤 Bạn: Vẽ cho tôi một con chó cute đang chơi đùa
🤖 Bot: 🖼️ **Hình ảnh được tạo:**

         ![Generated Image](https://image.pollinations.ai/prompt/...)

         *Từ mô tả: con chó cute đang chơi đùa*
```

### Ví dụ cuộc trò chuyện:

```
👤 Bạn: Xin chào
🤖 Bot: 👋 Xin chào! Tôi là AI Chatbot Assistant
         Tôi có thể giúp bạn với: ...

👤 Bạn: Kể về trí tuệ nhân tạo
🤖 Bot: Trí tuệ nhân tạo (AI) là một lĩnh vực của khoa học máy tính...
```

## 📁 Cấu trúc Dự án

```
chatbot/
├── app.py                 # Entry point chính
├── requirements.txt       # Dependencies Python
├── env.example           # Mẫu cấu hình API keys
├── README.md             # Tài liệu này
├── test_structure.py     # Script test cấu trúc
├── demo.py              # Script demo (cần API key)
└── src/
    ├── __init__.py       # Python package
    └── main_chatbot.py   # Logic chính của chatbot
```

## 🔑 API Keys Cần thiết

| API Key          | Yêu cầu     | Mục đích                            |
| ---------------- | ----------- | ----------------------------------- |
| `GEMINI_API_KEY` | ✅ Bắt buộc | Chatbot chính sử dụng Google Gemini |

## 🛠️ Tính năng Kỹ thuật

### Framework sử dụng:

- **Agno**: Agent framework để quản lý AI
- **Streamlit**: Web UI framework
- **Google Gemini 2.0 Flash**: AI model chính (miễn phí)

### Tính năng chính:

- **Intent Analysis**: Phân tích ý định người dùng (chat hoặc tạo ảnh)
- **Image Generation**: Tạo hình ảnh từ text prompt sử dụng pollinations.ai
- **Chat Persistence**: Lưu trữ lịch sử chat trong JSON
- **Context Awareness**: Sử dụng ngữ cảnh hội thoại để trả lời tốt hơn
- **Error Handling**: Xử lý lỗi graceful và quota exceeded
- **Responsive UI**: Giao diện thân thiện với Streamlit
- **Command Processing**: Xử lý lệnh đặc biệt
- **Vietnamese Support**: Hỗ trợ đầy đủ tiếng Việt

## 🧪 Testing

### Test cấu trúc (không cần API key):

```bash
python test_structure.py
```

### Test demo (cần API key):

```bash
python demo.py
```

## 🤝 Đóng góp

1. Fork dự án
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📝 License

Dự án này sử dụng MIT License.

## ⚠️ Lưu ý

- Chỉ cần 1 API key duy nhất (Gemini) để chạy chatbot
- Gemini cung cấp 1,500 requests miễn phí mỗi ngày
- Chatbot hoạt động hoàn toàn offline sau khi có API key
- Lịch sử chat được lưu trữ cục bộ

## 🆘 Hỗ trợ

Nếu gặp vấn đề:

1. Kiểm tra console logs để xem lỗi chi tiết
2. Đảm bảo đã cài đặt đúng dependencies
3. Kiểm tra API key có hợp lệ không
4. Chạy `python test_structure.py` để kiểm tra cấu trúc

---

**Tạo bởi AI Assistant Team** 🤖✨
