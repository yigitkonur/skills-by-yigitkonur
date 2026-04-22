        # Cheap Repo Signals

        Use these low-cost checks on shortlisted repos before deeper digging.

        ## 1. Base repo metadata

        ```bash
        gh api repos/OWNER/REPO           --jq '{repo: .full_name, stars: .stargazers_count, forks: .forks_count, pushed: .pushed_at[:10], archived: .archived, disabled: .disabled, license: (.license.spdx_id // "none"), open_issues: .open_issues_count, default_branch: .default_branch}'
        ```

        Good for: stars, freshness, archived status, license, and basic maintenance posture.

        ## 2. Recent commit glance

        ```bash
        gh api 'repos/OWNER/REPO/commits?per_page=5'           --jq '.[] | "\(.commit.author.date[:10])	\(.author.login // .commit.author.name)	\(.commit.message | split("
")[0] | .[:80])"'
        ```

        Good for: whether the project still moves, how recently, and whether maintenance looks human and coherent.

        ## 3. Recent releases

        ```bash
        gh api 'repos/OWNER/REPO/releases?per_page=3'           --jq '.[] | "\(.tag_name)	\(.published_at[:10])	\(.name // "")"'
        ```

        Good for: release cadence and whether the repo ships usable milestones.

        ## 4. Community profile

        ```bash
        gh api repos/OWNER/REPO/community/profile           --jq '{health: .health_percentage, readme: (if .files.readme then true else false end), contributing: (if .files.contributing then true else false end), license: (.files.license.spdx_id // "none")}'
        ```

        Good for: README presence, contributing guide, and basic project hygiene.

        ## 5. Workflow or CI presence

        ```bash
        gh api 'repos/OWNER/REPO/actions/workflows' --jq '.total_count'
        ```

        Good for: cheap CI visibility. If the repo does not use GitHub Actions, fall back to root file checks instead of forcing more API calls.

        ## Usage rules

        - Run these on shortlisted repos, not the whole field.
        - Stop when you already have enough evidence to explain the recommendation.
        - If a repo is obviously off-fit, drop it instead of collecting more metadata.
