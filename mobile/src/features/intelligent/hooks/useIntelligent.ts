import { useQuery } from "@tanstack/react-query";

import { api } from "../../../api/client";

export function useCoachingInsights(matchId: string) {
  return useQuery({
    queryKey: ["coaching-insights", matchId],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/matches/{match_id}/coaching-insights", {
        params: { path: { match_id: matchId } },
      });
      if (error) throw error;
      return data;
    },
    enabled: Boolean(matchId),
  });
}

export function useCompatibilityScore(matchId: string) {
  return useQuery({
    queryKey: ["compatibility-score", matchId],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/matches/{match_id}/compatibility-score", {
        params: { path: { match_id: matchId } },
      });
      if (error) throw error;
      return data;
    },
    enabled: Boolean(matchId),
  });
}
