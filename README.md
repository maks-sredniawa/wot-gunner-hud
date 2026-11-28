# Gunner HUD

A World of Tanks mod that shows what your gun is doing next to the crosshair:

- The load time of **every shell** in an autoreloader magazine (Italian tanks and any other gun with the `autoreload` mechanic), not just the one that's loading now.
- The shells left and their potential damage on every magazine tank.
- How long an Ares gun needs to cool down and the damage left before it locks.
- An aim timer on every tank, which also shows the dual accuracy cooldown of the Type 71 line and, in red, how much a damaged gun, an injured crew member or a stun costs your aim.
- How long each stance's ability needs to charge on tanks with Fight and Turbo stances, such as the CS-67 Szakal.

Until 0.6.0 it was called Autoloader Shell Timer.

All the times it shows are estimates from the gun's state right now: firing, moving, or a change to your reload or aim modifiers (crew, equipment, consumables, a damaged module) can change them. Potential damage uses the loaded shell's nominal (average) damage, as if every shell penetrates.

## Autoreloaders

```
4.5   16.2   26.7   35.5   1/4   390
```

- **Each number**: seconds until that shell is ready, counted from now. The amber one is loading now.
- **1/4**: shells in the magazine now.
- **390** at the end: potential damage of those shells, as if every one penetrates.
- When the magazine is full it shows each shell's own load time at your current reload speed in grey, fastest first, then **3/3** and the damage in green, for example `10.8   11.7   13.5   3/3   1170`.

The times always use your current reload speed. They're recalculated every 0.1 s from the reload time the server sends for the shell being loaded, so a damaged ammo rack, stun, or a crew member knocked out changes them right away. The rest of the magazine is predicted from the gun's per-shell reload table at that same speed, so the later shells and the full magazine time are estimates that shift whenever your reload speed changes.

## Regular autoloaders

Tanks whose whole magazine reloads at once show the shells left and their potential damage: `4/6   1560`, in green when full (`6/6   2340`). While the magazine reloads it reads `0/6` in amber.

## Ares tanks

The Ares line has no magazine: every shot heats the gun, and too much heat locks it. On these tanks the same line shows how long the gun needs to cool down and how much damage you can still deal before it locks:

- **8.4   560** while warm: the gun can fire and is estimated to be fully cold in 8.4 s if you stop shooting, including the delay before cooling starts. The last number is the damage of the shots left before it locks.
- **960** in green: the gun is cold and this is the damage of a full burst.
- While the gun is locked the line is hidden, because the game shows its own lockout timer.

The damage is shots left × the nominal (average) damage of the loaded shell, as if every shell penetrates. It's capped by the shells you have left.

The reload quick command stays the game's own on these tanks, and it already reports the overheat time.

## Aim timer

A thin bar to the right of the crosshair shows how far your gun has aimed, on every tank:

- **The seconds above it** estimate how long until the circle is fully aimed, at your current aiming speed; moving, turning or firing changes them. The **percentage below it** shows how far it has shrunk, in 5% steps until 95%. Both are amber while aiming.
- **Fully aimed**: the seconds disappear and the bar and `100%` turn green the moment the circle closes. After 0.3 s the bar, its track and the `100%` fade back so they don't pull your eye while you wait to shoot. It turns amber again once the circle has opened past 97% for 0.2 s, or at once after a shot or a sharp turn.
- **While you drive**, it measures against the circle you'd reach standing still, so the seconds show how long you'd still need to aim after stopping.

The bar eases toward the circle's real size instead of jumping with every bump, and the numbers change at most five times a second and only on a real change, so the circle's own wobble doesn't make them flicker. A sudden widening, such as a shot or a fast turn, shows at once.

### Damaged gun, injured crew, stun

A damaged gun, an injured crew member or an artillery stun makes the circle you can aim down to wider, so a plain `100%` would only mean "as good as it gets right now". Under such a penalty the aim timer measures against a healthy tank instead:

- **The percentage turns red** and shows how far you can aim compared with the healthy circle: fully aimed with a damaged gun reads, for example, `80%` instead of `100%`. While aiming it counts up to that value.
- **A red block tops the bar**: the part of a healthy aim you can't reach now. The bar below it fills and turns green as usual, because once it is green waiting no longer helps. The red block and percentage fade back with the rest of the bar, but stay readable.
- **The seconds** still count down to the widest circle you can reach now.
- Once the gun is repaired, the crew member healed or the stun over, the bar goes back to normal.

The server sends one aim multiplier with every modifier already in it, so the mod remembers the multiplier from the last moment none of these penalties was on and compares against it. It notices the penalty from the game's own damage panel (gun, any crew member) and stun timer; an injured loader or driver only shows in red if the multiplier actually got worse, which happens when it costs the crew a skill bonus such as the commander's or Brothers in Arms. Penalties under 1% are not shown. Turn it off with `aimTimer.penalty` or on the settings page.

### Type 71 line (dual accuracy)

On guns with dual accuracy, the circle gets much smaller once the gun has cooled after a shot. The game shows a second circle for it but no timer. The bar shows both stages:

- **100%** is the hot gun fully aimed, as on any tank. A tick on the bar marks it.
- **The part above the tick** is the extra the cooled gun gives. It is solid grey while the gun cools after a shot, with the seconds until it has cooled next to it, and empty once the gun has cooled.
- **Aiming past 100%** fills that part in cyan. The percentage keeps counting up to the gun's real gain, the hot circle divided by the cooled one, which the mod reads from the gun itself: 173% on the Type 71.
- **A full bar with no seconds left** is the best shot the gun can make. Only then does the bar fade back, the cyan part with it. While the gun cools it stays bright even with the hot circle reached, because the grey part and its countdown are still changing.
- **Under a penalty** the red block sits above all of this and the tick, grey and cyan parts shrink with the rest of the bar; the percentage shows the real gain in red, for example `138%` instead of `173%` with a damaged gun.

The game doesn't tell the client how long the cooldown is after crew skills, so the first countdown of a battle uses the gun's base delay. After one full cycle the mod counts with the delay it measured. The countdown starts when the server switches the accurate mode off, so ping shifts it slightly. It's an estimate: firing again restarts it.

## Stance ability charge (CS-67 Szakal)

Tanks with Fight and Turbo stances charge a separate energy gauge for each stance's ability. Beside each gauge, at its middle, the mod shows the estimated seconds until that ability can be used: the Fight (reload) ability's time left of the left gauge, the Turbo (speed) ability's time right of the right gauge.

- **Amber** is the stance you're in, counting at the rate you're charging now.
- **Grey** is the other stance: how long it would take at its passive rate once you switch to it.

- **Fight stance** charges slowly on its own (0.6 energy a second on the Szakal, so a full gauge takes about 2 min 47 s) and gains a chunk with every hit you land. A hit makes the countdown drop at once.
- **Turbo stance** charges at the same slow pace, much faster while you drive above the speed the game marks on the turbo gauge (40 km/h on the Szakal). Speeding up or slowing down changes the countdown straight away.
- Switching stance swaps the colours.
- Each time hides once its ability is ready or while it's running (the game shows its own timer). Both hide while the stance is switching and while the engine is destroyed.

The rates come from your tank as the game sets it up, so the Szakal's field modifications that speed up passive Fight or Turbo gain (+25% each) and any crew or equipment bonuses are already included.

The seconds assume you keep doing what you're doing now: they count the passive gain and the speed bonus that is on at this moment, never hits you haven't landed yet. Turn it off with `abilityCharge.enabled` or on the settings page. Drag either one with Ctrl like the other parts if it sits wrong at your resolution.

## Reload quick command

In an autoreloader, the reload quick command (its own key, or Z → "I'm reloading") sends one team chat line with the whole magazine instead of the game's line, which only knows about the next shell:

```
Magazine 1/4, full in 35 s
Magazine 0/4, first shell 9 s, full in 35 s
Magazine 4/4
```

The times in it are the same estimates as on screen, rounded up to whole seconds.

Allies don't get the game's reload icon over your tank or the minimap animation for that command. If team chat is unavailable (chat turned off, a chat ban, or the chat cooldown), or you're out of shells (magazine and ammo rack both empty), the game's own command goes out as usual. Other tanks are not affected. Turn the line off with `reloadChatLine` to always send the game's command.

## Install

1. Install [GUIFlash](https://github.com/CH4MPi/GUIFlash) (`gambiter.guiflash_*.wotmod`). Most modpacks include it.
2. Copy `maksforge.gunner_hud_<version>.wotmod` into `World_of_Tanks/mods/<game version>/`.
3. Optional: install ModsSettingsAPI for the [in-game settings](#in-game-settings) page.

### Upgrading from Autoloader Shell Timer

0.6.0 replaces `maksforge.autoloader_timer_<version>.wotmod`. Delete that file from `mods/<game version>/`, or both mods load and draw everything twice. Your settings carry over: the next game start copies `mods/configs/autoloader_timer/config.json` to the new config path and leaves the old file where it is.

## In-game settings

With [ModsSettingsAPI](https://github.com/IzeBerg/modssettingsapi) (`izeberg.modssettingsapi_*.wotmod`) installed, the mod gets a **Gunner HUD** page in the mods settings window, opened from the mods list button in the garage or on the login screen. ModsSettingsAPI needs ModsList API (`me.poliroid.modslistapi_*.wotmod`); modpacks that include one usually include both. It switches the whole mod, the aim timer, its red aim penalty, the stance ability charge times, each line, the reload quick command line and Hide when full, and sets the text size (10 to 24).

The page reads and writes `config.json`, so the file stays the one source of truth: a change on the page is saved there at once, and a value you edit in the file shows on the page at the next game start. Every change applies without a restart and shows from your next battle. Without ModsSettingsAPI the mod runs from `config.json` alone, as before.

## Settings

The game writes `mods/configs/gunner_hud/config.json` the first time it starts with the mod installed:

| Key | Default | Meaning |
| --- | --- | --- |
| `enabled` | `true` | Turns the mod off without uninstalling it |
| `x`, `y` | `0`, `60` | The panel's offset from the crosshair, which it follows frame by frame. Once you drag the panel in sniper or artillery view, a `sniper` or `strategic` key with its own `x`, `y` appears; until then that view uses these arcade values. |
| `fontSize` | `14` | Text size. The aim timer's seconds are 1 smaller and its percentage 2 smaller. The settings page offers 10 to 24. |
| `hideWhenFull` | `false` | Hide the panel while the magazine is full or an Ares gun is cold |
| `reloadChatLine` | `true` | Replace the reload quick command with the magazine status line in autoreloaders |
| `autoreloaderLine` | `true` | Show the shell times line on autoreloaders |
| `magazineLine` | `true` | Show the magazine line on regular autoloaders |
| `aresLine` | `true` | Show the cooldown and damage line on Ares tanks |
| `aimTimer` | | `enabled` (`true`) shows the aim timer. `penalty` (`true`) shows a damaged gun's, an injured crew member's or a stun's cost to your aim in red. `x`, `y` (`150`, `0`) are its offset from the crosshair. Like the panel, it uses this spot in sniper and artillery view too until you drag it there, which adds a `sniper` or `strategic` key with its own `x`, `y`. |
| `abilityCharge` | | `enabled` (`true`) shows the stance ability charge times. `fight` and `turbo` each hold their time's `x`, `y` offset from the crosshair (`-210`, `71` and `210`, `71`), with their own `sniper` or `strategic` key once you drag them in those views. |
| `colors` | | Hex colours for the count, a full magazine, the loading shell, the queued shells, the per-shell times, and the aim timer's red penalty percentage (`penalty`). The Ares line and the aim timer's text reuse them. The bar's own colours are built in. |

To move the panel, the aim timer or the stance ability charge time, hold Ctrl to show the cursor and drag it (the aim timer by its bar, seconds or percentage). The new position is saved. Sniper and artillery view use the same spot as arcade view; drag any of them while in one of those views to give that view its own position.

## Build

Needs Python 2.7, the game's script runtime (for example `pyenv install 2.7.18`).

```sh
./build.sh                                   # dist/maksforge.gunner_hud_<version>.wotmod
python2.7 tests/test_schedule.py
python2.7 tests/test_aim.py
python2.7 tests/test_mod_smoke.py
```

## How it works

`gun.autoreload.reloadTime` holds one base time per magazine slot. The first entry is the shell that fills the magazine, and the last is the shell loaded into an empty one. Every 0.1 s, the mod reads the shell loading now from the game's `AmmoController`. It takes the remaining time from the server, works out your reload factor from that shell's base time, and adds the scaled time of each shell after it.

## Support

Questions and bug reports: open an issue in this repository or write to wotmods.support@maksforge.com.

This is a free fan-made mod by MaksForge. It is not affiliated with or endorsed by Wargaming.
