# Changelog

## 1.0.0

- First stable public release.
- Promoted the tested standalone module from beta to stable release status.
- Includes theme-aware palettes, standalone slideshow styling, safe image storage and GitHub-ready metadata.

## 1.0.0-beta.16

- Prepared the module for standalone GitHub release.
- Aligned the PHP module version, `metadata.json` and `latest-version.txt`.
- Added a theme-aware hero palette setting:
  - Automatic from theme
  - Heritage blue and gold
  - Neutral light
  - Neutral dark
- Added a CSS variable layer so the slideshow can use Potts Modern Theme variables where present, Bootstrap/webtrees variables where available, and safe fallbacks for other themes.
- Renamed the admin label from **Image treatment** to **Photo style** to avoid confusion with theme colour selection.
- Improved README wording to clarify that Potts Modern Theme is optional and provides enhanced layout only.
- Added upload MIME checking after file upload, based on the stored file content.

## 1.0.0-beta.15

- Added an overlay caption position control so administrators can raise or lower the image title strip when using overlay captions.

## 1.0.0-beta.12

- Changed the randomisation option from random first image to randomise all enabled images into a fresh order each time the homepage loads.

## 1.0.0-beta.10

- Added an image title display option: title strip below image, overlay title or hidden titles.
- Reworked the caption strip layout so the below-frame caption is rendered outside the photo frame rather than being clipped inside the image area.
- Added a transition speed setting so administrators can control how quickly images fade, slide or blur between slides.

## 1.0.0-beta.5

- Added transition effects: gentle fade, slow zoom, slide from right, slide from below, soft focus fade and random.
- Added drag-and-drop slide ordering with up/down controls.
- Updated hero colours to follow Potts Modern Theme palette variables when used with the modern theme.
