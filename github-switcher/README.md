# GitHub Account Switcher

A PowerShell script to manage multiple GitHub accounts on Windows.

## Overview

This tool helps you switch between multiple GitHub accounts (aiwithr and raqueeb) by updating your SSH config file. It generates the correct SSH configuration based on your selected account.

## Prerequisites

Before using this tool, you need:

1. **Git installed** - Download from https://git-scm.com
2. **PowerShell** - Comes with Windows 10/11
3. **SSH keys generated** for both accounts

## SSH Key Setup

### Step 1: Generate SSH Keys

Open PowerShell and run:

```powershell
# For aiwithr account
ssh-keygen -t ed25519 -C "your_email@example.com"
# When asked for file: id_ed25519_aiwithr

# For raqueeb account
ssh-keygen -t ed25519 -C "your_email@example.com"
# When asked for file: id_ed25519_raqueeb
```

### Step 2: Add Keys to GitHub

1. Copy your public key:
```powershell
cat ~/.ssh/id_ed25519_aiwithr.pub
```

2. Go to github.com/settings/keys
3. Click "New SSH key"
4. Paste the key and save
5. Repeat for the other account

### Step 3: Verify Keys Work

```powershell
# Test aiwithr connection
ssh -T git@github.com

# Test specific account
ssh -T git@aiwithr.github.com
```

## Usage

### Check Current Account

```powershell
cd ~/github-switcher
.\switch.ps1
```

Output:
```
======================================
  Current Account: aiwithr
======================================

To switch, run:
  .\switch.ps1 aiwithr  (or .\switch.ps1 raqueeb)
```

### Switch to aiwithr

```powershell
.\switch.ps1 aiwithr
```

### Switch to raqueeb

```powershell
.\switch.ps1 raqueeb
```

## Cloning Repos

After switching, clone repos using:

```powershell
# Uses the currently active account (github.com)
git clone git@github.com:username/repo.git

# Force specific account
git clone git@raqueeb.github.com:raqueeb/fb_medium_all.git
git clone git@aiwithr.github.com:aiwithr/fb_medium.git
```

## Quick Install (New PC/Laptop)

1. **Clone this repository:**
```powershell
git clone https://github.com/raqueeb/fb_medium_all.git
cd fb_medium_all/github-switcher
```

2. **Generate SSH keys:**
```powershell
ssh-keygen -t ed25519 -C "wideangle@gmail.com"
# Save as: id_ed25519_aiwithr

ssh-keygen -t ed25519 -C "your_email@email.com"
# Save as: id_ed25519_raqueeb
```

3. **Add public keys to GitHub:**
```powershell
# View keys
cat ~/.ssh/id_ed25519_aiwithr.pub
cat ~/.ssh/id_ed25519_raqueeb.pub

# Add to respective GitHub accounts at github.com/settings/keys
```

4. **Initialize SSH config:**
```powershell
.\switch.ps1 aiwithr
```

5. **Test connection:**
```powershell
ssh -T git@github.com
```

## File Structure

```
github-switcher/
|
|-- switch.ps1     # Main switcher script
|-- README.md     # This documentation
```

## How It Works

The script modifies your SSH config file at:
```
~/.ssh/config
```

It creates two Host entries:
- `github.com` - Uses the active account's key
- `raqueeb.github.com` - Forces raqueeb account
- `aiwithr.github.com` - Forces aiwithr account

## Troubleshooting

### "Could not resolve hostname"
- Check your internet connection
- GitHub may be down: status.github.com

### "Permission denied"
- Verify SSH key was added to GitHub
- Check key file permissions:
```powershell
Get-Item ~/.ssh/id_ed25519_aiwithr
# Should show: -a---- (not -a--r)
```

### "Agent admitted failure to sign"
- Add keys to ssh-agent:
```powershell
ssh-add ~/.ssh/id_ed25519_aiwithr
ssh-add ~/.ssh/id_ed25519_raqueeb
```

### Git says "not a git repository"
- You forgot to switch back after a specific clone
- Run: `.\switch.ps1` to check current account

## Customization

To change which account is default, edit `switch.ps1` and run:
```powershell
.\switch.ps1 <account-name>
```

To add more accounts, edit the config generation section in `switch.ps1`.

## Files NOT Included (Security)

For security, the following files are NOT included:
- Private SSH keys (`id_ed25519_*`)
- Public SSH keys (`id_ed25519_*.pub`)
- `~/.ssh/config`

Generate your own keys and keep them secure.

## License

MIT - Use freely, customize as needed.