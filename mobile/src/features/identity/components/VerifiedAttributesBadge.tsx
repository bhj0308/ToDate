import { StyleSheet, Text, View } from "react-native";

import type { components } from "../../../api/schema";
import { colors } from "../../../theme/colors";

type VerifiedAttributesOut = components["schemas"]["VerifiedAttributesOut"];

function eligibilityColor(eligibility: VerifiedAttributesOut["eligibility"]) {
  if (eligibility === "eligible") return colors.success;
  if (eligibility === "exception_granted") return colors.primary;
  return colors.textMuted;
}

export function VerifiedAttributesBadge({ attributes }: { attributes: VerifiedAttributesOut }) {
  return (
    <View style={styles.row}>
      <Badge label={attributes.identity_verified ? "Identity verified" : "Identity not verified"} tone={attributes.identity_verified ? colors.success : colors.textMuted} />
      <Badge label={`Background: ${attributes.criminal_check_status}`} tone={attributes.criminal_check_status === "passed" ? colors.success : colors.textMuted} />
      {attributes.income_percentile_tier && (
        <Badge label={`Income tier: ${attributes.income_percentile_tier}`} tone={colors.textMuted} />
      )}
      <Badge label={attributes.eligibility.replace(/_/g, " ")} tone={eligibilityColor(attributes.eligibility)} />
    </View>
  );
}

function Badge({ label, tone }: { label: string; tone: string }) {
  return (
    <View style={[styles.badge, { borderColor: tone }]}>
      <Text style={[styles.badgeText, { color: tone }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  badge: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: "600",
    textTransform: "capitalize",
  },
});
