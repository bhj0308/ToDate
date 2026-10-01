// The full application sequence, sign-up included, so the progress bar moves
// continuously from the phone step through to the birthday.
export const ONBOARDING_STEPS = [
  "PhoneNumber",
  "PhoneVerification",
  "ValuesRanking",
  "DatingGoals",
  "Intent",
  "Gender",
  "InterestedIn",
  "FirstName",
  "Birthday",
] as const;

export type OnboardingStepName = (typeof ONBOARDING_STEPS)[number];

/** Position of a step in the application, for the progress bar. */
export function useStep(name: OnboardingStepName) {
  return {
    step: ONBOARDING_STEPS.indexOf(name) + 1,
    totalSteps: ONBOARDING_STEPS.length,
  };
}
