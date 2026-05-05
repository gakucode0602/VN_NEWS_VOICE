import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { UIChatMessage } from '../../../types/chat';

interface ChatAreaProps {
    messages: UIChatMessage[];
    isLoading: boolean;
    isStreaming: boolean;
    onSendMessage: (text: string) => Promise<void>;
}

export const ChatArea = ({ messages, isLoading, isStreaming, onSendMessage }: ChatAreaProps) => {
    return (
        <div className="flex-grow-1 d-flex flex-column h-100 bg-white position-relative overflow-hidden">
            {/* Khung hiển thị tin nhắn */}
            <div className="flex-grow-1 overflow-hidden">
                <MessageList messages={messages} />
            </div>

            {/* Khung gõ chat */}
            <div className="p-3 border-top bg-white flex-shrink-0">
                <ChatInput
                    onSendMessage={onSendMessage}
                    disabled={isLoading || isStreaming}
                />
            </div>
        </div>
    );
};

