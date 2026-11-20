# Integration dependencies and rollback

```mermaid
flowchart TD
 A[Verified main revision] --> B[Point-in-time feature audit]
 A --> C[Request contract audit]
 B --> D[Development forecast]
 B --> E[CPU decision audit]
 C --> F[Draft room and persistence]
 D --> G[Paired five-season simulation]
 E --> G
 F --> H[Hosted browser checks]
 G --> I[Statistical gates]
 H --> J[Release decision]
 I --> J
```

The API persists versioned state in D1. Immutable challenge configuration binds runs to scenario, model, disclosure and engine versions. The clean data, modeling and simulation boundaries are documented in the root ARCHITECTURE.md and DATA_DICTIONARY.md. The full physical ERD and its relational constraints live under docs/erd and docs/warehouse. Revert subsystem commits on the review branch to roll back. No production database migration accompanies this revision.
