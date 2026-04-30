export const mockOpportunities = [
  {
    id: 'opt-1',
    title: 'Looking for a reliable way to bypass Reddit API for scraping without getting blocked',
    source: 'r/SaaS',
    source_group: 'reddit',
    published: '2026-04-30T08:12:00Z',
    category: {
      name: 'pain_point',
      description: 'User expressing clear pain points',
    },
    total_score: 8.2,
    rating: '🟢 GREEN',
    content_summary: 'User is frustrated with Reddit API limits and is looking for a stable proxy/scraping solution. Willing to pay $50/mo for a reliable endpoint.',
    key_insight: 'High willingness to pay. Clear pain point. Development is straightforward for solo developer.',
    action_items: 'Build a simple proxy wrapper around public RSS feeds or use residential proxies. Offer a $49/mo lifetime deal to early adopters.',
    scores: {
      'Pain': 8.5,
      'Dev Fit': 9.0,
      'Stability': 6.0,
      'Growth': 8.5,
      'Monetization': 9.0
    },
    redlines: [],
  },
  {
    id: 'opt-2',
    title: 'Alternative to Hubspot that doesn\'t cost an arm and a leg for startups?',
    source: 'r/EntrepreneurRideAlong',
    source_group: 'reddit',
    published: '2026-04-29T14:30:00Z',
    category: {
      name: 'competitor_complaint',
      description: 'User unhappy with competitor pricing',
    },
    total_score: 6.4,
    rating: '🟢 GREEN',
    content_summary: 'Startups find Hubspot too expensive as they scale. Looking for a CRM that has basic email tracking and pipeline management without the enterprise bloat.',
    key_insight: 'Classic unbundling opportunity. High demand for simple CRMs.',
    action_items: 'Create a micro-CRM focused purely on email tracking and pipeline for founders.',
    scores: {
      'Pain': 7.0,
      'Dev Fit': 6.0,
      'Stability': 7.5,
      'Growth': 5.5,
      'Monetization': 6.0
    },
    redlines: [],
  },
  {
    id: 'opt-3',
    title: 'I want to build a new Google Search AI alternative',
    source: 'r/SideProject',
    source_group: 'reddit',
    published: '2026-04-29T10:15:00Z',
    category: {
      name: 'idea_request',
      description: 'User seeking idea validation',
    },
    total_score: 2.1,
    rating: '🔴 RED',
    content_summary: 'Wants to index the entire web and build an AI model to compete with Google and Perplexity.',
    key_insight: 'Impossible for solo dev. Requires massive capital.',
    action_items: 'Skip.',
    scores: {
      'Pain': 3.0,
      'Dev Fit': 0.0,
      'Stability': 1.0,
      'Growth': 1.0,
      'Monetization': 5.5
    },
    redlines: ['红线1: 巨头压制', '红线3: 技术泥潭'],
  },
  {
    id: 'opt-4',
    title: 'How do you guys handle Stripe VAT tax compliance in the EU? It\'s a nightmare',
    source: 'r/indiehackers',
    source_group: 'reddit',
    published: '2026-04-28T18:45:00Z',
    category: {
      name: 'pain_point',
      description: 'User expressing clear pain points',
    },
    total_score: 4.5,
    rating: '🟡 YELLOW',
    content_summary: 'Solo founder is confused by EU VAT rules and Merchant of Record setup. Stripe Tax is too complex to integrate.',
    key_insight: 'Real pain, but compliance involves legal risks.',
    action_items: 'Could build a simple MoR wrapper or a localized tax calculator. Need to verify legal liabilities.',
    scores: {
      'Pain': 8.0,
      'Dev Fit': 3.0,
      'Stability': 4.0,
      'Growth': 4.0,
      'Monetization': 3.5
    },
    redlines: [],
  }
];
