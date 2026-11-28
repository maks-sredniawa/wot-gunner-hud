from __future__ import division

import math

from constants import STANCE_DANCE_STATE
from items.vehicle_mechanics_types import VehicleMechanicKeys
from vehicles.mechanics.mechanic_helpers import getPlayerVehicleMechanicComponent

FIGHT = 'fight'
TURBO = 'turbo'


class StanceCharge(object):
    __slots__ = ('stance', 'energy', 'cost', 'rate', 'flags', 'active')

    def __init__(self, stance, energy, cost, rate, flags, active):
        self.stance = stance
        self.energy = energy
        self.cost = cost
        self.rate = rate
        self.flags = flags
        self.active = active


def gain_per_second(params, stance, flags):
    if params.gainEnergyTime <= 0:
        return 0.0
    points = 0.0
    if flags & STANCE_DANCE_STATE.ENERGY_TIMER_ON:
        points += params.gainTurboEnergyPoints if stance == TURBO else params.gainFightEnergyPoints
    if stance == TURBO and flags & STANCE_DANCE_STATE.ENERGY_SPD_BOOSTED:
        points += params.gainTurboEnergyBonusPoints
    return points / params.gainEnergyTime


def _stance_charge(state, stance, active_stance):
    params = state.params
    if stance == TURBO:
        energy, cost, running = state.energyTurbo, params.activeTurboCost, STANCE_DANCE_STATE.ACTIVE_ABILITY_TURBO
    else:
        energy, cost, running = state.energyFight, params.activeFightCost, STANCE_DANCE_STATE.ACTIVE_ABILITY_FIGHT
    if state.state & running:
        return None
    active = stance == active_stance
    flags = state.state if active else STANCE_DANCE_STATE.ENERGY_TIMER_ON
    return StanceCharge(stance, energy, cost, gain_per_second(params, stance, flags), state.state, active)


def charges_from_state(state):
    if state.state & (STANCE_DANCE_STATE.SWITCHING_STANCE | STANCE_DANCE_STATE.ENGINE_DEAD):
        return {}
    is_turbo = state.state & STANCE_DANCE_STATE.STANCE_MASK == STANCE_DANCE_STATE.STANCE_TURBO
    active_stance = TURBO if is_turbo else FIGHT
    return dict((stance, _stance_charge(state, stance, active_stance)) for stance in (FIGHT, TURBO))


def read_charges():
    component = getPlayerVehicleMechanicComponent(VehicleMechanicKeys.STANCE_DANCE)
    if component is None:
        return {}
    state = component.getMechanicState()
    return {} if state is None else charges_from_state(state)


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
        remaining = (charge.cost - charge.energy) / charge.rate
        if not charge.active:
            self.reset()
            return remaining
        basis = (charge.energy, charge.rate)
        if basis != self._basis:
            self._basis = basis
            self._since = now
        return max(0.0, remaining - (now - self._since))
