import { useState } from "react";
import { Alert, StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "../../../components/PrimaryButton";
import { Screen } from "../../../components/Screen";
import { StatusMessage } from "../../../components/StatusMessage";
import { colors } from "../../../theme/colors";
import type { components } from "../../../api/schema";
import {
  useCancelSubscription,
  useCatalog,
  useCreateSubscription,
  useMyEntitlements,
  useMySubscription,
} from "../hooks/useEntitlements";

type Plan = components["schemas"]["Plan"];

const PLANS: { label: string; value: Plan }[] = [
  { label: "Premium", value: "premium" },
  { label: "Premium+", value: "premium_plus" },
  { label: "Elite", value: "elite" },
];

export function BillingScreen() {
  const entitlements = useMyEntitlements();
  const subscription = useMySubscription();
  const catalog = useCatalog();
  const createSubscription = useCreateSubscription();
  const cancelSubscription = useCancelSubscription();
  const [selectedPlan, setSelectedPlan] = useState<Plan>("premium_plus");

  if (entitlements.isLoading || subscription.isLoading) return <StatusMessage variant="loading" />;
  if (entitlements.isError) return <StatusMessage variant="error" />;

  return (
    <Screen>
      <Text style={styles.heading}>Your plan</Text>
      <Text style={styles.body}>Effective plan: {entitlements.data?.effective_plan}</Text>
      {subscription.data ? (
        <View style={styles.card}>
          <Text style={styles.body}>
            {subscription.data.plan} · {subscription.data.billing_cycle}
          </Text>
          <Text style={styles.meta}>Status: {subscription.data.status}</Text>
          <PrimaryButton
            title="Cancel subscription"
            variant="secondary"
            loading={cancelSubscription.isPending}
            onPress={() =>
              cancelSubscription.mutate(undefined, {
                onError: () => Alert.alert("Couldn't cancel", "Try again in a moment."),
              })
            }
          />
        </View>
      ) : (
        <View style={styles.card}>
          <Text style={styles.meta}>No active subscription — you're on the free Premium tier.</Text>
          <View style={styles.row}>
            {PLANS.map((p) => (
              <PrimaryButton
                key={p.value}
                title={p.label}
                variant={selectedPlan === p.value ? "primary" : "secondary"}
                onPress={() => setSelectedPlan(p.value)}
              />
            ))}
          </View>
          <PrimaryButton
            title="Subscribe (monthly)"
            loading={createSubscription.isPending}
            onPress={() =>
              createSubscription.mutate(
                { plan: selectedPlan, billing_cycle: "monthly" },
                { onError: () => Alert.alert("Couldn't subscribe", "Try again in a moment.") },
              )
            }
          />
        </View>
      )}

      <Text style={styles.heading}>Included features</Text>
      {entitlements.data?.features.map((feature) => (
        <Text key={feature} style={styles.feature}>
          • {feature.replace(/_/g, " ")}
        </Text>
      ))}

      <Text style={styles.heading}>Plan comparison</Text>
      {catalog.data &&
        Object.entries(catalog.data).map(([feature, plans]) => (
          <View key={feature} style={styles.catalogRow}>
            <Text style={styles.feature}>{feature.replace(/_/g, " ")}</Text>
            <Text style={styles.meta}>{plans.join(", ")}</Text>
          </View>
        ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  heading: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.text,
    marginTop: 8,
  },
  body: {
    fontSize: 15,
    color: colors.text,
  },
  meta: {
    fontSize: 13,
    color: colors.textMuted,
  },
  card: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    padding: 16,
    gap: 10,
  },
  row: {
    flexDirection: "row",
    gap: 8,
    flexWrap: "wrap",
  },
  feature: {
    color: colors.text,
    fontSize: 14,
    textTransform: "capitalize",
  },
  catalogRow: {
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingBottom: 8,
    gap: 2,
  },
});
