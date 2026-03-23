#!/bin/bash
set -e

# Mapping: worktree-dir -> branch-name
declare -A WORKTREE_BRANCHES
WORKTREE_BRANCHES=(
  ["agent-ab839650"]="ai-feature/database-schemas"
  ["agent-a247a69f"]="ai-feature/auth-system"
  ["agent-aeccd493"]="ai-feature/api-gateway"
  ["agent-a98132728"]="ai-feature/forge-data-fabric"
  ["agent-afeba158"]="ai-feature/forgecore-orchestrator"
  ["agent-a38869e0"]="ai-feature/player-twin"
  ["agent-a18a8223"]="ai-feature/impact-rank"
  ["agent-aeb0997a"]="ai-feature/truth-engine"
  ["agent-aa36b4e4"]="ai-feature/loop-ai"
  ["agent-ae9b38e2"]="ai-feature/transfer-input-lab"
  ["agent-a05bcbee"]="ai-feature/integrity-trust"
  ["agent-ac091318"]="ai-feature/madden-scheme-gameplan"
  ["agent-a184141a"]="ai-feature/madden-roster-matchup"
  ["agent-a98c94bb"]="ai-feature/madden-clock-killsheet"
  ["agent-ac738af8"]="ai-feature/opponent-intelligence"
  ["agent-acb19b1b"]="ai-feature/cfb26-module"
  ["agent-a9a2f05c"]="ai-feature/mental-performance"
  ["agent-ae51a3ba"]="ai-feature/frontend-dashboard"
  ["agent-a7c57fbd"]="ai-feature/frontend-game-intel"
  ["agent-aa7efd4c"]="ai-feature/cicd-deploy"
)

echo "Collecting worktree code into branches..."
