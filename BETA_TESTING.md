# Potts Hero Slideshow 1.1.0-beta.1 testing

This beta adds per-tree Hero Slideshow configuration for webtrees 2.2.x.

## What to test

1. Upgrade from 1.0.1 with the existing Hero Slideshow data folder still present.
2. Confirm the existing hero remains on the tree that previously used the module.
3. Open the Hero Slideshow administration page and switch between trees using the new tree selector.
4. Confirm changing text, timing or display settings on one tree does not alter another tree.
5. Upload an image to one tree and confirm it does not appear in another tree.
6. Delete an image from one tree and confirm images in other trees are unaffected.
7. Confirm each tree homepage displays only its own enabled slides.
8. Check signed-in and signed-out display for public trees.
9. Confirm existing uploaded images were copied into the migrated tree-specific folder rather than removed from the legacy folder.

## Migration behaviour

The beta preserves the existing global Hero configuration by migrating it once to the most appropriate existing tree: the site default tree when it already uses Hero Slideshow, otherwise the first tree that has the Hero Slideshow block configured. Other trees start with independent defaults and empty image collections.

The legacy data folder is not deleted during migration.

## Release status

This is a beta build. `latest-version.txt` intentionally remains at the stable 1.0.1 release until multi-tree behaviour has been tested on a real webtrees installation.
