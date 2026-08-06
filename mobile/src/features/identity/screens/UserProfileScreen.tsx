import { useState } from "react";
import { Text, View } from "react-native";

import { PrimaryButton } from "../../../components/PrimaryButton";
import { Screen } from "../../../components/Screen";
import { StatusMessage } from "../../../components/StatusMessage";
import { TextField } from "../../../components/TextField";
import { colors } from "../../../theme/colors";
import { useReportSubject } from "../../admin/hooks/useAdmin";
import { useUserProfile } from "../hooks/useProfile";
import type { DiscoveryStackScreenProps, MatchesStackScreenProps } from "../../../navigation/types";

type Props = DiscoveryStackScreenProps<"UserProfile"> | MatchesStackScreenProps<"UserProfile">;

export function UserProfileScreen({ route }: Props) {
  const { userId } = route.params;
  const profile = useUserProfile(userId);
  const reportSubject = useReportSubject();
  const [showReportForm, setShowReportForm] = useState(false);
  const [reason, setReason] = useState("");

  if (profile.isLoading) return <StatusMessage variant="loading" />;
  if (profile.isError || !profile.data) return <StatusMessage variant="error" message="Profile not available." />;

  const { display_name, bio, interests, city_market } = profile.data;

  function handleSubmitReport() {
    reportSubject.mutate(
      { subject_type: "user", subject_id: userId, reason: reason.trim() },
      {
        onSuccess: () => {
          setShowReportForm(false);
          setReason("");
        },
      },
    );
  }

  return (
    <Screen>
      <Text style={{ fontSize: 22, fontWeight: "700", color: colors.text }}>
        {display_name ?? "Member"}
      </Text>
      {city_market && <Text style={{ color: colors.textMuted }}>{city_market}</Text>}
      {bio && <Text style={{ color: colors.text, marginTop: 8 }}>{bio}</Text>}
      {Array.isArray(interests) && interests.length > 0 && (
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
          {interests.map((interest, index) => (
            <Text
              key={index}
              style={{
                borderWidth: 1,
                borderColor: colors.border,
                borderRadius: 999,
                paddingHorizontal: 10,
                paddingVertical: 4,
                fontSize: 12,
                color: colors.text,
              }}
            >
              {String(interest)}
            </Text>
          ))}
        </View>
      )}

      <View style={{ height: 8 }} />
      {reportSubject.isSuccess ? (
        <StatusMessage variant="empty" message="Report submitted. Our team will review it." />
      ) : showReportForm ? (
        <>
          <TextField
            label="Why are you reporting this profile?"
            value={reason}
            onChangeText={setReason}
            multiline
            numberOfLines={3}
          />
          {reportSubject.isError && (
            <StatusMessage variant="error" message="Couldn't submit the report." />
          )}
          <PrimaryButton
            title="Submit report"
            loading={reportSubject.isPending}
            disabled={!reason.trim()}
            onPress={handleSubmitReport}
          />
        </>
      ) : (
        <PrimaryButton title="Report" variant="secondary" onPress={() => setShowReportForm(true)} />
      )}
    </Screen>
  );
}
