import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "../../../api/client";

export function useBlockUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (userId: string) => {
      const { error } = await api.POST("/v1/users/{user_id}/block", {
        params: { path: { user_id: userId } },
      });
      if (error) throw error;
    },
    onSuccess: () => {
      // The blocked person disappears from discovery and their match closes.
      queryClient.invalidateQueries({ queryKey: ["discovery"] });
      queryClient.invalidateQueries({ queryKey: ["matches"] });
    },
  });
}
