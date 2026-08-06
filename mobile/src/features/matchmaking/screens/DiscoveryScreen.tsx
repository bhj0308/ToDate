import { useState } from "react";
import { Alert, FlatList, Pressable, StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "../../../components/PrimaryButton";
import { Screen } from "../../../components/Screen";
import { StatusMessage } from "../../../components/StatusMessage";
import { TextField } from "../../../components/TextField";
import { colors } from "../../../theme/colors";
import { useMyEntitlements } from "../../entitlements/hooks/useEntitlements";
import { useCreateMatch, useDiscoveryFeed } from "../hooks/useMatchmaking";
import type { components } from "../../../api/schema";
import type { DiscoveryStackScreenProps } from "../../../navigation/types";

type IncomePercentileTier = components["schemas"]["IncomePercentileTier"];

const INCOME_TIERS: IncomePercentileTier[] = ["0-25", "25-50", "50-75", "75-90", "90+"];

export function DiscoveryScreen({ navigation }: DiscoveryStackScreenProps<"DiscoveryList">) {
  const entitlements = useMyEntitlements();
  const canFilterIncome = entitlements.data?.features.includes("income_filter_advanced") ?? false;
  const canFilterEducation = entitlements.data?.features.includes("education_filter") ?? false;

  const [minIncomeTier, setMinIncomeTier] = useState<IncomePercentileTier | undefined>();
  const [educationLevel, setEducationLevel] = useState("");

  const feed = useDiscoveryFeed({
    min_income_tier: canFilterIncome ? minIncomeTier : undefined,
    education_level: canFilterEducation && educationLevel.trim() ? educationLevel.trim() : undefined,
  });
  const createMatch = useCreateMatch();

  if (feed.isLoading) return <StatusMessage variant="loading" />;
  if (feed.isError) return <StatusMessage variant="error" />;

  return (
    <Screen scroll={false}>
      {(canFilterIncome || canFilterEducation) && (
        <View style={styles.filters}>
          {canFilterIncome && (
            <View style={styles.filterGroup}>
              <Text style={styles.filterLabel}>Min. income tier</Text>
              <View style={styles.chipRow}>
                {INCOME_TIERS.map((tier) => (
                  <Pressable
                    key={tier}
                    style={[styles.chip, minIncomeTier === tier && styles.chipActive]}
                    onPress={() => setMinIncomeTier(minIncomeTier === tier ? undefined : tier)}
                  >
                    <Text style={[styles.chipText, minIncomeTier === tier && styles.chipTextActive]}>
                      {tier}
                    </Text>
                  </Pressable>
                ))}
              </View>
            </View>
          )}
          {canFilterEducation && (
            <TextField
              label="Education level"
              placeholder="e.g. PhD"
              value={educationLevel}
              onChangeText={setEducationLevel}
            />
          )}
        </View>
      )}
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
  filters: {
    padding: 16,
    paddingBottom: 4,
    gap: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  filterGroup: {
    gap: 6,
  },
  filterLabel: {
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.8,
    textTransform: "uppercase",
    color: colors.textMuted,
  },
  chipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  chip: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  chipActive: {
    borderColor: colors.secondary,
    backgroundColor: colors.secondary,
  },
  chipText: {
    fontSize: 13,
    color: colors.text,
  },
  chipTextActive: {
    color: colors.onSecondary,
    fontWeight: "700",
  },
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
