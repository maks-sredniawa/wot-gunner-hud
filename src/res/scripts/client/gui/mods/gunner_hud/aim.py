from __future__ import division

import math

AIMED_BELOW_SECONDS = 0.05
_PLAUSIBLE_DELAY = (0.5, 2.0)

FILL_TIME_CONSTANT = 0.25
FILL_SNAP_DROP = 0.08
FULL_ENTER = 0.995
FULL_LEAVE = 0.97
LEAVE_TICKS = 2
PERCENT_STEP = 5
PERCENT_STEPS_BELOW = 95
PERCENT_HYSTERESIS = 3
SECONDS_HYSTERESIS = 0.15
SECONDS_RISE = 0.3
TEXT_REFRESH = 0.2
GREEN_HOLD = 0.3
FADE_SECONDS = 0.4
_EPSILON = 1e-6


class DualAccuracy(object):
    __slots__ = ('active', 'factor', 'cooldown')

    def __init__(self, active, factor, cooldown=None):
        self.active = active
        self.factor = factor
        self.cooldown = cooldown


class AimStatus(object):
    __slots__ = ('fill', 'percent', 'seconds', 'limit', 'locked', 'cooldown')

    def __init__(self, fill, percent, seconds, limit=None, locked=False, cooldown=None):
        self.fill = fill
        self.percent = percent
        self.seconds = seconds
        self.limit = limit
        self.locked = locked
        self.cooldown = cooldown


def seconds_to_aim(current, ideal, aiming_time):
    if current <= ideal or ideal <= 0 or aiming_time <= 0:
        return 0.0
    return aiming_time * math.log(current / ideal)


def _ratio(ideal, current):
    if current <= 0:
        return 1.0
    return max(0.0, min(1.0, ideal / current))


def accurate_mode_active(ideal, hot_ideal, factor):
    # The game widens its ideal circle to the hot one while the gun cools after a shot.
    return ideal < hot_ideal * (1 + factor) / 2


def aim_status(current, stationary_best, aiming_time, dual=None):
    accurate_ideal = stationary_best * dual.factor if dual is not None else stationary_best
    ideal = accurate_ideal if dual is not None and dual.active else stationary_best
    seconds = seconds_to_aim(current, ideal, aiming_time)
    if seconds < AIMED_BELOW_SECONDS:
        current = ideal
    if dual is None:
        percent = _ratio(ideal, current)
        return AimStatus(percent, percent, seconds)
    fill = _ratio(accurate_ideal, current)
    percent = fill / dual.factor
    if dual.active:
        return AimStatus(fill, percent, seconds, limit=dual.factor)
    return AimStatus(min(fill, dual.factor), percent, seconds, limit=dual.factor, locked=True, cooldown=dual.cooldown)


class CooldownTracker(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self._was_active = None
        self._since = None
        self._measured = None

    def shot(self, now):
        self._since = now

    def update(self, active, now, base_delay):
        was_active, self._was_active = self._was_active, active
        if active:
            if was_active is False and self._since is not None:
                self._remember(now - self._since, base_delay)
            self._since = None
            return None
        if was_active and self._since is None:
            self._since = now
        if self._since is None:
            return None
        delay = self._measured if self._measured is not None else base_delay
        left = delay - (now - self._since)
        return left if left > 0 else None

    def _remember(self, measured, base_delay):
        low, high = _PLAUSIBLE_DELAY
        if base_delay * low < measured < base_delay * high:
            self._measured = measured if self._measured is None else min(self._measured, measured)


class AimDisplay(object):
    __slots__ = ('fill', 'normal_reached', 'best_reached', 'fade', 'percent', 'seconds', 'limit', 'locked',
                 'cooldown')

    def __init__(self, fill, normal_reached, best_reached, fade, percent, seconds, limit=None, locked=False,
                 cooldown=None):
        self.fill = fill
        self.normal_reached = normal_reached
        self.best_reached = best_reached
        self.fade = fade
        self.percent = percent
        self.seconds = seconds
        self.limit = limit
        self.locked = locked
        self.cooldown = cooldown


class _Latch(object):

    def __init__(self):
        self.on = False
        self._low_ticks = 0

    def update(self, value):
        if value >= FULL_ENTER:
            self.on, self._low_ticks = True, 0
        elif value < FULL_LEAVE:
            self._low_ticks += 1
            if self._low_ticks >= LEAVE_TICKS:
                self.on = False
        else:
            self._low_ticks = 0
        return self.on

    def release(self):
        self.on, self._low_ticks = False, 0


def _quantized_percent(value, normal_reached):
    if normal_reached:
        return max(100, int(round(value)))
    if value < PERCENT_STEPS_BELOW:
        return int(PERCENT_STEP * round(value / PERCENT_STEP))
    return min(99, int(round(value)))


class AimSmoother(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self._normal_reached = _Latch()
        self._best_reached = _Latch()
        self._state = None
        self._locked = None
        self._fill = None
        self._raw_fill = None
        self._at = None
        self._best_reached_at = None
        self._percent = None
        self._percent_at = None
        self._seconds = None
        self._seconds_at = None

    def update(self, status, now):
        if status.locked != self._locked:
            self._locked = status.locked
            self._best_reached.release()
        snapped = self._raw_fill is not None and self._raw_fill - status.fill > FILL_SNAP_DROP
        if snapped:
            self._normal_reached.release()
            self._best_reached.release()
        normal_reached = self._normal_reached.update(status.percent)
        best_reached = self._best_reached.update(status.fill) and normal_reached
        nothing_to_aim = best_reached or (normal_reached and status.locked)
        changed = (normal_reached, best_reached) != self._state
        self._state = (normal_reached, best_reached)
        reseed = changed or snapped
        self._smooth(status.fill, now, reseed)
        if changed:
            self._best_reached_at = now if best_reached else None
        if best_reached:
            fill = 1.0
        elif normal_reached:
            fill = max(self._fill, status.limit or 1.0)
        else:
            fill = self._fill
        return AimDisplay(fill, normal_reached, best_reached, self._fade(now),
                          self._update_percent(status, now, normal_reached, nothing_to_aim, reseed),
                          self._update_seconds(status.seconds, now, nothing_to_aim, reseed),
                          status.limit, status.locked, status.cooldown)

    def _smooth(self, raw, now, reseed):
        if reseed:
            self._fill = raw
        else:
            elapsed = max(0.0, now - self._at)
            self._fill += (raw - self._fill) * (1 - math.exp(-elapsed / FILL_TIME_CONSTANT))
        self._raw_fill, self._at = raw, now

    def _fade(self, now):
        if self._best_reached_at is None:
            return 0.0
        return max(0.0, min(1.0, (now - self._best_reached_at - GREEN_HOLD) / FADE_SECONDS))

    def _update_percent(self, status, now, normal_reached, nothing_to_aim, reseed):
        smoothed = self._fill / (status.limit or 1.0) * 100
        if reseed:
            self._percent, self._percent_at = _quantized_percent(smoothed, normal_reached), now
        elif (not nothing_to_aim and now - self._percent_at >= TEXT_REFRESH - _EPSILON
              and abs(smoothed - self._percent) >= PERCENT_HYSTERESIS):
            self._percent, self._percent_at = _quantized_percent(smoothed, normal_reached), now
        return self._percent

    def _update_seconds(self, raw, now, nothing_to_aim, reseed):
        if nothing_to_aim:
            self._seconds = None
        elif reseed or self._seconds is None:
            self._seconds, self._seconds_at = raw, now
        elif now - self._seconds_at >= TEXT_REFRESH - _EPSILON:
            change = raw - self._seconds
            if change <= -SECONDS_HYSTERESIS + _EPSILON or change >= SECONDS_RISE - _EPSILON:
                self._seconds, self._seconds_at = raw, now
        return self._seconds
