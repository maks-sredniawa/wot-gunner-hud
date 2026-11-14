import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'res', 'scripts', 'client', 'gui', 'mods'))

from gunner_hud.aim import (ACCURATE, AIMED, AIMING, AimSmoother, AimStatus, CooldownTracker, DualAccuracy,
                            accurate_mode_active, aim_status, seconds_to_aim)


class SecondsToAimTest(unittest.TestCase):

    def test_circle_twice_the_ideal_needs_aiming_time_times_ln2(self):
        self.assertAlmostEqual(seconds_to_aim(0.4, 0.2, 2.0), 2.0 * math.log(2))

    def test_circle_at_ideal_is_aimed(self):
        self.assertEqual(seconds_to_aim(0.2, 0.2, 2.0), 0.0)

    def test_bad_data_reads_as_aimed(self):
        self.assertEqual(seconds_to_aim(0.4, 0.0, 2.0), 0.0)
        self.assertEqual(seconds_to_aim(0.4, 0.2, 0.0), 0.0)


class AimStatusTest(unittest.TestCase):

    def test_normal_gun_aiming(self):
        status = aim_status(0.4, 0.2, 2.0)
        self.assertEqual((status.phase, status.fill, status.percent, status.limit), (AIMING, 0.5, 0.5, None))
        self.assertFalse(status.locked)

    def test_normal_gun_aimed(self):
        status = aim_status(0.2, 0.2, 2.0)
        self.assertEqual((status.phase, status.fill, status.percent), (AIMED, 1.0, 1.0))

    def test_circle_one_percent_above_best_reads_as_fully_aimed(self):
        status = aim_status(0.202, 0.2, 2.0)
        self.assertEqual((status.phase, status.fill, status.percent), (AIMED, 1.0, 1.0))

    def test_moving_tank_counts_against_the_stationary_best_circle(self):
        status = aim_status(0.8, 0.2, 2.0)
        self.assertEqual((status.phase, status.percent), (AIMING, 0.25))
        self.assertAlmostEqual(status.seconds, 2.0 * math.log(4))

    def test_accurate_mode_one_percent_above_best_reads_as_fully_aimed(self):
        status = aim_status(0.2424, 0.4, 2.0, DualAccuracy(True, 0.6))
        self.assertEqual((status.phase, status.fill), (AIMED, 1.0))
        self.assertAlmostEqual(status.percent, 1 / 0.6)

    def test_cooling_gun_fills_up_to_the_hot_limit_and_counts_against_the_hot_circle(self):
        status = aim_status(0.5, 0.4, 2.0, DualAccuracy(False, 0.6, 3.1))
        self.assertEqual((status.phase, status.limit, status.cooldown), (AIMING, 0.6, 3.1))
        self.assertTrue(status.locked)
        self.assertAlmostEqual(status.fill, 0.48)
        self.assertAlmostEqual(status.percent, 0.8)

    def test_cooling_gun_aimed_stops_at_the_limit_and_reads_100_percent(self):
        status = aim_status(0.4, 0.4, 2.0, DualAccuracy(False, 0.6, 1.0))
        self.assertEqual(status.phase, AIMED)
        self.assertAlmostEqual(status.fill, 0.6)
        self.assertAlmostEqual(status.percent, 1.0)
        self.assertTrue(status.locked)

    def test_accurate_mode_aiming_is_cyan_phase_past_the_limit(self):
        status = aim_status(0.32, 0.4, 2.0, DualAccuracy(True, 0.6))
        self.assertEqual((status.phase, status.limit), (ACCURATE, 0.6))
        self.assertFalse(status.locked)
        self.assertAlmostEqual(status.fill, 0.75)
        self.assertAlmostEqual(status.percent, 1.25)

    def test_accurate_mode_aimed_is_the_best_shot(self):
        status = aim_status(0.24, 0.4, 2.0, DualAccuracy(True, 0.6))
        self.assertEqual((status.phase, status.fill), (AIMED, 1.0))
        self.assertAlmostEqual(status.percent, 1 / 0.6)


class AccurateModeActiveTest(unittest.TestCase):

    def test_ideal_at_the_cool_circle_means_the_mode_is_on(self):
        self.assertTrue(accurate_mode_active(0.24, 0.4, 0.6))

    def test_ideal_at_the_hot_circle_means_the_gun_is_cooling(self):
        self.assertFalse(accurate_mode_active(0.4, 0.4, 0.6))

    def test_holds_while_driving_widens_both_circles(self):
        self.assertFalse(accurate_mode_active(1.2, 1.2, 0.6))
        self.assertTrue(accurate_mode_active(0.72, 1.2, 0.6))


class CooldownTrackerTest(unittest.TestCase):

    def test_unknown_start_shows_no_countdown(self):
        self.assertIsNone(CooldownTracker().update(False, 10.0, 4.0))

    def test_counts_down_the_base_delay_from_the_switch_off(self):
        tracker = CooldownTracker()
        tracker.update(True, 9.0, 4.0)
        self.assertEqual(tracker.update(False, 10.0, 4.0), 4.0)
        self.assertEqual(tracker.update(False, 11.5, 4.0), 2.5)

    def test_hides_the_countdown_once_it_runs_out_but_the_gun_is_still_hot(self):
        tracker = CooldownTracker()
        tracker.update(True, 9.0, 4.0)
        tracker.update(False, 10.0, 4.0)
        self.assertIsNone(tracker.update(False, 20.0, 4.0))

    def test_ignores_a_flicker_far_shorter_than_the_base_delay(self):
        tracker = CooldownTracker()
        tracker.update(False, 0.0, 4.0)
        tracker.update(True, 0.4, 4.0)
        tracker.update(False, 0.8, 4.0)
        tracker.update(True, 1.2, 4.0)
        tracker.update(False, 10.0, 4.0)
        self.assertEqual(tracker.update(False, 11.0, 4.0), 3.0)

    def test_keeps_the_shortest_plausible_cycle(self):
        tracker = CooldownTracker()
        tracker.update(True, 0.0, 4.0)
        tracker.update(False, 1.0, 4.0)
        tracker.update(True, 4.5, 4.0)
        tracker.update(False, 10.0, 4.0)
        tracker.update(True, 17.0, 4.0)
        tracker.update(False, 20.0, 4.0)
        self.assertEqual(tracker.update(False, 21.0, 4.0), 2.5)

    def test_uses_the_measured_delay_after_one_full_cycle(self):
        tracker = CooldownTracker()
        tracker.update(True, 9.0, 4.0)
        tracker.update(False, 10.0, 4.0)
        self.assertIsNone(tracker.update(True, 13.5, 4.0))
        tracker.update(False, 20.0, 4.0)
        self.assertEqual(tracker.update(False, 21.0, 4.0), 2.5)

    def test_ignores_a_cycle_far_longer_than_the_base_delay(self):
        tracker = CooldownTracker()
        tracker.update(True, 0.0, 4.0)
        tracker.update(False, 1.0, 4.0)
        tracker.update(True, 30.0, 4.0)
        tracker.update(False, 40.0, 4.0)
        self.assertEqual(tracker.update(False, 41.0, 4.0), 3.0)

    def test_a_shot_while_hot_restarts_the_countdown(self):
        tracker = CooldownTracker()
        tracker.update(True, 0.0, 4.0)
        tracker.shot(1.0)
        tracker.update(False, 1.1, 4.0)
        tracker.shot(3.0)
        self.assertEqual(tracker.update(False, 4.0, 4.0), 3.0)

    def test_measures_from_the_last_shot(self):
        tracker = CooldownTracker()
        tracker.update(True, 0.0, 4.0)
        tracker.shot(1.0)
        tracker.update(False, 1.1, 4.0)
        tracker.shot(3.0)
        tracker.update(True, 6.5, 4.0)
        tracker.update(False, 10.0, 4.0)
        self.assertEqual(tracker.update(False, 11.0, 4.0), 2.5)

    def test_reset_forgets_the_measurement(self):
        tracker = CooldownTracker()
        tracker.update(True, 9.0, 4.0)
        tracker.update(False, 10.0, 4.0)
        tracker.update(True, 13.0, 4.0)
        tracker.reset()
        tracker.update(True, 0.0, 4.0)
        self.assertEqual(tracker.update(False, 1.0, 4.0), 4.0)



def aiming(fill, seconds=1.0):
    return AimStatus(AIMING, fill, fill, seconds)


def aimed():
    return AimStatus(AIMED, 1.0, 1.0, 0.0)


class AimSmootherTest(unittest.TestCase):

    def setUp(self):
        self.smoother = AimSmoother()
        self.now = 0.0

    def feed(self, status, after=0.1):
        self.now += after
        return self.smoother.update(status, self.now)

    def test_first_tick_shows_the_raw_values(self):
        display = self.feed(aiming(0.5, 1.4))
        self.assertEqual((display.fill, display.percent, display.seconds, display.full), (0.5, 50, 1.4, False))

    def test_rising_fill_eases_in_with_a_quarter_second_time_constant(self):
        self.feed(aiming(0.5))
        display = self.feed(aiming(0.8))
        self.assertAlmostEqual(display.fill, 0.5 + 0.3 * (1 - math.exp(-0.4)))

    def test_small_jitter_is_damped(self):
        self.feed(aiming(0.6))
        fills = [self.feed(aiming(raw)).fill for raw in (0.63, 0.57, 0.63, 0.57, 0.63, 0.57)]
        self.assertTrue(all(abs(fill - 0.6) < 0.015 for fill in fills))

    def test_a_drop_of_more_than_8_points_snaps_to_the_raw_fill(self):
        self.feed(aiming(0.7))
        self.assertEqual(self.feed(aiming(0.3)).fill, 0.3)

    def test_a_drop_of_8_points_or_less_is_smoothed(self):
        self.feed(aiming(0.7))
        self.assertGreater(self.feed(aiming(0.63)).fill, 0.63)

    def test_percent_moves_in_5_percent_steps_below_95(self):
        self.assertEqual(self.feed(aiming(0.43)).percent, 45)
        self.assertEqual(self.feed(aiming(0.62), after=10.0).percent, 60)
        self.assertEqual(self.feed(aiming(0.96), after=10.0).percent, 96)

    def test_percent_waits_until_the_smoothed_value_is_3_points_away(self):
        self.feed(aiming(0.5))
        self.assertEqual(self.feed(aiming(0.52), after=10.0).percent, 50)
        self.assertEqual(self.feed(aiming(0.53), after=10.0).percent, 55)

    def test_percent_never_reads_100_before_the_gun_is_fully_aimed(self):
        self.assertEqual(self.feed(aiming(0.994)).percent, 99)

    def test_text_changes_at_most_every_0_2_seconds(self):
        self.feed(aiming(0.2, 3.0))
        display = self.feed(aiming(0.4, 2.5))
        self.assertEqual((display.percent, display.seconds), (20, 3.0))
        display = self.feed(aiming(0.4, 2.5))
        self.assertEqual(display.seconds, 2.5)
        self.assertGreater(display.percent, 20)

    def test_seconds_change_only_on_a_drop_of_0_15_or_more(self):
        self.feed(aiming(0.5, 2.0))
        self.assertEqual(self.feed(aiming(0.5, 1.9), after=0.2).seconds, 2.0)
        self.assertEqual(self.feed(aiming(0.5, 1.85), after=0.2).seconds, 1.85)

    def test_seconds_rise_only_on_a_rise_of_0_3_or_more(self):
        self.feed(aiming(0.5, 2.0))
        self.assertEqual(self.feed(aiming(0.5, 2.25), after=0.2).seconds, 2.0)
        self.assertEqual(self.feed(aiming(0.5, 2.3), after=0.2).seconds, 2.3)

    def test_fully_aimed_is_decided_from_the_raw_value_on_the_same_tick(self):
        self.feed(aiming(0.6))
        display = self.feed(AimStatus(AIMING, 0.996, 0.996, 0.01))
        self.assertEqual((display.full, display.settled, display.fill, display.percent, display.seconds),
                         (True, True, 1.0, 100, None))

    def test_leaves_aimed_after_two_ticks_below_97_seeded_from_raw(self):
        self.feed(aimed())
        self.assertTrue(self.feed(aiming(0.96)).full)
        display = self.feed(aiming(0.95, 0.1))
        self.assertFalse(display.full)
        self.assertEqual((display.fill, display.percent, display.seconds), (0.95, 95, 0.1))

    def test_dips_between_97_and_99_5_stay_aimed(self):
        self.feed(aimed())
        for raw in (0.98, 0.96, 0.975, 0.96, 0.99):
            display = self.feed(aiming(raw))
            self.assertEqual((display.full, display.fill, display.percent, display.seconds), (True, 1.0, 100, None))

    def test_a_shot_leaves_aimed_at_once(self):
        self.feed(aimed())
        display = self.feed(aiming(0.4, 1.8))
        self.assertEqual((display.full, display.fill, display.percent, display.seconds), (False, 0.4, 40, 1.8))

    def test_aimed_holds_green_0_3_seconds_then_fades_over_0_4(self):
        fades = [self.feed(aimed()).fade for _ in range(9)]
        self.assertEqual([round(fade, 2) for fade in fades], [0.0, 0.0, 0.0, 0.0, 0.25, 0.5, 0.75, 1.0, 1.0])

    def test_leaving_aimed_ends_the_fade(self):
        for _ in range(8):
            self.feed(aimed())
        self.feed(aiming(0.9))
        self.assertEqual(self.feed(aiming(0.9)).fade, 0.0)

    def test_accurate_mode_turns_green_at_100_and_fades_only_at_the_best_shot(self):
        factor = 0.6
        display = self.feed(AimStatus(ACCURATE, 0.7, 0.7 / factor, 0.3, limit=factor))
        self.assertEqual((display.full, display.settled, display.percent, display.seconds), (True, False, 117, 0.3))
        for _ in range(8):
            display = self.feed(AimStatus(ACCURATE, 0.8, 0.8 / factor, 0.2, limit=factor))
        self.assertEqual(display.fade, 0.0)
        display = self.feed(AimStatus(AIMED, 1.0, 1 / factor, 0.0, limit=factor))
        self.assertEqual((display.settled, display.fill, display.percent, display.seconds), (True, 1.0, 167, None))

    def test_cooling_gun_aimed_at_the_hot_circle_settles_at_the_limit(self):
        display = self.feed(AimStatus(AIMED, 0.6, 1.0, 0.0, limit=0.6, locked=True, cooldown=2.0))
        self.assertEqual((display.full, display.settled, display.fill, display.percent, display.cooldown),
                         (True, True, 0.6, 100, 2.0))

    def test_cooled_gun_starts_aiming_the_accurate_circle_at_once(self):
        self.feed(AimStatus(AIMED, 0.6, 1.0, 0.0, limit=0.6, locked=True, cooldown=0.1))
        display = self.feed(AimStatus(ACCURATE, 0.6, 1.0, 1.0, limit=0.6))
        self.assertEqual((display.full, display.settled, display.fill, display.seconds), (True, False, 0.6, 1.0))


if __name__ == '__main__':
    unittest.main()
