# Release Process

1. Bump the package version (example: [https://github.com/climatepolicyradar/azure-pdf-parser/pull/93](https://github.com/climatepolicyradar/azure-pdf-parser/pull/93)).
2. Compare the most recent release to `main` (example: [https://github.com/climatepolicyradar/azure-pdf-parser/compare/v0.4.1...main](https://github.com/climatepolicyradar/azure-pdf-parser/compare/v0.4.1...main)). You'll generally do a release at the `HEAD` of `main`, but, you can do a release at any point after the last release.
3. Tag the commit you want to do a release at (example: on `main`, do `git tag v0.4.2`).
4. Push the tag (example: `git push origin v0.4.2`).
5. Create a new release ([https://github.com/climatepolicyradar/azure-pdf-parser/releases/new](https://github.com/climatepolicyradar/azure-pdf-parser/releases/new)).
6. For "Choose a tag", select your new tag, and for "Previous tag", change it from "auto" to the last release (example: `v0.4.1`).
7. Press "Generate release notes" and verify that they're as expected.
8. Ensure "Set as the latest release" is selected.
9. Press "Publish release".

NB: We follow SemVer.
