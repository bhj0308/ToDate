import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../../api/client";
import type { components } from "../../../api/schema";

type IncomePercentileTier = components["schemas"]["IncomePercentileTier"];

export type DiscoveryFilters = {
  min_income_tier?: IncomePercentileTier;
  education_level?: string;
};

export function useDiscoveryFeed(filters: DiscoveryFilters = {}) {
  return useQuery({
    queryKey: ["discovery", filters],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/discovery", {
        params: { query: filters },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function useCreateMatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (targetUserId: string) => {
      const { data, error } = await api.POST("/v1/matches", {
        body: { target_user_id: targetUserId },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matches"] });
    },
  });
}

export function useMatches() {
  return useQuery({
    queryKey: ["matches"],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/matches");
      if (error) throw error;
      return data;
    },
  });
}

export function useMatch(matchId: string) {
  return useQuery({
    queryKey: ["matches", matchId],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/matches/{match_id}", {
        params: { path: { match_id: matchId } },
      });
      if (error) throw error;
      return data;
    },
    enabled: Boolean(matchId),
  });
}
