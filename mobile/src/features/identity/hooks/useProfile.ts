import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { API_BASE_URL, APP_VERSION, api } from "../../../api/client";
import { getTokens } from "../../../auth/tokenStore";
import type { components } from "../../../api/schema";

type ProfileUpdate = components["schemas"]["ProfileUpdate"];
type ProfileOut = components["schemas"]["ProfileOut"];

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

/**
 * Bypasses the typed client for multipart upload — openapi-fetch's JSON-first
 * body handling doesn't fit React Native's {uri, name, type} FormData file shape.
 */
export function useUploadProfilePhoto() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (asset: { uri: string; fileName?: string | null; mimeType?: string | null }) => {
      const tokens = getTokens();
      const formData = new FormData();
      formData.append("file", {
        uri: asset.uri,
        name: asset.fileName ?? "photo.jpg",
        type: asset.mimeType ?? "image/jpeg",
      } as unknown as Blob);

      const response = await fetch(`${API_BASE_URL}/v1/profiles/me/photos`, {
        method: "POST",
        headers: {
          "X-App-Version": APP_VERSION,
          ...(tokens ? { Authorization: `Bearer ${tokens.accessToken}` } : {}),
        },
        body: formData,
      });
      if (!response.ok) throw new Error("upload failed");
      return (await response.json()) as ProfileOut;
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

export function useSetDateOfBirth() {
  return useMutation({
    mutationFn: async (dateOfBirth: string) => {
      const { data, error, response } = await api.PUT("/v1/users/me/date-of-birth", {
        body: { date_of_birth: dateOfBirth },
      });
      if (error) throw Object.assign(new Error("date of birth rejected"), { status: response.status });
      return data;
    },
  });
}

export function useDeleteAccount() {
  return useMutation({
    mutationFn: async () => {
      const { error } = await api.DELETE("/v1/users/me");
      if (error) throw error;
    },
  });
}
