import React, { useState, useCallback } from "react";

export const ChatInput = React.memo(({ onSendMessage, disabled, placeholder }: {
    onSendMessage: (text: string) => void;
    disabled: boolean;
    placeholder?: string;
}) => {
    const [text, setText] = useState<string>('');

    const sendMessage = useCallback((textStr: string) => {
        if (textStr.trim() && !disabled) {
            onSendMessage(textStr);
            setText('');
        }
    }, [onSendMessage, disabled]);

    return (
        <div className="d-flex gap-2 align-items-end mx-auto" style={{ maxWidth: '800px' }}>
            <textarea
                className="form-control rounded-4 shadow-sm"
                style={{ resize: 'none', maxHeight: '150px' }}
                rows={1}
                placeholder={placeholder ?? "Nhắn tin cho VNNewsVoice AI..."}
                value={text}
                onChange={(e) => {
                    setText(e.target.value);
                }}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage(text);
                    }
                }}
                disabled={disabled}
            />
            <button
                onClick={() => sendMessage(text)}
                disabled={disabled || !text.trim()}
                className="btn btn-primary rounded-circle shadow-sm d-flex justify-content-center align-items-center"
                style={{ width: '45px', height: '45px', flexShrink: 0 }}
            >
                {/* SVG icon for send */}
                <svg width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M15.854.146a.5.5 0 0 1 .11.54l-5.819 14.547a.75.75 0 0 1-1.329.124l-3.178-4.995L.643 7.184a.75.75 0 0 1 .124-1.33L15.314.037a.5.5 0 0 1 .54.11ZM6.636 10.07l2.761 4.338L14.13 2.576 6.636 10.07Zm6.787-8.201L1.591 6.602l4.339 2.76 7.494-7.493Z" />
                </svg>
            </button>
        </div>
    );
});