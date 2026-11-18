# Phase 3 synthetic Discord pilot on macOS

Status is **`BLOCKED_OWNER_APPROVAL`** for public ingress and Discord setup. Operate from the pinned P3-D checkout and keep the Phase 2 workflow and catalogue authority separate. [Phase 3 tracker](https://github.com/KanujVerma/jobbie/issues/8)

## Local preparation

Use Python with `requirements-phase3.txt` installed. Run from the reviewed checkout. Create a new directory outside Git for each pilot. The initializer generates the synthetic catalogue, PDF and DOCX, pins their hashes and creates separate storage and download keys. The directory uses mode 0700, the fixture catalogue uses 0400 and the credentials use 0600. The environment passed to the service contains only pilot settings. The runner accepts only the pinned synthetic catalogue and documents. A production checkpoint or real resume requires separate approval and a different setup.

```sh
PILOT_DIR="$HOME/Library/Application Support/Jobbie Phase 3 Synthetic Pilot"
python -m jobbie_private.pilot init "$PILOT_DIR"
```

The built-in local tests run separate server, download and worker processes without LaunchAgents or system settings. The supervisor restarts a failed process twice, then shuts down its children if the restart limit is exceeded. It holds an exclusive lock per pilot directory. A restart resumes queued work and preserves the existing task ownership rules for uncertain in-flight work.

The interaction listener binds to `127.0.0.1:18765` and accepts only `POST /interactions`. It limits requests to eight in flight, a two-second server deadline and the existing 64 KiB body cap. The signed app, configured owner and approved guild gate commands. Discord's signed PING remains side-effect free. Private downloads use `127.0.0.1:18766` with both a separate bearer and a signed 5-minute ticket. Keep 18766 outside Funnel. Logs record status, elapsed time and worker outcome without bodies, tokens, owner IDs, query strings or document data.

The parser runs in the macOS Seatbelt sandbox using an allowlist of interpreter files and the parser entrypoint. Tests on macOS confirmed PDF and DOCX parsing and denied private-file reads, writes and TCP connections. The parser retains its six-second parent deadline and CPU limit. Startup verifies the supplied PDF and DOCX under the installed sandbox. Treat this temporary, synthetic-only profile as an explicit Mac compatibility boundary. [Phase 3 security controls](SECURITY.md#phase-3-private-interaction-boundary)

## Owner approval required for live setup

Approve the following together before connecting Funnel, installing or registering the Discord app, or starting the live worker:

1. Reconnect the existing Mac Tailscale node, leaving its existing port 443 configuration in place. Review that existing route before reconnecting. Confirm MagicDNS and HTTPS are enabled, the subscription needs no purchase, and HTTPS port 8443 has neither Serve nor Funnel configuration. Grant `funnel` in `nodeAttrs` to this Mac's exact Tailscale address only after approving the policy diff. Use the existing node and domain. Funnel is public and the certificate can disclose the node's DNS name through Certificate Transparency. The Personal plan is free and Funnel is available on all plans. [Funnel requirements](https://tailscale.com/docs/features/tailscale-funnel) · [macOS CLI support](https://tailscale.com/docs/reference/tailscale-cli/funnel) · [Node selectors](https://tailscale.com/docs/reference/targets-and-selectors) · [HTTPS](https://tailscale.com/docs/features/https) · [Pricing](https://tailscale.com/pricing)
2. Create a **separate** Discord developer application named for the synthetic pilot. Disable public bot installation, enable Guild Install only, and install it only in a private pilot guild with the `applications.commands` and `bot` scopes and **zero bot permissions**. Use gateway intents disabled. Provide its application ID, Ed25519 public key, your Discord user ID, and the private guild ID through the local no-echo `configure` prompt. The dedicated bot token is needed only at guild command registration. Enter it into the local no-echo prompt or the approved secure secret channel. [Discord command authorization and guild registration](https://docs.discord.com/developers/interactions/application-commands)
3. Approve the generated synthetic catalogue and documents for the live session and the foreground process lifetime on this Mac. Approve the ingress URL only for the pilot application. A private test member is optional if Discord-side non-owner rejection needs a live second-account receipt. Otherwise record direct unauthorized HTTP denial as local evidence and the live second-account check as pending. Phase 3 production release remains a separate approval.

Expected incremental provider cost is **$0** on the existing Mac and a zero-cost eligible tailnet. Confirm the account's actual plan in Billing. The pilot requires no purchased hosting or custom domain.

## Owner-approved live sequence

Use the reviewed checkout and keep the same `PILOT_DIR` throughout. Configure the dedicated IDs outside Git and inspect the local command manifest.

```sh
python -m jobbie_private.pilot configure "$PILOT_DIR"
python -m jobbie_private.pilot manifest "$PILOT_DIR"
printf '%s' '{"target_roles":["Software Engineer"],"target_locations":["San Francisco"]}' |
  python -m jobbie_private.pilot owner "$PILOT_DIR" profile-set --request-id synthetic-profile
python -m jobbie_private.pilot run "$PILOT_DIR" --approved-live-pilot
```

After confirming both listeners and the worker are ready, start **foreground** Funnel in a separate terminal. Record the assigned public URL. Keep the download listener local.

```sh
tailscale funnel --https=8443 http://127.0.0.1:18765
```

In the dedicated Discord app, set its **Interactions Endpoint URL** to `https://<assigned-node>.ts.net:8443/interactions`. The portal must accept the URL and validate signed PING. Discord compatibility with this exact nondefault port and host is a live gate. The code constrains registration to the configured application and guild and refuses to overwrite existing commands. No global registration is used.

```sh
python -m jobbie_private.pilot register "$PILOT_DIR" --approved-live-pilot
```

From the owner's Discord account, use `/health`, `/settings`, `/profile show`, `/jobs find` and `/jobs top`. Check View, Save and Explain for the synthetic listing. Upload the generated PDF or DOCX and use `/resume propose` with the resulting version ID. Use owner-console `facts-propose` to list the existing proposal IDs, then `fact-inspect` and `fact-decide` to confirm and revoke the synthetic Python fact. Explain must reflect both transitions. Open a synthetic application record from the saved snapshot ID, record an owner-confirmed synthetic status and check `/applications`. This updates the local test ledger only.

Use `resume-link` to obtain a short-lived local ticket. Request it against `127.0.0.1:18766` with the independent bearer from the private settings file. Check wrong bearer, expiry and deletion. Create an encrypted backup and prove restore into a new private path with the matching key. Check key mismatch and restart through the offline test path. Record actual Discord command outcomes, response and completion latency, deferred task status, and sanitized failures. A local fixture pass and a portal endpoint save are separate from successful live commands. [Discord deadlines and deferred replies](https://docs.discord.com/developers/interactions/receiving-and-responding)

## Rollback

Remove the endpoint and uninstall the dedicated pilot app from the pilot guild. Stop the foreground Funnel command. If the dedicated route remains, turn off only `--https=8443` and confirm it is gone. Avoid Funnel reset because other routes are outside this pilot. Remove only the approved pilot node attribute. Return the Tailscale connection to its recorded starting state after confirming it is safe to do so. Stop the local supervisor with Ctrl+C. Retain the owner-only encrypted pilot files pending the owner's cleanup decision.

After a successful live pilot and separate release approval, integrate #39 through #42 in order and recheck the base, head, CI, review and Phase 2 fingerprints at each step.
