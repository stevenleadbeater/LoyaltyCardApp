# Flathub Publishing Plan

Plan for publishing **Loyalty Cards** (`com.github.loyaltycardapp.LoyaltyCardApp`) to Flathub
so PostmarketOS users can install it via `flatpak install flathub com.github.loyaltycardapp.LoyaltyCardApp`.

## Accounts Required

| Account | Purpose | Status |
|---------|---------|--------|
| GitHub (`stevenleadbeater`) | Source repo owner, fork flathub/flathub, receive write access | Exists |
| GitHub 2FA | **Required** before accepting Flathub repo write access | Verify enabled |
| Flathub Developer Portal | App verification ("Verified" badge) via GitHub OAuth | Create after acceptance |

## Pre-Submission Checklist

Before opening the Flathub PR, complete these items:

- [ ] **Create a tagged release** (e.g. `v0.1.0`) on `stevenleadbeater/loyalty-card-app`
- [ ] **Remove `--device=all`** from `finish-args` in the manifest (keep `--device=dri`; camera goes through portal)
- [ ] **Add `<developer>` tag** to metainfo (required by Flathub linter)
- [ ] **Add `<url type="vcs-browser">`** to metainfo
- [ ] **Add screenshots** to metainfo with stable URLs (host images in a git tag, not a branch)
- [ ] **Run the linter locally**:
  ```bash
  flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest com.github.loyaltycardapp.LoyaltyCardApp.json
  ```
- [ ] **Build and test locally**:
  ```bash
  flatpak-builder --user --install --force-clean build-dir com.github.loyaltycardapp.LoyaltyCardApp.json
  flatpak run com.github.loyaltycardapp.LoyaltyCardApp
  ```

## Submission Process

### 1. Prepare the Flathub Manifest

The Flathub manifest differs from the local development manifest. The app source must use
`type: git` (with tag + commit) or `type: archive` instead of `type: dir`:

```json
{
    "type": "git",
    "url": "https://github.com/stevenleadbeater/loyalty-card-app.git",
    "tag": "v0.1.0",
    "commit": "<full-40-char-sha>",
    "x-checker-data": {
        "type": "git",
        "tag-pattern": "^v([\\d.]+)$"
    }
}
```

The `x-checker-data` block enables Flathub's bot to auto-detect new releases hourly.

### 2. Fork and Branch

```bash
# Fork flathub/flathub on GitHub (uncheck "Copy the master branch only")
git clone --branch=new-pr git@github.com:stevenleadbeater/flathub.git
cd flathub
git checkout -b com.github.loyaltycardapp.LoyaltyCardApp
```

### 3. Add Manifest and Open PR

Place the Flathub-specific manifest at the repo root:
```
flathub/
  com.github.loyaltycardapp.LoyaltyCardApp.json
```

```bash
git add com.github.loyaltycardapp.LoyaltyCardApp.json
git commit -m "Add com.github.loyaltycardapp.LoyaltyCardApp"
git push origin com.github.loyaltycardapp.LoyaltyCardApp
```

Open a PR against the **`new-pr`** branch (not `master`). Title: `Add com.github.loyaltycardapp.LoyaltyCardApp`.

### 4. Review Process

Reviewers (volunteers) check for:

- **Linter compliance** (automated check runs on the PR)
- **Source stability** (tagged releases, not branch tips)
- **Minimal sandbox permissions** (no `--device=all`, no `--filesystem=home`)
- **Valid MetaInfo/AppStream** (developer tag, screenshots, content rating, releases)
- **Valid desktop file** (passes `desktop-file-validate`)
- **Icons** (scalable SVG or minimum 128px PNG)
- **License** (must allow redistribution)

**Common rejection reasons:**
1. `type: dir` in sources (must be git tag or archive)
2. Missing `<developer>` tag in metainfo
3. Missing screenshots
4. Excessive permissions (`--device=all`, `--filesystem=home`)
5. Missing or broken icons

**Important:** Never close and reopen the PR. Push new commits to address feedback.

### 5. Post-Acceptance

After reviewers merge the PR:

1. A new repo is created: `github.com/flathub/com.github.loyaltycardapp.LoyaltyCardApp`
2. You receive a write access invitation -- **accept within one week**
3. The first build publishes to Flathub within 1-2 hours
4. Add a `flathub.json` to the new repo to enable auto-merge of bot PRs:
   ```json
   {
       "automerge-flathubbot-prs": true
   }
   ```

### 6. Ongoing Maintenance

- Pushing/merging to `master` in the Flathub app repo triggers an official build
- The `x-checker-data` bot runs hourly and creates PRs when new tags are detected
- With `automerge-flathubbot-prs: true`, new releases publish automatically
- Use `beta` branch for beta/testing channel

### 7. App Verification

After acceptance, get the "Verified" badge:

1. Log into https://flathub.org with your GitHub account (`stevenleadbeater`)
2. Navigate to your app in the developer portal
3. Follow the verification flow (GitHub OAuth proves repo ownership)

## Architecture Notes for PostmarketOS/Phosh

- The app builds for both `x86_64` and `aarch64` (PostmarketOS devices are ARM)
- The existing CI already builds both architectures
- `X-Purism-FormFactor=Workstation;Mobile;` in the desktop file signals Phosh compatibility
- MetaInfo `<recommends>` with `<control>touch</control>` and `<requires><display_length compare="ge">360</display_length></requires>` correctly describes mobile support
- PostmarketOS includes Flatpak support; users add the Flathub remote and install directly

## GitHub Actions Workflow

A `flathub-release.yml` workflow is included in `.github/workflows/` to automate:

- Creating GitHub releases on version tags (`v*`)
- Building Flatpak bundles for both architectures
- Attaching bundles to the release

This pairs with Flathub's `x-checker-data` for fully automated publishing:
tag a release -> GitHub Actions builds bundles -> Flathub bot detects the tag -> bot PRs the update -> auto-merged -> published on Flathub.
