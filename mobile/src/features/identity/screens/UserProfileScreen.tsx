import { Text, View } from "react-native";

import { Screen } from "../../../components/Screen";
import { StatusMessage } from "../../../components/StatusMessage";
import { colors } from "../../../theme/colors";
import { useUserProfile } from "../hooks/useProfile";
import type { DiscoveryStackScreenProps, MatchesStackScreenProps } from "../../../navigation/types";

type Props = DiscoveryStackScreenProps<"UserProfile"> | MatchesStackScreenProps<"UserProfile">;

export function UserProfileScreen({ route }: Props) {
  const { userId } = route.params;
  const profile = useUserProfile(userId);

  if (profile.isLoading) return <StatusMessage variant="loading" />;
  if (profile.isError || !profile.data) return <StatusMessage variant="error" message="Profile not available." />;

  const { display_name, bio, interests, city_market } = profile.data;

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
    </Screen>
  );
}
