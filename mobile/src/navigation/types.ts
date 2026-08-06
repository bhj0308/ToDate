import type { NativeStackScreenProps } from "@react-navigation/native-stack";

export type AuthStackParamList = {
  OtpRequest: undefined;
  OtpVerify: { challengeId: string; destination: string; devCode?: string };
};
export type AuthStackScreenProps<T extends keyof AuthStackParamList> = NativeStackScreenProps<
  AuthStackParamList,
  T
>;

export type DiscoveryStackParamList = {
  DiscoveryList: undefined;
  UserProfile: { userId: string };
};
export type DiscoveryStackScreenProps<T extends keyof DiscoveryStackParamList> =
  NativeStackScreenProps<DiscoveryStackParamList, T>;

export type MatchesStackParamList = {
  MatchList: undefined;
  MatchDetail: { matchId: string };
  UserProfile: { userId: string };
};
export type MatchesStackScreenProps<T extends keyof MatchesStackParamList> = NativeStackScreenProps<
  MatchesStackParamList,
  T
>;

export type BillingStackParamList = {
  Billing: undefined;
};
export type BillingStackScreenProps<T extends keyof BillingStackParamList> = NativeStackScreenProps<
  BillingStackParamList,
  T
>;

export type ProfileStackParamList = {
  MyProfile: undefined;
  VerificationStatus: undefined;
};
export type ProfileStackScreenProps<T extends keyof ProfileStackParamList> = NativeStackScreenProps<
  ProfileStackParamList,
  T
>;

export type AdminStackParamList = {
  Admin: undefined;
};
export type AdminStackScreenProps<T extends keyof AdminStackParamList> = NativeStackScreenProps<
  AdminStackParamList,
  T
>;

export type AppTabParamList = {
  DiscoveryTab: undefined;
  MatchesTab: undefined;
  BillingTab: undefined;
  ProfileTab: undefined;
  AdminTab: undefined;
};
