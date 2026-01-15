#!/usr/bin/env node

/**
 * BMAD Progress Watcher
 * Monitors story files for changes and automatically updates the progress dashboard
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

// Configuration
const CONFIG = {
  watchPaths: [
    'docs/stories',
    'docs/prd',
    'docs/architecture'
  ],
  debounceMs: 2000, // Wait 2 seconds after last change before updating
  dashboardPath: 'docs/progress-dashboard.md',
  // These will be determined based on project version
  progressScriptV4: '.bmad-core/utils/update-progress.js',
  progressScriptV6: 'tools/progress-tracking/update-progress.js'
};

// State
let updateTimeout = null;
let isUpdating = false;
let lastUpdateTime = 0;
let projectRoot = null;
let projectVersion = null;

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

// Logging functions
function log(message, color = '') {
  const timestamp = new Date().toISOString().substring(11, 19);
  console.log(`${colors.dim}[${timestamp}]${colors.reset} ${color}${message}${colors.reset}`);
}

function logInfo(message) {
  log(message, colors.cyan);
}

function logSuccess(message) {
  log(message, colors.green);
}

function logWarning(message) {
  log(message, colors.yellow);
}

function logError(message) {
  log(`ERROR: ${message}`, colors.bright);
}

// Check if path exists and is accessible
async function checkPath(filepath) {
  try {
    await fs.promises.access(filepath);
    return true;
  } catch {
    return false;
  }
}

// Get project root by looking for bmad-core or .bmad-core directory
async function getProjectRoot() {
  let currentDir = process.cwd();

  while (currentDir !== '/') {
    // Check for v6 first
    const bmadCoreV6Path = path.join(currentDir, 'bmad-core');
    if (await checkPath(bmadCoreV6Path)) {
      return { root: currentDir, version: 'v6' };
    }

    // Then check for v4
    const bmadCoreV4Path = path.join(currentDir, '.bmad-core');
    if (await checkPath(bmadCoreV4Path)) {
      return { root: currentDir, version: 'v4' };
    }
    currentDir = path.dirname(currentDir);
  }

  return null;
}

// Update progress dashboard
async function updateProgress() {
  if (isUpdating) {
    log('Progress update already in progress, skipping...');
    return;
  }

  const now = Date.now();
  if (now - lastUpdateTime < 1000) {
    log('Too soon since last update, skipping...');
    return;
  }

  isUpdating = true;
  lastUpdateTime = now;

  try {
    logInfo('Updating progress dashboard...');

    // Execute the update-progress.js script based on project version
    const scriptPath = projectVersion === 'v6'
      ? path.join(projectRoot, CONFIG.progressScriptV6)
      : path.join(projectRoot, CONFIG.progressScriptV4);
    const { stdout, stderr } = await execAsync(`node "${scriptPath}"`, {
      cwd: projectRoot,
      timeout: 30000 // 30 second timeout
    });

    if (stderr && !stderr.includes('[WARNING]')) {
      logWarning(`Update warnings: ${stderr}`);
    }

    logSuccess('Progress dashboard updated successfully!');

    // Show brief summary if available
    const summaryMatch = stdout.match(/Overall:\s*\[.*?\]\s*(\d+)%/);
    if (summaryMatch) {
      log(`Overall progress: ${colors.bright}${summaryMatch[1]}%${colors.reset}`);
    }

  } catch (error) {
    logError(`Failed to update progress: ${error.message}`);
  } finally {
    isUpdating = false;
  }
}

// Debounced update function
function scheduleUpdate() {
  if (updateTimeout) {
    clearTimeout(updateTimeout);
  }

  updateTimeout = setTimeout(() => {
    updateProgress();
  }, CONFIG.debounceMs);
}

// File change handler
function handleFileChange(eventType, filename) {
  if (!filename) return;

  // Ignore temporary files and non-markdown files
  if (filename.startsWith('.') || filename.includes('.swp') || !filename.endsWith('.md')) {
    return;
  }

  // Ignore the dashboard file itself to prevent infinite loops
  if (filename.includes('progress-dashboard.md')) {
    return;
  }

  log(`File ${eventType}: ${colors.bright}${filename}${colors.reset}`);
  scheduleUpdate();
}

// Setup file watchers
async function setupWatchers(projectRoot) {
  const watchers = [];

  for (const watchPath of CONFIG.watchPaths) {
    const fullPath = path.join(projectRoot, watchPath);

    if (await checkPath(fullPath)) {
      logInfo(`Watching: ${watchPath}`);

      const watcher = fs.watch(fullPath, { recursive: true }, (eventType, filename) => {
        handleFileChange(eventType, path.join(watchPath, filename || ''));
      });

      watchers.push(watcher);
    } else {
      logWarning(`Path not found, skipping: ${watchPath}`);
    }
  }

  return watchers;
}

// Graceful shutdown
function shutdown(watchers) {
  log('\nShutting down progress watcher...');

  if (updateTimeout) {
    clearTimeout(updateTimeout);
  }

  for (const watcher of watchers) {
    watcher.close();
  }

  logSuccess('Progress watcher stopped');
  process.exit(0);
}

// Main function
async function main() {
  console.log(`${colors.bright}${colors.cyan}BMAD Progress Watcher${colors.reset}`);
  console.log(`${colors.dim}${'='.repeat(40)}${colors.reset}\n`);

  // Find project root and version
  const projectInfo = await getProjectRoot();
  if (!projectInfo) {
    logError('Not in a BMAD project (no bmad-core or .bmad-core directory found)');
    process.exit(1);
  }

  // Set global variables
  projectRoot = projectInfo.root;
  projectVersion = projectInfo.version;

  logInfo(`Project root: ${projectRoot}`);
  logInfo(`BMAD version: ${projectVersion}`);

  // Check if update script exists based on version
  const updateScriptPath = projectVersion === 'v6'
    ? path.join(projectRoot, CONFIG.progressScriptV6)
    : path.join(projectRoot, CONFIG.progressScriptV4);
  if (!await checkPath(updateScriptPath)) {
    logWarning(`Update script not found at ${updateScriptPath}, will create it...`);
    // The update script will be created separately
  }

  // Setup file watchers
  const watchers = await setupWatchers(projectRoot);

  if (watchers.length === 0) {
    logError('No paths to watch, exiting');
    process.exit(1);
  }

  logSuccess(`Watching ${watchers.length} path(s) for changes`);
  log(`Dashboard will be updated to: ${CONFIG.dashboardPath}`);
  log(`${colors.dim}Press Ctrl+C to stop watching${colors.reset}\n`);

  // Initial progress update
  await updateProgress();

  // Setup signal handlers for graceful shutdown
  process.on('SIGINT', () => shutdown(watchers));
  process.on('SIGTERM', () => shutdown(watchers));

  // Keep the process alive
  process.stdin.resume();
}

// Run if executed directly
if (require.main === module) {
  main().catch(error => {
    logError(`Fatal error: ${error.message}`);
    process.exit(1);
  });
}

module.exports = {
  updateProgress,
  scheduleUpdate
};