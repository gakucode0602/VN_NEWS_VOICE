import { useState, useEffect, useCallback } from 'react';
import { ConversationSummary } from '../../../types/chat';
import { fetchConversations } from '../../../services/chat.service';

export const useConversations = () => {
    const [conversations, setConversations] = useState<ConversationSummary[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const refetch = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await fetchConversations();
            setConversations(data);
        } catch (err: any) {
            setError(err.message || 'Không thể tải lịch sử trò chuyện');
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        refetch();
    }, [refetch]);

    return { conversations, isLoading, error, refetch };
};

