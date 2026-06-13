# Slack app setup

Target app: [A0BABMXDYJW](https://api.slack.com/apps/A0BABMXDYJW)

The bot uses Socket Mode, so local development does not require a public webhook
or tunnelling service.

## 1. Apply the manifest

1. Open the target app.
2. Select **App Manifest**.
3. Choose YAML and replace the current manifest with `slack-manifest.yaml`.
4. Save the changes.

The least-privilege manifest enables one slash command, bot mentions, file reads,
message replies, and the channel history needed for Slack-native operation.

## 2. Create the Socket Mode token

1. Open **Basic Information**.
2. Under **App-Level Tokens**, choose **Generate Token and Scopes**.
3. Name it `local-socket-mode`.
4. Add only `connections:write`.
5. Generate the token.
6. Save it locally as `SLACK_APP_TOKEN` in `.env.local`.

The value begins with `xapp-`. Never paste it into chat or commit it.

## 3. Install the bot

1. Open **Install App**.
2. Select **Install to Workspace** or **Reinstall to Workspace**.
3. Review and allow the requested scopes.
4. Save the **Bot User OAuth Token** locally as `SLACK_BOT_TOKEN` in `.env.local`.

The value begins with `xoxb-`.

## 4. Start and invite

```powershell
uv run slack-kb
```

Invite the bot to each channel whose team knowledge it should serve:

```text
/invite @Knowledge Base
```

Test:

```text
@Knowledge Base add team Our support hours are 9 AM to 6 PM IST.
@Knowledge Base ask What are our support hours?
```

Continue a follow-up question in the bot's reply thread to demonstrate isolated
multi-turn memory.

Set `ORG_ADMIN_USER_IDS` to a comma-separated list of Slack user IDs allowed to
publish organisation-wide knowledge. An empty list disables org ingestion.

To ingest a past Slack thread, copy its message permalink and submit it from the
same channel:

```text
@Knowledge Base add team https://your-workspace.slack.com/archives/C.../p...
```

The same-channel restriction prevents a user from using the bot to move private
channel history into another channel. Direct messages support personal Q&A and
personal ingestion without requiring an `@mention`.

## Verification checklist

- `/knowledge help` returns command guidance.
- A mention receives a threaded response.
- A PDF or DOCX attached to `@Knowledge Base add team` is indexed.
- A cited answer is returned in the same channel.
- The same team-only question in another channel is refused.
- An unsupported question produces the explicit insufficient-evidence response.

Slack references:

- [App manifests](https://docs.slack.dev/reference/app-manifest/)
- [Socket Mode with Bolt for Python](https://docs.slack.dev/tools/bolt-python/concepts/socket-mode/)
- [Slash commands](https://docs.slack.dev/interactivity/implementing-slash-commands/)
