export interface SourceInfo {
    article_id: string;
    title: string;
    url: string | null;
    published_at: string | null;
    relevance_score: number;
}

export interface ChatResponse {
    query: string;
    answer: string;
    conversationId: string;
    sources: SourceInfo[];
    retrievalTimeMs: number;
    generationTimeMs: number;
    totalTimeMs: number;
}

export interface ChatRequest {
    query: string;
    conversationId: string | null;
    topK: number;
    filters: Record<string, string>
}

export interface UIChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    isStreaming: boolean;
    sources?: SourceInfo[]
}

export interface ConversationSummary {
    id: string;
    title: string;
    updated_at: string;
}
