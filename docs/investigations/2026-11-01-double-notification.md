# Two notifications for Instagram 453.0.0.57.79

Investigated on Nox on 2026-11-01. All times below are NZDT (UTC+13).

## Finding

The two ready messages announced separate APK builds of the same Instagram
version. A manual Home-hiding fix rebuilt the APK between notifications. The
scheduled updater subsequently detected the changed APK payload and published
it. This was not a retry of the first Matrix event.

## Evidence

| Time | Record | Result |
| --- | --- | --- |
| 09:31:25–09:31:36 | Pueue task 3969, `./cron-update.sh` | Successful publication; Matrix event at 09:31:36.265 linked `instagram-patched-453.0.0.57.79-809bf10196d1.apk` and included upstream release notes. |
| 09:55:02–09:56:50 | Pueue task 3978, `./update-apps.sh instagram` | Successful rebuild from patch profile `…-v2` to `…-v3`; log explicitly reports `Home hidden=True`. |
| 09:56:46 | Local APK modification time | Rebuilt `apk/instagram-patched-453.0.0.57.79.apk` replaced the prior APK. |
| 12:17:00–12:17:10 | `gramforge-update.service` journal | Scheduled run succeeded. Its update log says `already patched` with the v3 profile. |
| 12:17:10.775 | Matrix room history | Second ready message linked `instagram-patched-453.0.0.57.79-5bbe11a72524.apk`. |

Task 3978 records this transition:

```text
instagram: 453.0.0.57.79/feur-v453-0-0-57-79-brosssh-v2.8.2-ads-nav-true-false-false-false-false-false-v2 -> 453.0.0.57.79/feur-v453-0-0-57-79-brosssh-v2.8.2-ads-nav-true-false-false-false-false-false-v3
FeurStagram profile normalized: ads on; other Feur blocks/prompts/updater off; Home hidden=True
instagram: created apk/instagram-patched-453.0.0.57.79.apk
```

The current successful notification checkpoint is
`payload-v1:c0075e87767e28b3d3ebf8bc8071cab4b986003b14f6f92414732c4acb61ebb0`,
with version 453.0.0.57.79, the v3 patch profile, FeurStagram
`v453-0-0-57-79`, and navigation patches `v2.8.2`.

## Why the second message had no changelog

`cron-update.sh` compares the canonical APK payload with the last successfully
announced payload, rather than comparing only Instagram versions. Direct runs
of `update-apps.sh` rebuild the local APK without publishing it or advancing the
notification checkpoint. The next cron run therefore announces that rebuild,
even if its own build step has nothing left to do.

Changelog generation separately compares upstream release tags. Both upstream
tags were unchanged after the first announcement, so the second message said
“No applicable changelog entries for this build.” Local patch changes such as
the Home-hiding fix are not included in that upstream changelog.

The notification behavior matches the current payload-based policy. The
presentation gap is that same-version rebuilds use the same ready message and
do not explain the local patch change. A possible follow-up is to identify
same-version messages as rebuilt APKs and report local patch-profile changes.
Suppressing every same-version notification would also suppress corrected APKs.

## Scope

Verified Matrix history, Pueue history and rebuild logs, systemd journal,
published filenames, local file timestamps, notification checkpoints, and the
notification code. No production configuration or notification behavior was
changed. No byte-level APK comparison was needed to establish the recorded
v2-to-v3 rebuild; an optional queued comparison was removed before execution.
