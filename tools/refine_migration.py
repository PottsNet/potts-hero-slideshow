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
    "use Fisharebest\\Webtrees\\Auth;\nuse Fisharebest\\Webtrees\\Http",
    "use Fisharebest\\Webtrees\\Auth;\nuse Fisharebest\\Webtrees\\DB;\nuse Fisharebest\\Webtrees\\Http",
    'DB import',
)
old = '''    private function legacyMigrationTree(): ?Tree
    {
        $trees = $this->treeService()->all();
        $default_tree_name = Site::getPreference('DEFAULT_GEDCOM');

        if ($default_tree_name !== '') {
            $default_tree = $trees->get($default_tree_name);

            if ($default_tree instanceof Tree) {
                return $default_tree;
            }
        }

        $first_tree = $trees->first();

        return $first_tree instanceof Tree ? $first_tree : null;
    }
'''
new = '''    private function legacyMigrationTree(): ?Tree
    {
        $trees = $this->treeService()->all();
        $hero_tree_ids = DB::table('block')
            ->where('module_name', '=', $this->name())
            ->where('gedcom_id', '>', 0)
            ->pluck('gedcom_id')
            ->map(static fn ($tree_id): int => (int) $tree_id)
            ->all();
        $default_tree_name = Site::getPreference('DEFAULT_GEDCOM');

        if ($default_tree_name !== '') {
            $default_tree = $trees->get($default_tree_name);

            if ($default_tree instanceof Tree && ($hero_tree_ids === [] || in_array($default_tree->id(), $hero_tree_ids, true))) {
                return $default_tree;
            }
        }

        foreach ($trees as $tree) {
            if (in_array($tree->id(), $hero_tree_ids, true)) {
                return $tree;
            }
        }

        $first_tree = $trees->first();

        return $first_tree instanceof Tree ? $first_tree : null;
    }
'''
text = replace_once(text, old, new, 'legacy migration tree')
path.write_text(text, encoding='utf-8', newline='\n')
