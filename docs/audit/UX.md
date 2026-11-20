# Draft room UX audit

## Observed brief, before implementation

The existing home page exposes exactly two playable choices: historical draft and daily challenge. Drafting defaults to three guided anonymous profiles. Scouting and review are separate actions; a review modal is required before selecting. Current browser tests cover phone and desktop scouting, review, save/reload, modal containment and focus, keyboard dismissal, horizontal overflow, and runtime errors.

The status console contains a pixel football scene, but CSS hides it at widths below 1000px, removing the football identity on phones. The phone status panel squeezes explanatory copy beside actions. The guided cards explain measurements but do not give a visible short sequence connecting scouting, comparison and selection. Existing CSS has multiple chronological overrides, making broad restyling unnecessarily risky.

## Implementation plan

1. Keep the two modes, masking rules, native controls and review-before-selection flow intact.
2. Give phones a stacked console with a small visible football scene and full-width primary action.
3. Add a compact three-step decision guide, with explicit evidence limitations and an accessible current step.
4. Increase spacing and legibility around card actions and resources without inserting another setup gate.
5. Run TypeScript and the existing browser smoke suite when dependencies are available.

## Result and validation

The phone console now stacks its status copy above the action and keeps the original football pixel field visible beside that action. Tablet layouts retain the scene as well. Guided drafting has a three-step sequence with the current step derived from the reports visible and comparison selections. Cards have larger phone action targets, clearer measurement spacing, and an 18px comparison checkbox. The scout suggestion now says to explore an undrafted role rather than implying that it fills a team need.

- `node_modules/.bin/tsc --noEmit`: passed.
- Existing real browser suite was attempted twice. The default Playwright Chromium binary is absent; the installed `/usr/bin/chromium` fails before page creation because the execution environment prohibits its process-singleton socket. No browser pass or screenshot review is claimed.
- No modes, identity fields, scouting probability values, or selection mutations changed.
