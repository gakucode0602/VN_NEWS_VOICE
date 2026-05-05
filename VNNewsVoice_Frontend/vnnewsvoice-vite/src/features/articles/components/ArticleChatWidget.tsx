import { useState, useCallback, useEffect } from 'react';
import { useChat } from '../../chat/hooks/useChat';
import { MessageBubble } from '../../chat/components/MessageBubble';
import { ChatInput } from '../../chat/components/ChatInput';
import { UIChatMessage } from '../../../types/chat';

interface ArticleChatWidgetProps {
    articleId: string;
    articleTitle: string;
}

export const ArticleChatWidget = ({ articleId, articleTitle }: ArticleChatWidgetProps) => {
    const [isOpen, setIsOpen] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);
    const { messages, isLoading, isStreaming, sendMessage, resetChat } = useChat();

    // Wrap sendMessage: always pass article_id as a filter so RAG restricts to this article
    const handleSend = useCallback(async (text: string) => {
        await sendMessage(text, { article_id: articleId });
    }, [sendMessage, articleId]);

    const handleToggle = () => {
        setIsOpen(prev => !prev);
    };

    const handleResetChat = useCallback(() => {
        resetChat();
    }, [resetChat]);

    const handleToggleExpand = useCallback(() => {
        setIsExpanded(prev => !prev);
    }, []);

    useEffect(() => {
        // Clear chat state when leaving this article page.
        return () => {
            resetChat();
        };
    }, [resetChat]);

    const panelWidth = isExpanded ? 'min(96vw, 960px)' : '380px';
    const panelHeight = isExpanded ? 'min(88vh, 820px)' : '520px';
    const panelBottom = isExpanded ? '16px' : '96px';

    return (
        <>
            {/* Floating Action Button */}
            <button
                onClick={handleToggle}
                className="btn btn-primary shadow-lg rounded-circle d-flex align-items-center justify-content-center"
                style={{
                    position: 'fixed',
                    bottom: '28px',
                    right: '28px',
                    width: '56px',
                    height: '56px',
                    zIndex: 1050,
                    fontSize: '1.25rem',
                    transition: 'transform 0.2s',
                }}
                title="Hỏi AI về bài này"
            >
                {isOpen ? '✕' : '💬'}
            </button>

            {/* Chat Panel — slide in from right */}
            <div
                style={{
                    position: 'fixed',
                    bottom: panelBottom,
                    right: '24px',
                    width: panelWidth,
                    height: panelHeight,
                    zIndex: 1049,
                    display: 'flex',
                    flexDirection: 'column',
                    borderRadius: isExpanded ? '18px' : '16px',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
                    background: '#fff',
                    overflow: 'hidden',
                    transform: isOpen ? 'translateY(0) scale(1)' : 'translateY(20px) scale(0.97)',
                    opacity: isOpen ? 1 : 0,
                    pointerEvents: isOpen ? 'all' : 'none',
                    transition: 'transform 0.25s ease, opacity 0.2s ease',
                }}
            >
                {/* Header */}
                <div
                    className="d-flex align-items-center gap-2 px-3 py-2 border-bottom"
                    style={{ background: '#0d6efd', color: '#fff', flexShrink: 0 }}
                >
                    <span style={{ fontSize: '1.1rem' }}>🤖</span>
                    <div className="flex-grow-1 overflow-hidden">
                        <div className="fw-semibold small">VNNewsVoice AI</div>
                        <div
                            className="text-truncate"
                            style={{ fontSize: '0.7rem', opacity: 0.85, maxWidth: '260px' }}
                            title={articleTitle}
                        >
                            📰 {articleTitle}
                        </div>
                    </div>
                    <button
                        className="btn btn-sm text-white p-0"
                        style={{ opacity: 0.8, fontSize: '1rem', lineHeight: 1 }}
                        onClick={handleToggleExpand}
                        title={isExpanded ? 'Thu nhỏ khung chat' : 'Phóng to khung chat'}
                    >
                        {isExpanded ? '🗗' : '🗖'}
                    </button>
                    <button
                        className="btn btn-sm text-white p-0"
                        style={{ opacity: 0.8, fontSize: '1rem', lineHeight: 1 }}
                        onClick={handleResetChat}
                        title="Xóa cuộc trò chuyện"
                    >
                        🗑
                    </button>
                </div>

                {/* Messages */}
                <div className="flex-grow-1 overflow-y-auto p-3 d-flex flex-column gap-2">
                    {messages.length === 0 ? (
                        <div className="text-center text-muted mt-4">
                            <div style={{ fontSize: '2rem' }}>📰</div>
                            <p className="small mt-2">
                                Hỏi tôi bất cứ điều gì về bài viết này!
                            </p>
                            <div className="d-flex flex-wrap gap-2 justify-content-center mt-3">
                                {[
                                    'Bài này nói về điều gì?',
                                    'Sự kiện xảy ra ở đâu?',
                                    'Ai là nhân vật chính?',
                                ].map(suggestion => (
                                    <button
                                        key={suggestion}
                                        className="btn btn-outline-primary btn-sm rounded-pill"
                                        style={{ fontSize: '0.75rem' }}
                                        onClick={() => handleSend(suggestion)}
                                    >
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        messages.map((msg: UIChatMessage) => (
                            <MessageBubble key={msg.id} message={msg} compact />
                        ))
                    )}
                </div>

                {/* Input */}
                <div className="border-top p-2" style={{ flexShrink: 0 }}>
                    <ChatInput
                        onSendMessage={handleSend}
                        disabled={isLoading || isStreaming}
                        placeholder="Hỏi về bài viết này..."
                    />
                </div>
            </div>
        </>
    );
};
