# Potts Hero Slideshow

Potts Hero Slideshow is a standalone homepage hero/slideshow block for **webtrees 2.2**.

It gives site administrators a configurable hero banner with family photographs, captions, buttons, timing controls, transition effects and safe image storage outside the module folder.

## Recommended release model

This module is designed to be released independently from Potts Modern Theme.

- With any webtrees 2.2 theme, it works as a normal tree-homepage block.
- With Potts Modern Theme, the theme can optionally enhance the block by placing it as a full-width hero banner above the normal homepage columns.
- The slideshow owns its own markup, slideshow JavaScript, image handling and default CSS.
- Themes should only provide layout enhancements and optional CSS variables.

## Features

- Tree-homepage hero block for webtrees 2.2.
- Administrator settings page.
- Upload and manage hero images.
- Captions and alt text for each image.
- Image order, enable/disable and delete controls.
- Drag-and-drop slide ordering with up/down controls.
- Global image fit control: show whole image or crop to fill frame.
- Per-image focal point control.
- Frame styles: vintage exact frame, offset photo mount, simple frame or no frame.
- Photo style options: soft historic, original colour, sepia or black and white.
- Theme-aware hero palettes: automatic from theme, heritage blue and gold, neutral light or neutral dark.
- Slide timing, transition speed and selector-dot controls.
- Transition effects: fade, slow zoom, slide from right, slide from below, soft focus fade or random.
- Optional randomised image order each time the homepage loads.
- Caption display options: strip below frame, overlay title on image or hidden titles.
- Overlay caption vertical position control.
- Images are stored in the webtrees `data/potts-hero-slideshow/` folder so module updates do not overwrite them.

## Theme compatibility

Potts Hero Slideshow does not require Potts Modern Theme.

The automatic palette uses theme variables where available, including Potts Modern variables such as `--potts-blue`, `--potts-blue-dark` and `--potts-gold`, and Bootstrap/webtrees variables such as `--bs-primary`, `--bs-primary-rgb`, `--bs-warning` and `--bs-body-bg`.

If the active theme does not expose useful variables, the module falls back to a safe heritage palette. Administrators can also select a fixed palette in the settings page.

## Installation

1. Copy the `potts_hero_slideshow` folder into your webtrees `modules_v4/` folder.
2. In webtrees, go to **Control panel → Modules → All modules**.
3. Enable **Potts Hero Slideshow**.
4. Open the module settings and upload your hero images.
5. Add the **Potts Hero Slideshow** block to your tree homepage.

## Updating

Uploaded images are stored in the webtrees `data/potts-hero-slideshow/` folder, not inside the module folder. Replacing the module during an update should not overwrite uploaded images.

As usual, keep a backup of your webtrees `data` folder and database before updating production sites.

## Notes

- Uploads require the web server to be able to write to the webtrees `data` folder.
- Supported image types: JPG, PNG, WEBP and GIF.
- If a photo is being cropped too much, choose **Show whole image**. If the frame has too much empty space, choose **Fill frame and crop edges** and adjust the focal point for each slide.
- The internal setting name `COLOUR_MODE` is retained for backwards compatibility, but the admin interface now describes this as **Photo style** because it controls the treatment of the photograph, not the website theme colour palette.

## Version

1.0.0
