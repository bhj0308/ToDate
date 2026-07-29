import { useEffect, useState } from "react";
import { Text, View } from "react-native";

import { PrimaryButton } from "../../../components/PrimaryButton";
import { Screen } from "../../../components/Screen";
import { StatusMessage } from "../../../components/StatusMessage";
import { TextField } from "../../../components/TextField";
import { colors } from "../../../theme/colors";
import { useAuth } from "../../../auth/AuthContext";
import { VerifiedAttributesBadge } from "../components/VerifiedAttributesBadge";
import { useMyProfile, useUpdateMyProfile, useVerifiedAttributes } from "../hooks/useProfile";
import type { ProfileStackScreenProps } from "../../../navigation/types";

export function ProfileScreen({ navigation }: ProfileStackScreenProps<"MyProfile">) {
  const { user, logout } = useAuth();
  const profile = useMyProfile();
  const verifiedAttributes = useVerifiedAttributes();
  const updateProfile = useUpdateMyProfile();

  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [cityMarket, setCityMarket] = useState("");

  useEffect(() => {
    if (!profile.data) return;
    setDisplayName(profile.data.display_name ?? "");
    setBio(profile.data.bio ?? "");
    setCityMarket(profile.data.city_market ?? "");
  }, [profile.data]);

  if (profile.isLoading) return <StatusMessage variant="loading" />;
  if (profile.isError) return <StatusMessage variant="error" />;

  return (
    <Screen>
      <Text style={{ fontSize: 22, fontWeight: "700", color: colors.text }}>
        {user?.email}
      </Text>
      <Text style={{ color: colors.textMuted }}>Account: {user?.account_state}</Text>

      {verifiedAttributes.data && (
        <VerifiedAttributesBadge attributes={verifiedAttributes.data} />
      )}

      <View style={{ height: 8 }} />
      <TextField label="Display name" value={displayName} onChangeText={setDisplayName} />
      <TextField label="Bio" value={bio} onChangeText={setBio} multiline numberOfLines={4} />
      <TextField label="City / market" value={cityMarket} onChangeText={setCityMarket} />

      {updateProfile.isError && (
        <StatusMessage variant="error" message="Couldn't save your profile." />
      )}
      <PrimaryButton
        title="Save"
        loading={updateProfile.isPending}
        onPress={() =>
          updateProfile.mutate({
            display_name: displayName || null,
            bio: bio || null,
            city_market: cityMarket || null,
          })
        }
      />

      <View style={{ height: 16 }} />
      <PrimaryButton
        title="Verification status"
        variant="secondary"
        onPress={() => navigation.navigate("VerificationStatus")}
      />
      <PrimaryButton title="Log out" variant="secondary" onPress={logout} />
    </Screen>
  );
}
