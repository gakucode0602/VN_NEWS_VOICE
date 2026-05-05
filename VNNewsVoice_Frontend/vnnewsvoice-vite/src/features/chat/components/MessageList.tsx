import { useEffect, useRef, useState, useCallback } from "react";
import { UIChatMessage } from "../../../types/chat";
import { MessageBubble } from "./MessageBubble";

export const MessageList = (props: { messages: UIChatMessage[] }) => {

    const containerRef = useRef<HTMLDivElement>(null);
    const [isAutoScroll, setIsAutoScroll] = useState(true);

    const handleScroll = useCallback(() => {
        if (!containerRef.current) return;
        const { scrollTop, scrollHeight, clientHeight } = containerRef.current;

        // Nếu người dùng cuộn lên trên (cách đáy > 150px) thì TẮT tự động cuộn
        const isNearBottom = scrollHeight - scrollTop - clientHeight < 150;
        setIsAutoScroll(isNearBottom);
    }, []);

    useEffect(() => {
        if (!isAutoScroll || !containerRef.current) return;
        // Dùng scrollTop thay vì scrollIntoView để follow ngay lập tức theo từng dòng
        containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }, [props.messages, isAutoScroll]);

    return (
        <div
            ref={containerRef}
            onScroll={handleScroll}
            className="h-100 overflow-y-auto w-100"
        >
            <div className="p-4 d-flex flex-column gap-3 mx-auto" style={{ maxWidth: '800px' }}>
                {props.messages.length === 0 ? (
                    <div className="text-center text-muted mt-5">
                        <h5>VNNewsVoice AI</h5>
                        <p>Tôi có thể giúp bạn tìm kiếm và tổng hợp tin tức hôm nay!</p>
                    </div>
                ) : (
                    props.messages.map((message) => (
                        <MessageBubble key={message.id} message={message} />
                    ))
                )}
            </div>
        </div>
    );
};