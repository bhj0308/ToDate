# Design tokens

⚠️ **These are eyeballed from 1x PNG exports, not read from Figma.** Treat every
value as approximate until someone confirms it in Figma (click a layer →
Properties tab shows the exact hex, font and size) or the designer sends their
styles list. Replace this file, then update `src/theme/colors.ts` to match.

## Color (approximate)

| Role | Approx. value | Seen in |
|---|---|---|
| Background (top of gradient) | `#3A2318` | all screens, warm dark brown |
| Background (bottom of gradient) | `#1E1208` | all screens |
| Surface / unselected chip | `#3B2A20` | chips, input fields |
| Chip selected | `#C9A063` | gold/tan fill, dark text |
| Chip selected (alt, lighter) | `#D9B678` | 03/04 |
| Primary CTA | `#8C1D3F` | "Continue", "My age is correct" — deep wine |
| CTA text | `#F5EFE7` | |
| CTA disabled | `#3E1A22` | 03, 06, 10 |
| Heading text | `#F7F1E8` | serif headings |
| Body text | `#CBBCAE` | subtitles |
| Label text (uppercase) | `#9C8B7C` | "PHONE NUMBER", "BIRTHDAY" |
| Error / destructive | `#E0452F` | error border + message (05-error, 04-warning) |
| Progress fill | `#C9A063` | |
| Progress track | `#6B5B4E` | |

## Type

| Role | Observation |
|---|---|
| Headings | **Serif** (a Didone/transitional face — get the exact family from the designer), ~30px, regular weight |
| Body / subtitle | Sans-serif, ~16px, ~1.4 line height |
| Section label | Sans-serif, ~12px, uppercase, wide letter-spacing (~2px) |
| Chip / button text | Sans-serif, ~15–16px |

**The heading font is the single most important thing to confirm** — it carries
the whole "luxury, not lifestyle" brand and can't be guessed reliably.

## Spacing and shape

| Token | Approx. |
|---|---|
| Screen horizontal padding | 24px |
| Chip corner radius | 8px |
| Input / button corner radius | 10px |
| Bottom-sheet corner radius | 24px |
| Button height | 52px |
| Gap between stacked options | 12px |
