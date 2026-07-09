<?php

/**
 * Potts Hero Slideshow for webtrees 2.2.
 *
 * A full-width homepage hero block with administrator-managed images.
 */

declare(strict_types=1);

namespace PottsHeroSlideshow;

use Fig\Http\Message\StatusCodeInterface;
use Fisharebest\Localization\Translation;
use Fisharebest\Webtrees\Auth;
use Fisharebest\Webtrees\Http\Exceptions\HttpAccessDeniedException;
use Fisharebest\Webtrees\Http\Exceptions\HttpNotFoundException;
use Fisharebest\Webtrees\I18N;
use Fisharebest\Webtrees\Module\AbstractModule;
use Fisharebest\Webtrees\Module\ModuleBlockInterface;
use Fisharebest\Webtrees\Module\ModuleBlockTrait;
use Fisharebest\Webtrees\Module\ModuleConfigInterface;
use Fisharebest\Webtrees\Module\ModuleConfigTrait;
use Fisharebest\Webtrees\Module\ModuleCustomInterface;
use Fisharebest\Webtrees\Module\ModuleCustomTrait;
use Fisharebest\Webtrees\Registry;
use Fisharebest\Webtrees\Tree;
use Fisharebest\Webtrees\Validator;
use Fisharebest\Webtrees\View;
use Fisharebest\Webtrees\Webtrees;
use Illuminate\Support\Str;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Message\UploadedFileInterface;

use function array_key_exists;
use function array_values;
use function basename;
use function bin2hex;
use function dirname;
use function file_exists;
use function file_get_contents;
use function filesize;
use function implode;
use function in_array;
use function is_array;
use function is_dir;
use function is_file;
use function is_readable;
use function is_string;
use function json_decode;
use function json_encode;
use function ksort;
use function max;
use function mime_content_type;
use function mkdir;
use function pathinfo;
use function preg_replace;
use function random_bytes;
use function redirect;
use function route;
use function scandir;
use function strtolower;
use function trim;
use function unlink;
use function usort;
use function view;

use const JSON_HEX_AMP;
use const JSON_HEX_APOS;
use const JSON_HEX_QUOT;
use const JSON_HEX_TAG;
use const JSON_UNESCAPED_SLASHES;
use const JSON_UNESCAPED_UNICODE;

final class PottsHeroSlideshow extends AbstractModule implements ModuleCustomInterface, ModuleConfigInterface, ModuleBlockInterface
{
    use ModuleCustomTrait;
    use ModuleConfigTrait;
    use ModuleBlockTrait;

    private const CUSTOM_VERSION = '1.0.0';
    private const LATEST_VERSION_URL = 'https://raw.githubusercontent.com/PottsNet/potts-hero-slideshow/main/latest-version.txt';

    /** @var array<string,string> */
    private const DEFAULTS = [
        'ENABLED'        => '1',
        'KICKER'         => 'Family history since 1994',
        'TITLE'          => 'Welcome to OurFamily',
        'SUBTITLE'       => 'A living archive of our family’s people, places, records and stories — shared online for more than thirty years.',
        'BUTTON_1_TEXT'  => 'Explore the tree',
        'BUTTON_1_URL'   => '/tree/OurFamily',
        'BUTTON_2_TEXT'  => 'Read family books',
        'BUTTON_2_URL'   => '/tree/OurFamily/books',
        'SHOW_BUTTON_1'  => '1',
        'SHOW_BUTTON_2'  => '1',
        'INTERVAL'       => '7000',
        'TRANSITION_SPEED' => '1150',
        'DOTS'           => '1',
        'RANDOM_START'   => '0',
        'IMAGE_FIT'      => 'contain',
        'FRAME_STYLE'    => 'vintage',
        'COLOUR_MODE'    => 'soft',
        'PALETTE'        => 'auto',
        'TRANSITION'     => 'zoom',
        'CAPTION_STYLE'  => 'below',
        'CAPTION_OFFSET' => '20',
        'SLIDES_JSON'    => '[]',
    ];

    /** @var array<string,string> */
    private const IMAGE_MIME_TYPES = [
        'jpg'  => 'image/jpeg',
        'jpeg' => 'image/jpeg',
        'png'  => 'image/png',
        'webp' => 'image/webp',
        'gif'  => 'image/gif',
    ];

    public function title(): string
    {
        return I18N::translate('Potts Hero Slideshow');
    }

    public function description(): string
    {
        return I18N::translate('A standalone, theme-aware homepage hero banner with a family photo slideshow.');
    }

    public function isEnabledByDefault(): bool
    {
        return false;
    }

    public function customModuleVersion(): string
    {
        return self::CUSTOM_VERSION;
    }

    public function customModuleLatestVersion(): string
    {
        return self::CUSTOM_VERSION;
    }

    public function customModuleLatestVersionUrl(): string
    {
        return self::LATEST_VERSION_URL;
    }

    public function customModuleAuthorName(): string
    {
        return 'Jason Potts';
    }

    public function customModuleSupportUrl(): string
    {
        return 'https://github.com/PottsNet/potts-hero-slideshow/issues';
    }

    /** @return array<string,string> */
    public function customTranslations(string $language): array
    {
        $file = $this->resourcesFolder() . 'lang/' . $language . '.mo';

        return file_exists($file) ? (new Translation($file))->asArray() : [];
    }

    public function resourcesFolder(): string
    {
        return __DIR__ . '/resources/';
    }

    public function boot(): void
    {
        // Register views during module boot only. Do not call assetUrl() here.
        // In webtrees 2.2 the request object is not available during module boot,
        // and assetUrl() can trigger route generation too early.
        View::registerNamespace('potts-hero-slideshow', $this->resourcesFolder() . 'views/');
    }


    private function pushAssets(): void
    {
        $css = $this->resourcesFolder() . 'css/hero.css';
        $js  = $this->resourcesFolder() . 'js/hero.js';

        if (is_file($css) && is_readable($css)) {
            View::pushunique('styles');
            echo '<style id="potts-hero-slideshow-css">' . file_get_contents($css) . '</style>';
            View::endpushunique();
        }

        if (is_file($js) && is_readable($js)) {
            View::pushunique('javascript');
            echo '<script id="potts-hero-slideshow-js">' . file_get_contents($js) . '</script>';
            View::endpushunique();
        }
    }

    public function defaultBlockTitle(): string
    {
        return $this->title();
    }

    public function defaultBlockOrder(): int
    {
        return 5;
    }

    public function isUserBlock(): bool
    {
        return false;
    }

    public function isTreeBlock(): bool
    {
        return true;
    }

    public function loadAjax(): bool
    {
        return false;
    }

    /**
     * @param array<string,string> $config
     */
    public function getBlock(Tree $tree, int $block_id, string $context, array $config = []): string
    {
        $this->pushAssets();

        $settings = $this->settings();

        if ($settings['ENABLED'] !== '1') {
            return '';
        }

        $slides = array_values(array_filter($this->slides(), static fn (array $slide): bool => $slide['enabled'] === '1'));

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

        return $this->viewResponse('potts-hero-slideshow::admin/settings', [
            'title'          => I18N::translate('Potts Hero Slideshow settings'),
            'action_url'     => route('module', [
                'module' => $this->name(),
                'action' => 'Admin',
            ]),
            'settings'           => $this->settings(),
            'slides'             => $this->slides(),
            'fit_choices'        => $this->fitChoices(),
            'frame_choices'      => $this->frameChoices(),
            'colour_choices'     => $this->colourChoices(),
            'palette_choices'    => $this->paletteChoices(),
            'transition_choices' => $this->transitionChoices(),
            'caption_choices'    => $this->captionChoices(),
            'start_choices'      => $this->startChoices(),
            'focal_choices'      => $this->focalChoices(),
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

        if (isset($data['delete_slide']) && is_string($data['delete_slide']) && $data['delete_slide'] !== '') {
            $this->deleteSlide($data['delete_slide']);

            return redirect(route('module', [
                'module'  => $this->name(),
                'action'  => 'Admin',
                'deleted' => '1',
            ]));
        }

        if ($task === 'reset') {
            foreach (self::DEFAULTS as $key => $value) {
                $this->setPreference($key, $value);
            }

            return redirect(route('module', [
                'module' => $this->name(),
                'action' => 'Admin',
                'saved'  => '1',
            ]));
        }

        $this->saveSettings($data);
        $this->saveSlides($data);

        $uploaded = $this->handleUploads($request);

        return redirect(route('module', [
            'module'   => $this->name(),
            'action'   => 'Admin',
            $uploaded ? 'uploaded' : 'saved' => '1',
        ]));
    }

    public function getImageAction(ServerRequestInterface $request): ResponseInterface
    {
        $file = Validator::queryParams($request)->string('file', '');
        $file = basename($file);
        $path = $this->imageDirectory() . $file;

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

    /** @return array<string,string> */
    private function settings(): array
    {
        $settings = [];

        foreach (self::DEFAULTS as $key => $default) {
            if ($key === 'SLIDES_JSON') {
                continue;
            }

            $settings[$key] = $this->getPreference($key, $default);
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
    private function saveSettings(array $data): void
    {
        foreach (['ENABLED', 'SHOW_BUTTON_1', 'SHOW_BUTTON_2', 'DOTS', 'RANDOM_START'] as $key) {
            $field = strtolower($key);
            $this->setPreference($key, isset($data[$field]) && (string) $data[$field] === '1' ? '1' : '0');
        }

        foreach (['KICKER', 'TITLE', 'SUBTITLE', 'BUTTON_1_TEXT', 'BUTTON_1_URL', 'BUTTON_2_TEXT', 'BUTTON_2_URL'] as $key) {
            $field = strtolower($key);
            $value = isset($data[$field]) && is_string($data[$field]) ? trim($data[$field]) : self::DEFAULTS[$key];
            $this->setPreference($key, $value);
        }

        $interval = isset($data['interval']) ? (int) $data['interval'] : (int) self::DEFAULTS['INTERVAL'];
        $this->setPreference('INTERVAL', (string) max(3500, $interval));

        $transition_speed = isset($data['transition_speed']) ? (int) $data['transition_speed'] : (int) self::DEFAULTS['TRANSITION_SPEED'];
        $this->setPreference('TRANSITION_SPEED', (string) min(5000, max(300, $transition_speed)));

        $caption_offset = isset($data['caption_offset']) ? (int) $data['caption_offset'] : (int) self::DEFAULTS['CAPTION_OFFSET'];
        $this->setPreference('CAPTION_OFFSET', (string) min(120, max(0, $caption_offset)));

        $fit = isset($data['image_fit']) && is_string($data['image_fit']) ? $data['image_fit'] : self::DEFAULTS['IMAGE_FIT'];
        $this->setPreference('IMAGE_FIT', array_key_exists($fit, $this->fitChoices()) ? $fit : self::DEFAULTS['IMAGE_FIT']);

        $frame = isset($data['frame_style']) && is_string($data['frame_style']) ? $data['frame_style'] : self::DEFAULTS['FRAME_STYLE'];
        $this->setPreference('FRAME_STYLE', array_key_exists($frame, $this->frameChoices()) ? $frame : self::DEFAULTS['FRAME_STYLE']);

        $colour = isset($data['colour_mode']) && is_string($data['colour_mode']) ? $data['colour_mode'] : self::DEFAULTS['COLOUR_MODE'];
        $this->setPreference('COLOUR_MODE', array_key_exists($colour, $this->colourChoices()) ? $colour : self::DEFAULTS['COLOUR_MODE']);

        $palette = isset($data['palette']) && is_string($data['palette']) ? $data['palette'] : self::DEFAULTS['PALETTE'];
        $this->setPreference('PALETTE', array_key_exists($palette, $this->paletteChoices()) ? $palette : self::DEFAULTS['PALETTE']);

        $transition = isset($data['transition']) && is_string($data['transition']) ? $data['transition'] : self::DEFAULTS['TRANSITION'];
        $this->setPreference('TRANSITION', array_key_exists($transition, $this->transitionChoices()) ? $transition : self::DEFAULTS['TRANSITION']);

        $caption_style = isset($data['caption_style']) && is_string($data['caption_style']) ? $data['caption_style'] : self::DEFAULTS['CAPTION_STYLE'];
        $this->setPreference('CAPTION_STYLE', array_key_exists($caption_style, $this->captionChoices()) ? $caption_style : self::DEFAULTS['CAPTION_STYLE']);
    }

    /** @return array<int,array<string,string>> */
    private function slides(): array
    {
        $saved = json_decode($this->getPreference('SLIDES_JSON', self::DEFAULTS['SLIDES_JSON']), true);
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
                'image_url'  => $this->imageUrl($file),
            ];
        }

        foreach ($this->imageFiles() as $file) {
            if (!isset($known[$file])) {
                $known[$file] = [
                    'file'       => $file,
                    'caption'    => '',
                    'alt'        => '',
                    'enabled'    => '1',
                    'sort'       => (string) (count($known) + 1),
                    'focal'      => 'center',
                    'image_url'  => $this->imageUrl($file),
                ];
            }
        }

        $slides = array_values(array_filter($known, fn (array $slide): bool => is_file($this->imageDirectory() . $slide['file'])));

        usort($slides, static function (array $a, array $b): int {
            $sort_a = (int) ($a['sort'] ?? 0);
            $sort_b = (int) ($b['sort'] ?? 0);

            return $sort_a <=> $sort_b ?: strcmp((string) $a['file'], (string) $b['file']);
        });

        return $slides;
    }

    /** @param array<string,mixed> $data */
    private function saveSlides(array $data): void
    {
        $slides_input = isset($data['slides']) && is_array($data['slides']) ? $data['slides'] : [];
        $slides = [];

        foreach ($this->slides() as $slide) {
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

        $this->setPreference('SLIDES_JSON', (string) json_encode($slides, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT));
    }

    private function handleUploads(ServerRequestInterface $request): bool
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
        $slides = $this->slides();
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
            $destination = $this->imageDirectory() . $filename;

            $this->ensureImageDirectory();
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
            $this->setPreference('SLIDES_JSON', (string) json_encode($slides, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT));
        }

        return $uploaded;
    }

    private function deleteSlide(string $file): void
    {
        $file = basename($file);
        $path = $this->imageDirectory() . $file;

        if ($this->isAllowedImageFilename($file) && is_file($path)) {
            @unlink($path);
        }

        $slides = array_values(array_filter($this->slides(), static fn (array $slide): bool => $slide['file'] !== $file));
        $this->setPreference('SLIDES_JSON', (string) json_encode($slides, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT));
    }

    /** @return array<int,string> */
    private function imageFiles(): array
    {
        $this->ensureImageDirectory();
        $files = scandir($this->imageDirectory());

        if ($files === false) {
            return [];
        }

        $image_files = [];

        foreach ($files as $file) {
            if ($this->isAllowedImageFilename($file) && is_file($this->imageDirectory() . $file)) {
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

    private function imageDirectory(): string
    {
        return Webtrees::DATA_DIR . 'potts-hero-slideshow/';
    }

    private function ensureImageDirectory(): void
    {
        $directory = $this->imageDirectory();

        if (!is_dir($directory)) {
            mkdir($directory, 0775, true);
        }

        $htaccess = $directory . '.htaccess';

        if (!is_file($htaccess)) {
            @file_put_contents($htaccess, "Require all denied\nDeny from all\n");
        }
    }

    private function imageUrl(string $file): string
    {
        return route('module', [
            'module' => $this->name(),
            'action' => 'Image',
            'file'   => basename($file),
        ]);
    }

    /** @return array<string,string> */
    private function fitChoices(): array
    {
        return [
            'contain' => I18N::translate('Show whole image'),
            'cover'   => I18N::translate('Fill frame and crop edges'),
        ];
    }

    /** @return array<string,string> */
    private function frameChoices(): array
    {
        return [
            'vintage' => I18N::translate('Vintage exact frame'),
            'mount'   => I18N::translate('Offset photo mount'),
            'simple'  => I18N::translate('Simple frame'),
            'none'    => I18N::translate('No frame'),
        ];
    }

    /** @return array<string,string> */
    private function colourChoices(): array
    {
        return [
            'soft'   => I18N::translate('Soft historic'),
            'colour' => I18N::translate('Original colour'),
            'sepia'  => I18N::translate('Sepia'),
            'mono'   => I18N::translate('Black and white'),
        ];
    }

    /** @return array<string,string> */
    private function paletteChoices(): array
    {
        return [
            'auto'          => I18N::translate('Automatic from theme'),
            'heritage'      => I18N::translate('Heritage blue and gold'),
            'neutral-light' => I18N::translate('Neutral light'),
            'neutral-dark'  => I18N::translate('Neutral dark'),
        ];
    }

    /** @return array<string,string> */
    private function transitionChoices(): array
    {
        return [
            'fade'       => I18N::translate('Gentle fade'),
            'zoom'       => I18N::translate('Fade with slow zoom'),
            'slide-left' => I18N::translate('Slide from right'),
            'slide-up'   => I18N::translate('Slide from below'),
            'blur'       => I18N::translate('Soft focus fade'),
            'random'     => I18N::translate('Random effect'),
        ];
    }

    /** @return array<string,string> */
    private function captionChoices(): array
    {
        return [
            'below'   => I18N::translate('Caption strip below frame'),
            'overlay' => I18N::translate('Overlay title on image'),
            'hidden'  => I18N::translate('Hide image titles'),
        ];
    }


    /** @return array<string,string> */
    private function startChoices(): array
    {
        return [
            '0' => I18N::translate('First slide in saved order'),
            '1' => I18N::translate('Randomise image order each visit'),
        ];
    }

    /** @return array<string,string> */
    private function focalChoices(): array
    {
        return [
            'center' => I18N::translate('Centre'),
            'top'    => I18N::translate('Top'),
            'bottom' => I18N::translate('Bottom'),
            'left'   => I18N::translate('Left'),
            'right'  => I18N::translate('Right'),
        ];
    }
}
