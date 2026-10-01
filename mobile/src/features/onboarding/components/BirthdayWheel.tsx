import { LinearGradient } from "expo-linear-gradient";
import { useEffect, useRef, useState } from "react";
import {
  type NativeScrollEvent,
  type NativeSyntheticEvent,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

/**
 * Month · day · year wheel from design/screens/10-birthday.png.
 *
 * Plain ScrollViews rather than a native date picker: on Android the native
 * picker is a one-shot dialog, not an inline wheel, and neither platform's
 * native look matches the design. This renders the same on iOS and Android.
 */

const ITEM_H = 34;
const VISIBLE = 7; // odd, so one row sits in the middle
const EDGE = ITEM_H * Math.floor(VISIBLE / 2);

// Sampled from design/screens/10-birthday.png.
const BOX = "#34231E";
const BAND = "#3E2E29";
const SELECTED = "#FEFEFD";
const UNSELECTED = "#A08E86";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const daysIn = (month: number, year: number) => new Date(year, month + 1, 0).getDate();

type ColumnProps = {
  items: string[];
  index: number;
  onChange: (index: number) => void;
  flex: number;
  align: "left" | "center";
  unselectedSize: number;
};

function WheelColumn({ items, index, onChange, flex, align, unselectedSize }: ColumnProps) {
  const ref = useRef<ScrollView>(null);
  const [live, setLive] = useState(index);
  const momentum = useRef(false);
  const clamp = (i: number) => Math.max(0, Math.min(items.length - 1, i));
  const indexAt = (e: NativeSyntheticEvent<NativeScrollEvent>) =>
    clamp(Math.round(e.nativeEvent.contentOffset.y / ITEM_H));

  // Follow outside changes, e.g. the day clamping when switching to February.
  useEffect(() => {
    setLive(index);
    ref.current?.scrollTo({ y: index * ITEM_H, animated: false });
  }, [index, items.length]);

  const settle = (i: number) => {
    if (i !== index) onChange(i);
  };

  return (
    <View style={{ flex, height: ITEM_H * VISIBLE }}>
      <ScrollView
        ref={ref}
        nestedScrollEnabled
        showsVerticalScrollIndicator={false}
        snapToInterval={ITEM_H}
        decelerationRate="fast"
        contentOffset={{ x: 0, y: index * ITEM_H }}
        contentContainerStyle={{ paddingVertical: EDGE }}
        scrollEventThrottle={16}
        onScroll={(e) => {
          const i = indexAt(e);
          if (i !== live) setLive(i);
        }}
        onMomentumScrollBegin={() => {
          momentum.current = true;
        }}
        onMomentumScrollEnd={(e) => {
          momentum.current = false;
          settle(indexAt(e));
        }}
        // A slow drag can end exactly on a row with no momentum phase at all,
        // so commit after a beat unless momentum took over.
        onScrollEndDrag={(e) => {
          const i = indexAt(e);
          setTimeout(() => {
            if (!momentum.current) settle(i);
          }, 120);
        }}
      >
        {items.map((label, i) => {
          const distance = Math.abs(i - live);
          const selected = distance === 0;
          return (
            <View key={label} style={styles.item}>
              <Text
                numberOfLines={1}
                style={{
                  textAlign: align,
                  paddingLeft: align === "left" ? 24 : 0,
                  color: selected ? SELECTED : UNSELECTED,
                  fontSize: selected ? 24 : unselectedSize,
                  fontWeight: selected ? "500" : "400",
                  opacity: selected ? 1 : Math.max(0.15, 0.85 - (distance - 1) * 0.3),
                }}
              >
                {label}
              </Text>
            </View>
          );
        })}
      </ScrollView>
    </View>
  );
}

const thisYear = new Date().getFullYear();
// The full range, under-18 included: an honest answer has to be possible —
// the API refuses under-18s and suspends the account (set_date_of_birth).
const YEARS = Array.from({ length: 101 }, (_, i) => thisYear - 100 + i);

export function BirthdayWheel({ value, onChange }: { value: Date; onChange: (d: Date) => void }) {
  const year = value.getFullYear();
  const month = value.getMonth();
  const day = value.getDate();
  const days = Array.from({ length: daysIn(month, year) }, (_, i) => String(i + 1).padStart(2, "0"));

  // Keep the day valid when the month or year changes (31 Jan -> Feb).
  const set = (y: number, m: number, d: number) =>
    onChange(new Date(y, m, Math.min(d, daysIn(m, y))));

  return (
    <View style={styles.box}>
      <View style={styles.band} pointerEvents="none" />
      <View style={styles.columns}>
        <WheelColumn
          items={MONTHS}
          index={month}
          onChange={(m) => set(year, m, day)}
          flex={1.5}
          align="left"
          unselectedSize={17}
        />
        <WheelColumn
          items={days}
          index={day - 1}
          onChange={(d) => set(year, month, d + 1)}
          flex={0.8}
          align="center"
          unselectedSize={17}
        />
        <WheelColumn
          items={YEARS.map(String)}
          index={YEARS.indexOf(year)}
          onChange={(y) => set(YEARS[y], month, day)}
          flex={1.1}
          align="center"
          unselectedSize={21}
        />
      </View>
      {/* Fade the outer rows into the box, as in the design. */}
      <LinearGradient
        pointerEvents="none"
        colors={[BOX, `${BOX}00`]}
        style={[styles.fade, { top: 0 }]}
      />
      <LinearGradient
        pointerEvents="none"
        colors={[`${BOX}00`, BOX]}
        style={[styles.fade, { bottom: 0 }]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  box: { backgroundColor: BOX, borderRadius: 12, overflow: "hidden" },
  band: {
    position: "absolute",
    left: 4,
    right: 4,
    top: EDGE - 4,
    height: ITEM_H + 8,
    borderRadius: 8,
    backgroundColor: BAND,
  },
  columns: { flexDirection: "row" },
  item: { height: ITEM_H, justifyContent: "center" },
  fade: { position: "absolute", left: 0, right: 0, height: ITEM_H * 1.5 },
});
