import { useMutation } from "@tanstack/react-query";

import { api } from "../../../api/client";
import { useAuth } from "../../../auth/AuthContext";

export function useRegister() {
  return useMutation({
    mutationFn: async (body: { email: string; phone?: string }) => {
      const { data, error } = await api.POST("/v1/users", { body });
      if (error) throw error;
      return data;
    },
  });
}

export function useRequestOtp() {
  return useMutation({
    mutationFn: async (body: { destination: string; channel: "phone" | "email" }) => {
      const { data, error } = await api.POST("/v1/auth/otp/start", { body });
      if (error) throw error;
      return data;
    },
  });
}

export function useVerifyOtp() {
  const { login } = useAuth();
  return useMutation({
    mutationFn: async (body: { challenge_id: string; code: string }) => {
      const { data, error } = await api.POST("/v1/auth/otp/verify", { body });
      if (error) throw error;
      return data;
    },
    onSuccess: async (data) => {
      await login({ accessToken: data.access_token, refreshToken: data.refresh_token });
    },
  });
}
