import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { StatusMessage } from "../../../components/StatusMessage";
import { colors } from "../../../theme/colors";
import { ConversationScreen } from "../../structured/screens/ConversationScreen";
import { DateProgressionScreen } from "../../structured/screens/DateProgressionScreen";
import { InsightsScreen } from "../../intelligent/screens/InsightsScreen";
import { useMatch } from "../hooks/useMatchmaking";
import type { MatchesStackScreenProps } from "../../../navigation/types";

const SEGMENTS = ["Chat", "Date", "Insights"] as const;
type Segment = (typeof SEGMENTS)[number];

export function MatchDetailScreen({ route }: MatchesStackScreenProps<"MatchDetail">) {
  const { matchId } = route.params;
  const [segment, setSegment] = useState<Segment>("Chat");
  const match = useMatch(matchId);

  if (match.isLoading) return <StatusMessage variant="loading" />;
  if (match.isError || !match.data) return <StatusMessage variant="error" />;

  return (
    <SafeAreaView style={styles.flex} edges={["bottom"]}>
      <View style={styles.tabs}>
        {SEGMENTS.map((label) => (
          <Pressable
            key={label}
            style={[styles.tab, segment === label && styles.tabActive]}
            onPress={() => setSegment(label)}
          >
            <Text style={[styles.tabLabel, segment === label && styles.tabLabelActive]}>
              {label}
            </Text>
          </Pressable>
        ))}
      </View>

      <View style={styles.flex}>
        {segment === "Chat" && <ConversationScreen matchId={matchId} />}
        {segment === "Date" && <DateProgressionScreen match={match.data} />}
        {segment === "Insights" && <InsightsScreen matchId={matchId} />}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
    backgroundColor: colors.background,
  },
  tabs: {
    flexDirection: "row",
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: "center",
    borderBottomWidth: 2,
    borderBottomColor: "transparent",
  },
  tabActive: {
    borderBottomColor: colors.secondary,
  },
  tabLabel: {
    color: colors.textMuted,
    fontWeight: "600",
  },
  tabLabelActive: {
    color: colors.secondary,
  },
});
