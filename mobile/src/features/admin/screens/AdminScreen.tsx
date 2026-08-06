import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "../../../components/PrimaryButton";
import { Screen } from "../../../components/Screen";
import { StatusMessage } from "../../../components/StatusMessage";
import { TextField } from "../../../components/TextField";
import { colors } from "../../../theme/colors";
import {
  useActionModerationCase,
  useActivateProfile,
  useAuditEvents,
  useCreateBetaInvite,
  useCurationQueue,
  useModerationQueue,
  useSetVerifiedAttributes,
} from "../hooks/useAdmin";
import type { components } from "../../../api/schema";

type IncomePercentileTier = components["schemas"]["IncomePercentileTier"];
type AdminUserOut = components["schemas"]["AdminUserOut"];

const INCOME_TIERS: IncomePercentileTier[] = ["0-25", "25-50", "50-75", "75-90", "90+"];

function CurationRow({ item }: { item: AdminUserOut }) {
  const activateProfile = useActivateProfile();
  const setAttributes = useSetVerifiedAttributes();
  const [incomeTier, setIncomeTier] = useState<IncomePercentileTier | undefined>();
  const [educationLevel, setEducationLevel] = useState("");

  return (
    <View style={styles.card}>
      <Text style={styles.body}>{item.display_name ?? "(no display name)"}</Text>
      <Text style={styles.meta}>{item.email}</Text>

      <Text style={styles.filterLabel}>Income tier</Text>
      <View style={styles.chipRow}>
        {INCOME_TIERS.map((tier) => (
          <Text
            key={tier}
            onPress={() => setIncomeTier(incomeTier === tier ? undefined : tier)}
            style={[styles.chip, incomeTier === tier && styles.chipActive]}
          >
            {tier}
          </Text>
        ))}
      </View>
      <TextField
        label="Education level"
        placeholder="e.g. PhD"
        value={educationLevel}
        onChangeText={setEducationLevel}
      />
      {setAttributes.isError && (
        <StatusMessage variant="error" message="Couldn't save verified attributes." />
      )}
      <View style={styles.row}>
        <PrimaryButton
          title="Save attributes"
          variant="secondary"
          loading={setAttributes.isPending}
          disabled={!incomeTier && !educationLevel.trim()}
          onPress={() =>
            setAttributes.mutate({
              userId: item.id,
              body: {
                ...(incomeTier ? { income_percentile_tier: incomeTier } : {}),
                ...(educationLevel.trim() ? { education_level: educationLevel.trim() } : {}),
              },
            })
          }
        />
        <PrimaryButton
          title="Activate"
          loading={activateProfile.isPending}
          onPress={() => activateProfile.mutate(item.id)}
        />
      </View>
    </View>
  );
}

export function AdminScreen() {
  const curationQueue = useCurationQueue();
  const queue = useModerationQueue("open");
  const actionCase = useActionModerationCase();
  const createInvite = useCreateBetaInvite();
  const auditEvents = useAuditEvents();
  const [email, setEmail] = useState("");

  return (
    <Screen>
      <Text style={styles.heading}>Pending activation</Text>
      <Text style={styles.meta}>
        Verification is blocked, so this is the only path to PROFILE_ACTIVE. Set
        income/education here too — it's the only way those discovery filters get real data.
      </Text>
      {curationQueue.isLoading && <StatusMessage variant="loading" />}
      {curationQueue.isError && <StatusMessage variant="error" />}
      {curationQueue.data?.length === 0 && (
        <StatusMessage variant="empty" message="Nobody waiting on activation." />
      )}
      {curationQueue.data?.map((item) => (
        <CurationRow key={item.id} item={item} />
      ))}

      <View style={{ height: 16 }} />
      <Text style={styles.heading}>Beta invites</Text>
      <TextField
        label="Email to invite"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
      />
      {createInvite.isError && (
        <StatusMessage variant="error" message="Couldn't create that invite." />
      )}
      {createInvite.isSuccess && <StatusMessage variant="empty" message="Invite created." />}
      <PrimaryButton
        title="Send invite"
        loading={createInvite.isPending}
        disabled={!email.trim()}
        onPress={() => createInvite.mutate(email.trim(), { onSuccess: () => setEmail("") })}
      />

      <View style={{ height: 16 }} />
      <Text style={styles.heading}>Moderation queue</Text>
      {queue.isLoading && <StatusMessage variant="loading" />}
      {queue.isError && <StatusMessage variant="error" />}
      {queue.data?.length === 0 && <StatusMessage variant="empty" message="No open reports." />}
      {queue.data?.map((item) => (
        <View key={item.id} style={styles.card}>
          <Text style={styles.meta}>
            {item.subject_type} · {item.subject_id}
          </Text>
          <Text style={styles.body}>{item.reason}</Text>
          <Text style={styles.timestamp}>
            Reported by {item.reporter_id} · {new Date(item.created_at).toLocaleString()}
          </Text>
          <View style={styles.row}>
            <PrimaryButton
              title="Action"
              loading={actionCase.isPending}
              onPress={() => actionCase.mutate({ caseId: item.id, decision: "actioned" })}
            />
            <PrimaryButton
              title="Dismiss"
              variant="secondary"
              loading={actionCase.isPending}
              onPress={() => actionCase.mutate({ caseId: item.id, decision: "dismissed" })}
            />
          </View>
        </View>
      ))}

      <View style={{ height: 16 }} />
      <Text style={styles.heading}>Audit log</Text>
      <Text style={styles.meta}>Most recent 50 admin/system actions.</Text>
      {auditEvents.isLoading && <StatusMessage variant="loading" />}
      {auditEvents.isError && <StatusMessage variant="error" />}
      {auditEvents.data?.length === 0 && (
        <StatusMessage variant="empty" message="No audit events yet." />
      )}
      {auditEvents.data?.map((event) => (
        <View key={event.id} style={styles.auditRow}>
          <Text style={styles.body}>{event.event_type.replace(/_/g, " ")}</Text>
          <Text style={styles.timestamp}>
            {event.actor_type}
            {event.actor_id ? ` (${event.actor_id})` : ""} → {event.subject_type}/{event.subject_id}
            {" · "}
            {new Date(event.occurred_at).toLocaleString()}
          </Text>
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
  card: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    padding: 16,
    gap: 8,
    backgroundColor: colors.surface,
  },
  body: {
    fontSize: 14,
    color: colors.text,
  },
  meta: {
    fontSize: 12,
    color: colors.textMuted,
    textTransform: "capitalize",
  },
  timestamp: {
    fontSize: 11,
    color: colors.textMuted,
  },
  auditRow: {
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingBottom: 8,
    gap: 2,
  },
  row: {
    flexDirection: "row",
    gap: 8,
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
    fontSize: 13,
    color: colors.text,
    overflow: "hidden",
  },
  chipActive: {
    borderColor: colors.secondary,
    backgroundColor: colors.secondary,
    color: colors.onSecondary,
    fontWeight: "700",
  },
});
