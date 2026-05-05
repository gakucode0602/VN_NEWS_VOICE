import { useState, useCallback } from 'react';
import { streamChat } from '../../../services/chat.service';
import { UIChatMessage, ChatRequest } from '../../../types/chat';
import { getAccessToken } from '../../../services/apiClient';

export const useChat = () => {
    // Lưu trữ toàn bộ lịch sử tin nhắn hiển thị trên UI
    const [messages, setMessages] = useState<UIChatMessage[]>([]);

    // Lưu id của cuộc hội thoại để RAG Service nhớ ngữ cảnh
    const [conversationId, setConversationId] = useState<string | null>(null);

    // Trạng thái đang gọi API nhưng chưa trả về chữ nào
    const [isLoading, setIsLoading] = useState(false);

    // Trạng thái đang nhận chữ stream
    const [isStreaming, setIsStreaming] = useState(false);

    // Lỗi nếu có
    const [error, setError] = useState<string | null>(null);

    const sendMessage = useCallback(async (text: string, extraFilters?: Record<string, string>) => {
        if (!text.trim() || isStreaming || isLoading) return;

        // 1. Tạo tin nhắn của User
        const userMsgId = Date.now().toString();
        const userMessage: UIChatMessage = {
            id: userMsgId,
            role: 'user',
            content: text,
            isStreaming: false
        };

        // 2. Tạo tin nhắn "đang chờ" của Assistant
        const botMsgId = (Date.now() + 1).toString();
        const initialBotMessage: UIChatMessage = {
            id: botMsgId,
            role: 'assistant',
            content: '', // Bắt đầu trống rỗng
            isStreaming: true
        };

        // Cập nhật UI ngay lập tức
        setMessages(prev => [...prev, userMessage, initialBotMessage]);
        setIsLoading(true);
        setError(null);

        try {
            // Lấy access token từ memory auth store.
            const token = getAccessToken();
            if (!token) throw new Error("Vui lòng đăng nhập để sử dụng tính năng Chat");

            // Chuẩn bị Request payload
            const request: ChatRequest = {
                query: text,
                conversationId: conversationId,
                topK: 5,
                filters: extraFilters ?? {}
            };

            // Tiến hành Stream
            setIsLoading(false);
            setIsStreaming(true);

            // Fetch Data từ Service
            const stream = streamChat(request);

            for await (const event of stream) {
                if (event.type === 'text') {
                    // Nối thêm chữ vào tin nhắn hiện tại của bot
                    setMessages(prev => prev.map(msg =>
                        msg.id === botMsgId
                            ? { ...msg, content: msg.content + event.content }
                            : msg
                    ));
                } else if (event.type === 'sources') {
                    // Đính kèm danh sách bài báo tham khảo
                    setMessages(prev => prev.map(msg =>
                        msg.id === botMsgId
                            ? { ...msg, sources: event.sources }
                            : msg
                    ));
                } else if (event.type === 'conv_id') {
                    // Lưu lại Conversation ID do server trả về (nếu có)
                    // Server sẽ gửi cái này ở đầu luồng stream
                    setConversationId(event.id);
                }
            }

            // Hoàn tất Stream
            setMessages(prev => prev.map(msg =>
                msg.id === botMsgId
                    ? {
                        ...msg,
                        content: msg.content.trim()
                            ? msg.content
                            : "Mình chưa hiểu rõ yêu cầu. Bạn có thể hỏi cụ thể hơn về nội dung bài viết này.",
                        isStreaming: false,
                    }
                    : msg
            ));

        } catch (err: any) {
            console.error("Chat error:", err);
            setError(err.message || "Đã xảy ra lỗi khi kết nối với AI Assistant");

            // Xóa tin nhắn bot đang chờ hoặc báo lỗi thẳng vào đó
            setMessages(prev => prev.map(msg =>
                msg.id === botMsgId
                    ? { ...msg, content: `🚨 Lỗi: ${err.message}`, isStreaming: false, role: 'assistant' }
                    : msg
            ));
        } finally {
            setIsLoading(false);
            setIsStreaming(false);
        }
    }, [conversationId, isStreaming, isLoading]);

    const resetChat = useCallback(() => {
        setMessages([]);
        setConversationId(null);
        setError(null);
    }, []);

    return {
        messages,
        isLoading,
        isStreaming,
        error,
        conversationId,
        sendMessage,
        resetChat,
        // Expose setter if you need to restore history from DB later
        setMessages,
        setConversationId
    };
};
