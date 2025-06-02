#!/bin/bash

# Type Labels (Blue - #1d76db)
gh label create "type:feature" --color "1d76db" --description "New feature"
gh label create "type:bug" --color "1d76db" --description "Bug report"
gh label create "type:documentation" --color "1d76db" --description "Documentation updates"
gh label create "type:enhancement" --color "1d76db" --description "Improvement to existing feature"
gh label create "type:refactor" --color "1d76db" --description "Code refactoring"
gh label create "type:test" --color "1d76db" --description "Adding or updating tests"
gh label create "type:chore" --color "1d76db" --description "Maintenance tasks"

# Priority Labels (Red - #d73a4a)
gh label create "priority:high" --color "d73a4a" --description "Critical priority"
gh label create "priority:medium" --color "d73a4a" --description "Medium priority"
gh label create "priority:low" --color "d73a4a" --description "Low priority"
gh label create "priority:blocker" --color "d73a4a" --description "Blocks other work"

# Component Labels (Green - #0e8a16)
gh label create "component:ui" --color "0e8a16" --description "UI/Frontend related"
gh label create "component:backend" --color "0e8a16" --description "Backend services"
gh label create "component:rag" --color "0e8a16" --description "RAG system specific"
gh label create "component:flink" --color "0e8a16" --description "Flink processing"
gh label create "component:api" --color "0e8a16" --description "API related"
gh label create "component:database" --color "0e8a16" --description "Database related"
gh label create "component:security" --color "0e8a16" --description "Security related"

# Status Labels (Yellow - #fbca04)
gh label create "status:needs-review" --color "fbca04" --description "Ready for review"
gh label create "status:in-progress" --color "fbca04" --description "Currently being worked on"
gh label create "status:blocked" --color "fbca04" --description "Blocked by something"
gh label create "status:ready-for-qa" --color "fbca04" --description "Ready for testing"
gh label create "status:needs-more-info" --color "fbca04" --description "Requires more information"
gh label create "status:completed" --color "fbca04" --description "Work completed"

# Size Labels (Purple - #7057ff)
gh label create "size:small" --color "7057ff" --description "Quick fixes, small changes"
gh label create "size:medium" --color "7057ff" --description "Moderate changes"
gh label create "size:large" --color "7057ff" --description "Major changes"
gh label create "size:epic" --color "7057ff" --description "Very large changes"

# Special Labels (Orange - #ff7922)
gh label create "good-first-issue" --color "ff7922" --description "Good for new contributors"
gh label create "help-wanted" --color "ff7922" --description "Looking for help"
gh label create "breaking-change" --color "ff7922" --description "Will break existing functionality"
gh label create "security" --color "ff7922" --description "Security related issues"
gh label create "performance" --color "ff7922" --description "Performance related issues" 