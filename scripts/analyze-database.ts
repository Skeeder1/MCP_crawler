#!/usr/bin/env node
/**
 * MCP Servers Database Analysis Script
 *
 * Analyzes the SQLite database and generates comprehensive reports on:
 * - Configuration statistics (NPM, Docker)
 * - GitHub reliability metrics (health scores, activity, popularity, quality)
 * - Data completeness/proportions for all fields
 * - Actionable insights
 *
 * Outputs: Console (colored) + Markdown report
 */

import Database from 'better-sqlite3';
import chalk from 'chalk';
import Table from 'cli-table3';
import { formatDistanceToNow, parseISO, differenceInDays } from 'date-fns';
import * as fs from 'fs';
import * as path from 'path';
import type {
  Server,
  GithubInfo,
  NpmInfo,
  McpConfigNpm,
  McpConfigDocker,
  Tool,
  ConfigStats,
  HealthScoreDistribution,
  ActivityMetrics,
  PopularityMetrics,
  QualityMetrics,
  CompletenessReport,
  AnalysisReport,
} from './types/database.types';

// ============================================================================
// Database Connection
// ============================================================================

const DB_PATH = path.join(__dirname, '..', 'data', 'mcp_servers.db');
const REPORTS_DIR = path.join(__dirname, '..', 'reports');

if (!fs.existsSync(DB_PATH)) {
  console.error(chalk.red.bold(`❌ Database not found at: ${DB_PATH}`));
  process.exit(1);
}

const db = new Database(DB_PATH, { readonly: true });

// Ensure reports directory exists
if (!fs.existsSync(REPORTS_DIR)) {
  fs.mkdirSync(REPORTS_DIR, { recursive: true });
}

// ============================================================================
// Utility Functions
// ============================================================================

function calculatePercentage(count: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((count / total) * 10000) / 100;
}

function calculateMedian(values: number[]): number {
  if (values.length === 0) return 0;
  const sorted = values.slice().sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0
    ? (sorted[mid - 1] + sorted[mid]) / 2
    : sorted[mid];
}

function calculateAverage(values: number[]): number {
  if (values.length === 0) return 0;
  return Math.round((values.reduce((a, b) => a + b, 0) / values.length) * 100) / 100;
}

// ============================================================================
// Data Fetchers
// ============================================================================

function getAllServers(): Server[] {
  return db.prepare('SELECT * FROM servers').all() as Server[];
}

function getAllGithubInfo(): GithubInfo[] {
  return db.prepare('SELECT * FROM github_info').all() as GithubInfo[];
}

function getAllNpmInfo(): NpmInfo[] {
  return db.prepare('SELECT * FROM npm_info').all() as NpmInfo[];
}

function getAllMcpConfigNpm(): McpConfigNpm[] {
  return db.prepare('SELECT * FROM mcp_config_npm').all() as McpConfigNpm[];
}

function getAllMcpConfigDocker(): McpConfigDocker[] {
  return db.prepare('SELECT * FROM mcp_config_docker').all() as McpConfigDocker[];
}

function getAllTools(): Tool[] {
  return db.prepare('SELECT * FROM tools').all() as Tool[];
}

// ============================================================================
// Analyzers
// ============================================================================

/**
 * Analyze configuration statistics
 */
function analyzeConfigurations(): ConfigStats {
  const servers = getAllServers();
  const npmConfigs = getAllMcpConfigNpm();
  const dockerConfigs = getAllMcpConfigDocker();
  const githubInfos = getAllGithubInfo();
  const tools = getAllTools();

  const totalServers = servers.length;
  const withNpmConfig = npmConfigs.length;
  const withDockerConfig = dockerConfigs.length;
  const withNoConfig = totalServers - withNpmConfig - withDockerConfig;
  const withGithubInfo = githubInfos.length;

  // Count unique servers with tools
  const serversWithTools = new Set(tools.map(t => t.server_id)).size;

  return {
    totalServers,
    withNpmConfig,
    withDockerConfig,
    withNoConfig,
    withGithubInfo,
    withTools: serversWithTools,
    npmConfigPercentage: calculatePercentage(withNpmConfig, totalServers),
    dockerConfigPercentage: calculatePercentage(withDockerConfig, totalServers),
    noConfigPercentage: calculatePercentage(withNoConfig, totalServers),
  };
}

/**
 * Analyze GitHub health scores distribution
 */
function analyzeHealthScores(): HealthScoreDistribution {
  const githubInfos = getAllGithubInfo();

  const distribution: HealthScoreDistribution = {
    excellent: 0,
    good: 0,
    medium: 0,
    poor: 0,
    unknown: 0,
  };

  githubInfos.forEach((info) => {
    const score = info.github_health_score;
    if (score === null) {
      distribution.unknown++;
    } else if (score >= 80) {
      distribution.excellent++;
    } else if (score >= 60) {
      distribution.good++;
    } else if (score >= 40) {
      distribution.medium++;
    } else {
      distribution.poor++;
    }
  });

  return distribution;
}

/**
 * Analyze activity metrics
 */
function analyzeActivity(): ActivityMetrics {
  const githubInfos = getAllGithubInfo();

  const commitFrequencies = githubInfos
    .filter(g => g.commit_frequency !== null)
    .map(g => g.commit_frequency!);

  let lastCommitLessThan1Month = 0;
  let lastCommitLessThan3Months = 0;
  let lastCommitLessThan6Months = 0;
  let lastCommitMoreThan6Months = 0;
  let noLastCommitData = 0;

  const now = new Date();

  githubInfos.forEach((info) => {
    if (!info.github_last_commit) {
      noLastCommitData++;
      return;
    }

    try {
      const lastCommit = parseISO(info.github_last_commit);
      const daysSinceCommit = differenceInDays(now, lastCommit);

      if (daysSinceCommit < 30) {
        lastCommitLessThan1Month++;
      } else if (daysSinceCommit < 90) {
        lastCommitLessThan3Months++;
      } else if (daysSinceCommit < 180) {
        lastCommitLessThan6Months++;
      } else {
        lastCommitMoreThan6Months++;
      }
    } catch (error) {
      noLastCommitData++;
    }
  });

  return {
    avgCommitFrequency: calculateAverage(commitFrequencies),
    medianCommitFrequency: calculateMedian(commitFrequencies),
    lastCommitLessThan1Month,
    lastCommitLessThan3Months,
    lastCommitLessThan6Months,
    lastCommitMoreThan6Months,
    noLastCommitData,
  };
}

/**
 * Analyze popularity metrics
 */
function analyzePopularity(): PopularityMetrics {
  const githubInfos = getAllGithubInfo();

  const stars = githubInfos.filter(g => g.github_stars !== null).map(g => g.github_stars!);
  const forks = githubInfos.filter(g => g.github_forks !== null).map(g => g.github_forks!);
  const watchers = githubInfos.filter(g => g.github_watchers !== null).map(g => g.github_watchers!);
  const contributors = githubInfos.filter(g => g.contributors_count !== null).map(g => g.contributors_count!);

  // Stars distribution
  const starsDistribution = {
    '0-100': 0,
    '100-1000': 0,
    '1000-10000': 0,
    '>10000': 0,
  };

  githubInfos.forEach((info) => {
    const starCount = info.github_stars || 0;
    if (starCount <= 100) {
      starsDistribution['0-100']++;
    } else if (starCount <= 1000) {
      starsDistribution['100-1000']++;
    } else if (starCount <= 10000) {
      starsDistribution['1000-10000']++;
    } else {
      starsDistribution['>10000']++;
    }
  });

  // Top 10 by stars
  const top10ByStars = db
    .prepare(
      `
      SELECT s.name, gh.github_stars, gh.github_url
      FROM servers s
      INNER JOIN github_info gh ON gh.server_id = s.id
      WHERE gh.github_stars IS NOT NULL
      ORDER BY gh.github_stars DESC
      LIMIT 10
      `
    )
    .all() as Array<{ name: string; github_stars: number; github_url: string | null }>;

  return {
    avgStars: calculateAverage(stars),
    medianStars: calculateMedian(stars),
    avgForks: calculateAverage(forks),
    medianForks: calculateMedian(forks),
    avgWatchers: calculateAverage(watchers),
    medianWatchers: calculateMedian(watchers),
    avgContributors: calculateAverage(contributors),
    medianContributors: calculateMedian(contributors),
    starsDistribution,
    top10ByStars: top10ByStars.map((row) => ({
      name: row.name,
      stars: row.github_stars,
      githubUrl: row.github_url,
    })),
  };
}

/**
 * Analyze quality metrics
 */
function analyzeQuality(): QualityMetrics {
  const githubInfos = getAllGithubInfo();

  let hasReadme = 0;
  let hasLicense = 0;
  let hasContributing = 0;
  let hasCodeOfConduct = 0;
  let isArchived = 0;
  let isDisabled = 0;
  let isFork = 0;

  const primaryLanguages: Record<string, number> = {};

  githubInfos.forEach((info) => {
    if (info.has_readme === 1) hasReadme++;
    if (info.has_license === 1) hasLicense++;
    if (info.has_contributing === 1) hasContributing++;
    if (info.has_code_of_conduct === 1) hasCodeOfConduct++;
    if (info.is_archived === 1) isArchived++;
    if (info.is_disabled === 1) isDisabled++;
    if (info.is_fork === 1) isFork++;

    if (info.primary_language) {
      primaryLanguages[info.primary_language] =
        (primaryLanguages[info.primary_language] || 0) + 1;
    }
  });

  return {
    hasReadme,
    hasLicense,
    hasContributing,
    hasCodeOfConduct,
    isArchived,
    isDisabled,
    isFork,
    primaryLanguages,
  };
}

/**
 * Analyze data completeness for all fields
 */
function analyzeCompleteness(): CompletenessReport[] {
  const servers = getAllServers();
  const githubInfos = getAllGithubInfo();
  const npmInfos = getAllNpmInfo();
  const npmConfigs = getAllMcpConfigNpm();
  const dockerConfigs = getAllMcpConfigDocker();
  const tools = getAllTools();

  const reports: CompletenessReport[] = [];
  const totalServers = servers.length;

  // Helper to add report
  const addReport = (
    tableName: string,
    fieldName: string,
    presentCount: number,
    totalCount: number,
    description: string
  ) => {
    reports.push({
      tableName,
      fieldName,
      presentCount,
      totalCount,
      percentage: calculatePercentage(presentCount, totalCount),
      description,
    });
  };

  // Servers table
  addReport('servers', 'display_name', servers.filter(s => s.display_name).length, totalServers, 'Servers with display name');
  addReport('servers', 'tagline', servers.filter(s => s.tagline).length, totalServers, 'Servers with tagline');
  addReport('servers', 'short_description', servers.filter(s => s.short_description).length, totalServers, 'Servers with description');
  addReport('servers', 'logo_url', servers.filter(s => s.logo_url).length, totalServers, 'Servers with logo');
  addReport('servers', 'homepage_url', servers.filter(s => s.homepage_url).length, totalServers, 'Servers with homepage');
  addReport('servers', 'creator_name', servers.filter(s => s.creator_name).length, totalServers, 'Servers with creator name');

  // GitHub info
  addReport('github_info', 'linked', githubInfos.length, totalServers, 'Servers with GitHub info');
  addReport('github_info', 'github_stars', githubInfos.filter(g => g.github_stars !== null).length, totalServers, 'Servers with GitHub stars data');
  addReport('github_info', 'github_last_commit', githubInfos.filter(g => g.github_last_commit).length, totalServers, 'Servers with last commit data');
  addReport('github_info', 'commit_frequency', githubInfos.filter(g => g.commit_frequency !== null).length, totalServers, 'Servers with commit frequency');
  addReport('github_info', 'license', githubInfos.filter(g => g.license).length, totalServers, 'Servers with license');
  addReport('github_info', 'primary_language', githubInfos.filter(g => g.primary_language).length, totalServers, 'Servers with primary language');
  addReport('github_info', 'github_health_score', githubInfos.filter(g => g.github_health_score !== null).length, totalServers, 'Servers with health score');
  addReport('github_info', 'contributors_count', githubInfos.filter(g => g.contributors_count !== null).length, totalServers, 'Servers with contributors data');

  // NPM info
  addReport('npm_info', 'npm_package', npmInfos.length, totalServers, 'Servers with NPM package info');
  addReport('npm_info', 'npm_downloads_weekly', npmInfos.filter(n => n.npm_downloads_weekly !== null).length, totalServers, 'Servers with NPM weekly downloads');

  // Configs
  addReport('mcp_config_npm', 'config', npmConfigs.length, totalServers, 'Servers with NPM config');
  addReport('mcp_config_docker', 'config', dockerConfigs.length, totalServers, 'Servers with Docker config');

  // Tools
  const serversWithTools = new Set(tools.map(t => t.server_id)).size;
  addReport('tools', 'tools', serversWithTools, totalServers, 'Servers with MCP tools defined');
  addReport('tools', 'total_tools', tools.length, totalServers, 'Total MCP tools in database');

  return reports.sort((a, b) => b.percentage - a.percentage);
}

/**
 * Generate actionable insights
 */
function generateInsights(
  configStats: ConfigStats,
  healthScores: HealthScoreDistribution,
  activity: ActivityMetrics,
  popularity: PopularityMetrics,
  quality: QualityMetrics
): string[] {
  const insights: string[] = [];
  const total = configStats.totalServers;

  // Configuration insights
  if (configStats.withNoConfig > total * 0.8) {
    insights.push(
      `⚠️  ${configStats.withNoConfig} serveurs (${configStats.noConfigPercentage}%) n'ont AUCUNE configuration d'installation (NPM/Docker)`
    );
  }

  // Health score insights
  if (healthScores.poor > 0) {
    insights.push(
      `🔴 ${healthScores.poor} serveurs ont un score de santé FAIBLE (<40%)`
    );
  }

  // Activity insights
  if (activity.lastCommitMoreThan6Months > 0) {
    insights.push(
      `⏰ ${activity.lastCommitMoreThan6Months} serveurs n'ont PAS eu de commit depuis plus de 6 mois`
    );
  }

  // Quality insights
  if (quality.isArchived > 0) {
    insights.push(`📦 ${quality.isArchived} serveurs sont ARCHIVÉS sur GitHub`);
  }

  if (quality.hasLicense < total * 0.8) {
    insights.push(
      `⚖️  Seulement ${quality.hasLicense} serveurs (${calculatePercentage(quality.hasLicense, total)}%) ont une LICENSE`
    );
  }

  // Positive insights
  if (healthScores.excellent > total * 0.5) {
    insights.push(
      `✅ ${healthScores.excellent} serveurs (${calculatePercentage(healthScores.excellent, total)}%) ont un EXCELLENT score de santé (≥80%)`
    );
  }

  if (activity.lastCommitLessThan1Month > total * 0.3) {
    insights.push(
      `🚀 ${activity.lastCommitLessThan1Month} serveurs sont ACTIFS (commit dans le dernier mois)`
    );
  }

  // Popularity insights
  const topLanguages = Object.entries(quality.primaryLanguages)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

  if (topLanguages.length > 0) {
    const langStr = topLanguages.map(([lang, count]) => `${lang} (${count})`).join(', ');
    insights.push(`💻 Langages principaux: ${langStr}`);
  }

  return insights;
}

// ============================================================================
// Formatters
// ============================================================================

/**
 * Print colored console report
 */
function printConsoleReport(report: AnalysisReport): void {
  console.log('\n');
  console.log(chalk.cyan.bold('═'.repeat(70)));
  console.log(chalk.cyan.bold('   🔍 ANALYSE BASE DE DONNÉES MCP SERVERS'));
  console.log(chalk.gray(`   Date: ${report.timestamp}`));
  console.log(chalk.cyan.bold('═'.repeat(70)));

  // Configuration Statistics
  console.log('\n' + chalk.yellow.bold('📊 STATISTIQUES GÉNÉRALES'));
  const generalTable = new Table({
    head: [chalk.white('Métrique'), chalk.white('Valeur')],
    style: { head: [], border: ['gray'] },
  });
  generalTable.push(
    ['Total Serveurs', chalk.green(report.configStats.totalServers.toString())],
    ['Avec GitHub Info', `${report.configStats.withGithubInfo} (${calculatePercentage(report.configStats.withGithubInfo, report.configStats.totalServers)}%)`],
    ['Avec Outils (Tools)', `${report.configStats.withTools} serveurs / ${getAllTools().length} tools`]
  );
  console.log(generalTable.toString());

  // Configurations
  console.log('\n' + chalk.yellow.bold('🔧 CONFIGURATIONS D\'INSTALLATION'));
  const configTable = new Table({
    head: [chalk.white('Type Config'), chalk.white('Count'), chalk.white('%')],
    style: { head: [], border: ['gray'] },
  });
  configTable.push(
    ['NPM Config', report.configStats.withNpmConfig.toString(), chalk.red(`${report.configStats.npmConfigPercentage}%`)],
    ['Docker Config', report.configStats.withDockerConfig.toString(), chalk.red(`${report.configStats.dockerConfigPercentage}%`)],
    ['Sans Config', chalk.red(report.configStats.withNoConfig.toString()), chalk.red.bold(`${report.configStats.noConfigPercentage}%`)]
  );
  console.log(configTable.toString());

  // Health Scores
  console.log('\n' + chalk.yellow.bold('⭐ FIABILITÉ GITHUB (Health Score 0-100)'));
  const healthTable = new Table({
    head: [chalk.white('Catégorie'), chalk.white('Seuil'), chalk.white('Count'), chalk.white('%')],
    style: { head: [], border: ['gray'] },
  });
  const totalWithGithub = report.configStats.withGithubInfo;
  healthTable.push(
    [chalk.green('Excellent'), '≥80%', chalk.green(report.healthScoreDistribution.excellent.toString()), chalk.green(`${calculatePercentage(report.healthScoreDistribution.excellent, totalWithGithub)}%`)],
    [chalk.blue('Bon'), '≥60%', report.healthScoreDistribution.good.toString(), `${calculatePercentage(report.healthScoreDistribution.good, totalWithGithub)}%`],
    [chalk.yellow('Moyen'), '≥40%', report.healthScoreDistribution.medium.toString(), `${calculatePercentage(report.healthScoreDistribution.medium, totalWithGithub)}%`],
    [chalk.red('Faible'), '<40%', chalk.red(report.healthScoreDistribution.poor.toString()), chalk.red(`${calculatePercentage(report.healthScoreDistribution.poor, totalWithGithub)}%`)],
    [chalk.gray('Inconnu'), 'null', chalk.gray(report.healthScoreDistribution.unknown.toString()), chalk.gray(`${calculatePercentage(report.healthScoreDistribution.unknown, totalWithGithub)}%`)]
  );
  console.log(healthTable.toString());

  // Activity Metrics
  console.log('\n' + chalk.yellow.bold('🚀 ACTIVITÉ RÉCENTE'));
  const activityTable = new Table({
    head: [chalk.white('Métrique'), chalk.white('Valeur')],
    style: { head: [], border: ['gray'] },
  });
  activityTable.push(
    ['Commit Frequency (moy.)', `${report.activityMetrics.avgCommitFrequency} commits/30j`],
    ['Commit Frequency (médiane)', `${report.activityMetrics.medianCommitFrequency} commits/30j`],
    ['Dernier commit < 1 mois', chalk.green(`${report.activityMetrics.lastCommitLessThan1Month} serveurs`)],
    ['Dernier commit < 3 mois', `${report.activityMetrics.lastCommitLessThan3Months} serveurs`],
    ['Dernier commit < 6 mois', chalk.yellow(`${report.activityMetrics.lastCommitLessThan6Months} serveurs`)],
    ['Dernier commit > 6 mois', chalk.red(`${report.activityMetrics.lastCommitMoreThan6Months} serveurs`)],
    ['Sans données', chalk.gray(`${report.activityMetrics.noLastCommitData} serveurs`)]
  );
  console.log(activityTable.toString());

  // Popularity Metrics
  console.log('\n' + chalk.yellow.bold('🌟 POPULARITÉ'));
  const popularityTable = new Table({
    head: [chalk.white('Métrique'), chalk.white('Moyenne'), chalk.white('Médiane')],
    style: { head: [], border: ['gray'] },
  });
  popularityTable.push(
    ['GitHub Stars', report.popularityMetrics.avgStars.toString(), report.popularityMetrics.medianStars.toString()],
    ['GitHub Forks', report.popularityMetrics.avgForks.toString(), report.popularityMetrics.medianForks.toString()],
    ['GitHub Watchers', report.popularityMetrics.avgWatchers.toString(), report.popularityMetrics.medianWatchers.toString()],
    ['Contributors', report.popularityMetrics.avgContributors.toString(), report.popularityMetrics.medianContributors.toString()]
  );
  console.log(popularityTable.toString());

  // Stars Distribution
  console.log('\n' + chalk.yellow.bold('📊 DISTRIBUTION DES STARS'));
  const starsTable = new Table({
    head: [chalk.white('Tranche'), chalk.white('Count'), chalk.white('%')],
    style: { head: [], border: ['gray'] },
  });
  Object.entries(report.popularityMetrics.starsDistribution).forEach(([range, count]) => {
    starsTable.push([range, count.toString(), `${calculatePercentage(count, totalWithGithub)}%`]);
  });
  console.log(starsTable.toString());

  // Top 10
  console.log('\n' + chalk.yellow.bold('🏆 TOP 10 SERVEURS PAR STARS'));
  const topTable = new Table({
    head: [chalk.white('#'), chalk.white('Nom'), chalk.white('Stars'), chalk.white('GitHub URL')],
    style: { head: [], border: ['gray'] },
  });
  report.popularityMetrics.top10ByStars.forEach((server, idx) => {
    topTable.push([
      (idx + 1).toString(),
      server.name,
      chalk.yellow(server.stars.toLocaleString()),
      server.githubUrl || 'N/A'
    ]);
  });
  console.log(topTable.toString());

  // Quality Metrics
  console.log('\n' + chalk.yellow.bold('✅ QUALITÉ DES PROJETS'));
  const qualityTable = new Table({
    head: [chalk.white('Indicateur'), chalk.white('Count'), chalk.white('%')],
    style: { head: [], border: ['gray'] },
  });
  qualityTable.push(
    ['Has README', report.qualityMetrics.hasReadme.toString(), `${calculatePercentage(report.qualityMetrics.hasReadme, totalWithGithub)}%`],
    ['Has LICENSE', report.qualityMetrics.hasLicense.toString(), `${calculatePercentage(report.qualityMetrics.hasLicense, totalWithGithub)}%`],
    ['Has CONTRIBUTING', report.qualityMetrics.hasContributing.toString(), `${calculatePercentage(report.qualityMetrics.hasContributing, totalWithGithub)}%`],
    ['Has CODE_OF_CONDUCT', report.qualityMetrics.hasCodeOfConduct.toString(), `${calculatePercentage(report.qualityMetrics.hasCodeOfConduct, totalWithGithub)}%`],
    ['', '', ''],
    [chalk.red('Archived'), chalk.red(report.qualityMetrics.isArchived.toString()), chalk.red(`${calculatePercentage(report.qualityMetrics.isArchived, totalWithGithub)}%`)],
    [chalk.red('Disabled'), chalk.red(report.qualityMetrics.isDisabled.toString()), chalk.red(`${calculatePercentage(report.qualityMetrics.isDisabled, totalWithGithub)}%`)],
    [chalk.yellow('Fork'), report.qualityMetrics.isFork.toString(), `${calculatePercentage(report.qualityMetrics.isFork, totalWithGithub)}%`]
  );
  console.log(qualityTable.toString());

  // Completeness Report (Top 20)
  console.log('\n' + chalk.yellow.bold('📈 COMPLÉTUDE DES DONNÉES (Top 20)'));
  const completenessTable = new Table({
    head: [chalk.white('Table'), chalk.white('Champ'), chalk.white('Présent'), chalk.white('Total'), chalk.white('%')],
    style: { head: [], border: ['gray'] },
  });
  report.completenessReports.slice(0, 20).forEach((item) => {
    const color = item.percentage >= 80 ? chalk.green : item.percentage >= 50 ? chalk.yellow : chalk.red;
    completenessTable.push([
      item.tableName,
      item.fieldName,
      item.presentCount.toString(),
      item.totalCount.toString(),
      color(`${item.percentage}%`)
    ]);
  });
  console.log(completenessTable.toString());

  // Insights
  console.log('\n' + chalk.yellow.bold('💡 INSIGHTS CLÉS'));
  report.insights.forEach((insight) => {
    console.log(`  ${insight}`);
  });

  console.log('\n' + chalk.cyan.bold('═'.repeat(70)));
  console.log(chalk.green.bold('✅ Analyse terminée !'));
  console.log(chalk.cyan.bold('═'.repeat(70)) + '\n');
}

/**
 * Generate Markdown report
 */
function generateMarkdownReport(report: AnalysisReport): string {
  let md = '';

  md += `# Analyse Base de Données MCP Servers\n\n`;
  md += `**Date:** ${report.timestamp}\n\n`;
  md += `---\n\n`;

  // General Stats
  md += `## 📊 Statistiques Générales\n\n`;
  md += `| Métrique | Valeur |\n`;
  md += `|----------|--------|\n`;
  md += `| Total Serveurs | ${report.configStats.totalServers} |\n`;
  md += `| Avec GitHub Info | ${report.configStats.withGithubInfo} (${calculatePercentage(report.configStats.withGithubInfo, report.configStats.totalServers)}%) |\n`;
  md += `| Avec Outils (Tools) | ${report.configStats.withTools} serveurs / ${getAllTools().length} tools |\n\n`;

  // Configurations
  md += `## 🔧 Configurations d'Installation\n\n`;
  md += `| Type Config | Count | % |\n`;
  md += `|-------------|-------|---|\n`;
  md += `| NPM Config | ${report.configStats.withNpmConfig} | ${report.configStats.npmConfigPercentage}% |\n`;
  md += `| Docker Config | ${report.configStats.withDockerConfig} | ${report.configStats.dockerConfigPercentage}% |\n`;
  md += `| **Sans Config** | **${report.configStats.withNoConfig}** | **${report.configStats.noConfigPercentage}%** |\n\n`;

  // Health Scores
  md += `## ⭐ Fiabilité GitHub (Health Score)\n\n`;
  md += `| Catégorie | Seuil | Count | % |\n`;
  md += `|-----------|-------|-------|---|\n`;
  const totalWithGithub = report.configStats.withGithubInfo;
  md += `| Excellent | ≥80% | ${report.healthScoreDistribution.excellent} | ${calculatePercentage(report.healthScoreDistribution.excellent, totalWithGithub)}% |\n`;
  md += `| Bon | ≥60% | ${report.healthScoreDistribution.good} | ${calculatePercentage(report.healthScoreDistribution.good, totalWithGithub)}% |\n`;
  md += `| Moyen | ≥40% | ${report.healthScoreDistribution.medium} | ${calculatePercentage(report.healthScoreDistribution.medium, totalWithGithub)}% |\n`;
  md += `| Faible | <40% | ${report.healthScoreDistribution.poor} | ${calculatePercentage(report.healthScoreDistribution.poor, totalWithGithub)}% |\n`;
  md += `| Inconnu | null | ${report.healthScoreDistribution.unknown} | ${calculatePercentage(report.healthScoreDistribution.unknown, totalWithGithub)}% |\n\n`;

  // Activity
  md += `## 🚀 Activité Récente\n\n`;
  md += `| Métrique | Valeur |\n`;
  md += `|----------|--------|\n`;
  md += `| Commit Frequency (moyenne) | ${report.activityMetrics.avgCommitFrequency} commits/30j |\n`;
  md += `| Commit Frequency (médiane) | ${report.activityMetrics.medianCommitFrequency} commits/30j |\n`;
  md += `| Dernier commit < 1 mois | ${report.activityMetrics.lastCommitLessThan1Month} serveurs |\n`;
  md += `| Dernier commit < 3 mois | ${report.activityMetrics.lastCommitLessThan3Months} serveurs |\n`;
  md += `| Dernier commit < 6 mois | ${report.activityMetrics.lastCommitLessThan6Months} serveurs |\n`;
  md += `| Dernier commit > 6 mois | ${report.activityMetrics.lastCommitMoreThan6Months} serveurs |\n`;
  md += `| Sans données | ${report.activityMetrics.noLastCommitData} serveurs |\n\n`;

  // Popularity
  md += `## 🌟 Popularité\n\n`;
  md += `| Métrique | Moyenne | Médiane |\n`;
  md += `|----------|---------|----------|\n`;
  md += `| GitHub Stars | ${report.popularityMetrics.avgStars} | ${report.popularityMetrics.medianStars} |\n`;
  md += `| GitHub Forks | ${report.popularityMetrics.avgForks} | ${report.popularityMetrics.medianForks} |\n`;
  md += `| GitHub Watchers | ${report.popularityMetrics.avgWatchers} | ${report.popularityMetrics.medianWatchers} |\n`;
  md += `| Contributors | ${report.popularityMetrics.avgContributors} | ${report.popularityMetrics.medianContributors} |\n\n`;

  // Stars Distribution
  md += `### Distribution des Stars\n\n`;
  md += `| Tranche | Count | % |\n`;
  md += `|---------|-------|---|\n`;
  Object.entries(report.popularityMetrics.starsDistribution).forEach(([range, count]) => {
    md += `| ${range} | ${count} | ${calculatePercentage(count, totalWithGithub)}% |\n`;
  });
  md += `\n`;

  // Top 10
  md += `### 🏆 Top 10 Serveurs par Stars\n\n`;
  md += `| # | Nom | Stars | GitHub URL |\n`;
  md += `|---|-----|-------|------------|\n`;
  report.popularityMetrics.top10ByStars.forEach((server, idx) => {
    md += `| ${idx + 1} | ${server.name} | ${server.stars.toLocaleString()} | ${server.githubUrl || 'N/A'} |\n`;
  });
  md += `\n`;

  // Quality
  md += `## ✅ Qualité des Projets\n\n`;
  md += `| Indicateur | Count | % |\n`;
  md += `|------------|-------|---|\n`;
  md += `| Has README | ${report.qualityMetrics.hasReadme} | ${calculatePercentage(report.qualityMetrics.hasReadme, totalWithGithub)}% |\n`;
  md += `| Has LICENSE | ${report.qualityMetrics.hasLicense} | ${calculatePercentage(report.qualityMetrics.hasLicense, totalWithGithub)}% |\n`;
  md += `| Has CONTRIBUTING | ${report.qualityMetrics.hasContributing} | ${calculatePercentage(report.qualityMetrics.hasContributing, totalWithGithub)}% |\n`;
  md += `| Has CODE_OF_CONDUCT | ${report.qualityMetrics.hasCodeOfConduct} | ${calculatePercentage(report.qualityMetrics.hasCodeOfConduct, totalWithGithub)}% |\n`;
  md += `| Archived | ${report.qualityMetrics.isArchived} | ${calculatePercentage(report.qualityMetrics.isArchived, totalWithGithub)}% |\n`;
  md += `| Disabled | ${report.qualityMetrics.isDisabled} | ${calculatePercentage(report.qualityMetrics.isDisabled, totalWithGithub)}% |\n`;
  md += `| Fork | ${report.qualityMetrics.isFork} | ${calculatePercentage(report.qualityMetrics.isFork, totalWithGithub)}% |\n\n`;

  // Primary Languages
  md += `### Langages Primaires\n\n`;
  const sortedLangs = Object.entries(report.qualityMetrics.primaryLanguages)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);
  md += `| Langage | Count | % |\n`;
  md += `|---------|-------|---|\n`;
  sortedLangs.forEach(([lang, count]) => {
    md += `| ${lang} | ${count} | ${calculatePercentage(count, totalWithGithub)}% |\n`;
  });
  md += `\n`;

  // Completeness
  md += `## 📈 Complétude des Données\n\n`;
  md += `| Table | Champ | Présent | Total | % |\n`;
  md += `|-------|-------|---------|-------|---|\n`;
  report.completenessReports.forEach((item) => {
    md += `| ${item.tableName} | ${item.fieldName} | ${item.presentCount} | ${item.totalCount} | ${item.percentage}% |\n`;
  });
  md += `\n`;

  // Insights
  md += `## 💡 Insights Clés\n\n`;
  report.insights.forEach((insight) => {
    md += `- ${insight}\n`;
  });
  md += `\n`;

  md += `---\n\n`;
  md += `*Rapport généré automatiquement par analyze-database.ts*\n`;

  return md;
}

// ============================================================================
// Main Execution
// ============================================================================

function main(): void {
  console.log(chalk.cyan('\n🔍 Démarrage de l\'analyse de la base de données...\n'));

  try {
    // Run all analyzers
    const configStats = analyzeConfigurations();
    const healthScores = analyzeHealthScores();
    const activityMetrics = analyzeActivity();
    const popularityMetrics = analyzePopularity();
    const qualityMetrics = analyzeQuality();
    const completenessReports = analyzeCompleteness();
    const insights = generateInsights(
      configStats,
      healthScores,
      activityMetrics,
      popularityMetrics,
      qualityMetrics
    );

    // Build report
    const report: AnalysisReport = {
      timestamp: new Date().toISOString(),
      configStats,
      healthScoreDistribution: healthScores,
      activityMetrics,
      popularityMetrics,
      qualityMetrics,
      completenessReports,
      insights,
    };

    // Print to console
    printConsoleReport(report);

    // Generate Markdown
    const markdown = generateMarkdownReport(report);
    const reportFileName = `db-analysis-${new Date().toISOString().split('T')[0]}.md`;
    const reportPath = path.join(REPORTS_DIR, reportFileName);
    fs.writeFileSync(reportPath, markdown, 'utf8');

    console.log(chalk.green(`\n📄 Rapport Markdown généré: ${reportPath}\n`));
  } catch (error) {
    console.error(chalk.red('\n❌ Erreur lors de l\'analyse:\n'));
    console.error(error);
    process.exit(1);
  } finally {
    db.close();
  }
}

// Run
main();
