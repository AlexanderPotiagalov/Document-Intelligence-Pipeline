#!/bin/bash

# DFO Project Bootstrap Script

# Step 1: Create standard folders
mkdir -p data logs scripts output

# Step 2: Add a README and starter Python file
echo "# DFO Document Intelligence Pipeline" > README.md
touch scripts/main.py # creates blank file

# Step 3: Initialize Git
git init

# Step 4: Confirm success
echo "✅ Project initialized with standard structure!"

# run script with --> chmod +x init_project.sh