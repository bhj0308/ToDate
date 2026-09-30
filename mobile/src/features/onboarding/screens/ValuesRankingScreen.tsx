import { useRef, useState } from "react";
import { Animated, PanResponder, StyleSheet, Text, View } from "react-native";

import { colors } from "../../../theme/colors";
import { VALUES } from "../content";
import { OnboardingLayout } from "../components/OnboardingLayout";
import { useOnboarding } from "../OnboardingContext";
import { useStep } from "../useStep";
import type { OnboardingScreenProps } from "../../../navigation/types";

const ROW_HEIGHT = 64;
const ROW_GAP = 12;
const SLOT = ROW_HEIGHT + ROW_GAP;

function move<T>(list: T[], from: number, to: number): T[] {
  const next = [...list];
  next.splice(to, 0, ...next.splice(from, 1));
  return next;
}

/**
 * Drag-to-reorder ranking, built on PanResponder + Animated from React Native
 * core. Deliberately no Reanimated/draggable-flatlist dependency for one screen.
 */
export function ValuesRankingScreen({ navigation }: OnboardingScreenProps<"ValuesRanking">) {
  const { answers, setAnswer } = useOnboarding();
  const step = useStep("ValuesRanking");
  const [order, setOrder] = useState<string[]>(
    answers.values.length ? answers.values : [...VALUES],
  );
  const [dragging, setDragging] = useState<number | null>(null);

  // Snapshot at gesture start so each move recomputes from a stable baseline.
  const grant = useRef({ index: 0, order: [] as string[] });
  const dragY = useRef(new Animated.Value(0)).current;

  function responderFor(index: number) {
    return PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: (_, g) => Math.abs(g.dy) > 2,
      // The page ScrollView will otherwise steal a vertical drag a few pixels in.
      onPanResponderTerminationRequest: () => false,
      onShouldBlockNativeResponder: () => true,
      onPanResponderGrant: () => {
        grant.current = { index, order };
        setDragging(index);
        dragY.setValue(0);
      },
      onPanResponderMove: (_, g) => {
        const { index: from, order: base } = grant.current;
        const target = Math.max(0, Math.min(base.length - 1, from + Math.round(g.dy / SLOT)));
        const reordered = move(base, from, target);
        setOrder((prev) => (prev.join() === reordered.join() ? prev : reordered));
        setDragging(target);
        // Follow the finger, minus the distance already taken up by re-slotting.
        dragY.setValue(g.dy - (target - from) * SLOT);
      },
      onPanResponderRelease: () => {
        setDragging(null);
        dragY.setValue(0);
      },
      onPanResponderTerminate: () => {
        setDragging(null);
        dragY.setValue(0);
      },
    });
  }

  return (
    <OnboardingLayout
      eyebrow="Application"
      title="What do you value most in a relationship?"
      subtitle="Every lasting relationship is built on strong values. Which matters most to you?"
      {...step}
      scrollEnabled={dragging === null}
      onCta={() => {
        setAnswer("values", order);
        navigation.navigate("DatingGoals");
      }}
      onBack={navigation.goBack}
    >
      <Text style={styles.hint}>Drag to reorder</Text>
      <View style={styles.list}>
        {order.map((value, index) => {
          const isDragging = dragging === index;
          return (
            <Animated.View
              key={value}
              style={[
                styles.row,
                isDragging && styles.rowDragging,
                isDragging && { transform: [{ translateY: dragY }], zIndex: 10 },
              ]}
            >
              <View style={styles.rank}>
                <Text style={styles.rankText}>{index + 1}</Text>
              </View>
              <Text style={styles.label}>{value}</Text>
              {/* Drag from the handle only: a row-wide gesture fights the page scroll. */}
              <View style={styles.grip} hitSlop={12} {...responderFor(index).panHandlers}>
                {[0, 1, 2].map((r) => (
                  <View key={r} style={styles.gripRow}>
                    <View style={styles.gripDot} />
                    <View style={styles.gripDot} />
                  </View>
                ))}
              </View>
            </Animated.View>
          );
        })}
      </View>
    </OnboardingLayout>
  );
}

const styles = StyleSheet.create({
  hint: { color: colors.textMuted, fontSize: 15, marginBottom: 14 },
  list: { gap: ROW_GAP },
  row: {
    height: ROW_HEIGHT,
    borderRadius: 10,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 14,
    gap: 14,
  },
  rowDragging: {
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.secondaryDim,
    shadowColor: "#000",
    shadowOpacity: 0.4,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
    elevation: 6,
  },
  rank: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.backgroundBottom,
    alignItems: "center",
    justifyContent: "center",
  },
  rankText: { color: colors.textMuted, fontSize: 13 },
  label: { flex: 1, color: colors.text, fontSize: 16 },
  grip: { gap: 3 },
  gripRow: { flexDirection: "row", gap: 3 },
  gripDot: { width: 3, height: 3, borderRadius: 1.5, backgroundColor: colors.textSubtle },
});
