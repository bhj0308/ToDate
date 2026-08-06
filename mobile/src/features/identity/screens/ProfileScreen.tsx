import { useEffect, useState } from "react";
import * as ImagePicker from "expo-image-picker";
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "../../../components/PrimaryButton";
import { Screen } from "../../../components/Screen";
import { StatusMessage } from "../../../components/StatusMessage";
import { TextField } from "../../../components/TextField";
import { colors } from "../../../theme/colors";
import { useAuth } from "../../../auth/AuthContext";
import { VerifiedAttributesBadge } from "../components/VerifiedAttributesBadge";
import {
  useMyProfile,
  useUpdateMyProfile,
  useUploadProfilePhoto,
  useVerifiedAttributes,
} from "../hooks/useProfile";
import type { ProfileStackScreenProps } from "../../../navigation/types";

export function ProfileScreen({ navigation }: ProfileStackScreenProps<"MyProfile">) {
  const { user, logout } = useAuth();
  const profile = useMyProfile();
  const verifiedAttributes = useVerifiedAttributes();
  const updateProfile = useUpdateMyProfile();
  const uploadPhoto = useUploadProfilePhoto();

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

  const photos = (profile.data?.photos ?? []) as string[];

  async function handleAddPhoto() {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) return;
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      quality: 0.8,
    });
    const asset = result.assets?.[0];
    if (result.canceled || !asset) return;
    uploadPhoto.mutate({ uri: asset.uri, fileName: asset.fileName, mimeType: asset.mimeType });
  }

  function handleRemovePhoto(url: string) {
    updateProfile.mutate({ photos: photos.filter((p) => p !== url) });
  }

  return (
    <Screen>
      <Text style={{ fontSize: 22, fontWeight: "700", color: colors.text }}>
        {user?.email}
      </Text>
      <Text style={{ color: colors.textMuted }}>Account: {user?.account_state}</Text>

      {verifiedAttributes.data && (
        <VerifiedAttributesBadge attributes={verifiedAttributes.data} />
      )}

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.photoRow}>
        {photos.map((url) => (
          <Pressable key={url} style={styles.photoWrap} onPress={() => handleRemovePhoto(url)}>
            <Image source={{ uri: url }} style={styles.photo} />
            <View style={styles.removeBadge}>
              <Text style={styles.removeBadgeText}>Remove</Text>
            </View>
          </Pressable>
        ))}
        <Pressable style={styles.addPhoto} onPress={handleAddPhoto} disabled={uploadPhoto.isPending}>
          <Text style={styles.addPhotoText}>{uploadPhoto.isPending ? "Uploading…" : "+ Add photo"}</Text>
        </Pressable>
      </ScrollView>
      {uploadPhoto.isError && (
        <StatusMessage variant="error" message="Couldn't upload that photo." />
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

const styles = StyleSheet.create({
  photoRow: {
    flexGrow: 0,
  },
  photoWrap: {
    marginRight: 10,
  },
  photo: {
    width: 96,
    height: 128,
    borderRadius: 12,
    backgroundColor: colors.surface,
  },
  removeBadge: {
    position: "absolute",
    bottom: 6,
    left: 6,
    right: 6,
    backgroundColor: "rgba(34, 29, 23, 0.72)",
    borderRadius: 6,
    paddingVertical: 3,
    alignItems: "center",
  },
  removeBadgeText: {
    color: colors.onSecondary,
    fontSize: 11,
    fontWeight: "600",
  },
  addPhoto: {
    width: 96,
    height: 128,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
  },
  addPhotoText: {
    color: colors.secondary,
    fontSize: 12,
    fontWeight: "700",
    textAlign: "center",
    paddingHorizontal: 8,
  },
});
