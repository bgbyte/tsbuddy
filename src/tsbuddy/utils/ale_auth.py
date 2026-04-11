import os
import sys
import subprocess
import tempfile
import time

SECRETS_FILE = os.path.join(os.path.expanduser("~"), ".tsbuddy_secrets")
EXPECTED_DOMAIN = "github.com/tsbuddy"


def load_secrets_file():
    """Load key-value pairs from ~/.tsbuddy_secrets into os.environ"""
    if os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE, encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, sep, value = line.strip().partition("=")
                    if sep:
                        os.environ[key] = value


def set_secret_variable(key, value):
    """Set or update a key=value in ~/.tsbuddy_secrets file."""
    lines = []
    found = False
    if os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE, encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f"{key}={value}\n")
    with open(SECRETS_FILE, "w", encoding='utf-8') as f:
        f.writelines(lines)


def build_git_config_value(token):
    """Build the GIT_CONFIG_PARAMETERS value from a token."""
    return f"'url.https://{token}@github.com/tsbuddy/.insteadOf=https://github.com/tsbuddy/'"


def prompt_for_token():
    """Prompt the user for their GitHub token and save it."""
    print("\nPlease enter your GitHub access token for tsbuddy private repo:")
    token = input("Token: ").strip()
    if not token:
        print("No token provided. Aborting.")
        return False
    value = build_git_config_value(token)
    set_secret_variable("GIT_CONFIG_PARAMETERS", value)
    os.environ["GIT_CONFIG_PARAMETERS"] = value
    print("Token saved to ~/.tsbuddy_secrets")
    return True


def ale_upgrade_safe(package_name="tsbuddy", current_version=None):
    """Upgrade tsbuddy from private GitHub repo (similar to update_package_safe)."""
    updater_path = os.path.join(tempfile.gettempdir(), "_tsbuddy_updater.py")

    print(f"\n🔄 Preparing to upgrade '{package_name}' from private repo...")

    updater_script = f"""\
import time
import subprocess
import sys

print("Waiting for current process to exit...")
time.sleep(2)

print("\\n","Purging pip cache to ensure clean install...")
subprocess.check_call([r"{sys.executable}", "-m", "pip", "cache", "purge"])
time.sleep(2)
subprocess.check_call([r"{sys.executable}", "-m", "pip", "uninstall", "tsbuddy", "-y"])
time.sleep(2)

print("\\n","Upgrading {package_name} from private GitHub repository...")
subprocess.check_call([r"{sys.executable}", "-m", "pip", "install", "tsbuddy @ git+https://github.com/tsbuddy/tsbuddy", "--upgrade", "--trusted-host", "github.com"])
print("\\n"+("#"*15))
print("Please report any bugs to Brian.")
if "{current_version or ''}":
    print("If there is an issue, you can revert to your previous version using: ")
    print("pip install tsbuddy=={current_version}")
print("#"*15,"\\n","\\nPlease wait...")
time.sleep(5)
print("\\n* Upgrade complete. You can now rerun tsbuddy...")
"""

    with open(updater_path, "w") as f:
        f.write(updater_script)

    # ✅ Explicitly pass environment to ensure GIT_CONFIG_PARAMETERS is preserved
    env = os.environ.copy()

    subprocess.Popen([sys.executable, updater_path], close_fds=True, env=env)

    if current_version:
        from .tsbuddy_version import set_env_variable
        set_env_variable("TSBUDDY_PREVIOUS_VERSION", current_version)
        set_env_variable("TSBUDDY_IGNORE_VERSION", "")

    print("Exiting to allow upgrade to complete...")
    sys.exit(0)


def ale_auth_and_upgrade():
    """Main entry point: load secrets, check/prompt for token, then offer upgrade."""
    load_secrets_file()

    git_config = os.environ.get("GIT_CONFIG_PARAMETERS", "")

    if git_config and EXPECTED_DOMAIN in git_config:
        print(f"\n✅ ALE auth token is already configured.")
        choice = input("Do you want to replace your existing token? [y/N]: ").strip().lower()
        if choice == 'y':
            if not prompt_for_token():
                return
        else:
            print("Keeping existing token.")
    else:
        print("\n⚠ No ALE auth token found.")
        if not prompt_for_token():
            return

    # Prompt to upgrade from private repo
    confirm = input("\nDo you want to upgrade tsbuddy from the private repo now? [y/N]: ").strip().lower()
    if confirm == 'y':
        from .tsbuddy_version import get_installed_version
        current_version = get_installed_version("tsbuddy")
        ale_upgrade_safe("tsbuddy", current_version)
    else:
        print("Skipping upgrade.")

def main():
    ale_auth_and_upgrade()

if __name__ == "__main__":
    main()