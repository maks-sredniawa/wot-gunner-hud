from __future__ import division

from gui.mods.gambiter import g_guiFlash
from gui.mods.gambiter.flash import COMPONENT_ALIGN, COMPONENT_EVENT, COMPONENT_TYPE

from .view import dragged_offset, view_offset

# GUIFlash creates battle components in alphabetical order of alias, which is also their stacking order.
_PREFIX = 'maksforgeGunnerHudAim'
TRACK = _PREFIX + '1Track'
LOCKED = _PREFIX + '2Locked'
FILL = _PREFIX + '3Fill'
GAIN = _PREFIX + '4Gain'
LIMIT = _PREFIX + '5Limit'
SECONDS = _PREFIX + '6Seconds'
PERCENT = _PREFIX + '7Percent'
COOLDOWN = _PREFIX + '8Cooldown'
STACKING_ORDER = (TRACK, LOCKED, FILL, GAIN, LIMIT, SECONDS, PERCENT, COOLDOWN)

BAR_WIDTH = 6
BAR_HEIGHT = 64
TRACK_ALPHA = (0.35, 0.15)
AIMING_ALPHA = 0.85
FULL_ALPHA = (0.9, 0.35)
GAIN_ALPHA = (0.85, 0.6)
LOCKED_ALPHA = 0.5
LIMIT_ALPHA = 0.5
SECONDS_ALPHA = 0.9
PERCENT_ALPHA = (0.7, 0.35)
LIMIT_SIZE = (12, 2)
LABEL_GAP = 10
COOLDOWN_X = 26

_IMAGE_DIR = 'gui/maps/gunner_hud/'
_SHADOW = {'color': 0x000000, 'alpha': 0.8, 'blurX': 2, 'blurY': 2, 'strength': 2, 'quality': 2}
_LABEL_OFFSETS = {
    SECONDS: (0, -(BAR_HEIGHT // 2 + LABEL_GAP)),
    PERCENT: (0, BAR_HEIGHT // 2 + LABEL_GAP),
}
_DRAGGABLE = (TRACK, SECONDS, PERCENT)


def _image(name):
    path = _IMAGE_DIR + name + '.png'
    return {'image': '../../' + path, 'imageAlt': 'img://' + path}


def format_seconds(display):
    return None if display.seconds is None else '%.1f s' % display.seconds


def format_percent(display):
    return '%d%%' % display.percent


def format_cooldown(display):
    return None if not display.locked or display.cooldown is None else '%.1f s' % display.cooldown


def faded(alphas, fade):
    start, end = alphas
    return round(start + (end - start) * fade, 3)


class AimBarView(object):

    def __init__(self, settings, on_moved):
        self._settings = settings
        self._on_moved = on_moved
        self._anchor = (0, 0)
        self._view_id = None
        self._shown = {}
        self._display = None
        centered = {'alignX': COMPONENT_ALIGN.CENTER, 'alignY': COMPONENT_ALIGN.CENTER, 'visible': False}
        self._create(TRACK, COMPONENT_TYPE.IMAGE, dict(centered, alpha=TRACK_ALPHA[0], drag=True, width=BAR_WIDTH,
                                                       height=BAR_HEIGHT, **_image('black')))
        self._create(LOCKED, COMPONENT_TYPE.IMAGE, dict(centered, alpha=LOCKED_ALPHA, width=BAR_WIDTH,
                                                        **_image('grey')))
        self._create(FILL, COMPONENT_TYPE.IMAGE, dict(centered, width=BAR_WIDTH))
        self._create(GAIN, COMPONENT_TYPE.IMAGE, dict(centered, width=BAR_WIDTH, **_image('cyan')))
        self._create(LIMIT, COMPONENT_TYPE.IMAGE, dict(centered, alpha=LIMIT_ALPHA, width=LIMIT_SIZE[0],
                                                       height=LIMIT_SIZE[1], **_image('light')))
        for alias in (SECONDS, PERCENT, COOLDOWN):
            self._create(alias, COMPONENT_TYPE.LABEL, dict(centered, text='', isHtml=True, glowfilter=_SHADOW,
                                                           drag=alias in _DRAGGABLE))
        COMPONENT_EVENT.UPDATED += self._on_component_updated

    def destroy(self):
        COMPONENT_EVENT.UPDATED -= self._on_component_updated
        for alias in list(self._shown):
            g_guiFlash.deleteComponent(alias)
        self._shown = {}

    def set_anchor(self, x, y, view_id=None):
        if ((x, y), view_id) == (self._anchor, self._view_id):
            return
        self._anchor = (x, y)
        self._view_id = view_id
        self.show(self._display)

    def hide(self):
        self.show(None)

    def show(self, display):
        self._display = display
        if display is None:
            for alias in self._shown:
                self._update(alias, {'visible': False})
            return
        cx, cy = self._center()
        bottom = cy + BAR_HEIGHT / 2
        self._update(TRACK, {'visible': True, 'x': cx, 'y': cy, 'alpha': faded(TRACK_ALPHA, display.fade)})
        self._show_fill(display, cx, bottom)
        self._show_limit(display, cx, bottom)
        self._show_locked(display, cx, cy, bottom)
        colors = self._settings['colors']
        font_size = self._settings['fontSize']
        self._show_label(SECONDS, format_seconds(display), colors['loading'], font_size - 1, SECONDS_ALPHA,
                         self._label_position(SECONDS))
        percent_color = colors['loaded'] if display.normal_reached else colors['loading']
        self._show_label(PERCENT, format_percent(display), percent_color, font_size - 2,
                         faded(PERCENT_ALPHA, display.fade), self._label_position(PERCENT))
        locked_middle = (cy - BAR_HEIGHT / 2 + bottom - BAR_HEIGHT * (display.limit or 0)) / 2
        self._show_label(COOLDOWN, format_cooldown(display), colors['shellTime'], font_size - 2, 1.0,
                         (cx + COOLDOWN_X, int(round(locked_middle))))

    def _show_fill(self, display, cx, bottom):
        normal = int(round(BAR_HEIGHT * min(display.fill, display.limit or 1.0)))
        gain = int(round(BAR_HEIGHT * display.fill)) - normal
        fill_look = dict(_image('green'), alpha=faded(FULL_ALPHA, display.fade)) if display.normal_reached else \
            dict(_image('amber'), alpha=AIMING_ALPHA)
        self._show_segment(FILL, normal, cx, bottom, fill_look)
        self._show_segment(GAIN, gain, cx, bottom - normal, {'alpha': faded(GAIN_ALPHA, display.fade)})

    def _show_segment(self, alias, height, cx, bottom, look):
        if height <= 0:
            self._update(alias, {'visible': False})
            return
        self._update(alias, dict(look, visible=True, x=cx, y=int(round(bottom - height / 2)), height=height))

    def _show_limit(self, display, cx, bottom):
        if display.limit is None:
            self._update(LIMIT, {'visible': False})
            return
        self._update(LIMIT, {'visible': True, 'x': cx, 'y': int(round(bottom - BAR_HEIGHT * display.limit))})

    def _show_locked(self, display, cx, cy, bottom):
        height = int(round(BAR_HEIGHT * (1 - (display.limit or 1.0))))
        if not display.locked or height <= 0:
            self._update(LOCKED, {'visible': False})
            return
        top = cy - BAR_HEIGHT / 2
        self._update(LOCKED, {'visible': True, 'x': cx, 'y': int(round(top + height / 2)), 'height': height})

    def _show_label(self, alias, text, color, size, alpha, position):
        if text is None:
            self._update(alias, {'visible': False})
            return
        html = "<font face='$FieldFont' size='%d' color='#%s'>%s</font>" % (size, color, text)
        self._update(alias, {'visible': True, 'text': html, 'alpha': alpha, 'x': position[0], 'y': position[1]})

    def _center(self):
        offset = view_offset(self._settings['aimTimer'], self._view_id)
        return (self._anchor[0] + offset['x'], self._anchor[1] + offset['y'])

    def _label_position(self, alias):
        cx, cy = self._center()
        dx, dy = _LABEL_OFFSETS[alias]
        return (cx + dx, cy + dy)

    def _create(self, alias, component_type, props):
        g_guiFlash.createComponent(alias, component_type, props)
        self._shown[alias] = dict(props)

    def _update(self, alias, props):
        shown = self._shown[alias]
        changed = dict((key, value) for key, value in props.items() if shown.get(key) != value)
        if changed:
            shown.update(changed)
            g_guiFlash.updateComponent(alias, changed)

    def _on_component_updated(self, alias, props):
        if alias not in _DRAGGABLE or 'x' not in props or 'y' not in props:
            return
        dx, dy = _LABEL_OFFSETS.get(alias, (0, 0))
        self._shown[alias].update(x=props['x'], y=props['y'])
        offset = dragged_offset(self._settings['aimTimer'], self._view_id)
        offset['x'] = int(props['x']) - dx - self._anchor[0]
        offset['y'] = int(props['y']) - dy - self._anchor[1]
        self._on_moved()
