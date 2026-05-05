import { useState, useCallback } from 'react';
import { ChatSideBar } from '../components/ChatSideBar';
import { ChatArea } from '../components/ChatArea';
import { useChat } from '../hooks/useChat';
import { useConversations } from '../hooks/useConversations';
import { fetchConversationMessages } from '../../../services/chat.service';

const ChatPage = () => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const {
        messages,
        isLoading,
        isStreaming,
        conversationId,
        sendMessage,
        resetChat,
        setMessages,
        setConversationId,
    } = useChat();

    const { conversations, isLoading: convLoading, error: convError, refetch } = useConversations();

    // Wrap sendMessage: refresh sidebar after stream ends so new conversation appears
    const handleSendMessage = useCallback(async (text: string) => {
        await sendMessage(text);
        refetch();
    }, [sendMessage, refetch]);

    const handleSelectConversation = async (id: string) => {
        resetChat();
        setConversationId(id);

        try {
            const history = await fetchConversationMessages(id);
            const uiMessages = history.map((msg, idx) => ({
                id: `hist-${idx}`,
                role: msg.role?.toUpperCase() === 'USER' ? 'user' as const : 'assistant' as const,
                content: msg.content,
                isStreaming: false,
            }));
            setMessages(uiMessages);
        } catch (err) {
            console.error('Failed to load conversation history:', err);
        }
    };

    return (
        <div className="d-flex bg-light overflow-hidden" style={{ height: 'calc(100vh - 160px)', minHeight: '500px' }}>
            {/* Cột trái (Sidebar) */}
            <div
                className={`border-end bg-white overflow-y-auto flex-shrink-0 ${isSidebarOpen ? 'd-block' : 'd-none'}`}
                style={{ width: '300px' }}
            >
                <ChatSideBar
                    isOpen={isSidebarOpen}
                    onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
                    activeConversationId={conversationId}
                    onSelectConversation={handleSelectConversation}
                    onNewChat={resetChat}
                    conversations={conversations}
                    isLoading={convLoading}
                    error={convError}
                />
            </div>

            {/* Cột phải (Khu vực Chat Chính) */}
            <div className='flex-grow-1 d-flex flex-column overflow-hidden'>
                <ChatArea
                    messages={messages}
                    isLoading={isLoading}
                    isStreaming={isStreaming}
                    onSendMessage={handleSendMessage}
                />
            </div>
        </div>
    );
};

export default ChatPage;

