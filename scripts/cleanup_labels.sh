#!/bin/bash

# List of old labels to remove
old_labels=(
    "Priority: High"
    "Priority: Low"
    "Priority: Medium"
    "Status: Complete"
    "Status: Confirmed"
    "Status: Feedback Needed"
    "Status: In Progress"
    "Status: On Hold"
    "Status: Review Needed"
    "Type: bug"
    "Type: Enhancement"
    "Type: Feature"
    "Type: Help Needed"
    "Type: Idea"
    "Type: Question"
)

# Remove each old label
for label in "${old_labels[@]}"; do
    gh label delete "$label" --yes
done 