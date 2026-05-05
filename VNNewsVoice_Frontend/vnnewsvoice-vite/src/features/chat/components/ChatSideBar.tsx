import { ConversationSummary } from '../../../types/chat';

interface ChatSideBarProps {
    isOpen: boolean;
    onToggle: () => void;
    activeConversationId: string | null;
    onSelectConversation: (id: string) => void;
    onNewChat: () => void;
    conversations: ConversationSummary[];
    isLoading: boolean;
    error: string | null;
}

export const ChatSideBar = ({
    activeConversationId,
    onSelectConversation,
    onNewChat,
    conversations,
    isLoading,
    error,
}: ChatSideBarProps) => {
    return (
        <div className="p-3 h-100 d-flex flex-column">
            {/* Header */}
            <div className="d-flex align-items-center justify-content-between border-bottom pb-3 mb-3">
                <h6 className="text-primary fw-bold mb-0">Lịch sử trò chuyện</h6>
                <button
                    className="btn btn-sm btn-primary rounded-pill px-3"
                    onClick={onNewChat}
                    title="Cuộc trò chuyện mới"
                >
                    + Mới
                </button>
            </div>

            {/* Conversation list */}
            <div className="flex-grow-1 overflow-y-auto">
                {isLoading && (
                    <div className="text-center text-muted small py-3">
                        <div className="spinner-border spinner-border-sm me-2" role="status" />
                        Đang tải...
                    </div>
                )}

                {error && (
                    <div className="text-danger small px-2">{error}</div>
                )}

                {!isLoading && !error && conversations.length === 0 && (
                    <p className="text-muted small text-center mt-3">Chưa có cuộc trò chuyện nào.</p>
                )}

                <div className="d-flex flex-column gap-1">
                    {conversations.map((conv: ConversationSummary) => (
                        <button
                            key={conv.id}
                            className={`btn btn-sm text-start text-truncate rounded-3 px-3 py-2 ${activeConversationId === conv.id
                                ? 'btn-primary text-white'
                                : 'btn-light text-dark'
                                }`}
                            onClick={() => onSelectConversation(conv.id)}
                            title={conv.title}
                        >
                            <span className="d-block text-truncate" style={{ maxWidth: '220px' }}>
                                {conv.title}
                            </span>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};


