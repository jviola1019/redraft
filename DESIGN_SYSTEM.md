# UX and design system

Direction: original editorial sports draft room. Warm paper surfaces, dark ink typography, restrained red actions and schematic vector field geometry. Avoid generic neon, decorative analytics, fake athlete portraits or copied broadcast assets. The interface must make the next decision obvious, with room for evidence and uncertainty.

## Components and hierarchy

Landing communicates the two modes, resume and prior results. Setup defaults to random assignment and exposes only supported data. Draft room centers the on-clock selection, searchable prospect board, scouting/compare tools, pick ledger and trade proposals. Simulation progress is completed server work, not invented timing. Results distinguish actual, simulated baseline and alternate data, then let users inspect a season, cohort stars, actual draft trades and explicitly cohort-only awards.

Desktop supports multi-panel comparison; phone reflows into single-column controls, bottom navigation where useful, safe-area spacing and touch-sized actions. Do not shrink a wide dashboard into tiny text. Tables should either reflow or expose purposeful local scrolling, not page overflow.

## Disclosure interaction

Name-hidden historical profiles may still be recognizable. Daily profiles must show the current standardized band/suppression policy and a concise limitation. Scouting reveals only allowed genuine evidence, and the cumulative reveal matters. No client-side hidden names, private IDs, player URLs or full-precision probabilities. Exact provenance can remain server-side until an authorized reveal; broad provider attribution remains accessible.

An explicit name reveal ends blind evaluation for that run. The daily policy must not silently change mid-challenge. External searching cannot be perfectly prevented and must not be claimed away.

## Accessibility and motion

Target WCAG 2.2 AA without claiming certification from CSS. Use semantic controls, visible focus, sufficient contrast, non-color status, text/table chart equivalents, screen-reader labels, keyboard access, focus-managed dialogs and44px preferred touch targets. Respect reduced motion. Motion should communicate pick/round/trade/result state changes, not unrelated animated counters.

The new build’s actual palette, contrast ratios, viewport checks and browser observations must be recorded after implementation. Previous session visual checks are not current evidence. A manifest alone is not full PWA/offline support; no service-worker claim without actual caching and offline recovery.

## Pixel football treatment — 2026-11-02
Original SVG sprites and field geometry, limited ink/green/gold/coral palette, crisp pixel edges, solid offset button shadows, stepped state transitions. No Krillion assets or official team artwork copied. Pixel runner position tracks completed selections; selection notices and season content use brief entrance motion. Readable system typography retained for analytical content. Reduced-motion overrides remove stepped transitions and entrance effects. This is a visual treatment within the same two modes.

## Guided interface revision — 2026-11-02

The landing screen now has one welcome message and two gameplay actions. It explains the scout → choose → five-season sequence in plain language. Resume and the recent run are contextual secondary actions.

The draft opens with three guided profile cards. Position names and responsibilities are written out; a rookie snap is explained as one play. The free “Different profiles” control changes the visible subset using client-only presentation randomness. It never advances the game RNG, changes underlying prospects, spends scouting credit, or affects score calculations. Six cards are optional. Cards use only the available blind DTO, visible position groups, and unlocked shared report estimates; they are a varied set rather than a hidden ranking. The full searchable board remains available under “Full board · Advanced”, inside the same two gameplay modes. Trade access and remaining scouting/pick budgets remain immediately visible.

The new original vector stadium and player sprites are implemented in `components/redraft/stadium.tsx`; the bitmap lettermark is original rectangle geometry. No Krillion or NFL artwork is copied. Pick walks run when the completed-selection count increases. Trade handoffs run when the saved trade count increases. Simulation movement and its bar use saved replicate counts. The season view uses actual selected-season records and a trophy only when the simulated championship flag is true. Static text captions communicate the same events. No animation generates or substitutes for statistical outcomes.

Reduced-motion CSS disables the stepped sprites and entrance motion. Readable system fonts remain in prose, controls, tables, and probability descriptions. Pixel typography is confined to the short original mark and visual treatment. Guided cards, the full table, comparison modal, trade dialog, save/resume, and detailed results share the same authoritative API actions.

Primary design references reviewed:
- [NN/g: Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/) — supports deferring advanced controls while keeping their access obvious. This design uses one visible layout switch rather than adding a game mode.
- [W3C technique C39](https://www.w3.org/WAI/WCAG22/Techniques/css/C39) — documents respecting the operating-system reduced-motion preference for interaction-triggered motion.
- [Krillion original site](https://krillion.io/) — the requested broad visual reference. Its assets, logos, exact layouts, and additional modes are not imported.

These are design decisions informed by published guidance. They are not evidence of novice usability testing, WCAG certification, or a measured improvement in user performance. Record fresh browser and accessibility observations separately in TEST_RESULTS.md.

## November 12 interface integration

Scenario setup now defaults to a random supported year and franchise, with historical names and previous-season records from the selected bundle. The guided prospect board explains measurement units and uncertainty in plain language. It keeps colleges and exact identifying measurements out of blind profiles; a recognizable historical player can otherwise defeat blind evaluation. Original SVG football/stadium animation remains state-driven, not a static generated preview.

Current browser status: the Linux environment blocks Chromium before page creation. A runnable Playwright workflow covers desktop and phone viewport interaction, scouting, dialog dismissal, save/reload, runtime errors and horizontal overflow, with WebKit configured separately. No new screenshot, approved visual baseline, physical-iPhone test, accessibility certification or novice usability result is claimed.
