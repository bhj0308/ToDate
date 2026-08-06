import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../../api/client";
import type { components } from "../../../api/schema";

type ModerationSubjectType = components["schemas"]["ModerationSubjectType"];
type ModerationStatus = components["schemas"]["ModerationStatus"];
type VerifiedAttributesUpdate = components["schemas"]["VerifiedAttributesUpdate"];

export function useReportSubject() {
  return useMutation({
    mutationFn: async (body: {
      subject_type: ModerationSubjectType;
      subject_id: string;
      reason: string;
    }) => {
      const { data, error } = await api.POST("/v1/admin/moderation-cases", { body });
      if (error) throw error;
      return data;
    },
  });
}

export function useModerationQueue(status: ModerationStatus = "open") {
  return useQuery({
    queryKey: ["admin", "moderation-cases", status],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/admin/moderation-cases", {
        params: { query: { status } },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function useActionModerationCase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ caseId, decision }: { caseId: string; decision: ModerationStatus }) => {
      const { data, error } = await api.POST("/v1/admin/moderation-cases/{case_id}/action", {
        params: { path: { case_id: caseId } },
        body: { decision },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "moderation-cases"] });
    },
  });
}

export function useCreateBetaInvite() {
  return useMutation({
    mutationFn: async (email: string) => {
      const { data, error } = await api.POST("/v1/admin/beta-invites", { body: { email } });
      if (error) throw error;
      return data;
    },
  });
}

/** Members awaiting manual activation — verification is blocked, so this is the only path to PROFILE_ACTIVE. */
export function useCurationQueue() {
  return useQuery({
    queryKey: ["admin", "users", "REGISTERED"],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/admin/users", {
        params: { query: { account_state: "REGISTERED" } },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function useActivateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (userId: string) => {
      const { data, error } = await api.POST("/v1/admin/users/{user_id}/activate", {
        params: { path: { user_id: userId } },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

/** Manual override standing in for blocked Verification — the only way income/education filters get real data. */
export function useSetVerifiedAttributes() {
  return useMutation({
    mutationFn: async ({ userId, body }: { userId: string; body: VerifiedAttributesUpdate }) => {
      const { data, error } = await api.POST("/v1/admin/users/{user_id}/verified-attributes", {
        params: { path: { user_id: userId } },
        body,
      });
      if (error) throw error;
      return data;
    },
  });
}

export function useAuditEvents() {
  return useQuery({
    queryKey: ["admin", "audit-events"],
    queryFn: async () => {
      const { data, error } = await api.GET("/v1/admin/audit-events");
      if (error) throw error;
      return data;
    },
  });
}
