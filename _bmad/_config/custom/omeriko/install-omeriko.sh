#!/bin/bash
# Install Omeriko to a new project directory
# Usage: ./install-omeriko.sh /path/to/your/project

if [ -z "$1" ]; then
    echo "Usage: ./install-omeriko.sh /path/to/your/project"
    exit 1
fi

PROJECT_DIR="$1"
OMERIKO_SOURCE="/Users/yalul/Code/Agent/BMAD-METHOD/samples/sample-custom-modules/omeriko-module"

echo "⚔️ Installing Omeriko to $PROJECT_DIR..."

# Create directory structure
mkdir -p "$PROJECT_DIR/_bmad/agents/omeriko"
mkdir -p "$PROJECT_DIR/_bmad/_memory/omeriko-sidecar/projects"
mkdir -p "$PROJECT_DIR/_bmad/_memory/omeriko-sidecar/knowledge"

# Copy agent definition
cp "$OMERIKO_SOURCE/agents/omeriko/omeriko.agent.yaml" "$PROJECT_DIR/_bmad/agents/omeriko/"

# Copy sidecar files
cp "$OMERIKO_SOURCE/agents/omeriko/omeriko-sidecar/"*.md "$PROJECT_DIR/_bmad/_memory/omeriko-sidecar/"
cp "$OMERIKO_SOURCE/agents/omeriko/omeriko-sidecar/knowledge/"*.md "$PROJECT_DIR/_bmad/_memory/omeriko-sidecar/knowledge/"
cp "$OMERIKO_SOURCE/agents/omeriko/omeriko-sidecar/projects/.project-template.md" "$PROJECT_DIR/_bmad/_memory/omeriko-sidecar/projects/"

echo "✅ Omeriko installed!"
echo ""
echo "To use:"
echo "  1. cd $PROJECT_DIR"
echo "  2. cursor .   (or your preferred IDE)"
echo "  3. Tell your AI: 'Work with Omeriko on...'"
echo ""
echo "AI Design Commands:"
echo "  SD - System Design"
echo "  DP - Data Pipeline Analysis"
echo "  KB - Knowledge Base (RAG)"
echo "  TS - Training Strategy"
echo "  IO - Inference Optimization"
echo "  CR - Critical Review ⚔️"
echo "  RS - Research Scout (papers)"
echo ""
echo "Memory Commands:"
echo "  PM - Project Memory"
echo "  LP - Load Project"
echo "  LM - Lessons Learned"
echo ""
echo "BMM Handoff Commands: 🔄"
echo "  HO-PRD  - Generate PRD for BMM Architect"
echo "  HO-ARCH - Generate Architecture for BMM Dev"
echo "  HO-TEST - Generate Test Requirements for BMM QA"
echo "  HO-SUM  - Show BMM integration workflow"
