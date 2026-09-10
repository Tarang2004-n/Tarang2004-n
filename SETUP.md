# Profile visual kit

1. Create the public repository `Tarang2004-n/Tarang2004-n` with a README.
2. Upload this folder's contents to the repository root, including `.github/workflows/update-profile.yml`.
3. Open **Actions → Update profile visuals → Run workflow** for the first online generation. The built-in `GITHUB_TOKEN` is used; no additional secret is required.
4. View [your GitHub profile](https://github.com/Tarang2004-n). The workflow refreshes daily at 02:23 UTC and can be run manually.
5. For a local rebuild, run `python3 scripts/generate.py` from the repository root. Python 3.10+ and network access are sufficient; optional `GITHUB_TOKEN` enables contribution-calendar refresh.

The supplied portrait is used only in README assets. No account avatar, repository descriptions, repository contents outside this profile repository, or contribution history are changed. The spaceship is decorative.

`repositories.json` and `config.json` contain a dated public snapshot verified on 2026-09-10. Missing API data uses that snapshot rather than guessed values; the dates are displayed. On a contribution API failure, the previous activity image is retained. Primary-language counts describe the six selected repositories and do not represent proficiency or a percentage of all source code.

All visual assets are generated locally with the Python standard library. The repository owns every image; no third-party badge or widget service is needed.
