import { ChatRequest, SourceInfo, ConversationSummary } from "../types/chat";
import { RAG_API_BASE_URL, getAccessToken, ragApiGet } from "./apiClient";

// Định nghĩa 2 loại Event mà SSE sẽ trả về cho Frontend UI
export type StreamEvent =
    | { type: 'text'; content: string }
    | { type: 'sources'; sources: SourceInfo[] }
    | { type: 'conv_id'; id: string };

const parseJsonSafely = (raw: string): unknown => {
    try {
        return JSON.parse(raw);
    } catch {
        return null;
    }
};

const parseSseBlock = (block: string): { eventType: string; data: string } | null => {
    const lines = block.split(/\r?\n/);
    let eventType = 'message';
    const dataLines: string[] = [];

    for (const line of lines) {
        if (!line) continue;
        if (line.startsWith(':')) continue;

        if (line.startsWith('event:')) {
            eventType = line.slice(6).trim() || 'message';
            continue;
        }

        if (line.startsWith('data:')) {
            let value = line.slice(5);
            if (value.startsWith(' ')) {
                value = value.slice(1);
            }
            dataLines.push(value);
        }
    }

    if (dataLines.length === 0) {
        return null;
    }

    return {
        eventType,
        data: dataLines.join('\n'),
    };
};

export async function* streamChat(
    request: ChatRequest
): AsyncGenerator<StreamEvent, void, unknown> {

    // 1. Convert Camel Case (React) -> Snake Case (Python FastAPI)
    const apiRequest = {
        query: request.query,
        conversation_id: request.conversationId,
        top_k: request.topK,
        filters: request.filters
    };

    // 2. Native fetch() is required for SSE streaming — Axios does not support it
    const token = getAccessToken();
    const response = await fetch(`${RAG_API_BASE_URL}/stream`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token ?? ''}`
        },
        body: JSON.stringify(apiRequest)
    });

    if (!response.ok) {
        throw new Error(`RAG API Error: ${response.status} ${response.statusText}`);
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Decode Uint8Array bytes into string payload
        buffer += decoder.decode(value, { stream: true });

        // SSE format separates distinct events with double newlines
        let boundary = buffer.indexOf('\n\n');

        while (boundary !== -1) {
            const part = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2); // Cắt phần đã xử lý ra khỏi buffer

            if (!part) {
                boundary = buffer.indexOf('\n\n');
                continue;
            }

            const parsedBlock = parseSseBlock(part);
            if (!parsedBlock) {
                boundary = buffer.indexOf('\n\n');
                continue;
            }

            const { eventType, data } = parsedBlock;

            // New structured protocol (preferred): event + JSON payload
            if (eventType === 'done') {
                return;
            }

            if (eventType === 'error') {
                const payload = parseJsonSafely(data) as { message?: string } | null;
                throw new Error(payload?.message || data || 'Streaming error');
            }

            if (eventType === 'conversation') {
                const payload = parseJsonSafely(data) as { id?: string } | null;
                const convId = payload?.id?.trim();
                if (convId) {
                    yield { type: 'conv_id', id: convId };
                }
                boundary = buffer.indexOf('\n\n');
                continue;
            }

            if (eventType === 'sources') {
                const payload = parseJsonSafely(data) as
                    | SourceInfo[]
                    | { sources?: SourceInfo[] }
                    | null;

                const sourcesArray = Array.isArray(payload)
                    ? payload
                    : payload?.sources ?? [];

                yield { type: 'sources', sources: sourcesArray };
                boundary = buffer.indexOf('\n\n');
                continue;
            }

            if (eventType === 'text') {
                const payload = parseJsonSafely(data) as { content?: string } | null;
                const content = payload?.content ?? data;
                if (content) {
                    yield { type: 'text', content };
                }
                boundary = buffer.indexOf('\n\n');
                continue;
            }

            // Legacy protocol fallback: plain data markers
            const eventData = data;

            // Case A: End of stream
            if (eventData === "[DONE]") {
                return;
            }

            // Case B: Backend threw an exception
            if (eventData.startsWith("[ERROR]")) {
                throw new Error(eventData.replace("[ERROR]", "").trim());
            }

            // Case C: Sources metadata payload
            if (eventData.startsWith("[SOURCES]")) {
                const jsonStr = eventData.replace("[SOURCES]", "");
                const sourcesArray = JSON.parse(jsonStr) as SourceInfo[];
                yield { type: 'sources', sources: sourcesArray };

                boundary = buffer.indexOf('\n\n');
                continue;
            }

            // Case D: Conversation ID payload
            if (eventData.startsWith("[CONVERSATION_ID]")) {
                const convId = eventData.replace("[CONVERSATION_ID]", "").trim();
                yield { type: 'conv_id', id: convId };

                boundary = buffer.indexOf('\n\n');
                continue;
            }

            // Case E: Standard text character token (Giữ nguyên khoảng trắng và \n)
            yield { type: 'text', content: eventData };

            boundary = buffer.indexOf('\n\n');
        }
    }
}

export interface HistoricalMessage {
    role: 'USER' | 'ASSISTANT';
    content: string;
    created_at: string;
}

/** Fetch all messages for a conversation — uses ragApiClient (auth auto-attached). */
export function fetchConversationMessages(conversationId: string): Promise<HistoricalMessage[]> {
    return ragApiGet<HistoricalMessage[]>(`/conversations/${conversationId}/messages`);
}

/** Fetch list of conversations for the current user. */
export function fetchConversations(): Promise<ConversationSummary[]> {
    return ragApiGet<ConversationSummary[]>('/conversations');
}
