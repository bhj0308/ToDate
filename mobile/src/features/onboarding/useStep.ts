export const ONBOARDING_STEPS = [
  "ValuesRanking",
  "DatingGoals",
  "Intent",
  "Gender",
  "InterestedIn",
  "FirstName",
  "Birthday",
] as const;

export type OnboardingStepName = (typeof ONBOARDING_STEPS)[number];

/**
 * Progress for a step. The phone-number and verification steps from the Figma
 * (05, 06) aren't in this flow yet — they're blocked on the phone-vs-email
 * decision — so the denominator will grow when they land.
 */
export function useStep(name: OnboardingStepName) {
  return {
    step: ONBOARDING_STEPS.indexOf(name) + 1,
    totalSteps: ONBOARDING_STEPS.length,
  };
}
