import { useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { Text } from "react-native";

import { api } from "../../../api/client";
import { Screen } from "../../../components/Screen";
import { StatusMessage } from "../../../components/StatusMessage";
import { colors } from "../../../theme/colors";

/**
 * The backend deliberately returns 501 here — background-check flows are
 * blocked pending legal sign-off (see backend/app/modules/verification).
 * This screen just surfaces that status rather than building a real flow.
 */
export function VerificationStatusScreen() {
  const check = useMutation({
    mutationFn: async () => {
      await api.POST("/v1/verification-cases");
    },
  });

  useEffect(() => {
    check.mutate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Screen>
      <Text style={{ fontSize: 20, fontWeight: "700", color: colors.text }}>Verification</Text>
      <StatusMessage
        variant="empty"
        message="Identity, background, and income verification aren't available yet — this is pending legal sign-off of the background-check compliance requirements and vendor selection. You'll be notified when it opens."
      />
    </Screen>
  );
}
