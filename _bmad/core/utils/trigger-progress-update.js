#!/usr/bin/env node

/**
 * BMAD Progress Update Trigger
 * Utility for agents to trigger progress dashboard updates
 * Can be called programmatically or via command line
 */

const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

// Configuration
const UPDATE_SCRIPT = '.bmad-core/utils/update-progress.js';
const LOCK_FILE = '.bmad-core/.progress-update-lock';
const LOCK_TIMEOUT_MS = 5000; // 5 second timeout for lock

/**
 * Check if update is already in progress
 */
function isUpdateLocked() {
  try {
    if (fs.existsSync(LOCK_FILE)) {
      const lockTime = fs.readFileSync(LOCK_FILE, 'utf8');
      const lockAge = Date.now() - parseInt(lockTime);

      // If lock is older than timeout, consider it stale
      if (lockAge > LOCK_TIMEOUT_MS) {
        fs.unlinkSync(LOCK_FILE);
        return false;
      }

      return true;
    }
  } catch {
    // If we can't read the lock file, assume it's not locked
  }

  return false;
}

/**
 * Create lock file
 */
function createLock() {
  try {
    const dir = path.dirname(LOCK_FILE);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(LOCK_FILE, Date.now().toString(), 'utf8');
  } catch (error) {
    console.error(`[WARNING] Could not create lock file: ${error.message}`);
  }
}

/**
 * Remove lock file
 */
function removeLock() {
  try {
    if (fs.existsSync(LOCK_FILE)) {
      fs.unlinkSync(LOCK_FILE);
    }
  } catch (error) {
    console.error(`[WARNING] Could not remove lock file: ${error.message}`);
  }
}

/**
 * Trigger progress update
 * @param {Object} options - Configuration options
 * @param {string} options.context - Context of the trigger (e.g., 'agent:dev', 'manual', 'watcher')
 * @param {string} options.action - Action that triggered update (e.g., 'story-complete', 'task-update')
 * @param {boolean} options.silent - If true, suppress output
 * @param {Function} callback - Optional callback function
 */
function triggerProgressUpdate(options = {}, callback) {
  const {
    context = 'manual',
    action = 'update',
    silent = false
  } = options;

  // Check if update is already in progress
  if (isUpdateLocked()) {
    if (!silent) {
      console.log('[INFO] Progress update already in progress, skipping...');
    }
    if (callback) {
      callback(null, { skipped: true, reason: 'locked' });
    }
    return;
  }

  // Create lock
  createLock();

  // Find project root
  const scriptPath = path.join(process.cwd(), UPDATE_SCRIPT);

  if (!fs.existsSync(scriptPath)) {
    if (!silent) {
      console.error('[ERROR] Update script not found at:', scriptPath);
    }
    removeLock();
    if (callback) {
      callback(new Error('Update script not found'));
    }
    return;
  }

  // Log the trigger
  if (!silent) {
    console.log(`[PROGRESS] Triggered by ${context}: ${action}`);
  }

  // Execute update script
  exec(`node "${scriptPath}"`, { cwd: process.cwd() }, (error, stdout, stderr) => {
    // Remove lock
    removeLock();

    if (error) {
      if (!silent) {
        console.error('[ERROR] Progress update failed:', error.message);
        if (stderr) console.error(stderr);
      }
      if (callback) {
        callback(error);
      }
      return;
    }

    if (!silent) {
      // Extract and display overall progress
      const progressMatch = stdout.match(/Overall:.*?(\d+)%/);
      if (progressMatch) {
        console.log(`[SUCCESS] Progress updated: ${progressMatch[1]}% complete`);
      } else {
        console.log('[SUCCESS] Progress dashboard updated');
      }

      // Show any warnings
      if (stderr && stderr.includes('[WARNING]')) {
        console.log(stderr);
      }
    }

    if (callback) {
      callback(null, {
        success: true,
        output: stdout,
        warnings: stderr
      });
    }
  });
}

/**
 * Agent-specific trigger functions
 */
const agentTriggers = {
  // Developer agent triggers
  dev: {
    storyComplete: () => triggerProgressUpdate({
      context: 'agent:dev',
      action: 'story-complete'
    }),
    storyImplemented: () => triggerProgressUpdate({
      context: 'agent:dev',
      action: 'story-implemented'
    }),
    testsComplete: () => triggerProgressUpdate({
      context: 'agent:dev',
      action: 'tests-complete'
    })
  },

  // Developer Junior agent triggers
  devJunior: {
    storyProgress: () => triggerProgressUpdate({
      context: 'agent:dev-junior',
      action: 'story-progress'
    }),
    taskComplete: () => triggerProgressUpdate({
      context: 'agent:dev-junior',
      action: 'task-complete'
    })
  },

  // Product Owner agent triggers
  po: {
    storyValidated: () => triggerProgressUpdate({
      context: 'agent:po',
      action: 'story-validated'
    }),
    storyDrafted: () => triggerProgressUpdate({
      context: 'agent:po',
      action: 'story-drafted'
    }),
    epicCreated: () => triggerProgressUpdate({
      context: 'agent:po',
      action: 'epic-created'
    })
  },

  // Scrum Master agent triggers
  sm: {
    storyDrafted: () => triggerProgressUpdate({
      context: 'agent:sm',
      action: 'story-drafted'
    }),
    checklistComplete: () => triggerProgressUpdate({
      context: 'agent:sm',
      action: 'checklist-complete'
    })
  },

  // Product Manager agent triggers
  pm: {
    prdUpdated: () => triggerProgressUpdate({
      context: 'agent:pm',
      action: 'prd-updated'
    }),
    epicCreated: () => triggerProgressUpdate({
      context: 'agent:pm',
      action: 'epic-created'
    }),
    documentSharded: () => triggerProgressUpdate({
      context: 'agent:pm',
      action: 'document-sharded'
    })
  },

  // Architect agent triggers
  architect: {
    architectureUpdated: () => triggerProgressUpdate({
      context: 'agent:architect',
      action: 'architecture-updated'
    }),
    documentSharded: () => triggerProgressUpdate({
      context: 'agent:architect',
      action: 'document-sharded'
    })
  }
};

/**
 * Command-line interface
 */
if (require.main === module) {
  const args = process.argv.slice(2);

  // Parse command line arguments
  let context = 'cli';
  let action = 'manual';
  let silent = false;

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--context':
      case '-c':
        context = args[++i] || 'cli';
        break;
      case '--action':
      case '-a':
        action = args[++i] || 'manual';
        break;
      case '--silent':
      case '-s':
        silent = true;
        break;
      case '--help':
      case '-h':
        console.log('BMAD Progress Update Trigger');
        console.log('\nUsage:');
        console.log('  node trigger-progress-update.js [options]');
        console.log('\nOptions:');
        console.log('  -c, --context <name>  Context that triggered update');
        console.log('  -a, --action <name>   Action that triggered update');
        console.log('  -s, --silent          Suppress output');
        console.log('  -h, --help            Show this help message');
        console.log('\nExamples:');
        console.log('  node trigger-progress-update.js');
        console.log('  node trigger-progress-update.js --context agent:dev --action story-complete');
        console.log('  node trigger-progress-update.js -c watcher -a file-change --silent');
        process.exit(0);
    }
  }

  // Trigger the update
  triggerProgressUpdate({ context, action, silent }, (error, result) => {
    if (error) {
      process.exit(1);
    }
    process.exit(0);
  });
}

// Export for use by other modules
module.exports = {
  triggerProgressUpdate,
  agentTriggers,
  isUpdateLocked
};