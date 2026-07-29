import { FlatList, Pressable, StyleSheet, Text } from "react-native";

import { Screen } from "../../../components/Screen";
import { StatusMessage } from "../../../components/StatusMessage";
import { colors } from "../../../theme/colors";
import { useAuth } from "../../../auth/AuthContext";
import { useUserProfile } from "../../identity/hooks/useProfile";
import { useMatches } from "../hooks/useMatchmaking";
import type { components } from "../../../api/schema";
import type { MatchesStackScreenProps } from "../../../navigation/types";

type MatchOut = components["schemas"]["MatchOut"];

const STATE_LABEL: Record<string, string> = {
  CHAT_OPEN: "Chatting",
  DATE_PROMPT_PENDING: "Date prompt pending",
  DATE_PROMPT_CAPTURED: "Waiting on both answers",
  EXTENDED_CHAT: "Extended chat",
  SCHEDULE_READY: "Ready to schedule",
  CLOSED: "Closed",
};

export function MatchListScreen({ navigation }: MatchesStackScreenProps<"MatchList">) {
  const matches = useMatches();

  if (matches.isLoading) return <StatusMessage variant="loading" />;
  if (matches.isError) return <StatusMessage variant="error" />;

  return (
    <Screen scroll={false}>
      <FlatList
        data={matches.data ?? []}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={<StatusMessage variant="empty" message="No matches yet — check Discovery." />}
        renderItem={({ item }) => (
          <MatchRow match={item} onPress={() => navigation.navigate("MatchDetail", { matchId: item.id })} />
        )}
      />
    </Screen>
  );
}

function MatchRow({ match, onPress }: { match: MatchOut; onPress: () => void }) {
  const { user } = useAuth();
  const counterpartId = match.user_a_id === user?.id ? match.user_b_id : match.user_a_id;
  const counterpart = useUserProfile(counterpartId);

  return (
    <Pressable style={styles.row} onPress={onPress}>
      <Text style={styles.title}>{counterpart.data?.display_name ?? "Match"}</Text>
      <Text style={styles.meta}>{STATE_LABEL[match.state] ?? match.state}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  list: {
    padding: 16,
    gap: 8,
  },
  row: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    padding: 16,
  },
  title: {
    fontSize: 16,
    fontWeight: "600",
    color: colors.text,
  },
  meta: {
    color: colors.textMuted,
    marginTop: 4,
  },
});
