#!/usr/bin/env node

/**
 * BMAD Progress Update Script
 * Calculates project progress and updates the dashboard
 * This is a standalone version of the track-progress.md implementation
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// Configuration defaults
const DEFAULT_CONFIG = {
  prdFile: 'docs/prd.md',
  architectureFile: 'docs/architecture.md',
  prdShardedLocation: 'docs/prd',
  architectureShardedLocation: 'docs/architecture',
  devStoryLocation: 'docs/stories',
  epicFilePattern: /epic-(\d+).*\.md$/i
};

// Load project configuration
function loadConfig() {
  // Try multiple possible config locations for compatibility
  const configPaths = [
    path.join(process.cwd(), 'tools/core-config.yaml'),
    path.join(process.cwd(), 'tools/bmad-config.yaml'),
    path.join(process.cwd(), '.bmad-core/core-config.yaml')
  ];

  for (const configPath of configPaths) {
    try {
      const configContent = fs.readFileSync(configPath, 'utf8');
      const config = yaml.load(configContent);

      return {
        prdFile: config?.prd?.prdFile || DEFAULT_CONFIG.prdFile,
        architectureFile: config?.architecture?.architectureFile || DEFAULT_CONFIG.architectureFile,
        prdShardedLocation: config?.prd?.prdShardedLocation || DEFAULT_CONFIG.prdShardedLocation,
        architectureShardedLocation: config?.architecture?.architectureShardedLocation || DEFAULT_CONFIG.architectureShardedLocation,
        devStoryLocation: config?.devStoryLocation || DEFAULT_CONFIG.devStoryLocation,
        epicFilePattern: DEFAULT_CONFIG.epicFilePattern
      };
    } catch {
      // Try next path
    }
  }

  console.warn('[WARNING] Cannot load config from any location, using defaults');
  return DEFAULT_CONFIG;
}

// Load milestone state (supports both BMAD v4 and v6)
function loadMilestoneState() {
  // Try both possible locations
  const statePaths = [
    path.join(process.cwd(), 'tools/milestone-state.yaml'),
    path.join(process.cwd(), '.bmad-core/milestone-state.yaml')
  ];

  let statePath;
  for (const p of statePaths) {
    if (fs.existsSync(p)) {
      statePath = p;
      break;
    }
  }

  if (!statePath) {
    return { complete: [] };
  }

  try {
    const stateContent = fs.readFileSync(statePath, 'utf8');
    const state = yaml.load(stateContent);

    // Support both old and new format for backward compatibility
    const complete = state?.complete || [];
    const skipped = state?.skipped || [];
    const manual_complete = state?.manual_complete || [];

    // Merge old format into new format
    const allComplete = [...new Set([...complete, ...skipped, ...manual_complete])];

    return {
      complete: allComplete
    };
  } catch (error) {
    console.warn('[WARNING] Cannot load milestone-state.yaml:', error.message);
    return {
      complete: []
    };
  }
}

// Check if file/directory exists
function exists(filepath) {
  try {
    fs.accessSync(filepath);
    return true;
  } catch {
    return false;
  }
}

// Check if directory has files
function hasFiles(dirPath) {
  try {
    const files = fs.readdirSync(dirPath);
    return files.some(file => file.endsWith('.md'));
  } catch {
    return false;
  }
}

// Parse story file to count tasks
function parseStoryFile(filepath) {
  try {
    const content = fs.readFileSync(filepath, 'utf8');
    const lines = content.split('\n');

    let totalTasks = 0;
    let completedTasks = 0;

    for (const line of lines) {
      if (line.includes('- [ ]')) {
        totalTasks++;
      } else if (line.includes('- [x]') || line.includes('- [X]')) {
        totalTasks++;
        completedTasks++;
      }
    }

    const percentage = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

    // Extract story ID from filename
    const filename = path.basename(filepath);
    const idMatch = filename.match(/^(\d+\.?\d*)\./);
    const id = idMatch ? idMatch[1] : filename.replace('.md', '');

    return {
      file: filepath,
      id,
      totalTasks,
      completedTasks,
      percentage
    };
  } catch (error) {
    console.warn(`[WARNING] Cannot parse story file: ${filepath}`);
    return null;
  }
}

// Scan project for progress data
function scanProject(config) {
  const scanResult = {
    planning: {
      brief: { exists: false, path: null },
      prd: { exists: false, path: null, sharded: false },
      architecture: { exists: false, path: null, sharded: false }
    },
    development: {
      epics: [],
      stories: [],
      totalStories: 0,
      completedStories: 0
    }
  };

  // Check for Project Brief
  if (exists('docs/brief.md')) {
    scanResult.planning.brief = { exists: true, path: 'docs/brief.md' };
  } else if (exists('docs/project-brief.md')) {
    scanResult.planning.brief = { exists: true, path: 'docs/project-brief.md' };
  }

  // Check for PRD
  if (exists(config.prdFile)) {
    scanResult.planning.prd = { exists: true, path: config.prdFile, sharded: false };
  }

  // Check for Architecture
  if (exists(config.architectureFile)) {
    scanResult.planning.architecture = { exists: true, path: config.architectureFile, sharded: false };
  }

  // Check if documents are sharded
  if (exists(config.prdShardedLocation) && hasFiles(config.prdShardedLocation)) {
    scanResult.planning.prd.sharded = true;
    scanResult.planning.prd.exists = true;

    // Scan for epics
    const files = fs.readdirSync(config.prdShardedLocation);
    for (const file of files) {
      const match = file.match(config.epicFilePattern);
      if (match) {
        const epicId = parseInt(match[1]);
        const epicPath = path.join(config.prdShardedLocation, file);

        try {
          const content = fs.readFileSync(epicPath, 'utf8');
          const titleMatch = content.match(/^#\s+Epic\s+\d+[:\s]+(.+)$/m) ||
                            content.match(/^title:\s*(.+)$/m);
          const title = titleMatch ? titleMatch[1].trim() : `Epic ${epicId}`;

          scanResult.development.epics.push({
            id: epicId,
            title,
            file: epicPath,
            stories: []
          });
        } catch {
          scanResult.development.epics.push({
            id: epicId,
            title: `Epic ${epicId}`,
            file: epicPath,
            stories: []
          });
        }
      }
    }
  }

  if (exists(config.architectureShardedLocation) && hasFiles(config.architectureShardedLocation)) {
    scanResult.planning.architecture.sharded = true;
    scanResult.planning.architecture.exists = true;
  }

  // Scan story files
  if (exists(config.devStoryLocation)) {
    const files = fs.readdirSync(config.devStoryLocation);

    for (const file of files) {
      if (!file.endsWith('.md')) continue;

      const storyPath = path.join(config.devStoryLocation, file);
      const storyData = parseStoryFile(storyPath);

      if (storyData) {
        scanResult.development.stories.push(storyData);
        scanResult.development.totalStories++;

        if (storyData.percentage === 100) {
          scanResult.development.completedStories++;
        }

        // Link story to epic
        const epicNumber = storyData.id.split('.')[0];
        const epic = scanResult.development.epics.find(e => e.id === parseInt(epicNumber));
        if (epic) {
          epic.stories.push(storyData);
        }
      }
    }
  }

  return scanResult;
}

// Calculate planning progress
function calculatePlanningProgress(scanResult, milestoneState = null) {
  let progress = 0;
  const state = milestoneState || { complete: [] };

  // Check if milestones are manually marked as complete
  const isBriefComplete = state.complete.includes('Project Brief Complete');
  const isPRDComplete = state.complete.includes('PRD Approved');
  const isArchComplete = state.complete.includes('Architecture Approved');
  const isShardingComplete = state.complete.includes('Documents Sharded');

  // Brief: actual existence OR manually marked complete
  if (scanResult.planning.brief.exists || isBriefComplete) progress += 25;

  // PRD: actual existence OR manually marked complete
  if (scanResult.planning.prd.exists || scanResult.planning.prd.sharded || isPRDComplete) progress += 25;

  // Architecture: actual existence OR manually marked complete
  if (scanResult.planning.architecture.exists || scanResult.planning.architecture.sharded || isArchComplete) progress += 25;

  // Sharding: actual sharding OR manually marked complete
  if ((scanResult.planning.prd.sharded && scanResult.planning.architecture.sharded) || isShardingComplete) progress += 25;

  return progress;
}

// Calculate development progress
function calculateDevelopmentProgress(scanResult) {
  let progress = 0;

  if (scanResult.development.epics.length === 0) {
    if (scanResult.development.totalStories > 0) {
      progress = (scanResult.development.completedStories / scanResult.development.totalStories) * 100;
    }
  } else {
    let totalEpicProgress = 0;

    for (const epic of scanResult.development.epics) {
      let epicProgress = 0;

      if (epic.stories.length > 0) {
        let completed = 0;
        for (const story of epic.stories) {
          if (story.percentage === 100) {
            completed++;
          } else if (story.percentage > 0) {
            completed += story.percentage / 100;
          }
        }
        epicProgress = (completed / epic.stories.length) * 100;
      }

      totalEpicProgress += epicProgress;
    }

    progress = totalEpicProgress / scanResult.development.epics.length;
  }

  return Math.round(progress);
}

// Calculate overall progress
function calculateOverallProgress(planningProgress, developmentProgress) {
  return Math.round((planningProgress * 0.4) + (developmentProgress * 0.6));
}

// Determine milestones
function determineMilestones(scanResult, planningProgress, developmentProgress, milestoneState = null) {
  const milestones = {
    planning: [],
    development: [],
    next: null,
    nextRequirement: ''
  };

  const state = milestoneState || { complete: [] };

  // Helper function to check if a milestone is manually marked complete
  const isManuallyComplete = (name) => {
    return state.complete.includes(name);
  };

  // Helper function to sort stories by ID numerically
  const sortStoriesByID = (stories) => {
    return [...stories].sort((a, b) => {
      const aNum = parseFloat(a.id);
      const bNum = parseFloat(b.id);
      if (isNaN(aNum) || isNaN(bNum)) {
        return a.id.localeCompare(b.id);
      }
      return aNum - bNum;
    });
  };

  // Helper function to get first incomplete story
  const getFirstIncompleteStory = () => {
    const sortedStories = sortStoriesByID(scanResult.development.stories);
    return sortedStories.find(s => s.percentage < 100);
  };

  // Planning milestones
  const briefComplete = scanResult.planning.brief.exists || isManuallyComplete('Project Brief Complete');

  if (briefComplete) {
    milestones.planning.push({
      name: 'Project Brief Complete',
      completed: true
    });
  } else {
    milestones.planning.push({ name: 'Project Brief Complete', completed: false });
    if (!milestones.next) {
      milestones.next = 'Project Brief Complete';
      milestones.nextRequirement = 'Create docs/brief.md or docs/project-brief.md';
    }
  }

  const prdComplete = scanResult.planning.prd.exists || scanResult.planning.prd.sharded || isManuallyComplete('PRD Approved');

  if (prdComplete) {
    milestones.planning.push({
      name: 'PRD Approved',
      completed: true
    });
  } else {
    milestones.planning.push({ name: 'PRD Approved', completed: false });
    if (!milestones.next) {
      milestones.next = 'PRD Approved';
      milestones.nextRequirement = 'Create PRD document';
    }
  }

  const archComplete = scanResult.planning.architecture.exists || scanResult.planning.architecture.sharded || isManuallyComplete('Architecture Approved');

  if (archComplete) {
    milestones.planning.push({
      name: 'Architecture Approved',
      completed: true
    });
  } else {
    milestones.planning.push({ name: 'Architecture Approved', completed: false });
    if (!milestones.next) {
      milestones.next = 'Architecture Approved';
      milestones.nextRequirement = 'Create Architecture document';
    }
  }

  const shardingComplete = (scanResult.planning.prd.sharded && scanResult.planning.architecture.sharded) || isManuallyComplete('Documents Sharded');

  if (shardingComplete) {
    milestones.planning.push({
      name: 'Documents Sharded',
      completed: true
    });
  } else {
    milestones.planning.push({ name: 'Documents Sharded', completed: false });
    if (!milestones.next) {
      milestones.next = 'Documents Sharded';
      milestones.nextRequirement = 'Shard PRD and Architecture documents';
    }
  }

  // Development milestones
  const hasStories = scanResult.development.totalStories > 0;
  const firstEpicComplete = hasStories || isManuallyComplete('First Epic Started');

  if (firstEpicComplete) {
    milestones.development.push({
      name: 'First Epic Started',
      completed: true
    });
  } else {
    milestones.development.push({ name: 'First Epic Started', completed: false });
    if (!milestones.next) {
      milestones.next = 'First Epic Started';
      // If epics are defined but no stories yet, show which epic to start
      if (scanResult.development.epics.length > 0) {
        const firstEpic = scanResult.development.epics[0];
        milestones.nextRequirement = `Create first story for Epic ${firstEpic.id}: ${firstEpic.title}`;
      } else {
        milestones.nextRequirement = 'Create first story file';
      }
    }
  }

  const hasCompletedStory = scanResult.development.completedStories > 0;
  const firstStoryComplete = hasCompletedStory || isManuallyComplete('First Story Completed');

  if (firstStoryComplete) {
    milestones.development.push({
      name: 'First Story Completed',
      completed: true
    });
  } else {
    milestones.development.push({ name: 'First Story Completed', completed: false });
    if (!milestones.next) {
      milestones.next = 'First Story Completed';
      const firstIncomplete = getFirstIncompleteStory();
      if (firstIncomplete) {
        milestones.nextRequirement = `Complete Story ${firstIncomplete.id} (${firstIncomplete.completedTasks}/${firstIncomplete.totalTasks} tasks done)`;
      } else {
        milestones.nextRequirement = 'Complete all tasks in at least one story';
      }
    }
  }

  const storyCompletionPercent = scanResult.development.totalStories > 0
    ? (scanResult.development.completedStories / scanResult.development.totalStories) * 100
    : 0;

  const fiftyPercentComplete = storyCompletionPercent >= 50 || isManuallyComplete('50% Stories Complete');

  if (fiftyPercentComplete) {
    milestones.development.push({
      name: '50% Stories Complete',
      completed: true,
      current: Math.round(storyCompletionPercent)
    });
  } else {
    const storiesNeeded = Math.ceil((scanResult.development.totalStories * 0.5) - scanResult.development.completedStories);
    milestones.development.push({
      name: '50% Stories Complete',
      completed: false,
      current: Math.round(storyCompletionPercent)
    });
    if (!milestones.next && scanResult.development.totalStories > 0) {
      milestones.next = '50% Stories Complete';
      const firstIncomplete = getFirstIncompleteStory();
      if (firstIncomplete) {
        milestones.nextRequirement = `Complete ${storiesNeeded} more stories. Next: Story ${firstIncomplete.id}`;
      } else {
        milestones.nextRequirement = `Complete ${storiesNeeded} more stories`;
      }
    }
  }

  // Check all epics complete
  let allEpicsActuallyComplete = scanResult.development.epics.length > 0;
  for (const epic of scanResult.development.epics) {
    if (epic.stories.length === 0) {
      allEpicsActuallyComplete = false;
      break;
    }
    for (const story of epic.stories) {
      if (story.percentage < 100) {
        allEpicsActuallyComplete = false;
        break;
      }
    }
  }

  const allEpicsComplete = (allEpicsActuallyComplete && scanResult.development.epics.length > 0) || isManuallyComplete('All Epics Complete');

  if (allEpicsComplete) {
    milestones.development.push({
      name: 'All Epics Complete',
      completed: true
    });
  } else {
    milestones.development.push({ name: 'All Epics Complete', completed: false });
    if (!milestones.next) {
      milestones.next = 'All Epics Complete';
      const firstIncomplete = getFirstIncompleteStory();
      if (firstIncomplete) {
        milestones.nextRequirement = `Complete all epic stories. Next: Story ${firstIncomplete.id}`;
      } else {
        milestones.nextRequirement = 'Complete all epic stories';
      }
    }
  }

  const overallProgress = calculateOverallProgress(planningProgress, developmentProgress);
  const projectComplete = overallProgress >= 100 || isManuallyComplete('Project Complete');

  if (projectComplete) {
    milestones.development.push({
      name: 'Project Complete',
      completed: true
    });
  } else {
    milestones.development.push({ name: 'Project Complete', completed: false });
    if (!milestones.next) {
      milestones.next = 'Project Complete';
      const incompleteStories = scanResult.development.stories.filter(s => s.percentage < 100);
      if (incompleteStories.length > 0) {
        const sortedIncomplete = sortStoriesByID(incompleteStories);
        const firstIncomplete = sortedIncomplete[0];
        milestones.nextRequirement = `Complete ${incompleteStories.length} remaining stories. Next: Story ${firstIncomplete.id}`;
      } else {
        milestones.nextRequirement = 'Complete all remaining tasks';
      }
    }
  }

  return milestones;
}

// Generate markdown progress bar
function generateProgressBar(percentage, width = 24) {
  const filled = Math.round((percentage / 100) * width);
  const empty = width - filled;

  return `[${'#'.repeat(filled)}${'-'.repeat(empty)}] ${percentage}%`;
}

// Generate compact progress bar for grid
function generateCompactBar(percentage, width = 12) {
  const filled = Math.round((percentage / 100) * width);
  const empty = width - filled;
  return `[${'█'.repeat(filled)}${'░'.repeat(empty)}]`;
}

// Generate dashboard content
function generateDashboard(scanResult, planningProgress, developmentProgress, overallProgress, milestones) {
  const now = new Date();
  const timestamp = now.toISOString().replace('T', ' ').substring(0, 19);

  let dashboard = '# BMAD Project Progress Dashboard\n\n';
  dashboard += `**Last Updated:** ${timestamp}\n\n`;

  // Calculate additional metrics for grid
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

  // Epic progress calculations
  const epic1 = scanResult.development.epics[0];
  const epic2 = scanResult.development.epics[1];
  const epic1Progress = epic1 ? calculateEpicProgress(epic1) : 0;
  const epic2Progress = epic2 ? calculateEpicProgress(epic2) : 0;

  // Generate grid dashboard
  dashboard += '## 📊 Progress Overview\n\n';
  dashboard += '| | | |\n';
  dashboard += '|:---|:---|:---|\n';
  dashboard += `| **🎯 Overall Progress**<br>**${overallProgress}%**<br>${generateCompactBar(overallProgress)} | **📋 Planning Phase**<br>**${planningProgress}%**<br>${generateCompactBar(planningProgress)} | **🚀 Development Phase**<br>**${developmentProgress}%**<br>${generateCompactBar(developmentProgress)} |\n`;

  if (epic1 || epic2) {
    const epic1Title = epic1 ? (epic1.title.length > 15 ? 'Epic 1' : `Epic 1`) : 'Epic 1';
    const epic2Title = epic2 ? (epic2.title.length > 15 ? 'Epic 2' : `Epic 2`) : 'Epic 2';
    dashboard += `| **📦 ${epic1Title}**<br>**${epic1Progress}%**<br>${generateCompactBar(epic1Progress)} | **📦 ${epic2Title}**<br>**${epic2Progress}%**<br>${generateCompactBar(epic2Progress)} | **📝 Stories Complete**<br>**${scanResult.development.completedStories}/${scanResult.development.totalStories}** (${storyProgress}%)<br>${generateCompactBar(storyProgress)} |\n`;
  } else {
    dashboard += `| **📝 Stories**<br>**${scanResult.development.completedStories}/${scanResult.development.totalStories}** (${storyProgress}%)<br>${generateCompactBar(storyProgress)} | **✅ Tasks**<br>**${completedTasks}/${totalTasks}** (${taskProgress}%)<br>${generateCompactBar(taskProgress)} | **🏁 Next Milestone**<br>**${milestones.next || 'Complete'}**<br>${milestones.next ? '⏳ In Progress' : '✅ Done'} |\n`;
  }

  const nextMilestoneShort = milestones.next ? milestones.next.replace('Project Brief Complete', 'Project Brief').replace('First Story Completed', 'First Story').replace('50% Stories Complete', '50% Stories') : 'Complete';
  dashboard += `| **✅ Tasks Complete**<br>**${completedTasks}/${totalTasks}** (${taskProgress}%)<br>${generateCompactBar(taskProgress)} | **📈 Velocity**<br>**${taskProgress}%** completion<br>${generateCompactBar(taskProgress)} | **🏁 Next Milestone**<br>**${nextMilestoneShort}**<br>${milestones.next ? '⏳ Pending' : '✅ All Done'} |\n`;

  dashboard += '\n---\n\n';

  // Keep the detailed sections below
  dashboard += '## Overall Progress\n';
  dashboard += `Progress: ${generateProgressBar(overallProgress)}\n\n`;

  dashboard += '## Planning Phase\n';
  dashboard += `Status: ${generateProgressBar(planningProgress)}\n\n`;

  dashboard += '### Documents\n';
  dashboard += `- Brief: ${scanResult.planning.brief.exists ? '✓ Complete' : '✗ Missing'}\n`;
  dashboard += `- PRD: ${scanResult.planning.prd.exists || scanResult.planning.prd.sharded ?
    '✓ Complete' + (scanResult.planning.prd.sharded ? ' (Sharded)' : '') : '✗ Missing'}\n`;
  dashboard += `- Architecture: ${scanResult.planning.architecture.exists || scanResult.planning.architecture.sharded ?
    '✓ Complete' + (scanResult.planning.architecture.sharded ? ' (Sharded)' : '') : '✗ Missing'}\n`;
  dashboard += `- Sharding: ${scanResult.planning.prd.sharded && scanResult.planning.architecture.sharded ?
    '✓ Complete' : '✗ Incomplete'}\n\n`;

  dashboard += '### Planning Milestones\n';
  for (const milestone of milestones.planning) {
    dashboard += `- [${milestone.completed ? 'x' : ' '}] ${milestone.name}\n`;
  }
  dashboard += '\n';

  dashboard += '## Development Phase\n';
  dashboard += `Status: ${generateProgressBar(developmentProgress)}\n\n`;

  dashboard += '### Statistics\n';
  if (scanResult.development.epics.length > 0) {
    const completedEpics = scanResult.development.epics.filter(e =>
      e.stories.length > 0 && e.stories.every(s => s.percentage === 100)
    ).length;
    dashboard += `- Epics: ${completedEpics}/${scanResult.development.epics.length} complete\n`;
  } else {
    dashboard += '- Epics: No epics defined\n';
  }
  dashboard += `- Stories: ${scanResult.development.completedStories}/${scanResult.development.totalStories} complete\n`;

  // Find current story
  const inProgressStories = scanResult.development.stories.filter(s => s.percentage > 0 && s.percentage < 100);
  if (inProgressStories.length > 0) {
    const current = inProgressStories[0];
    dashboard += `- Current: Story ${current.id} (${current.completedTasks}/${current.totalTasks} tasks)\n`;
  }
  dashboard += '\n';

  dashboard += '### Development Milestones\n';
  for (const milestone of milestones.development) {
    dashboard += `- [${milestone.completed ? 'x' : ' '}] ${milestone.name}`;
    if (milestone.name === '50% Stories Complete' && milestone.current !== undefined) {
      dashboard += ` (${milestone.current}%)`;
    }
    dashboard += '\n';
  }
  dashboard += '\n';

  // Epic breakdown
  if (scanResult.development.epics.length > 0) {
    dashboard += '## Epic Progress\n';
    for (const epic of scanResult.development.epics) {
      const epicProgress = calculateEpicProgress(epic);
      dashboard += `- **Epic ${epic.id}**: ${epic.title}\n`;
      dashboard += `  - Progress: ${generateProgressBar(epicProgress, 20)}\n`;
      const completedStories = epic.stories.filter(s => s.percentage === 100).length;
      dashboard += `  - Stories: ${completedStories}/${epic.stories.length} complete\n`;
    }
    dashboard += '\n';
  }

  // Story details
  if (scanResult.development.stories.length > 0) {
    dashboard += '## Story Progress Details\n\n';

    const completed = scanResult.development.stories.filter(s => s.percentage === 100);
    const inProgress = scanResult.development.stories.filter(s => s.percentage > 0 && s.percentage < 100);
    const notStarted = scanResult.development.stories.filter(s => s.percentage === 0);

    if (completed.length > 0) {
      dashboard += '### Completed Stories\n';
      for (const story of completed) {
        const filename = path.basename(story.file);
        dashboard += `- **Story ${story.id}**: ${filename}\n`;
        dashboard += `  - Progress: ${generateProgressBar(100)}\n`;
        dashboard += `  - Tasks: ${story.completedTasks}/${story.totalTasks} complete\n\n`;
      }
    }

    if (inProgress.length > 0) {
      dashboard += '### In Progress Stories\n';
      for (const story of inProgress) {
        const filename = path.basename(story.file);
        dashboard += `- **Story ${story.id}**: ${filename}\n`;
        dashboard += `  - Progress: ${generateProgressBar(story.percentage)}\n`;
        dashboard += `  - Tasks: ${story.completedTasks}/${story.totalTasks} complete\n`;
        dashboard += `  - Remaining: ${story.totalTasks - story.completedTasks} tasks\n\n`;
      }
    }

    if (notStarted.length > 0) {
      dashboard += '### Not Started Stories\n';
      for (const story of notStarted) {
        const filename = path.basename(story.file);
        dashboard += `- **Story ${story.id}**: ${filename}\n`;
        dashboard += `  - Progress: ${generateProgressBar(0)}\n`;
        dashboard += `  - Tasks: 0/${story.totalTasks} complete\n\n`;
      }
    }
  }

  // Milestones summary
  dashboard += '## Milestones Summary\n\n';

  const completed = [...milestones.planning, ...milestones.development].filter(m => m.completed);
  if (completed.length > 0) {
    dashboard += '### ✅ Completed\n';
    for (const milestone of completed) {
      dashboard += `- ${milestone.name}\n`;
    }
    dashboard += '\n';
  }

  const upcoming = [...milestones.planning, ...milestones.development].filter(m => !m.completed);
  if (upcoming.length > 0) {
    dashboard += '### ⏳ Upcoming\n';
    for (const milestone of upcoming) {
      dashboard += `- ${milestone.name}\n`;
    }
    dashboard += '\n';
  }

  // Next actions
  dashboard += '## Next Actions\n';
  dashboard += `**Next Milestone:** ${milestones.next || 'Project Complete'}\n\n`;
  dashboard += `**Requirement:** ${milestones.nextRequirement || 'All tasks complete'}\n\n`;

  // Velocity metrics
  if (scanResult.development.totalStories > 0) {
    dashboard += '## Velocity Metrics\n';
    dashboard += `- Total Stories: ${scanResult.development.totalStories}\n`;
    dashboard += `- Completed: ${scanResult.development.completedStories}\n`;
    dashboard += `- Completion Rate: ${Math.round((scanResult.development.completedStories / scanResult.development.totalStories) * 100)}%\n`;

    // Calculate total tasks
    let totalTasks = 0;
    let completedTasks = 0;
    for (const story of scanResult.development.stories) {
      totalTasks += story.totalTasks;
      completedTasks += story.completedTasks;
    }

    dashboard += `- Total Tasks: ${totalTasks}\n`;
    dashboard += `- Tasks Completed: ${completedTasks}\n`;
    dashboard += `- Task Completion Rate: ${totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0}%\n`;
  }

  return dashboard;
}

// Calculate epic progress
function calculateEpicProgress(epic) {
  if (epic.stories.length === 0) return 0;

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

// Main function
async function main() {
  try {
    // Load configuration
    const config = loadConfig();

    // Load milestone state
    const milestoneState = loadMilestoneState();

    // Scan project
    const scanResult = scanProject(config);

    // Calculate progress (with milestone state for planning)
    const planningProgress = calculatePlanningProgress(scanResult, milestoneState);
    const developmentProgress = calculateDevelopmentProgress(scanResult);
    const overallProgress = calculateOverallProgress(planningProgress, developmentProgress);

    // Determine milestones (with milestone state)
    const milestones = determineMilestones(scanResult, planningProgress, developmentProgress, milestoneState);

    // Generate dashboard
    const dashboard = generateDashboard(
      scanResult,
      planningProgress,
      developmentProgress,
      overallProgress,
      milestones
    );

    // Write dashboard
    const dashboardPath = 'docs/progress-dashboard.md';
    fs.writeFileSync(dashboardPath, dashboard, 'utf8');

    // Output summary
    console.log(`Overall: [${generateProgressBar(overallProgress).substring(1, 26)}] ${overallProgress}%`);
    console.log(`Dashboard updated: ${dashboardPath}`);

  } catch (error) {
    console.error(`[ERROR] Failed to update progress: ${error.message}`);
    process.exit(1);
  }
}

// Check for js-yaml dependency
try {
  require('js-yaml');
} catch {
  // If js-yaml is not installed, create a simple YAML parser
  module.exports = {
    load: function(content) {
      const result = {};
      const lines = content.split('\n');
      let currentPath = [];

      for (const line of lines) {
        const indent = line.search(/\S/);
        if (indent === -1) continue;

        const level = Math.floor(indent / 2);
        currentPath = currentPath.slice(0, level);

        const match = line.match(/^\s*([^:]+):\s*(.*)$/);
        if (match) {
          const key = match[1].trim();
          const value = match[2].trim();

          if (value) {
            let obj = result;
            for (const p of currentPath) {
              if (!obj[p]) obj[p] = {};
              obj = obj[p];
            }
            obj[key] = value;
          } else {
            currentPath.push(key);
          }
        }
      }

      return result;
    }
  };

  // Replace yaml require with simple parser
  const yaml = module.exports;
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = {
  scanProject,
  calculatePlanningProgress,
  calculateDevelopmentProgress,
  calculateOverallProgress,
  generateDashboard,
  loadMilestoneState,
  determineMilestones
};