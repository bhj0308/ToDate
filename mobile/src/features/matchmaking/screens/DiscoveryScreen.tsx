import { Alert, FlatList, Pressable, StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "../../../components/PrimaryButton";
import { Screen } from "../../../components/Screen";
import { StatusMessage } from "../../../components/StatusMessage";
import { colors } from "../../../theme/colors";
import { useCreateMatch, useDiscoveryFeed } from "../hooks/useMatchmaking";
import type { DiscoveryStackScreenProps } from "../../../navigation/types";

export function DiscoveryScreen({ navigation }: DiscoveryStackScreenProps<"DiscoveryList">) {
  const feed = useDiscoveryFeed();
  const createMatch = useCreateMatch();

  if (feed.isLoading) return <StatusMessage variant="loading" />;
  if (feed.isError) return <StatusMessage variant="error" />;

  return (
    <Screen scroll={false}>
      <FlatList
        data={feed.data ?? []}
        keyExtractor={(item) => item.user_id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={<StatusMessage variant="empty" message="No candidates right now." />}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Pressable onPress={() => navigation.navigate("UserProfile", { userId: item.user_id })}>
              <Text style={styles.name}>{item.display_name ?? "Member"}</Text>
              {item.city_market && <Text style={styles.meta}>{item.city_market}</Text>}
              {item.bio && (
                <Text style={styles.bio} numberOfLines={2}>
                  {item.bio}
                </Text>
              )}
            </Pressable>
            <PrimaryButton
              title="Match"
              loading={createMatch.isPending}
              onPress={() =>
                createMatch.mutate(item.user_id, {
                  onSuccess: () => Alert.alert("Match created", "Check the Matches tab to start chatting."),
                  onError: () => Alert.alert("Couldn't create match", "Try again in a moment."),
                })
              }
            />
          </View>
        )}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  list: {
    padding: 16,
    gap: 12,
  },
  card: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    padding: 16,
    gap: 10,
    backgroundColor: colors.surface,
    shadowColor: colors.text,
    shadowOpacity: 0.06,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 1,
  },
  name: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.text,
  },
  meta: {
    color: colors.textMuted,
    fontSize: 13,
  },
  bio: {
    color: colors.text,
    fontSize: 14,
  },
});
