import { useCallback, useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { API_BASE_URL, api } from "../../../api/client";
import { getTokens } from "../../../auth/tokenStore";
import type { components } from "../../../api/schema";

type DatePromptChoice = components["schemas"]["DatePromptChoice"];
type DateOutcome = components["schemas"]["DateOutcome"];
type Message = components["schemas"]["MessageOut"];

export function useConversation(matchId: string) {
  return useQuery({
    queryKey: ["conversation", matchId],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/matches/{match_id}/conversation", {
        params: { path: { match_id: matchId } },
      });
      if (error) throw error;
      return data;
    },
    enabled: Boolean(matchId),
    // Realtime delivery/broadcast comes from useConversationSocket (ADR-0002 WS transport);
    // this query just seeds the initial history.
  });
}

type SocketStatus = "connecting" | "open" | "closed";

function socketUrl(matchId: string, token: string) {
  const base = API_BASE_URL.replace(/^http/, "ws");
  return `${base}/v1/matches/${matchId}/ws?token=${encodeURIComponent(token)}`;
}

/** Opens the realtime conversation socket and streams incoming messages into the query cache. */
export function useConversationSocket(matchId: string) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<SocketStatus>("connecting");
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!matchId) return;
    let cancelled = false;
    let retryDelay = 1000;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let socket: WebSocket | null = null;

    function connect() {
      const tokens = getTokens();
      if (!tokens || cancelled) return;
      setStatus("connecting");
      socket = new WebSocket(socketUrl(matchId, tokens.accessToken));
      socketRef.current = socket;

      socket.onopen = () => {
        retryDelay = 1000;
        if (cancelled) return;
        setStatus("open");
        // Catches up on anything sent while disconnected (e.g. app backgrounded).
        queryClient.invalidateQueries({ queryKey: ["conversation", matchId] });
      };
      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        if (payload.type !== "message") return;
        const message = payload.data as Message;
        queryClient.setQueryData(["conversation", matchId], (prev: any) => {
          if (!prev) return prev;
          if (prev.messages.some((m: Message) => m.id === message.id)) return prev;
          return { ...prev, messages: [...prev.messages, message] };
        });
      };
      socket.onclose = () => {
        socketRef.current = null;
        if (cancelled) return;
        setStatus("closed");
        retryTimer = setTimeout(connect, retryDelay);
        retryDelay = Math.min(retryDelay * 2, 10000);
      };
      socket.onerror = () => socket?.close();
    }

    connect();

    return () => {
      cancelled = true;
      if (retryTimer) clearTimeout(retryTimer);
      socket?.close();
      socketRef.current = null;
    };
  }, [matchId, queryClient]);

  const sendMessage = useCallback((body: string) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return false;
    socket.send(JSON.stringify({ body }));
    return true;
  }, []);

  return { status, sendMessage };
}

export function useTriggerDatePrompt(matchId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data, error } = await api.POST("/v1/matches/{match_id}/date-prompt", {
        params: { path: { match_id: matchId } },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matches", matchId] });
    },
  });
}

export function useDatePromptState(matchId: string) {
  return useQuery({
    queryKey: ["date-prompt", matchId],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/matches/{match_id}/date-prompt", {
        params: { path: { match_id: matchId } },
      });
      if (error) throw error;
      return data;
    },
    enabled: Boolean(matchId),
  });
}

export function useSubmitDatePromptResponse(matchId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (choice: DatePromptChoice) => {
      const { data, error } = await api.POST("/v1/matches/{match_id}/date-prompt/response", {
        params: { path: { match_id: matchId } },
        body: { choice },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["date-prompt", matchId], data);
      queryClient.invalidateQueries({ queryKey: ["matches", matchId] });
    },
  });
}

export function useSubmitAvailability(matchId: string) {
  return useMutation({
    mutationFn: async (slots: string[]) => {
      const { data, error } = await api.POST("/v1/matches/{match_id}/availability", {
        params: { path: { match_id: matchId } },
        body: { slots },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function useVenueRecommendations(matchId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["venue-recommendations", matchId],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/matches/{match_id}/venue-recommendations", {
        params: { path: { match_id: matchId } },
      });
      if (error) throw error;
      return data;
    },
    enabled: Boolean(matchId) && enabled,
  });
}

export function useCreateDatePlan(matchId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { venue_name: string; venue_address?: string; scheduled_at: string }) => {
      const { data, error } = await api.POST("/v1/matches/{match_id}/date-plan", {
        params: { path: { match_id: matchId } },
        body,
      });
      if (error) throw error;
      return data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["date-plan", matchId], data);
    },
  });
}

export function useRecordDateOutcome(matchId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (outcome: DateOutcome) => {
      const { data, error } = await api.POST("/v1/matches/{match_id}/date-plan/outcome", {
        params: { path: { match_id: matchId } },
        body: { outcome },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["date-plan", matchId], data);
    },
  });
}
