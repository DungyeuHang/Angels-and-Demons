# Asset Sources

This file tracks free-use asset sources that fit the current "Angels and Demons" direction.

## Current local candidate

- Generated brand art used by the app:
  - `assets/images/friendly_brand_emblem.png`
  - `assets/images/friendly_app_icon.png`
  - `assets/images/friendly_app_icon.ico`
  - `assets/images/angel_badge.png`
  - `assets/images/demon_badge.png`
  - `assets/images/effect_angel.png`
  - `assets/images/effect_devil.png`
  - `assets/images/effect_gun.png`
  - `assets/images/effect_lucky.png`
  - `assets/images/effect_lottery.png`
  - `assets/images/effect_rps.png`
  - `assets/images/effect_double.png`
  - `assets/images/effect_half.png`
  - Source: generated locally by `tools/generate_brand_assets.py`
  - License: project-owned/generated in-repo

- Generated sound effects used by the app:
  - `assets/sounds/ui_click.wav`
  - `assets/sounds/box_flip.wav`
  - `assets/sounds/point_gain.wav`
  - `assets/sounds/point_loss.wav`
  - `assets/sounds/achievement.wav`
  - `assets/sounds/bot_move.wav`
  - Source: generated locally by `tools/generate_sound_fx.py`
  - License: project-owned/generated in-repo

- App/icon candidate downloaded locally:
  - `assets/images/angel_and_demon_icon_candidate.svg`
  - Source: https://www.svgrepo.com/svg/118868/angel-and-demon
  - License: CC0
  - Note: good starting point for replacing `ui/demon.ico`, but it still needs conversion to `.ico` before wiring into the packer spec.

- Music candidates downloaded locally:
  - `assets/music_candidates/dungeon_ambience.ogg`
  - `assets/music_candidates/heroic_stance.mp3`
  - `assets/music_candidates/mysterious_cave_theme_loop.ogg`
  - `assets/music_candidates/treasure_hunter.mp3`
  - Source pages and licenses are listed below.

- Music tracks currently wired into the app:
  - `assets/music/menu_theme.mp3`
  - `assets/music/game_theme.ogg`
  - `assets/music/result_theme.mp3`
  - `assets/music/history_theme.ogg`

## Recommended icon sources

- Angel and Demon icon:
  - https://www.svgrepo.com/svg/118868/angel-and-demon
  - License: CC0
  - Best fit for the app/window icon concept because it already combines both themes.

- Angel icon:
  - https://www.svgrepo.com/svg/104226/angel-with-open-arms
  - License: CC0
  - Useful when we want extra angel-themed UI markers or bonus/heal effects.

- Japanese Demon icon:
  - https://www.svgrepo.com/svg/80598/japanese-demon
  - License: CC0
  - Good fallback if you want a sharper demon-only badge for effects or danger markers.

- Devil icon:
  - https://www.svgrepo.com/svg/521631/emoji-devil-smile
  - License: CC0
  - Nice option for danger, curse, or negative-status markers.

- Kenney UI Pack:
  - https://kenney.nl/assets/ui-pack
  - License: CC0
  - Great for buttons, frames, and clean game UI polish.

- Kenney UI Pack (RPG Expansion):
  - https://kenney.nl/assets/ui-pack-rpg-expansion
  - License: CC0
  - Best match if we want more fantasy-flavored interface pieces.

## Recommended music sources

- CC0 fantasy music collection:
  - https://opengameart.org/content/cc0-fantasy-music-sounds
  - License: collection of CC0 fantasy-friendly tracks
  - Best place to browse for menu, battle, inn, cave, and ambience tracks without attribution friction.

- The Field Of Dreams:
  - https://opengameart.org/content/the-field-of-dreams
  - License: CC0
  - Great candidate for the main menu or intro because it feels soft, magical, and readable under UI.

- Dungeon Ambience:
  - https://opengameart.org/content/dungeon-ambience
  - License: CC0
  - Good for quiet suspense, slower rounds, or history screen ambience.

- Mysterious Cave Theme Loop:
  - https://opengameart.org/content/mysterious-cave-theme-loop
  - License: CC0
  - Nice backup gameplay loop if you want something a bit more magical and less dark.

- Heroic Stance:
  - https://opengameart.org/content/heroic-stance
  - License: CC0
  - Strong candidate for intense result screen or boss/battle moments.

- Treasure Hunter:
  - https://opengameart.org/content/treasure-hunter
  - License: CC0
  - Good victory/result music if you want a brighter orchestral feel.

- Pixabay license summary:
  - https://pixabay.com/service/license-summary/
  - Allows free use, no attribution required, and modification.
  - Note: Pixabay content is not CC0, so for the safest packaging path I still prefer the OpenGameArt CC0 music above.

- Pixabay fantasy music search:
  - https://pixabay.com/music/search/fantasy-soundtrack/
  - Good backup source if you want more polished modern fantasy music quickly.

## My practical recommendation

- App icon:
  - Use the downloaded SVG Repo "Angel and Demon" icon as the design base, then convert it to `.ico`.

- Menu/background music:
  - Start with an OpenGameArt CC0 ambience track.

- Big moments/result screen:
  - Try a more heroic CC0 track like "Heroic Stance".
