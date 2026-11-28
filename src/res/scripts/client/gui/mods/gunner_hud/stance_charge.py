from __future__ import division

import math

from constants import STANCE_DANCE_STATE
from items.vehicle_mechanics_types import VehicleMechanicKeys
from vehicles.mechanics.mechanic_helpers import getPlayerVehicleMechanicComponent

FIGHT = 'fight'
TURBO = 'turbo'


class StanceCharge(object):
    __slots__ = ('stance', 'energy', 'cost', 'rate', 'flags')

    def __init__(self, stance, energy, cost, rate, flags):
        self.stance = stance
        self.energy = energy
        self.cost = cost
        self.rate = rate
        self.flags = flags


def gain_per_second(params, stance, flags):
    if params.gainEnergyTime <= 0:
        return 0.0
    points = 0.0
    if flags & STANCE_DANCE_STATE.ENERGY_TIMER_ON:
        points += params.gainTurboEnergyPoints if stance == TURBO else params.gainFightEnergyPoints
    if stance == TURBO and flags & STANCE_DANCE_STATE.ENERGY_SPD_BOOSTED:
        points += params.gainTurboEnergyBonusPoints
    return points / params.gainEnergyTime


def charge_from_state(state):
    flags = state.state
    busy = (STANCE_DANCE_STATE.SWITCHING_STANCE | STANCE_DANCE_STATE.ACTIVE_ABILITY_MASK |
            STANCE_DANCE_STATE.ENGINE_DEAD)
    if flags & busy:
        return None
    params = state.params
    if flags & STANCE_DANCE_STATE.STANCE_MASK == STANCE_DANCE_STATE.STANCE_TURBO:
        stance, energy, cost = TURBO, state.energyTurbo, params.activeTurboCost
    else:
        stance, energy, cost = FIGHT, state.energyFight, params.activeFightCost
    return StanceCharge(stance, energy, cost, gain_per_second(params, stance, flags), flags)


def read_charge():
    component = getPlayerVehicleMechanicComponent(VehicleMechanicKeys.STANCE_DANCE)
    if component is None:
        return None
    state = component.getMechanicState()
    return None if state is None else charge_from_state(state)


def format_seconds(seconds):
    return '%d s' % int(math.ceil(seconds - 1e-6))


class ChargeCountdown(object):
    """Server energy updates arrive once per gain tick, so the countdown runs on between them."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._basis = None
        self._since = None

    def update(self, charge, now):
        if charge is None or charge.energy >= charge.cost or charge.rate <= 0:
            self.reset()
            return None
        basis = (charge.stance, charge.energy, charge.rate)
        if basis != self._basis:
            self._basis = basis
            self._since = now
        return max(0.0, (charge.cost - charge.energy) / charge.rate - (now - self._since))
