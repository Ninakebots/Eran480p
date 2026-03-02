import os
import sys
import subprocess
import logging

LOGGER = logging.getLogger(__name__)

def run_git_command(args):
    try:
        return subprocess.check_output(['git'] + args, stderr=subprocess.STDOUT).decode().strip()
    except subprocess.CalledProcessError as e:
        LOGGER.error(f"Git command failed: {e.output.decode()}")
        raise Exception(e.output.decode())

async def check_for_updates(remote=None, branch=None):
    if remote:
        if branch:
            run_git_command(['fetch', remote, branch])
        else:
            run_git_command(['fetch', remote])
    else:
        # Try to get remote URL from origin, fallback to hardcoded if it fails
        try:
            remote_url = run_git_command(['remote', 'get-url', 'origin'])
            run_git_command(['fetch', remote_url])
        except Exception:
            run_git_command(['fetch', 'https://github.com/Ninakebots/Eran480p', 'main'])

    curr_head = run_git_command(['rev-parse', 'HEAD'])
    new_head = run_git_command(['rev-parse', 'FETCH_HEAD'])

    return curr_head != new_head, curr_head, new_head

async def perform_update():
    out = run_git_command(['reset', '--hard', 'FETCH_HEAD'])
    return out

def restart_bot():
    LOGGER.info("Restarting bot...")
    os.execl(sys.executable, sys.executable, "-m", "bot")
