import * as React from "react";
import { UIChatMessage } from "../../../types/chat";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export const MessageBubble = React.memo(({ message, compact = false }: { message: UIChatMessage; compact?: boolean }) => {

    // Nếu là User: Lề phải, nền xanh, chữ trắng
    if (message.role === 'user') {
        return (
            <div className="d-flex justify-content-end mb-3">
                <div className="bg-primary text-white p-3 rounded-4 shadow-sm" style={{ maxWidth: '80%' }}>
                    <div className="text-break" style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
                </div>
            </div>
        );
    }

    // Nếu là AI: Lề trái, không nền, avatar
    return (
        <div className="d-flex justify-content-start mb-4 w-100">
            {/* AI Avatar */}
            <div
                className={`rounded-circle bg-dark text-white d-flex align-items-center justify-content-center flex-shrink-0 me-2 shadow-sm mt-1`}
                style={{ width: compact ? '28px' : '35px', height: compact ? '28px' : '35px' }}
            >
                <span className="small fw-bold">AI</span>
            </div>

            <div className="text-dark w-100" style={{ maxWidth: '85%' }}>
                {/* 1. Phần Nội dung (Render Markdown) */}
                <div className="markdown-body">
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            // Headings: scale down to reasonable sizes for chat context
                            h1: ({ ...props }) => <p className="fw-bold mb-2" style={{ fontSize: '1rem' }} {...props} />,
                            h2: ({ ...props }) => <p className="fw-bold mb-2" style={{ fontSize: '0.95rem' }} {...props} />,
                            h3: ({ ...props }) => <p className="fw-semibold mb-1" style={{ fontSize: '0.9rem' }} {...props} />,
                            p: ({ ...props }) => <p className="mb-2" style={{ lineHeight: '1.6' }} {...props} />,
                            a: ({ ...props }) => <a className="text-primary text-decoration-none fw-semibold" target="_blank" {...props} />,
                            ul: ({ ...props }) => <ul className="ps-3 mb-2" {...props} />,
                            ol: ({ ...props }) => <ol className="ps-3 mb-2" {...props} />,
                            li: ({ ...props }) => <li className="mb-1" {...props} />,
                            code: ({ className, children, ...props }) => {
                                const match = /language-(\w+)/.exec(className || '');
                                return match ? (
                                    <pre className="bg-dark text-light p-3 rounded-3 overflow-auto my-2 shadow-sm">
                                        <code className={className} {...props}>{children}</code>
                                    </pre>
                                ) : (
                                    <code className="bg-light text-danger px-2 py-1 rounded-2 small" style={{ fontFamily: 'monospace' }} {...props}>
                                        {children}
                                    </code>
                                )
                            }
                        }}
                    >
                        {message.content}
                    </ReactMarkdown>

                    {/* Hiệu ứng nhấp nháy khi đang Stream */}
                    {message.isStreaming && (
                        <span className="d-inline-block bg-secondary ms-1" style={{ width: '8px', height: '16px', animation: 'blink 1s step-end infinite' }}></span>
                    )}
                </div>

                {/* 2. Phần Nguồn tham khảo (Sources) */}
                {message.sources && message.sources.length > 0 && !message.isStreaming && (
                    <div className="mt-3 border-top pt-2">
                        <small className="text-secondary text-uppercase fw-bold d-block mb-2">Nguồn tham khảo:</small>
                        <div className="d-flex flex-wrap gap-2">
                            {message.sources.map((src, idx) => (
                                <a
                                    key={idx}
                                    href={src.url || '#'}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="btn btn-outline-secondary btn-sm text-start text-truncate d-flex align-items-center"
                                    style={{ maxWidth: '250px', borderRadius: '20px' }}
                                    title={src.title}
                                >
                                    <span className="me-2">📄</span>
                                    <span className="text-truncate">{src.title}</span>
                                </a>
                            ))}
                        </div>
                    </div>
                )}
            </div>
            {/* Inline style for the blinking cursor */}
            <style>
                {`@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }`}
            </style>
        </div>
    );
});
