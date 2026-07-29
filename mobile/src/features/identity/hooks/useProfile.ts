import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../../api/client";
import type { components } from "../../../api/schema";

type ProfileUpdate = components["schemas"]["ProfileUpdate"];

export function useMyProfile() {
  return useQuery({
    queryKey: ["profile", "me"],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/profiles/me");
      if (error) throw error;
      return data;
    },
  });
}

export function useUpdateMyProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: ProfileUpdate) => {
      const { data, error } = await api.PUT("/v1/profiles/me", { body });
      if (error) throw error;
      return data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["profile", "me"], data);
    },
  });
}

export function useVerifiedAttributes() {
  return useQuery({
    queryKey: ["verified-attributes", "me"],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/users/me/verified-attributes");
      if (error) throw error;
      return data;
    },
  });
}

export function useUserProfile(userId: string) {
  return useQuery({
    queryKey: ["profile", userId],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/profiles/{user_id}", {
        params: { path: { user_id: userId } },
      });
      if (error) throw error;
      return data;
    },
    enabled: Boolean(userId),
  });
}
