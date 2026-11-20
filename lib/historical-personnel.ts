type PersonnelFact = {
  label: string;
  detail: string;
  publishedOn: string;
  publisher: string;
  url: string;
};

type HistoricalPersonnel = {
  draftYear: number;
  teamId: string;
  through: string;
  groups: { title: string; facts: PersonnelFact[] }[];
};

const cleveland2025: HistoricalPersonnel = {
  draftYear: 2025,
  teamId: 'CLE',
  through: '2025-04-23',
  groups: [
    {
      title: 'Quarterback',
      facts: [
        {
          label: 'Arrived and departed · Kenny Pickett and Dorian Thompson-Robinson',
          detail: 'Cleveland acquired Pickett from Philadelphia and sent Thompson-Robinson and a fifth-round pick to the Eagles.',
          publishedOn: '2025-03-12',
          publisher: 'Cleveland Browns',
          url: 'https://www.clevelandbrowns.com/news/browns-acquire-kenny-pickett-in-exchange-for-dorian-thompson-robinson',
        },
        {
          label: 'Departed · Jameis Winston',
          detail: 'Winston signed with the Giants after starting seven games for Cleveland in 2024.',
          publishedOn: '2025-03-31',
          publisher: 'New York Giants',
          url: 'https://www.giants.com/news/giants-sign-quarterback-jameis-winston-2025-nfl-free-agency',
        },
        {
          label: 'Agreed to terms · Joe Flacco',
          detail: 'Cleveland announced an agreement to bring back Flacco, who had last played for the Browns in 2023.',
          publishedOn: '2025-04-11',
          publisher: 'Cleveland Browns',
          url: 'https://www.clevelandbrowns.com/news/flacco-s-back-browns-agree-to-terms-with-qb-joe-flacco',
        },
        {
          label: 'Return date unknown · Deshaun Watson',
          detail: 'The team reported a second Achilles surgery and said Watson would likely miss significant time in 2025. His return date was uncertain.',
          publishedOn: '2025-01-10',
          publisher: 'Cleveland Browns',
          url: 'https://www.clevelandbrowns.com/news/deshaun-watson-underwent-2nd-surgery-to-repair-achilles-tendon-rupture',
        },
      ],
    },
    {
      title: 'Defensive front',
      facts: [
        {
          label: 'Retained · Myles Garrett',
          detail: 'Cleveland announced an agreement on a four-year extension through the 2030 season.',
          publishedOn: '2025-03-09',
          publisher: 'Cleveland Browns',
          url: 'https://www.clevelandbrowns.com/news/myles-garrett-and-browns-agree-to-4-year-contract-extension-through-2030-season',
        },
        {
          label: 'Departed and agreed to terms · Dalvin Tomlinson and Maliek Collins',
          detail: 'Cleveland terminated Tomlinson’s contract on March 12 and announced terms with Collins on March 13.',
          publishedOn: '2025-03-13',
          publisher: 'Cleveland Browns transaction log',
          url: 'https://www.clevelandbrowns.com/team/transactions/2025',
        },
        {
          label: 'Reported scheme · Jim Schwartz',
          detail: 'The team described Schwartz’s defense as attack-oriented. Collins cited familiarity with that style when explaining his decision to join Cleveland.',
          publishedOn: '2025-03-20',
          publisher: 'Cleveland Browns',
          url: 'https://www.clevelandbrowns.com/news/maliek-collins-brings-experience-in-attack-style-defensive-scheme-to-the-browns',
        },
      ],
    },
    {
      title: 'Offensive coaching',
      facts: [
        {
          label: 'Announced coordinator and play-caller · Tommy Rees and Kevin Stefanski',
          detail: 'The Browns promoted Rees to offensive coordinator and said head coach Stefanski would call plays. Rees described an offense flexible enough to play to the quarterback’s strengths.',
          publishedOn: '2025-01-23',
          publisher: 'Cleveland Browns',
          url: 'https://www.clevelandbrowns.com/news/tommy-rees-has-come-full-circle-as-new-offensive-coordinator-for-the-browns',
        },
      ],
    },
  ],
};

export function getHistoricalPersonnel(draftYear: number, teamId: string): HistoricalPersonnel | undefined {
  if (draftYear === cleveland2025.draftYear && teamId === cleveland2025.teamId) {
    return cleveland2025;
  }
}
