from pathlib import Path
import json


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one match, found {count}')
    return text.replace(old, new, 1)


php_path = Path('PottsHeroSlideshow.php')
php = php_path.read_text(encoding='utf-8')

php = replace_once(
    php,
    "use Fisharebest\\Webtrees\\Registry;\nuse Fisharebest\\Webtrees\\Tree;",
    "use Fisharebest\\Webtrees\\Registry;\nuse Fisharebest\\Webtrees\\Services\\TreeService;\nuse Fisharebest\\Webtrees\\Site;\nuse Fisharebest\\Webtrees\\Tree;",
    'TreeService/Site imports',
)
php = replace_once(
    php,
    "use function bin2hex;\nuse function dirname;",
    "use function bin2hex;\nuse function copy;\nuse function dirname;",
    'copy import',
)
php = replace_once(
    php,
    "    private const CUSTOM_VERSION = '1.0.1';\n    private const LATEST_VERSION_URL = 'https://raw.githubusercontent.com/PottsNet/potts-hero-slideshow/main/latest-version.txt';",
    "    private const CUSTOM_VERSION = '1.1.0-beta.1';\n    private const LATEST_VERSION_URL = 'https://raw.githubusercontent.com/PottsNet/potts-hero-slideshow/main/latest-version.txt';\n    private const LEGACY_MIGRATION_PREF = 'MULTI_TREE_LEGACY_TREE_ID';\n    private const TREE_CONFIGURED = 'CONFIGURED';",
    'version/constants',
)

start = php.index('    public function getBlock(Tree $tree, int $block_id, string $context, array $config = []): string')
end_marker = '    /** @return array<string,string> */\n    private function fitChoices(): array'
end = php.index(end_marker, start)

new_region = r'''    public function getBlock(Tree $tree, int $block_id, string $context, array $config = []): string
    {
        $this->pushAssets();
        $this->ensureTreeConfiguration($tree);

        $settings = $this->settings($tree);

        if ($settings['ENABLED'] !== '1') {
            return '';
        }

        $slides = array_values(array_filter($this->slides($tree), static fn (array $slide): bool => $slide['enabled'] === '1'));

        $content = view('potts-hero-slideshow::block/hero', [
            'settings' => $settings,
            'slides'   => $slides,
        ]);

        if ($context !== self::CONTEXT_EMBED) {
            return view('modules/block-template', [
                'block'      => Str::kebab($this->name()),
                'id'         => $block_id,
                'config_url' => $this->configUrl($tree, $context, $block_id),
                'title'      => $this->title(),
                'content'    => $content,
            ]);
        }

        return $content;
    }

    public function hasBlockConfig(): bool
    {
        return false;
    }

    public function getAdminAction(ServerRequestInterface $request): ResponseInterface
    {
        $this->assertAdministrator($request);
        $this->layout = Webtrees::LAYOUT_ADMINISTRATION;

        View::registerNamespace('potts-hero-slideshow', $this->resourcesFolder() . 'views/');
        $this->pushAssets();

        $tree = $this->adminTreeFromRequest($request);
        $this->ensureTreeConfiguration($tree);

        return $this->viewResponse('potts-hero-slideshow::admin/settings', [
            'title'          => I18N::translate('Potts Hero Slideshow settings'),
            'action_url'     => route('module', [
                'module' => $this->name(),
                'action' => 'Admin',
            ]),
            'tree_choices'        => $this->treeChoices(),
            'selected_tree_id'    => (string) $tree->id(),
            'selected_tree_title' => $tree->title(),
            'settings'            => $this->settings($tree),
            'slides'              => $this->slides($tree),
            'fit_choices'         => $this->fitChoices(),
            'frame_choices'       => $this->frameChoices(),
            'colour_choices'      => $this->colourChoices(),
            'palette_choices'     => $this->paletteChoices(),
            'transition_choices'  => $this->transitionChoices(),
            'caption_choices'     => $this->captionChoices(),
            'start_choices'       => $this->startChoices(),
            'focal_choices'       => $this->focalChoices(),
            'saved'          => Validator::queryParams($request)->boolean('saved', false),
            'uploaded'       => Validator::queryParams($request)->boolean('uploaded', false),
            'deleted'        => Validator::queryParams($request)->boolean('deleted', false),
            'error'          => Validator::queryParams($request)->string('error', ''),
            'version'        => $this->customModuleVersion(),
        ]);
    }

    public function postAdminAction(ServerRequestInterface $request): ResponseInterface
    {
        $this->assertAdministrator($request);

        $parsed = $request->getParsedBody();
        $data   = is_array($parsed) ? $parsed : [];
        $task   = isset($data['task']) && is_string($data['task']) ? $data['task'] : 'save';
        $tree_id = isset($data['tree_id']) ? (int) $data['tree_id'] : 0;
        $tree = $this->treeById($tree_id);

        if (!$tree instanceof Tree) {
            throw new HttpNotFoundException();
        }

        $this->ensureTreeConfiguration($tree);

        if (isset($data['delete_slide']) && is_string($data['delete_slide']) && $data['delete_slide'] !== '') {
            $this->deleteSlide($tree, $data['delete_slide']);

            return redirect(route('module', [
                'module'   => $this->name(),
                'action'   => 'Admin',
                'tree_id'  => (string) $tree->id(),
                'deleted'  => '1',
            ]));
        }

        if ($task === 'reset') {
            foreach (self::DEFAULTS as $key => $value) {
                $this->setTreePreference($tree, $key, $value);
            }
            $this->markTreeConfigured($tree);

            return redirect(route('module', [
                'module'  => $this->name(),
                'action'  => 'Admin',
                'tree_id' => (string) $tree->id(),
                'saved'   => '1',
            ]));
        }

        $this->saveSettings($tree, $data);
        $this->saveSlides($tree, $data);

        $uploaded = $this->handleUploads($tree, $request);

        return redirect(route('module', [
            'module'   => $this->name(),
            'action'   => 'Admin',
            'tree_id'  => (string) $tree->id(),
            $uploaded ? 'uploaded' : 'saved' => '1',
        ]));
    }

    public function getImageAction(ServerRequestInterface $request): ResponseInterface
    {
        $tree_id = Validator::queryParams($request)->integer('tree_id', 0);
        $tree = $this->treeById($tree_id);

        if (!$tree instanceof Tree) {
            throw new HttpNotFoundException();
        }

        $this->ensureTreeConfiguration($tree);

        $file = Validator::queryParams($request)->string('file', '');
        $file = basename($file);
        $path = $this->imageDirectory($tree) . $file;

        if ($file === '' || !is_file($path) || !is_readable($path)) {
            throw new HttpNotFoundException();
        }

        $extension = strtolower((string) pathinfo($file, PATHINFO_EXTENSION));
        $mime      = self::IMAGE_MIME_TYPES[$extension] ?? (mime_content_type($path) ?: 'application/octet-stream');
        $content   = file_get_contents($path);

        if ($content === false) {
            throw new HttpNotFoundException();
        }

        return Registry::responseFactory()->response($content, StatusCodeInterface::STATUS_OK, [
            'content-type'   => $mime,
            'content-length' => (string) filesize($path),
            'cache-control'  => 'public, max-age=86400',
        ]);
    }

    private function assertAdministrator(ServerRequestInterface $request): void
    {
        $user = Validator::attributes($request)->user();

        if (!Auth::isAdmin($user)) {
            throw new HttpAccessDeniedException();
        }
    }

    private function treeService(): TreeService
    {
        return Registry::container()->get(TreeService::class);
    }

    private function treeById(int $tree_id): ?Tree
    {
        if ($tree_id <= 0) {
            return null;
        }

        $tree = $this->treeService()->all()->first(static fn (Tree $tree): bool => $tree->id() === $tree_id);

        return $tree instanceof Tree ? $tree : null;
    }

    private function adminTreeFromRequest(ServerRequestInterface $request): Tree
    {
        $tree_id = Validator::queryParams($request)->integer('tree_id', 0);
        $tree = $this->treeById($tree_id);

        if ($tree instanceof Tree) {
            return $tree;
        }

        $tree = $this->legacyMigrationTree();

        if ($tree instanceof Tree) {
            return $tree;
        }

        throw new HttpNotFoundException();
    }

    /** @return array<string,string> */
    private function treeChoices(): array
    {
        $choices = [];

        foreach ($this->treeService()->all() as $tree) {
            $choices[(string) $tree->id()] = $tree->title();
        }

        return $choices;
    }

    private function legacyMigrationTree(): ?Tree
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

    private function treePreferenceKey(Tree $tree, string $key): string
    {
        return 'TREE_' . $tree->id() . '_' . $key;
    }

    private function treePreference(Tree $tree, string $key, string $default): string
    {
        return $this->getPreference($this->treePreferenceKey($tree, $key), $default);
    }

    private function setTreePreference(Tree $tree, string $key, string $value): void
    {
        $this->setPreference($this->treePreferenceKey($tree, $key), $value);
    }

    private function hasTreeConfiguration(Tree $tree): bool
    {
        return $this->treePreference($tree, self::TREE_CONFIGURED, '0') === '1';
    }

    private function markTreeConfigured(Tree $tree): void
    {
        $this->setTreePreference($tree, self::TREE_CONFIGURED, '1');
    }

    private function ensureTreeConfiguration(Tree $tree): void
    {
        if ($this->hasTreeConfiguration($tree)) {
            return;
        }

        if ((int) $this->getPreference(self::LEGACY_MIGRATION_PREF, '0') > 0) {
            return;
        }

        $migration_tree = $this->legacyMigrationTree();

        if (!$migration_tree instanceof Tree || $migration_tree->id() !== $tree->id()) {
            return;
        }

        foreach (self::DEFAULTS as $key => $default) {
            $this->setTreePreference($tree, $key, $this->getPreference($key, $default));
        }

        $this->copyLegacyImagesToTree($tree);
        $this->markTreeConfigured($tree);
        $this->setPreference(self::LEGACY_MIGRATION_PREF, (string) $tree->id());
    }

    /** @return array<string,string> */
    private function settings(Tree $tree): array
    {
        $settings = [];

        foreach (self::DEFAULTS as $key => $default) {
            if ($key === 'SLIDES_JSON') {
                continue;
            }

            $settings[$key] = $this->treePreference($tree, $key, $default);
        }

        foreach (['ENABLED', 'SHOW_BUTTON_1', 'SHOW_BUTTON_2', 'DOTS', 'RANDOM_START'] as $key) {
            $settings[$key] = $settings[$key] === '1' ? '1' : '0';
        }

        $interval = (int) $settings['INTERVAL'];
        $settings['INTERVAL'] = (string) max(3500, $interval);

        $transition_speed = (int) ($settings['TRANSITION_SPEED'] ?? self::DEFAULTS['TRANSITION_SPEED']);
        $settings['TRANSITION_SPEED'] = (string) min(5000, max(300, $transition_speed));

        $caption_offset = (int) ($settings['CAPTION_OFFSET'] ?? self::DEFAULTS['CAPTION_OFFSET']);
        $settings['CAPTION_OFFSET'] = (string) min(120, max(0, $caption_offset));

        if (!array_key_exists($settings['IMAGE_FIT'], $this->fitChoices())) {
            $settings['IMAGE_FIT'] = self::DEFAULTS['IMAGE_FIT'];
        }

        if (!array_key_exists($settings['FRAME_STYLE'], $this->frameChoices())) {
            $settings['FRAME_STYLE'] = self::DEFAULTS['FRAME_STYLE'];
        }

        if (!array_key_exists($settings['COLOUR_MODE'], $this->colourChoices())) {
            $settings['COLOUR_MODE'] = self::DEFAULTS['COLOUR_MODE'];
        }

        if (!array_key_exists($settings['PALETTE'], $this->paletteChoices())) {
            $settings['PALETTE'] = self::DEFAULTS['PALETTE'];
        }

        if (!array_key_exists($settings['TRANSITION'], $this->transitionChoices())) {
            $settings['TRANSITION'] = self::DEFAULTS['TRANSITION'];
        }

        if (!array_key_exists($settings['CAPTION_STYLE'], $this->captionChoices())) {
            $settings['CAPTION_STYLE'] = self::DEFAULTS['CAPTION_STYLE'];
        }

        return $settings;
    }

    /** @param array<string,mixed> $data */
    private function saveSettings(Tree $tree, array $data): void
    {
        foreach (['ENABLED', 'SHOW_BUTTON_1', 'SHOW_BUTTON_2', 'DOTS', 'RANDOM_START'] as $key) {
            $field = strtolower($key);
            $this->setTreePreference($tree, $key, isset($data[$field]) && (string) $data[$field] === '1' ? '1' : '0');
        }

        foreach (['KICKER', 'TITLE', 'SUBTITLE', 'BUTTON_1_TEXT', 'BUTTON_1_URL', 'BUTTON_2_TEXT', 'BUTTON_2_URL'] as $key) {
            $field = strtolower($key);
            $value = isset($data[$field]) && is_string($data[$field]) ? trim($data[$field]) : self::DEFAULTS[$key];
            $this->setTreePreference($tree, $key, $value);
        }

        $interval = isset($data['interval']) ? (int) $data['interval'] : (int) self::DEFAULTS['INTERVAL'];
        $this->setTreePreference($tree, 'INTERVAL', (string) max(3500, $interval));

        $transition_speed = isset($data['transition_speed']) ? (int) $data['transition_speed'] : (int) self::DEFAULTS['TRANSITION_SPEED'];
        $this->setTreePreference($tree, 'TRANSITION_SPEED', (string) min(5000, max(300, $transition_speed)));

        $caption_offset = isset($data['caption_offset']) ? (int) $data['caption_offset'] : (int) self::DEFAULTS['CAPTION_OFFSET'];
        $this->setTreePreference($tree, 'CAPTION_OFFSET', (string) min(120, max(0, $caption_offset)));

        $fit = isset($data['image_fit']) && is_string($data['image_fit']) ? $data['image_fit'] : self::DEFAULTS['IMAGE_FIT'];
        $this->setTreePreference($tree, 'IMAGE_FIT', array_key_exists($fit, $this->fitChoices()) ? $fit : self::DEFAULTS['IMAGE_FIT']);

        $frame = isset($data['frame_style']) && is_string($data['frame_style']) ? $data['frame_style'] : self::DEFAULTS['FRAME_STYLE'];
        $this->setTreePreference($tree, 'FRAME_STYLE', array_key_exists($frame, $this->frameChoices()) ? $frame : self::DEFAULTS['FRAME_STYLE']);

        $colour = isset($data['colour_mode']) && is_string($data['colour_mode']) ? $data['colour_mode'] : self::DEFAULTS['COLOUR_MODE'];
        $this->setTreePreference($tree, 'COLOUR_MODE', array_key_exists($colour, $this->colourChoices()) ? $colour : self::DEFAULTS['COLOUR_MODE']);

        $palette = isset($data['palette']) && is_string($data['palette']) ? $data['palette'] : self::DEFAULTS['PALETTE'];
        $this->setTreePreference($tree, 'PALETTE', array_key_exists($palette, $this->paletteChoices()) ? $palette : self::DEFAULTS['PALETTE']);

        $transition = isset($data['transition']) && is_string($data['transition']) ? $data['transition'] : self::DEFAULTS['TRANSITION'];
        $this->setTreePreference($tree, 'TRANSITION', array_key_exists($transition, $this->transitionChoices()) ? $transition : self::DEFAULTS['TRANSITION']);

        $caption_style = isset($data['caption_style']) && is_string($data['caption_style']) ? $data['caption_style'] : self::DEFAULTS['CAPTION_STYLE'];
        $this->setTreePreference($tree, 'CAPTION_STYLE', array_key_exists($caption_style, $this->captionChoices()) ? $caption_style : self::DEFAULTS['CAPTION_STYLE']);
        $this->markTreeConfigured($tree);
    }

    /** @return array<int,array<string,string>> */
    private function slides(Tree $tree): array
    {
        $saved = json_decode($this->treePreference($tree, 'SLIDES_JSON', self::DEFAULTS['SLIDES_JSON']), true);
        $saved = is_array($saved) ? $saved : [];
        $known = [];

        foreach ($saved as $slide) {
            if (!is_array($slide) || !isset($slide['file']) || !is_string($slide['file'])) {
                continue;
            }

            $file = basename($slide['file']);

            if (!$this->isAllowedImageFilename($file)) {
                continue;
            }

            $known[$file] = [
                'file'       => $file,
                'caption'    => isset($slide['caption']) && is_string($slide['caption']) ? $slide['caption'] : '',
                'alt'        => isset($slide['alt']) && is_string($slide['alt']) ? $slide['alt'] : '',
                'enabled'    => isset($slide['enabled']) && (string) $slide['enabled'] === '1' ? '1' : '0',
                'sort'       => isset($slide['sort']) ? (string) (int) $slide['sort'] : '0',
                'focal'      => isset($slide['focal']) && is_string($slide['focal']) && array_key_exists($slide['focal'], $this->focalChoices()) ? $slide['focal'] : 'center',
                'image_url'  => $this->imageUrl($tree, $file),
            ];
        }

        foreach ($this->imageFiles($tree) as $file) {
            if (!isset($known[$file])) {
                $known[$file] = [
                    'file'       => $file,
                    'caption'    => '',
                    'alt'        => '',
                    'enabled'    => '1',
                    'sort'       => (string) (count($known) + 1),
                    'focal'      => 'center',
                    'image_url'  => $this->imageUrl($tree, $file),
                ];
            }
        }

        $slides = array_values(array_filter($known, fn (array $slide): bool => is_file($this->imageDirectory($tree) . $slide['file'])));

        usort($slides, static function (array $a, array $b): int {
            $sort_a = (int) ($a['sort'] ?? 0);
            $sort_b = (int) ($b['sort'] ?? 0);

            return $sort_a <=> $sort_b ?: strcmp((string) $a['file'], (string) $b['file']);
        });

        return $slides;
    }

    /** @param array<string,mixed> $data */
    private function saveSlides(Tree $tree, array $data): void
    {
        $slides_input = isset($data['slides']) && is_array($data['slides']) ? $data['slides'] : [];
        $slides = [];

        foreach ($this->slides($tree) as $slide) {
            $file = $slide['file'];
            $input = isset($slides_input[$file]) && is_array($slides_input[$file]) ? $slides_input[$file] : [];

            $caption = isset($input['caption']) && is_string($input['caption']) ? trim($input['caption']) : $slide['caption'];
            $alt     = isset($input['alt']) && is_string($input['alt']) ? trim($input['alt']) : $slide['alt'];
            $sort    = isset($input['sort']) ? (string) (int) $input['sort'] : $slide['sort'];
            $enabled = isset($input['enabled']) && (string) $input['enabled'] === '1' ? '1' : '0';
            $focal   = isset($input['focal']) && is_string($input['focal']) && array_key_exists($input['focal'], $this->focalChoices()) ? $input['focal'] : 'center';

            $slides[] = [
                'file'    => $file,
                'caption' => $caption,
                'alt'     => $alt,
                'enabled' => $enabled,
                'sort'    => $sort,
                'focal'   => $focal,
            ];
        }

        $this->setTreePreference($tree, 'SLIDES_JSON', (string) json_encode($slides, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT));
        $this->markTreeConfigured($tree);
    }

    private function handleUploads(Tree $tree, ServerRequestInterface $request): bool
    {
        $uploaded_files = $request->getUploadedFiles();
        $files = $uploaded_files['hero_images'] ?? [];

        if ($files instanceof UploadedFileInterface) {
            $files = [$files];
        }

        if (!is_array($files)) {
            return false;
        }

        $uploaded = false;
        $slides = $this->slides($tree);
        $next_sort = count($slides) + 1;

        foreach ($files as $file) {
            if (!$file instanceof UploadedFileInterface || $file->getError() !== UPLOAD_ERR_OK) {
                continue;
            }

            $client_filename = $file->getClientFilename() ?? 'hero-image';
            $extension = strtolower((string) pathinfo($client_filename, PATHINFO_EXTENSION));

            if (!array_key_exists($extension, self::IMAGE_MIME_TYPES)) {
                continue;
            }

            $base = strtolower((string) pathinfo($client_filename, PATHINFO_FILENAME));
            $base = (string) preg_replace('/[^a-z0-9]+/', '-', $base);
            $base = trim($base, '-') ?: 'hero-image';
            $filename = $base . '-' . bin2hex(random_bytes(4)) . '.' . $extension;
            $destination = $this->imageDirectory($tree) . $filename;

            $this->ensureImageDirectory($tree);
            $file->moveTo($destination);

            $detected_mime = mime_content_type($destination) ?: '';

            if ($detected_mime !== '' && $detected_mime !== 'application/octet-stream' && !in_array($detected_mime, array_values(self::IMAGE_MIME_TYPES), true)) {
                @unlink($destination);
                continue;
            }

            $slides[] = [
                'file'    => $filename,
                'caption' => '',
                'alt'     => '',
                'enabled' => '1',
                'sort'    => (string) $next_sort,
                'focal'   => 'center',
            ];
            $next_sort++;
            $uploaded = true;
        }

        if ($uploaded) {
            $this->setTreePreference($tree, 'SLIDES_JSON', (string) json_encode($slides, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT));
            $this->markTreeConfigured($tree);
        }

        return $uploaded;
    }

    private function deleteSlide(Tree $tree, string $file): void
    {
        $file = basename($file);
        $path = $this->imageDirectory($tree) . $file;

        if ($this->isAllowedImageFilename($file) && is_file($path)) {
            @unlink($path);
        }

        $slides = array_values(array_filter($this->slides($tree), static fn (array $slide): bool => $slide['file'] !== $file));
        $this->setTreePreference($tree, 'SLIDES_JSON', (string) json_encode($slides, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT));
        $this->markTreeConfigured($tree);
    }

    /** @return array<int,string> */
    private function imageFiles(Tree $tree): array
    {
        $this->ensureImageDirectory($tree);

        return $this->imageFilesInDirectory($this->imageDirectory($tree));
    }

    /** @return array<int,string> */
    private function legacyImageFiles(): array
    {
        return $this->imageFilesInDirectory($this->legacyImageDirectory());
    }

    /** @return array<int,string> */
    private function imageFilesInDirectory(string $directory): array
    {
        if (!is_dir($directory)) {
            return [];
        }

        $files = scandir($directory);

        if ($files === false) {
            return [];
        }

        $image_files = [];

        foreach ($files as $file) {
            if ($this->isAllowedImageFilename($file) && is_file($directory . $file)) {
                $image_files[] = $file;
            }
        }

        return $image_files;
    }

    private function isAllowedImageFilename(string $file): bool
    {
        $extension = strtolower((string) pathinfo($file, PATHINFO_EXTENSION));

        return $file === basename($file) && array_key_exists($extension, self::IMAGE_MIME_TYPES);
    }

    private function legacyImageDirectory(): string
    {
        return Webtrees::DATA_DIR . 'potts-hero-slideshow/';
    }

    private function imageDirectory(Tree $tree): string
    {
        return $this->legacyImageDirectory() . 'tree-' . $tree->id() . '/';
    }

    private function ensureImageDirectory(Tree $tree): void
    {
        $this->ensureDirectory($this->legacyImageDirectory());
        $this->ensureDirectory($this->imageDirectory($tree));
    }

    private function ensureDirectory(string $directory): void
    {
        if (!is_dir($directory)) {
            mkdir($directory, 0775, true);
        }

        $htaccess = $directory . '.htaccess';

        if (!is_file($htaccess)) {
            @file_put_contents($htaccess, "Require all denied\nDeny from all\n");
        }
    }

    private function copyLegacyImagesToTree(Tree $tree): void
    {
        $this->ensureImageDirectory($tree);
        $source_directory = $this->legacyImageDirectory();
        $destination_directory = $this->imageDirectory($tree);

        foreach ($this->legacyImageFiles() as $file) {
            $source = $source_directory . $file;
            $destination = $destination_directory . $file;

            if (!is_file($destination)) {
                @copy($source, $destination);
            }
        }
    }

    private function imageUrl(Tree $tree, string $file): string
    {
        return route('module', [
            'module'  => $this->name(),
            'action'  => 'Image',
            'tree_id' => (string) $tree->id(),
            'file'    => basename($file),
        ]);
    }

'''
php = php[:start] + new_region + php[end:]
php_path.write_text(php, encoding='utf-8', newline='\n')

view_path = Path('resources/views/admin/settings.phtml')
view = view_path.read_text(encoding='utf-8')
view = replace_once(
    view,
    " * @var string $action_url\n * @var array<string,string> $settings",
    " * @var string $action_url\n * @var array<string,string> $tree_choices\n * @var string $selected_tree_id\n * @var string $selected_tree_title\n * @var array<string,string> $settings",
    'admin view variables',
)
view = replace_once(
    view,
    "    <div class=\"potts-hero-intro\">",
    "    <form method=\"get\" action=\"<?= e($action_url) ?>\" class=\"card card-body mb-3\">\n        <div class=\"row g-2 align-items-end\">\n            <div class=\"col-md-8\">\n                <label class=\"form-label\" for=\"potts-hero-tree\"><?= e($t('Family tree')) ?></label>\n                <select class=\"form-select\" id=\"potts-hero-tree\" name=\"tree_id\" onchange=\"this.form.submit()\">\n                    <?php foreach ($tree_choices as $tree_id => $tree_title) : ?>\n                        <option value=\"<?= e($tree_id) ?>\" <?= $selected_tree_id === $tree_id ? 'selected' : '' ?>><?= e($tree_title) ?></option>\n                    <?php endforeach ?>\n                </select>\n            </div>\n            <noscript class=\"col-md-auto\">\n                <button class=\"btn btn-secondary\" type=\"submit\"><?= e($t('Go')) ?></button>\n            </noscript>\n        </div>\n    </form>\n\n    <div class=\"potts-hero-intro\">",
    'tree selector',
)
view = replace_once(
    view,
    "            <p><?= e($t('Manage the full-width homepage hero banner, rotating images, captions, buttons and display timing.')) ?></p>",
    "            <p><?= e($t('Manage the full-width homepage hero banner, rotating images, captions, buttons and display timing.')) ?><br><strong><?= e($selected_tree_title) ?></strong></p>",
    'selected tree title',
)
view = replace_once(
    view,
    "        <?= csrf_field() ?>\n\n        <section",
    "        <?= csrf_field() ?>\n        <input type=\"hidden\" name=\"tree_id\" value=\"<?= e($selected_tree_id) ?>\">\n\n        <section",
    'hidden tree id',
)
view_path.write_text(view, encoding='utf-8', newline='\n')

metadata_path = Path('metadata.json')
metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
metadata['version'] = '1.1.0-beta.1'
metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')

changelog_path = Path('CHANGELOG.md')
changelog = changelog_path.read_text(encoding='utf-8')
changelog = replace_once(
    changelog,
    '# Changelog\n\n',
    '# Changelog\n\n## 1.1.0-beta.1\n\n- Added independent hero settings, slide metadata and uploaded-image storage for each webtrees family tree.\n- Added a family-tree selector to the module administration page.\n- Existing global hero settings and images migrate once to the site default tree (or first tree when no default is set), while the legacy data is retained as a rollback source.\n- Image delivery now validates the requested tree against the current user\'s accessible trees and serves only that tree\'s image directory.\n- Public update feed remains on stable 1.0.1 while this multi-tree feature is tested.\n\n',
    'changelog entry',
)
changelog_path.write_text(changelog, encoding='utf-8', newline='\n')

readme_path = Path('README.md')
readme = readme_path.read_text(encoding='utf-8')
if '## Multi-tree configuration' not in readme:
    readme += "\n\n## Multi-tree configuration\n\nFrom 1.1.0, each webtrees family tree has independent hero text, display settings, slide metadata and uploaded images. The administration page includes a family-tree selector. Existing pre-1.1 global configuration is copied once to the site default tree (or the first tree if no default is configured); the original global preferences and image files are retained for rollback. Tree images are stored under `data/potts-hero-slideshow/tree-<tree-id>/`.\n"
readme_path.write_text(readme, encoding='utf-8', newline='\n')

pot_path = Path('resources/lang/messages.pot')
pot = pot_path.read_text(encoding='utf-8')
if 'msgid "Family tree"' not in pot:
    pot += '\nmsgid "Family tree"\nmsgstr ""\n'
pot_path.write_text(pot, encoding='utf-8', newline='\n')

po_path = Path('resources/lang/nl.po')
po = po_path.read_text(encoding='utf-8')
if 'msgid "Family tree"' not in po:
    po += '\nmsgid "Family tree"\nmsgstr "Stamboom"\n'
po_path.write_text(po, encoding='utf-8', newline='\n')
