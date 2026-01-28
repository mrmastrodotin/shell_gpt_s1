#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Installing shell_gpt_s1...${NC}"

# Install pipx if not already installed
if ! command -v pipx &> /dev/null; then
    echo -e "${GREEN}Installing pipx...${NC}"
    sudo apt update
    sudo apt install pipx -y
    pipx ensurepath
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install from GitHub
echo -e "${GREEN}Installing shell_gpt_s1 from GitHub...${NC}"
pipx install git+https://github.com/mrmastrodotin/shell_gpt_s1.git

# Install Playwright browsers
echo -e "${GREEN}Installing Playwright browsers...${NC}"
~/.local/pipx/venvs/shell-gpt/bin/playwright install --with-deps chromium

echo -e "${GREEN}✓ Installation complete!${NC}"
echo -e "${BLUE}Usage: sgpt 'your prompt'${NC}"
echo -e "${BLUE}Configure Ollama: sgpt --ollama-host${NC}"
echo -e "${BLUE}Check status: sgpt --status${NC}"
