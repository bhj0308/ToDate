import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../../api/client";
import type { components } from "../../../api/schema";

type Plan = components["schemas"]["Plan"];
type BillingCycle = components["schemas"]["BillingCycle"];

export function useCatalog() {
  return useQuery({
    queryKey: ["entitlements", "catalog"],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/entitlements/catalog");
      if (error) throw error;
      return data;
    },
  });
}

export function useMyEntitlements() {
  return useQuery({
    queryKey: ["entitlements", "me"],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/entitlements/me");
      if (error) throw error;
      return data;
    },
  });
}

export function useMySubscription() {
  return useQuery({
    queryKey: ["subscription", "me"],
    queryFn: async () => {
      const { data, error, response } = await api.GET("/v1/subscriptions/me");
      if (response.status === 404) return null;
      if (error) throw error;
      return data;
    },
  });
}

function useInvalidateSubscription() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ["subscription", "me"] });
    queryClient.invalidateQueries({ queryKey: ["entitlements", "me"] });
  };
}

export function useCreateSubscription() {
  const invalidate = useInvalidateSubscription();
  return useMutation({
    mutationFn: async (body: { plan: Plan; billing_cycle: BillingCycle; payment_token: string }) => {
      const { data, error } = await api.POST("/v1/subscriptions", { body });
      if (error) throw error;
      return data;
    },
    onSuccess: invalidate,
  });
}

export function useCancelSubscription() {
  const invalidate = useInvalidateSubscription();
  return useMutation({
    mutationFn: async () => {
      const { error } = await api.DELETE("/v1/subscriptions/me");
      if (error) throw error;
    },
    onSuccess: invalidate,
  });
}
