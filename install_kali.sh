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
    
    # Add valid paths to current session to proceed without restart
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install from GitHub
echo -e "${GREEN}Installing shell_gpt_s1 from GitHub...${NC}"
pipx install git+https://github.com/mrmastrodotin/shell_gpt_s1.git --force

# Install Playwright browsers
echo -e "${GREEN}Installing Playwright browsers...${NC}"
PLAYWRIGHT_BIN="$HOME/.local/pipx/venvs/shell-gpt/bin/playwright"

if [ -f "$PLAYWRIGHT_BIN" ]; then
    # Try installing with dependencies first
    echo -e "${BLUE}Attempting to install browser dependencies...${NC}"
    if ! "$PLAYWRIGHT_BIN" install --with-deps chromium; then
        echo -e "${BLUE}Dependency installation failed (common on Kali/Parrot due to package name mismatches).${NC}"
        echo -e "${BLUE}Attempting to install dependencies manually using standard Debian names...${NC}"
        
        # Standard Debian/Kali/Parrot package names (without Ubuntu's t64 suffix)
        sudo apt install -y libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi0 libcups2 libglib2.0-0 \
                            libnss3 libnspr4 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
                            libpango-1.0-0 libcairo2 libxkbcommon0
        
        echo -e "${BLUE}Attempting to install Chromium again...${NC}"
        "$PLAYWRIGHT_BIN" install chromium
        
        echo -e "${BLUE}NOTE: If web features still fail, some libraries might still be missing.${NC}"
    fi
else
    echo -e "${BLUE}Playwright binary not found in expected location. Skipping browser install.${NC}"
fi

echo -e "${GREEN}✓ Installation complete!${NC}"
echo -e "${BLUE}Usage: sgpt 'your prompt'${NC}"
echo -e "${BLUE}Configure Ollama: sgpt --ollama-host${NC}"
echo -e "${BLUE}Check status: sgpt --status${NC}"

# Remind user about PATH if needed
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo -e "${BLUE}WARNING: ~/.local/bin is not in your PATH. Run 'pipx ensurepath' and restart your terminal.${NC}" ;;
esac
