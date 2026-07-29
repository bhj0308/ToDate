import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../../api/client";
import type { components } from "../../../api/schema";

type DatePromptChoice = components["schemas"]["DatePromptChoice"];
type DateOutcome = components["schemas"]["DateOutcome"];

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
    // No WebSocket transport yet (see ADR-0002) — poll while the screen is open.
    refetchInterval: 5000,
  });
}

export function useSendMessage(matchId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: string) => {
      const { data, error } = await api.POST("/v1/matches/{match_id}/messages", {
        params: { path: { match_id: matchId } },
        body: { body },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversation", matchId] });
    },
  });
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
