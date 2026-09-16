import { Text } from "react-native";

import { Screen } from "../../components/Screen";
import { colors } from "../../theme/colors";

export function UpdateRequiredScreen() {
  return (
    <Screen>
      <Text style={{ fontSize: 22, fontWeight: "700", color: colors.text }}>Update required</Text>
      <Text style={{ color: colors.textMuted, marginTop: 8 }}>
        This version of ToDate is no longer supported. Please update from the App Store or Google
        Play to keep using the app.
      </Text>
    </Screen>
  );
}
