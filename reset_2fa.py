#!/usr/bin/env python3
"""
Railway 2FA Reset Tool
======================
A CLI tool to disable two-factor authentication on your Railway account
using the Railway GraphQL API.

Usage:
    python reset_2fa.py --token <RAILWAY_TOKEN> [--totp <TOTP_CODE>]

Alternatively, set the RAILWAY_TOKEN environment variable:
    export RAILWAY_TOKEN=your_token_here
    python reset_2fa.py [--totp <TOTP_CODE>]
"""

import argparse
import os
import sys

import requests

RAILWAY_GRAPHQL_URL = "https://backboard.railway.app/graphql/v2"

QUERY_ME = """
query Me {
  me {
    id
    email
    name
    twoFactorInfo {
      isVerified
    }
  }
}
"""

MUTATION_DISABLE_2FA = """
mutation TwoFactorAuthenticationDisable($token: String!) {
  twoFactorAuthenticationDisable(token: $token)
}
"""

MUTATION_GENERATE_RECOVERY_CODES = """
mutation TwoFactorAuthenticationGenerateRecoveryCodes($token: String!) {
  twoFactorAuthenticationGenerateRecoveryCodes(token: $token) {
    recoveryCodes
  }
}
"""


def railway_request(railway_token: str, query: str, variables: dict | None = None) -> dict:
    """Send a GraphQL request to the Railway API."""
    headers = {
        "Authorization": "Bearer " + railway_token,
        "Content-Type": "application/json",
    }
    payload: dict = {"query": query}
    if variables:
        payload["variables"] = variables

    try:
        response = requests.post(RAILWAY_GRAPHQL_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Railway API. Check your internet connection.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("Error: Request to Railway API timed out.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as exc:
        print(f"Error: HTTP {exc.response.status_code} from Railway API.", file=sys.stderr)
        if exc.response.status_code == 401:
            print("Your Railway token is invalid or has expired.", file=sys.stderr)
        sys.exit(1)

    data = response.json()
    if "errors" in data:
        errors = data["errors"]
        for error in errors:
            print(f"API Error: {error.get('message', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)

    return data.get("data", {})


def get_account_info(railway_token: str) -> dict:
    """Retrieve the current user's account information from Railway."""
    data = railway_request(railway_token, QUERY_ME)
    return data.get("me", {})


def disable_2fa(railway_token: str, totp_code: str) -> bool:
    """Disable 2FA on the Railway account using the current TOTP code."""
    data = railway_request(
        railway_token,
        MUTATION_DISABLE_2FA,
        variables={"token": totp_code},
    )
    return bool(data.get("twoFactorAuthenticationDisable"))


def print_account_info(account: dict) -> None:
    """Print formatted account information."""
    print("\n── Railway Account Info ─────────────────────────────")
    print(f"  Name  : {account.get('name', 'N/A')}")
    print(f"  Email : {account.get('email', 'N/A')}")
    two_factor_info = account.get("twoFactorInfo") or {}
    verified = two_factor_info.get("isVerified", False)
    status = "Enabled ✓" if verified else "Disabled ✗"
    print(f"  2FA   : {status}")
    print("─────────────────────────────────────────────────────\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reset (disable) two-factor authentication on your Railway account.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python reset_2fa.py --token YOUR_TOKEN --totp 123456
  RAILWAY_TOKEN=YOUR_TOKEN python reset_2fa.py --totp 123456

Obtaining your Railway API token:
  1. Log in to https://railway.app
  2. Go to Account Settings → API Tokens
  3. Create a new token and copy it

Note:
  The --totp code is the 6-digit code from your authenticator app.
  If you no longer have access to your authenticator, Railway support
  can help at https://railway.app/help
        """,
    )
    parser.add_argument(
        "--token",
        metavar="RAILWAY_TOKEN",
        help="Your Railway API token (or set the RAILWAY_TOKEN environment variable).",
    )
    parser.add_argument(
        "--totp",
        metavar="TOTP_CODE",
        help="The 6-digit TOTP code from your authenticator app.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print 2FA status for the account and exit without making changes.",
    )
    args = parser.parse_args()

    # Resolve token
    railway_token = args.token or os.environ.get("RAILWAY_TOKEN", "")
    if not railway_token:
        parser.error(
            "A Railway API token is required. "
            "Provide it with --token or set the RAILWAY_TOKEN environment variable."
        )

    print("Connecting to Railway API…")
    account = get_account_info(railway_token)

    if not account:
        print("Error: Could not retrieve account information.", file=sys.stderr)
        sys.exit(1)

    print_account_info(account)

    if args.status:
        sys.exit(0)

    two_factor_info = account.get("twoFactorInfo") or {}
    if not two_factor_info.get("isVerified", False):
        print("2FA is already disabled on this account. No action needed.")
        sys.exit(0)

    if not args.totp:
        parser.error(
            "A TOTP code is required to disable 2FA. Provide it with --totp <CODE>.\n"
            "If you no longer have access to your authenticator, contact Railway support at "
            "https://railway.app/help"
        )

    totp_code = args.totp.strip()
    if not totp_code.isdigit() or len(totp_code) != 6:
        parser.error("The TOTP code must be exactly 6 digits (e.g. --totp 123456).")

    print(f"Disabling 2FA for {account.get('email', 'your account')}…")
    success = disable_2fa(railway_token, totp_code)

    if success:
        print("✓  2FA has been successfully disabled on your Railway account.")
    else:
        print(
            "✗  2FA could not be disabled. The TOTP code may be incorrect or expired.\n"
            "   Please try again with a fresh code from your authenticator app.\n"
            "   If you are still having trouble, contact Railway support at https://railway.app/help",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
