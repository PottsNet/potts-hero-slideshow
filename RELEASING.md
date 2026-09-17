# Release process

The public update feed in `latest-version.txt` must never be advanced before the matching GitHub release has been published.

## Required sequence

1. Prepare and test the release code on a release branch.
2. Ensure the module's internal version and `metadata.json` match the intended release version.
3. Run PHP syntax checks and validate the install ZIP has `potts_hero_slideshow` as its module root.
4. Create and publish the GitHub release and attach the validated ZIP.
5. Only after the release exists, update `latest-version.txt`.
6. Confirm the update-feed validation succeeds.

The `Protect update feed` workflow fails if `latest-version.txt` points to a version for which no published GitHub release exists.

For localisation releases, include both the editable `.po` file and the compiled `.mo` file loaded by webtrees at runtime.
