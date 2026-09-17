from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one match, found {count}')
    return text.replace(old, new, 1)


path = Path('PottsHeroSlideshow.php')
text = path.read_text(encoding='utf-8')

text = replace_once(
    text,
    "use function preg_replace;\nuse function random_bytes;",
    "use function preg_replace;\nuse function random_bytes;\nuse function rawurlencode;",
    'rawurlencode import',
)

text = replace_once(
    text,
    "        if ($task === 'reset') {\n            foreach (self::DEFAULTS as $key => $value) {\n                $this->setTreePreference($tree, $key, $value);\n            }",
    "        if ($task === 'reset') {\n            foreach ($this->defaultsForTree($tree) as $key => $value) {\n                $this->setTreePreference($tree, $key, $value);\n            }",
    'reset defaults',
)

anchor = "    private function treePreferenceKey(Tree $tree, string $key): string\n    {\n        return 'TREE_' . $tree->id() . '_' . $key;\n    }\n\n"
defaults_method = "    /** @return array<string,string> */\n    private function defaultsForTree(Tree $tree): array\n    {\n        $defaults = self::DEFAULTS;\n        $tree_path = '/tree/' . rawurlencode($tree->name());\n\n        $defaults['TITLE'] = 'Welcome to ' . $tree->title();\n        $defaults['BUTTON_1_URL'] = $tree_path;\n        $defaults['BUTTON_2_URL'] = $tree_path . '/books';\n\n        return $defaults;\n    }\n\n"
text = replace_once(text, anchor, anchor + defaults_method, 'tree defaults method')

text = replace_once(
    text,
    "        foreach (self::DEFAULTS as $key => $default) {\n            $this->setTreePreference($tree, $key, $this->getPreference($key, $default));\n        }",
    "        foreach ($this->defaultsForTree($tree) as $key => $default) {\n            $this->setTreePreference($tree, $key, $this->getPreference($key, $default));\n        }",
    'migration defaults',
)

text = replace_once(
    text,
    "        $settings = [];\n\n        foreach (self::DEFAULTS as $key => $default) {",
    "        $settings = [];\n        $defaults = $this->defaultsForTree($tree);\n\n        foreach ($defaults as $key => $default) {",
    'settings defaults',
)

text = replace_once(
    text,
    "    private function saveSettings(Tree $tree, array $data): void\n    {\n        foreach (['ENABLED', 'SHOW_BUTTON_1', 'SHOW_BUTTON_2', 'DOTS', 'RANDOM_START'] as $key) {",
    "    private function saveSettings(Tree $tree, array $data): void\n    {\n        $defaults = $this->defaultsForTree($tree);\n\n        foreach (['ENABLED', 'SHOW_BUTTON_1', 'SHOW_BUTTON_2', 'DOTS', 'RANDOM_START'] as $key) {",
    'save defaults var',
)

text = text.replace(" : self::DEFAULTS[$key];", " : $defaults[$key];")
text = text.replace("(int) self::DEFAULTS['INTERVAL']", "(int) $defaults['INTERVAL']")
text = text.replace("(int) self::DEFAULTS['TRANSITION_SPEED']", "(int) $defaults['TRANSITION_SPEED']")
text = text.replace("(int) self::DEFAULTS['CAPTION_OFFSET']", "(int) $defaults['CAPTION_OFFSET']")
for key in ['IMAGE_FIT', 'FRAME_STYLE', 'COLOUR_MODE', 'PALETTE', 'TRANSITION', 'CAPTION_STYLE']:
    text = text.replace(f" : self::DEFAULTS['{key}'];", f" : $defaults['{key}'];")
    text = text.replace(f" ? ${{key.lower() if False else ''}}", f" ? ${{key.lower() if False else ''}}")

# Target the remaining saveSettings choice fallbacks explicitly.
text = text.replace("? $fit : self::DEFAULTS['IMAGE_FIT']", "? $fit : $defaults['IMAGE_FIT']")
text = text.replace("? $frame : self::DEFAULTS['FRAME_STYLE']", "? $frame : $defaults['FRAME_STYLE']")
text = text.replace("? $colour : self::DEFAULTS['COLOUR_MODE']", "? $colour : $defaults['COLOUR_MODE']")
text = text.replace("? $palette : self::DEFAULTS['PALETTE']", "? $palette : $defaults['PALETTE']")
text = text.replace("? $transition : self::DEFAULTS['TRANSITION']", "? $transition : $defaults['TRANSITION']")
text = text.replace("? $caption_style : self::DEFAULTS['CAPTION_STYLE']", "? $caption_style : $defaults['CAPTION_STYLE']")

path.write_text(text, encoding='utf-8', newline='\n')
