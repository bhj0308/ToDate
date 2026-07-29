import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "../../../components/PrimaryButton";
import { StatusMessage } from "../../../components/StatusMessage";
import { TextField } from "../../../components/TextField";
import { colors } from "../../../theme/colors";
import type { components } from "../../../api/schema";
import {
  useCreateDatePlan,
  useDatePromptState,
  useRecordDateOutcome,
  useSubmitAvailability,
  useSubmitDatePromptResponse,
  useTriggerDatePrompt,
  useVenueRecommendations,
} from "../hooks/useStructured";

type MatchOut = components["schemas"]["MatchOut"];
type DatePromptChoice = components["schemas"]["DatePromptChoice"];
type DateOutcome = components["schemas"]["DateOutcome"];
type DatePlanOut = components["schemas"]["DatePlanOut"];

const CHOICES: DatePromptChoice[] = ["yes", "maybe", "no"];
const OUTCOMES: { label: string; value: DateOutcome }[] = [
  { label: "Went well", value: "went_well" },
  { label: "Didn't go well", value: "did_not_go_well" },
  { label: "No-show", value: "no_show" },
  { label: "Cancelled", value: "cancelled" },
];

type DateProgressionScreenProps = {
  match: MatchOut;
  datePlan: DatePlanOut | null;
  onDatePlanChange: (plan: DatePlanOut) => void;
};

export function DateProgressionScreen({ match, datePlan, onDatePlanChange }: DateProgressionScreenProps) {
  if (match.state === "CLOSED") {
    return <StatusMessage variant="empty" message="This match has closed." />;
  }
  if (match.state === "DATE_PROMPT_PENDING") {
    return <DatePromptSection matchId={match.id} />;
  }
  if (match.state === "SCHEDULE_READY" || datePlan) {
    return (
      <SchedulingSection matchId={match.id} datePlan={datePlan} onPlanCreated={onDatePlanChange} />
    );
  }
  if (match.state === "CHAT_OPEN" || match.state === "EXTENDED_CHAT") {
    return <ReadyToPlanSection matchId={match.id} />;
  }
  // DATE_PROMPT_CAPTURED — momentary state between response resolution and
  // the transition landing; nothing to show.
  return <StatusMessage variant="empty" message="Resolving…" />;
}

function ReadyToPlanSection({ matchId }: { matchId: string }) {
  const trigger = useTriggerDatePrompt(matchId);
  return (
    <View style={styles.section}>
      <StatusMessage
        variant="empty"
        message="In production this triggers automatically after 3–5 days of chat."
      />
      <PrimaryButton
        title="Go on a date?"
        loading={trigger.isPending}
        onPress={() => trigger.mutate()}
      />
    </View>
  );
}

function DatePromptSection({ matchId }: { matchId: string }) {
  const promptState = useDatePromptState(matchId);
  const respond = useSubmitDatePromptResponse(matchId);

  if (promptState.isLoading) return <StatusMessage variant="loading" />;
  if (promptState.isError || !promptState.data) return <StatusMessage variant="error" />;

  if (promptState.data.my_choice) {
    return (
      <StatusMessage
        variant="empty"
        message={
          promptState.data.resolved
            ? `Both answered. Result: ${promptState.data.resolved_state}`
            : "Waiting on the other person's answer…"
        }
      />
    );
  }

  return (
    <View style={styles.section}>
      <Text style={styles.heading}>Go on a date?</Text>
      <View style={styles.row}>
        {CHOICES.map((choice) => (
          <PrimaryButton
            key={choice}
            title={choice[0].toUpperCase() + choice.slice(1)}
            variant={choice === "yes" ? "primary" : "secondary"}
            loading={respond.isPending}
            onPress={() => respond.mutate(choice)}
          />
        ))}
      </View>
    </View>
  );
}

function SchedulingSection({
  matchId,
  datePlan,
  onPlanCreated,
}: {
  matchId: string;
  datePlan: DatePlanOut | null;
  onPlanCreated: (plan: DatePlanOut) => void;
}) {
  const venues = useVenueRecommendations(matchId, !datePlan);
  const submitAvailability = useSubmitAvailability(matchId);
  const createPlan = useCreateDatePlan(matchId);
  const recordOutcome = useRecordDateOutcome(matchId);
  const [slot, setSlot] = useState("");
  const [selectedVenue, setSelectedVenue] = useState<string | null>(null);

  if (datePlan) {
    return (
      <View style={styles.section}>
        <Text style={styles.heading}>Date plan</Text>
        <Text style={styles.body}>{datePlan.venue_name}</Text>
        {datePlan.venue_address && <Text style={styles.meta}>{datePlan.venue_address}</Text>}
        <Text style={styles.meta}>{new Date(datePlan.scheduled_at).toLocaleString()}</Text>
        {datePlan.outcome ? (
          <Text style={styles.meta}>Outcome: {datePlan.outcome.replace(/_/g, " ")}</Text>
        ) : (
          <View style={styles.row}>
            {OUTCOMES.map((o) => (
              <PrimaryButton
                key={o.value}
                title={o.label}
                variant="secondary"
                loading={recordOutcome.isPending}
                onPress={() => recordOutcome.mutate(o.value, { onSuccess: onPlanCreated })}
              />
            ))}
          </View>
        )}
      </View>
    );
  }

  return (
    <View style={styles.section}>
      <Text style={styles.heading}>Submit availability</Text>
      <TextField
        label="Available slot (ISO date/time)"
        placeholder="2026-08-01T19:00:00Z"
        value={slot}
        onChangeText={setSlot}
      />
      {submitAvailability.isError && (
        <StatusMessage variant="error" message="Couldn't save that — check the date/time format." />
      )}
      <PrimaryButton
        title="Submit availability"
        loading={submitAvailability.isPending}
        disabled={!slot.trim()}
        onPress={() => submitAvailability.mutate([slot.trim()])}
      />

      <Text style={styles.heading}>Venue recommendations</Text>
      {venues.isLoading && <StatusMessage variant="loading" />}
      {venues.data?.map((venue) => (
        <View
          key={venue.name}
          style={[styles.venue, selectedVenue === venue.name && styles.venueSelected]}
        >
          <Text style={styles.body}>
            {venue.name} · {venue.price_tier}
          </Text>
          <Text style={styles.meta}>
            {venue.cuisine} · {venue.address}
          </Text>
          <PrimaryButton
            title={selectedVenue === venue.name ? "Selected" : "Choose"}
            variant="secondary"
            onPress={() => setSelectedVenue(venue.name)}
          />
        </View>
      ))}

      {createPlan.isError && (
        <StatusMessage variant="error" message="Couldn't confirm the date plan — check the date/time format." />
      )}
      {selectedVenue && (
        <PrimaryButton
          title="Confirm date plan"
          loading={createPlan.isPending}
          onPress={() => {
            const venue = venues.data?.find((v) => v.name === selectedVenue);
            if (!venue || !slot.trim()) return;
            createPlan.mutate(
              {
                venue_name: venue.name,
                venue_address: venue.address,
                scheduled_at: slot.trim(),
              },
              { onSuccess: onPlanCreated },
            );
          }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  section: {
    padding: 16,
    gap: 12,
  },
  heading: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.text,
    marginTop: 8,
  },
  row: {
    flexDirection: "row",
    gap: 8,
    flexWrap: "wrap",
  },
  body: {
    fontSize: 15,
    color: colors.text,
  },
  meta: {
    fontSize: 13,
    color: colors.textMuted,
  },
  venue: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    padding: 12,
    gap: 6,
  },
  venueSelected: {
    borderColor: colors.primary,
  },
});
