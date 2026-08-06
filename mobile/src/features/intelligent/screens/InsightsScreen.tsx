import { StyleSheet, Text, View } from "react-native";

import { StatusMessage } from "../../../components/StatusMessage";
import { colors } from "../../../theme/colors";
import { useCoachingInsights, useCompatibilityScore } from "../hooks/useIntelligent";

export function InsightsScreen({ matchId }: { matchId: string }) {
  const insights = useCoachingInsights(matchId);
  const score = useCompatibilityScore(matchId);

  if (insights.isLoading || score.isLoading) return <StatusMessage variant="loading" />;
  if (insights.isError || score.isError) return <StatusMessage variant="error" />;

  return (
    <View style={styles.section}>
      {score.data && (
        <View style={styles.scoreCard}>
          <Text style={styles.scoreValue}>{Math.round(score.data.score)}</Text>
          <Text style={styles.meta}>Compatibility score</Text>
        </View>
      )}

      <Text style={styles.heading}>Coaching insights</Text>
      {insights.data && insights.data.insights.length === 0 && (
        <StatusMessage variant="empty" message="No insights yet — keep chatting." />
      )}
      {insights.data?.insights.map((insight, index) => (
        <View key={index} style={styles.insightCard}>
          <Text style={styles.insightType}>{insight.type.replace(/_/g, " ")}</Text>
          <Text style={styles.body}>{insight.body}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  section: {
    padding: 16,
    gap: 12,
  },
  scoreCard: {
    alignItems: "center",
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 14,
    paddingVertical: 24,
    backgroundColor: colors.surface,
    shadowColor: colors.text,
    shadowOpacity: 0.08,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 3 },
    elevation: 2,
  },
  scoreValue: {
    fontSize: 36,
    fontWeight: "800",
    color: colors.secondary,
  },
  heading: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.text,
    marginTop: 8,
  },
  insightCard: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    padding: 12,
    gap: 4,
    backgroundColor: colors.surface,
  },
  insightType: {
    fontSize: 12,
    fontWeight: "700",
    color: colors.textMuted,
    textTransform: "capitalize",
  },
  body: {
    fontSize: 14,
    color: colors.text,
  },
  meta: {
    fontSize: 13,
    color: colors.textMuted,
  },
});
