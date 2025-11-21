/**
 * TypeScript types for SQLite database tables
 * Based on normalized schema v2.0
 */

export interface Server {
  id: string;
  slug: string;
  name: string;
  display_name: string | null;
  tagline: string | null;
  short_description: string | null;
  logo_url: string | null;
  homepage_url: string | null;
  install_count: number | null;
  favorite_count: number | null;
  tools_count: number | null;
  status: 'approved' | 'pending' | 'rejected' | null;
  verification_status: string | null;
  creator_id: string | null;
  creator_name: string | null;
  creator_username: string | null;
  created_at: string | null;
  published_at: string | null;
  updated_at: string | null;
}

export interface GithubInfo {
  id: string;
  server_id: string;
  github_url: string | null;
  github_owner: string | null;
  github_repo: string | null;
  github_full_name: string | null;
  github_description: string | null;
  github_stars: number | null;
  github_forks: number | null;
  github_watchers: number | null;
  github_last_commit: string | null;
  commit_frequency: number | null;
  github_open_issues: number | null;
  primary_language: string | null;
  languages: string | null; // JSON
  github_topics: string | null; // JSON
  license: string | null;
  license_name: string | null;
  is_archived: number | null; // 0 or 1 (SQLite boolean)
  is_fork: number | null;
  is_disabled: number | null;
  latest_github_version: string | null;
  latest_release_date: string | null;
  is_prerelease: number | null;
  contributors_count: number | null;
  top_contributors: string | null; // JSON
  github_health_score: number | null; // 0-100
  has_readme: number | null;
  has_license: number | null;
  has_contributing: number | null;
  has_code_of_conduct: number | null;
  stars_last_week: number | null;
  stars_last_month: number | null;
  updated_at: string | null;
}

export interface NpmInfo {
  id: string;
  server_id: string;
  npm_package: string | null;
  npm_version: string | null;
  npm_downloads_weekly: number | null;
  npm_downloads_monthly: number | null;
  npm_license: string | null;
  npm_homepage: string | null;
  npm_repository_url: string | null;
  latest_version: string | null;
  latest_version_published_at: string | null;
  updated_at: string | null;
}

export interface McpConfigNpm {
  id: string;
  server_id: string;
  command: string | null; // npx, node, npm
  args: string | null; // JSON array
  env_required: string | null; // JSON array
  env_descriptions: string | null; // JSON object
  runtime: string | null; // default: node
  created_at: string | null;
  updated_at: string | null;
}

export interface McpConfigDocker {
  id: string;
  server_id: string;
  docker_image: string | null;
  docker_tag: string | null;
  docker_command: string | null; // JSON array
  env_required: string | null; // JSON array
  env_descriptions: string | null; // JSON object
  ports: string | null; // JSON object
  volumes: string | null; // JSON object
  network_mode: string | null;
  runtime: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface Tool {
  id: string;
  server_id: string;
  name: string;
  display_name: string | null;
  description: string | null;
  input_schema: string | null; // JSON Schema as TEXT
  example_usage: string | null;
  example_response: string | null;
  category: string | null;
  is_dangerous: number | null;
  requires_auth: number | null;
  display_order: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ToolParameter {
  id: string;
  tool_id: string;
  name: string;
  type: string | null;
  description: string | null;
  required: number | null;
  default_value: string | null;
  example_value: string | null;
  display_order: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface Category {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  icon: string | null;
  color: string | null;
  server_count: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface Tag {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  color: string | null;
  server_count: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface MarkdownContent {
  id: string;
  server_id: string;
  content_type: 'about' | 'readme' | 'faq' | 'tools' | null;
  content: string | null;
  content_html: string | null;
  word_count: number | null;
  estimated_reading_time_minutes: number | null;
  created_at: string | null;
  updated_at: string | null;
}

/**
 * Analysis result types
 */

export interface ConfigStats {
  totalServers: number;
  withNpmConfig: number;
  withDockerConfig: number;
  withNoConfig: number;
  withGithubInfo: number;
  withTools: number;
  npmConfigPercentage: number;
  dockerConfigPercentage: number;
  noConfigPercentage: number;
}

export interface HealthScoreDistribution {
  excellent: number; // >= 80
  good: number; // >= 60
  medium: number; // >= 40
  poor: number; // < 40
  unknown: number; // null
}

export interface ActivityMetrics {
  avgCommitFrequency: number;
  medianCommitFrequency: number;
  lastCommitLessThan1Month: number;
  lastCommitLessThan3Months: number;
  lastCommitLessThan6Months: number;
  lastCommitMoreThan6Months: number;
  noLastCommitData: number;
}

export interface PopularityMetrics {
  avgStars: number;
  medianStars: number;
  avgForks: number;
  medianForks: number;
  avgWatchers: number;
  medianWatchers: number;
  avgContributors: number;
  medianContributors: number;
  starsDistribution: {
    '0-100': number;
    '100-1000': number;
    '1000-10000': number;
    '>10000': number;
  };
  top10ByStars: Array<{
    name: string;
    stars: number;
    githubUrl: string | null;
  }>;
}

export interface QualityMetrics {
  hasReadme: number;
  hasLicense: number;
  hasContributing: number;
  hasCodeOfConduct: number;
  isArchived: number;
  isDisabled: number;
  isFork: number;
  primaryLanguages: Record<string, number>;
}

export interface CompletenessReport {
  tableName: string;
  fieldName: string;
  presentCount: number;
  totalCount: number;
  percentage: number;
  description: string;
}

export interface AnalysisReport {
  timestamp: string;
  configStats: ConfigStats;
  healthScoreDistribution: HealthScoreDistribution;
  activityMetrics: ActivityMetrics;
  popularityMetrics: PopularityMetrics;
  qualityMetrics: QualityMetrics;
  completenessReports: CompletenessReport[];
  insights: string[];
}
