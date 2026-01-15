#!/usr/bin/env node

/**
 * BMAD Terminal Progress Dashboard
 * Interactive terminal display of project progress with visual progress bars
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Import progress calculation functions from update-progress.js
const {
  scanProject,
  calculatePlanningProgress,
  calculateDevelopmentProgress,
  calculateOverallProgress,
  loadMilestoneState,
  determineMilestones
} = require('./update-progress');

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
  bgBlack: '\x1b[40m',
  bgBlue: '\x1b[44m'
};

// Box drawing characters (with ASCII fallbacks)
const box = {
  // Double lines
  topLeft: '╔',
  topRight: '╗',
  bottomLeft: '╚',
  bottomRight: '╝',
  horizontal: '═',
  vertical: '║',
  // Single lines
  sTopLeft: '┌',
  sTopRight: '┐',
  sBottomLeft: '└',
  sBottomRight: '┘',
  sHorizontal: '─',
  sVertical: '│',
  // Junctions
  cross: '╬',
  topJunction: '╦',
  bottomJunction: '╩',
  leftJunction: '╠',
  rightJunction: '╣'
};

// ASCII fallbacks for simple mode
const asciiBox = {
  topLeft: '+',
  topRight: '+',
  bottomLeft: '+',
  bottomRight: '+',
  horizontal: '-',
  vertical: '|',
  sTopLeft: '+',
  sTopRight: '+',
  sBottomLeft: '+',
  sBottomRight: '+',
  sHorizontal: '-',
  sVertical: '|',
  cross: '+',
  topJunction: '+',
  bottomJunction: '+',
  leftJunction: '+',
  rightJunction: '+'
};

// Configuration
const config = {
  autoRefresh: false,
  refreshInterval: 30,
  simpleMode: false,
  compactMode: false,
  lastUpdate: 0,
  fileCache: new Map(),
  dataCache: null
};

// Parse command line arguments
function parseArgs() {
  const args = process.argv.slice(2);

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--auto':
        const interval = parseInt(args[++i]);
        if (interval && interval >= 10) {
          config.autoRefresh = true;
          config.refreshInterval = interval;
        } else {
          console.log('Auto-refresh interval must be at least 10 seconds');
          process.exit(1);
        }
        break;
      case '--simple':
        config.simpleMode = true;
        break;
      case '--compact':
        config.compactMode = true;
        break;
      case '--help':
      case '-h':
        showHelp();
        process.exit(0);
    }
  }
}

// Show help message
function showHelp() {
  console.log(`
BMAD Terminal Progress Dashboard

Usage: npm run progress:terminal [options]

Options:
  --auto <seconds>  Enable auto-refresh (minimum 10 seconds)
  --simple          Use ASCII characters only (no Unicode)
  --compact         Show compact view (percentages only)
  --help, -h        Show this help message

Interactive Controls:
  r    Refresh display
  a    Toggle auto-refresh
  m    Manage milestones (skip/mark done)
  q    Quit
  ?    Show help

Examples:
  npm run progress:terminal                  # Manual refresh mode
  npm run progress:terminal -- --auto 15     # Auto-refresh every 15 seconds
  npm run progress:terminal -- --simple      # ASCII-only mode
`);
}

// Load configuration
function loadConfig() {
  const configPath = path.join(process.cwd(), '.bmad-core/core-config.yaml');

  try {
    // Simple config loading - reuse from update-progress.js if needed
    return {
      prdFile: 'docs/prd.md',
      architectureFile: 'docs/architecture.md',
      prdShardedLocation: 'docs/prd',
      architectureShardedLocation: 'docs/architecture',
      devStoryLocation: 'docs/stories',
      epicFilePattern: /epic-(\d+).*\.md$/i
    };
  } catch (error) {
    return null;
  }
}

// Check if files have changed since last scan
function hasFilesChanged(projectConfig) {
  const paths = [
    projectConfig.devStoryLocation,
    projectConfig.prdShardedLocation,
    projectConfig.architectureShardedLocation
  ];

  let changed = false;

  for (const dirPath of paths) {
    try {
      const stats = fs.statSync(dirPath);
      const cached = config.fileCache.get(dirPath);

      if (!cached || stats.mtimeMs > cached) {
        config.fileCache.set(dirPath, stats.mtimeMs);
        changed = true;
      }
    } catch {
      // Directory doesn't exist, skip
    }
  }

  return changed;
}

// Generate progress bar for terminal
function generateProgressBar(percentage, width = 20, useColors = true) {
  const filled = Math.round((percentage / 100) * width);
  const empty = width - filled;

  let bar = '';

  // Color based on percentage
  if (useColors && !config.simpleMode) {
    if (percentage >= 80) {
      bar += colors.green;
    } else if (percentage >= 50) {
      bar += colors.yellow;
    } else {
      bar += colors.red;
    }
  }

  if (config.simpleMode) {
    bar += '#'.repeat(filled) + '-'.repeat(empty);
  } else {
    bar += '█'.repeat(filled) + '░'.repeat(empty);
  }

  if (useColors && !config.simpleMode) {
    bar += colors.reset;
  }

  return bar;
}

// Generate inverted progress bar (for metrics where lower is better, like outstanding tasks)
// Colors: low % = green (good), high % = red (bad)
function generateInvertedProgressBar(percentage, width = 20, useColors = true) {
  const filled = Math.round((percentage / 100) * width);
  const empty = width - filled;

  let bar = '';

  // Inverted color: low percentage = green, high = red
  if (useColors && !config.simpleMode) {
    if (percentage <= 20) {
      bar += colors.green;   // 0-20% outstanding = excellent
    } else if (percentage <= 50) {
      bar += colors.yellow;  // 21-50% outstanding = acceptable
    } else {
      bar += colors.red;     // >50% outstanding = needs attention
    }
  }

  if (config.simpleMode) {
    bar += '#'.repeat(filled) + '-'.repeat(empty);
  } else {
    bar += '█'.repeat(filled) + '░'.repeat(empty);
  }

  if (useColors && !config.simpleMode) {
    bar += colors.reset;
  }

  return bar;
}

// Generate segmented progress bar showing planning vs development portions
function generateSegmentedProgressBar(overallPct, planningPct, developmentPct, width = 60) {
  // Calculate segments based on 40% planning, 60% development weighting
  const planningWeight = 0.4;
  const developmentWeight = 0.6;

  // Calculate how many characters each segment should be
  const planningChars = Math.round((planningPct / 100) * width * planningWeight);
  const developmentChars = Math.round((developmentPct / 100) * width * developmentWeight);
  const totalFilled = planningChars + developmentChars;
  const empty = width - totalFilled;

  let bar = '';

  if (config.simpleMode) {
    // Simple mode: just use different characters
    bar += 'P'.repeat(planningChars) + 'D'.repeat(developmentChars) + '-'.repeat(empty);
  } else {
    // Planning segment (cyan/blue)
    if (planningChars > 0) {
      bar += colors.cyan + '█'.repeat(planningChars) + colors.reset;
    }

    // Development segment (green)
    if (developmentChars > 0) {
      bar += colors.green + '█'.repeat(developmentChars) + colors.reset;
    }

    // Empty segment
    if (empty > 0) {
      bar += colors.dim + '░'.repeat(empty) + colors.reset;
    }
  }

  return bar;
}

// Clear screen and move cursor to top
function clearScreen() {
  console.clear();
  process.stdout.write('\x1b[H');
}

// Calculate epic progress (from update-progress.js)
function calculateEpicProgress(epic) {
  if (!epic || epic.stories.length === 0) return 0;

  let completed = 0;
  for (const story of epic.stories) {
    if (story.percentage === 100) {
      completed++;
    } else if (story.percentage > 0) {
      completed += story.percentage / 100;
    }
  }

  return Math.round((completed / epic.stories.length) * 100);
}

// Render the dashboard
function renderDashboard(data) {
  const b = config.simpleMode ? asciiBox : box;
  const width = 76;
  const colWidth = 24;

  clearScreen();

  // Header
  console.log(b.topLeft + b.horizontal.repeat(width - 2) + b.topRight);
  const title = 'BMAD PROJECT PROGRESS DASHBOARD';
  const padding = Math.floor((width - title.length - 2) / 2);
  console.log(b.vertical + ' '.repeat(padding) + colors.bright + colors.cyan + title + colors.reset + ' '.repeat(width - padding - title.length - 2) + b.vertical);

  const now = new Date();
  // Use fixed-width format to prevent layout shift
  const timeStr = now.toISOString().substring(11, 19);  // "19:38:27" - always 8 chars
  const dateStr = now.toISOString().substring(0, 10);   // "2025-10-07" - always 10 chars
  const timestamp = `Updated: ${dateStr} ${timeStr}`;  // Fixed at 29 chars
  const tsPadding = Math.floor((width - timestamp.length - 2) / 2);
  console.log(b.vertical + ' '.repeat(tsPadding) + colors.dim + timestamp + colors.reset + ' '.repeat(width - tsPadding - timestamp.length - 2) + b.vertical);

  // Top border of grid
  console.log(b.leftJunction + b.horizontal.repeat(width - 2) + b.rightJunction);

  // Row 1: Overall Progress (Full Width)
  const overallLabel = `🎯 OVERALL PROGRESS: ${data.overall}%`;
  console.log(b.vertical + padCell(overallLabel, width - 2) + b.vertical);

  // Single-color progress bar (red <50%, yellow 50-80%, green >80%)
  const overallBar = ' ' + generateProgressBar(data.overall, width - 4) + ' ';
  console.log(b.vertical + padCell(overallBar, width - 2) + b.vertical);

  // Border after Row 1 (2 columns: Planning + Next Milestone spanning 2 cols)
  const nextMilestoneWidth = colWidth * 2 + 1;  // Span 2 columns (49 chars)
  console.log(b.leftJunction + b.horizontal.repeat(colWidth) + b.topJunction + b.horizontal.repeat(nextMilestoneWidth) + b.rightJunction);

  // Row 2: Planning (24 chars) | Next Milestone (49 chars)
  console.log(b.vertical + padCell(`📋 PLANNING: ${data.planning}%`, colWidth) +
              b.vertical + padCell(`🏁 NEXT MILESTONE`, nextMilestoneWidth) + b.vertical);

  // Row 2 Line 2: Planning progress bar | Next Milestone name (49 chars - plenty of space!)
  const planningBar = ' ' + generateProgressBar(data.planning, colWidth - 2) + ' ';
  console.log(b.vertical + padCell(planningBar, colWidth) +
              b.vertical + padCell(data.nextMilestone, nextMilestoneWidth) + b.vertical);

  // Row 2 Line 3: Empty | Requirement text (49 chars)
  console.log(b.vertical + padCell('', colWidth) +
              b.vertical + padCell(data.nextStatus, nextMilestoneWidth) + b.vertical);

  // Border after Row 2 (back to 3 columns for Row 3)
  console.log(b.leftJunction + b.horizontal.repeat(colWidth) + b.cross + b.horizontal.repeat(colWidth) + b.cross + b.horizontal.repeat(colWidth) + b.rightJunction);

  // Row 3: Development, Epic 1, Epic 2
  const epic1Progress = data.epic1 ? data.epic1.progress : 0;
  const epic2Progress = data.epic2 ? data.epic2.progress : 0;

  console.log(b.vertical + padCell(`🚀 DEVELOPMENT: ${data.development}%`, colWidth) +
              b.vertical + padCell(`📦 EPIC 1: ${epic1Progress}%`, colWidth) +
              b.vertical + padCell(`📦 EPIC 2: ${epic2Progress}%`, colWidth) + b.vertical);

  const devBar = ' ' + generateProgressBar(data.development, colWidth - 2) + ' ';
  const epic1Bar = ' ' + generateProgressBar(epic1Progress, colWidth - 2) + ' ';
  const epic2Bar = ' ' + generateProgressBar(epic2Progress, colWidth - 2) + ' ';
  console.log(b.vertical + padCell(devBar, colWidth) +
              b.vertical + padCell(epic1Bar, colWidth) +
              b.vertical + padCell(epic2Bar, colWidth) + b.vertical);

  // Middle border before Row 4
  console.log(b.leftJunction + b.horizontal.repeat(colWidth) + b.cross + b.horizontal.repeat(colWidth) + b.cross + b.horizontal.repeat(colWidth) + b.rightJunction);

  // Row 4: Stories, Completed, Outstanding (NO VELOCITY)
  const outstandingTasks = data.tasksTotal - data.tasksComplete;
  const outstandingPct = data.tasksTotal > 0 ? Math.round((outstandingTasks / data.tasksTotal) * 100) : 0;

  console.log(b.vertical + padCell(`📝 STORIES: ${data.storiesComplete}/${data.storiesTotal}`, colWidth) +
              b.vertical + padCell(`✅ COMPLETED`, colWidth) +
              b.vertical + padCell(`⏳ OUTSTANDING`, colWidth) + b.vertical);

  const storyBar = ' ' + generateProgressBar(data.storyProgress, colWidth - 2) + ' ';
  console.log(b.vertical + padCell(storyBar, colWidth) +
              b.vertical + padCell(`${data.tasksComplete}/${data.tasksTotal} done`, colWidth) +
              b.vertical + padCell(`${outstandingTasks}/${data.tasksTotal} remain`, colWidth) + b.vertical);

  const taskBar = ' ' + generateProgressBar(data.taskProgress, colWidth - 2) + ' ';
  const outstandingBar = ' ' + generateInvertedProgressBar(outstandingPct, colWidth - 2) + ' ';
  console.log(b.vertical + padCell('', colWidth) +
              b.vertical + padCell(taskBar, colWidth) +
              b.vertical + padCell(outstandingBar, colWidth) + b.vertical);

  // Bottom border
  console.log(b.bottomLeft + b.horizontal.repeat(colWidth) + b.bottomJunction + b.horizontal.repeat(colWidth) + b.bottomJunction + b.horizontal.repeat(colWidth) + b.bottomRight);

  // Controls
  console.log('\n' + colors.dim);
  if (config.autoRefresh) {
    console.log(`Auto-refresh: ON (${config.refreshInterval}s) | [r] Refresh  [a] Toggle Auto  [m] Milestones  [q] Quit  [?] Help`);
  } else {
    console.log('[r] Refresh  [a] Toggle Auto  [m] Milestones  [q] Quit  [?] Help');
  }
  console.log(colors.reset);
}

// Strip ANSI color codes from text to get actual visual content
function stripAnsi(text) {
  // Remove all ANSI escape sequences (color codes, etc.)
  return text.replace(/\x1b\[[0-9;]*m/g, '');
}

// Get visual length of text (excluding ANSI codes, accounting for wide chars)
function getVisualLength(text) {
  const stripped = stripAnsi(text);
  let width = 0;

  // Iterate through each character (code point)
  for (const char of stripped) {
    const code = char.codePointAt(0);

    // Wide characters take 2 terminal columns
    // Covers: emojis, emoticons, symbols, and CJK characters
    if (
      (code >= 0x1F300 && code <= 0x1F9FF) ||  // Misc Symbols and Pictographs
      (code >= 0x1F600 && code <= 0x1F64F) ||  // Emoticons
      (code >= 0x1F680 && code <= 0x1F6FF) ||  // Transport and Map
      (code >= 0x2600 && code <= 0x26FF) ||    // Misc symbols
      (code >= 0x2700 && code <= 0x27BF) ||    // Dingbats
      (code >= 0x2300 && code <= 0x23FF) ||    // Misc Technical (includes ⏳)
      (code >= 0x1F900 && code <= 0x1F9FF) ||  // Supplemental Symbols
      (code >= 0x1F000 && code <= 0x1F02F) ||  // Mahjong Tiles
      (code >= 0x1F0A0 && code <= 0x1F0FF) ||  // Playing Cards
      (code >= 0x1F100 && code <= 0x1F64F)     // Enclosed chars
    ) {
      width += 2;
    } else {
      width += 1;
    }
  }

  return width;
}

// Truncate text to maxLength with ellipsis
function truncateText(text, maxLength) {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

// Pad cell content to width (accounts for ANSI codes and emojis)
function padCell(text, width) {
  const visualLen = getVisualLength(text);

  // If over width, truncate by removing chars until it fits (preserve colors for exact matches!)
  if (visualLen > width) {
    const stripped = stripAnsi(text);
    let currentWidth = 0;
    let truncated = '';

    // Build truncated string char by char until we hit width limit
    for (const char of stripped) {
      const code = char.codePointAt(0);
      const charWidth = (
        (code >= 0x1F300 && code <= 0x1F9FF) ||
        (code >= 0x1F600 && code <= 0x1F64F) ||
        (code >= 0x1F680 && code <= 0x1F6FF) ||
        (code >= 0x2600 && code <= 0x26FF) ||
        (code >= 0x2700 && code <= 0x27BF) ||
        (code >= 0x2300 && code <= 0x23FF) ||
        (code >= 0x1F900 && code <= 0x1F9FF) ||
        (code >= 0x1F000 && code <= 0x1F02F) ||
        (code >= 0x1F0A0 && code <= 0x1F0FF) ||
        (code >= 0x1F100 && code <= 0x1F64F)
      ) ? 2 : 1;

      if (currentWidth + charWidth > width - 1) break;  // Leave 1 char for safety
      truncated += char;
      currentWidth += charWidth;
    }

    return truncated.trim();
  }

  // Calculate padding based on VISUAL length
  const padding = width - visualLen;
  const leftPad = Math.floor(padding / 2);
  const rightPad = padding - leftPad;

  return ' '.repeat(Math.max(0, leftPad)) + text + ' '.repeat(Math.max(0, rightPad));
}

// Fetch progress data
function fetchProgressData(projectConfig) {
  // Check if we can use cached data
  if (config.dataCache && !hasFilesChanged(projectConfig)) {
    return config.dataCache;
  }

  try {
    // Scan project
    const scanResult = scanProject(projectConfig);

    // Calculate progress
    const planningProgress = calculatePlanningProgress(scanResult);
    const developmentProgress = calculateDevelopmentProgress(scanResult);
    const overallProgress = calculateOverallProgress(planningProgress, developmentProgress);

    // Calculate additional metrics
    const storyProgress = scanResult.development.totalStories > 0
      ? Math.round((scanResult.development.completedStories / scanResult.development.totalStories) * 100)
      : 0;

    let totalTasks = 0;
    let completedTasks = 0;
    for (const story of scanResult.development.stories) {
      totalTasks += story.totalTasks;
      completedTasks += story.completedTasks;
    }
    const taskProgress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

    // Epic data
    const epic1 = scanResult.development.epics[0];
    const epic2 = scanResult.development.epics[1];

    // Load milestone state and determine next milestone
    const milestoneState = loadMilestoneState();
    const milestones = determineMilestones(
      scanResult,
      planningProgress,
      developmentProgress,
      milestoneState
    );

    // Extract next milestone info
    let nextMilestone = milestones.next || 'Complete';
    let nextStatus = '✅ All Done';

    if (milestones.next) {
      // Shorten milestone names for display
      nextMilestone = milestones.next
        .replace('Project Brief Complete', 'Project Brief')
        .replace('First Story Completed', 'First Story')
        .replace('50% Stories Complete', '50% Stories');
      nextStatus = `⏳ ${milestones.nextRequirement}`;
    }

    const data = {
      overall: overallProgress,
      planning: planningProgress,
      development: developmentProgress,
      epic1: epic1 ? { progress: calculateEpicProgress(epic1) } : null,
      epic2: epic2 ? { progress: calculateEpicProgress(epic2) } : null,
      storiesComplete: scanResult.development.completedStories,
      storiesTotal: scanResult.development.totalStories,
      storyProgress: storyProgress,
      tasksComplete: completedTasks,
      tasksTotal: totalTasks,
      taskProgress: taskProgress,
      velocity: taskProgress,
      nextMilestone: nextMilestone,
      nextStatus: nextStatus
    };

    // Cache the data
    config.dataCache = data;
    config.lastUpdate = Date.now();

    return data;
  } catch (error) {
    console.error('Error fetching progress data:', error);
    return config.dataCache || null;
  }
}

// Launch milestone manager
function launchMilestoneManager() {
  const { spawn } = require('child_process');

  // Restore terminal to normal mode
  if (process.stdin.isTTY) {
    process.stdin.setRawMode(false);
  }

  // Clear screen
  clearScreen();
  console.log(colors.cyan + 'Launching Milestone Manager...' + colors.reset);
  console.log();

  // Spawn milestone manager
  const managerPath = path.join(__dirname, 'milestone-manager.js');
  const manager = spawn('node', [managerPath], {
    stdio: 'inherit'
  });

  manager.on('exit', (code) => {
    // Restore raw mode
    if (process.stdin.isTTY) {
      process.stdin.setRawMode(true);
    }

    // Return to dashboard
    const projectConfig = loadConfig();
    const data = fetchProgressData(projectConfig);
    if (data) {
      renderDashboard(data);
    }
  });
}

// Setup keyboard input handling
function setupKeyboardInput(projectConfig) {
  readline.emitKeypressEvents(process.stdin);

  if (process.stdin.isTTY) {
    process.stdin.setRawMode(true);
  }

  process.stdin.on('keypress', (str, key) => {
    if (key.ctrl && key.name === 'c') {
      cleanup();
    }

    switch (key.name) {
      case 'q':
        cleanup();
        break;

      case 'r':
        const data = fetchProgressData(projectConfig);
        if (data) {
          renderDashboard(data);
        }
        break;

      case 'a':
        config.autoRefresh = !config.autoRefresh;
        if (config.autoRefresh) {
          startAutoRefresh(projectConfig);
        } else {
          stopAutoRefresh();
        }
        const currentData = fetchProgressData(projectConfig);
        if (currentData) {
          renderDashboard(currentData);
        }
        break;

      case 'm':
        // Launch milestone manager
        launchMilestoneManager();
        break;

      case '?':
      case 'h':
        clearScreen();
        showHelp();
        console.log('\nPress any key to return to dashboard...');
        break;

      default:
        // Return to dashboard from help
        const latestData = config.dataCache || fetchProgressData(projectConfig);
        if (latestData) {
          renderDashboard(latestData);
        }
    }
  });
}

// Auto-refresh timer
let refreshTimer = null;

function startAutoRefresh(projectConfig) {
  stopAutoRefresh();

  refreshTimer = setInterval(() => {
    const data = fetchProgressData(projectConfig);
    if (data) {
      renderDashboard(data);
    }
  }, config.refreshInterval * 1000);
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
}

// Cleanup and exit
function cleanup() {
  stopAutoRefresh();

  if (process.stdin.isTTY) {
    process.stdin.setRawMode(false);
  }

  console.log(colors.reset);
  console.log('\nGoodbye! 👋\n');
  process.exit(0);
}

// Main function
async function main() {
  parseArgs();

  const projectConfig = loadConfig();
  if (!projectConfig) {
    console.error('Error: Not in a BMAD project (no .bmad-core directory found)');
    process.exit(1);
  }

  // Initial render
  const data = fetchProgressData(projectConfig);
  if (!data) {
    console.error('Error: Could not fetch progress data');
    process.exit(1);
  }

  renderDashboard(data);

  // Setup controls
  setupKeyboardInput(projectConfig);

  // Start auto-refresh if enabled
  if (config.autoRefresh) {
    startAutoRefresh(projectConfig);
  }

  // Handle exit signals
  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);
}

// Run if executed directly
if (require.main === module) {
  main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

module.exports = {
  renderDashboard,
  fetchProgressData
};