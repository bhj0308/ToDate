import Constants from "expo-constants";
import * as Device from "expo-device";
import * as Notifications from "expo-notifications";
import { Platform } from "react-native";

import { api } from "../api/client";

// Show pushes as banners even while the app is open.
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

let registeredToken: string | null = null;

/**
 * Ask for permission, get this device's Expo push token and register it with
 * the API. Safe to call on every sign-in; quietly does nothing when push can't
 * work (simulator, permission denied, no EAS project configured yet).
 */
export async function registerForPushNotifications(): Promise<void> {
  if (!Device.isDevice) return; // simulators can't receive remote pushes

  const projectId = Constants.expoConfig?.extra?.eas?.projectId as string | undefined;
  if (!projectId) {
    console.warn("Push disabled: no EAS projectId. Run `eas init` to create one.");
    return;
  }

  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("default", {
      name: "default",
      importance: Notifications.AndroidImportance.DEFAULT,
    });
  }

  let { status } = await Notifications.getPermissionsAsync();
  if (status !== "granted") {
    ({ status } = await Notifications.requestPermissionsAsync());
  }
  if (status !== "granted") return;

  const { data: token } = await Notifications.getExpoPushTokenAsync({ projectId });
  const { error } = await api.POST("/v1/users/me/push-tokens", {
    body: { token, platform: Platform.OS === "ios" ? "ios" : "android" },
  });
  if (!error) registeredToken = token;
}

/** Call before clearing auth so this device stops receiving the account's pushes. */
export async function unregisterPushNotifications(): Promise<void> {
  if (!registeredToken) return;
  await api.DELETE("/v1/users/me/push-tokens", { body: { token: registeredToken } });
  registeredToken = null;
}

/** For account deletion: the server already removed every token. */
export function forgetPushRegistration(): void {
  registeredToken = null;
}
