export type OpsSummary = {
  active_users: number;
  new_signups: number;
  roadmaps_generated: number;
  chat_sessions: number;
  community_posts: number;
  dau_mau_ratio: number;
  signup_to_roadmap_rate: number;
  total_users: number;
  total_teams: number;
  total_roadmaps: number;
  active_users_delta: number | null;
  new_signups_delta: number | null;
  roadmaps_generated_delta: number | null;
  generated_at: string;
  range: string;
};
