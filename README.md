# Railway-2FA-Reset

A Python CLI tool to disable two-factor authentication (2FA) on a [Railway](https://railway.app) account using the Railway GraphQL API.

## Requirements

- Python 3.10+
- A valid [Railway API token](https://railway.app/account/tokens)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Check 2FA status

```bash
python reset_2fa.py --token YOUR_TOKEN --status
```

### Disable 2FA

Provide your Railway API token and the current 6-digit TOTP code from your authenticator app:

```bash
python reset_2fa.py --token YOUR_TOKEN --totp 123456
```

You can also supply the token via the `RAILWAY_TOKEN` environment variable:

```bash
export RAILWAY_TOKEN=YOUR_TOKEN
python reset_2fa.py --totp 123456
```

## Options

| Flag | Description |
|------|-------------|
| `--token` | Railway API token (or set `RAILWAY_TOKEN` env var) |
| `--totp` | 6-digit TOTP code from your authenticator app |
| `--status` | Print 2FA status and exit without making changes |

## Obtaining your Railway API token

1. Log in to <https://railway.app>
2. Go to **Account Settings → API Tokens**
3. Create a new token and copy it

## Locked out of 2FA?

If you no longer have access to your authenticator app and cannot generate a TOTP code, Railway support can assist you with a manual reset:

- Visit <https://railway.app/help>

## Example output

```
Connecting to Railway API…

── Railway Account Info ─────────────────────────────
  Name  : Jane Doe
  Email : jane@example.com
  2FA   : Enabled ✓
─────────────────────────────────────────────────────

Disabling 2FA for jane@example.com…
✓  2FA has been successfully disabled on your Railway account.
```
