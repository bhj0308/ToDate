import { useLayoutEffect, useRef, useState } from "react";
import { Animated, PanResponder, type PanResponderInstance, StyleSheet, Text, View } from "react-native";

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
 * Drag-to-reorder ranking on PanResponder + Animated (React Native core).
 *
 * Two rules keep it steady on a real device:
 * 1. Each row's gesture handler is created ONCE and kept in a ref. Creating it
 *    during render replaces it mid-drag and resets the drag offset, so the row
 *    jitters and drops in the wrong place.
 * 2. The list order doesn't change while dragging. The dragged row follows the
 *    finger, the rows in between slide aside to preview the drop, and the
 *    reorder is committed once, on release.
 */
export function ValuesRankingScreen({ navigation }: OnboardingScreenProps<"ValuesRanking">) {
  const { answers, setAnswer } = useOnboarding();
  const step = useStep("ValuesRanking");
  const [order, setOrder] = useState<string[]>(
    answers.values.length ? answers.values : [...VALUES],
  );
  const [drag, setDrag] = useState<{ from: number; to: number } | null>(null);

  // Handlers are created once, so they read live values through refs.
  const orderRef = useRef(order);
  orderRef.current = order;
  const dragRef = useRef(drag);
  dragRef.current = drag;

  const dragY = useRef(new Animated.Value(0)).current;
  const shifts = useRef(new Map<string, Animated.Value>()).current;
  const responders = useRef(new Map<string, PanResponderInstance>()).current;

  const shiftFor = (value: string) => {
    if (!shifts.has(value)) shifts.set(value, new Animated.Value(0));
    return shifts.get(value)!;
  };

  // Slide the rows between `from` and `to` one slot to open a gap at `to`.
  function previewDrop(from: number, to: number) {
    orderRef.current.forEach((value, i) => {
      if (i === from) return;
      let offset = 0;
      if (from < to && i > from && i <= to) offset = -SLOT;
      if (to < from && i >= to && i < from) offset = SLOT;
      Animated.timing(shiftFor(value), {
        toValue: offset,
        duration: 140,
        useNativeDriver: true,
      }).start();
    });
  }

  function finishDrag() {
    const current = dragRef.current;
    dragRef.current = null;
    if (current && current.from !== current.to) {
      setOrder(move(orderRef.current, current.from, current.to));
    }
    setDrag(null); // offsets are cleared in the layout effect below
  }

  // Clear the drag offsets only once the new order is laid out — before paint.
  // Clearing them at release, before the re-render, flashes every row back to
  // its old slot for a frame and reads as a jittery drop.
  useLayoutEffect(() => {
    if (drag === null) {
      dragY.setValue(0);
      shifts.forEach((v) => v.setValue(0));
    }
  }, [drag, order, dragY, shifts]);

  function responderFor(value: string): PanResponderInstance {
    const existing = responders.get(value);
    if (existing) return existing;
    const responder = PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      // The page ScrollView would otherwise steal a vertical drag a few pixels in.
      onPanResponderTerminationRequest: () => false,
      onShouldBlockNativeResponder: () => true,
      onPanResponderGrant: () => {
        const from = orderRef.current.indexOf(value);
        dragY.setValue(0);
        // Set the ref now: move events can arrive before the re-render does.
        dragRef.current = { from, to: from };
        setDrag({ from, to: from });
      },
      onPanResponderMove: (_, g) => {
        const current = dragRef.current;
        if (!current) return;
        dragY.setValue(g.dy);
        const last = orderRef.current.length - 1;
        const to = Math.max(0, Math.min(last, current.from + Math.round(g.dy / SLOT)));
        if (to !== current.to) {
          dragRef.current = { from: current.from, to };
          setDrag({ from: current.from, to });
          previewDrop(current.from, to);
        }
      },
      onPanResponderRelease: finishDrag,
      onPanResponderTerminate: finishDrag,
    });
    responders.set(value, responder);
    return responder;
  }

  return (
    <OnboardingLayout
      eyebrow="Application"
      title="What do you value most in a relationship?"
      subtitle="Every lasting relationship is built on strong values. Which matters most to you?"
      {...step}
      scrollEnabled={drag === null}
      onCta={() => {
        setAnswer("values", order);
        navigation.navigate("DatingGoals");
      }}
      onBack={navigation.goBack}
    >
      <Text style={styles.hint}>Drag to reorder</Text>
      <View style={styles.list}>
        {order.map((value, index) => {
          const isDragging = drag?.from === index;
          // The number shown is where the row will land, so it updates live.
          let rank = index;
          if (drag && !isDragging) {
            if (drag.from < drag.to && index > drag.from && index <= drag.to) rank = index - 1;
            if (drag.to < drag.from && index >= drag.to && index < drag.from) rank = index + 1;
          }
          if (isDragging && drag) rank = drag.to;
          return (
            <Animated.View
              key={value}
              style={[
                styles.row,
                isDragging && styles.rowDragging,
                { transform: [{ translateY: isDragging ? dragY : shiftFor(value) }] },
                isDragging && { zIndex: 10 },
              ]}
            >
              <View style={styles.rank}>
                <Text style={styles.rankText}>{rank + 1}</Text>
              </View>
              <Text style={styles.label}>{value}</Text>
              {/* Drag from the handle only: a row-wide gesture fights the page scroll. */}
              <View style={styles.grip} hitSlop={16} {...responderFor(value).panHandlers}>
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
  grip: { gap: 3, paddingVertical: 8, paddingLeft: 8 },
  gripRow: { flexDirection: "row", gap: 3 },
  gripDot: { width: 3, height: 3, borderRadius: 1.5, backgroundColor: colors.textSubtle },
});
