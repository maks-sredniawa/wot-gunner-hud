import math

from debug_utils import LOG_CURRENT_EXCEPTION, LOG_NOTE
from gui.battle_control import avatar_getter
from gui.battle_control.controllers.chat_cmd_ctrl import ChatCommandsController
from messenger.ext import isBattleChatEnabled
from messenger.m_constants import PROTO_TYPE
from messenger.proto import proto_getter

from . import schedule

TEAM_CHANNEL = 0


class _TeamChat(object):

    @proto_getter(PROTO_TYPE.BW_CHAT2)
    def proto(self):
        return None

    def try_send(self, text):
        arena_chat = self.proto.arenaChat
        if not isBattleChatEnabled() or arena_chat.isBroadcastInCooldown():
            LOG_NOTE('[gunner_hud] magazine line skipped: team chat off or in cooldown')
            return False
        arena_chat.broadcast(text, TEAM_CHANNEL)
        return True


def _seconds(value):
    return int(math.ceil(max(0.0, value)))


def _last_shell_text(slots, loaded, pending):
    seconds = _seconds(schedule.full_in(slots))
    reachable = loaded + len(pending)
    if reachable == len(slots):
        return 'full in %d s' % seconds
    return '%d/%d in %d s' % (reachable, len(slots), seconds)


def magazine_text(slots):
    loaded = sum(1 for slot in slots if slot.state == schedule.LOADED)
    pending = [slot for slot in slots if slot.state in (schedule.LOADING, schedule.QUEUED)]
    if loaded == 0:
        if not pending:
            return None
        return 'Magazine 0/%d, first shell %d s, %s' % (len(slots), _seconds(pending[0].ready_in),
                                                         _last_shell_text(slots, loaded, pending))
    text = 'Magazine %d/%d' % (loaded, len(slots))
    if pending:
        text += ', ' + _last_shell_text(slots, loaded, pending)
    return text


_METHOD = 'sendReloadingCommand'
_hook = {'original': None, 'original_raw': None, 'get_slots': None, 'is_on': None, 'active': False}
_team_chat = _TeamChat()


def _send_magazine_status():
    if not _hook['is_on']() or not avatar_getter.isPlayerOnArena() or not avatar_getter.isVehicleAlive():
        return False
    slots = _hook['get_slots']()
    text = magazine_text(slots) if slots else None
    return bool(text) and _team_chat.try_send(text)


def _send_reloading_command(self):
    if _hook['active']:
        try:
            if _send_magazine_status():
                return
        except Exception:
            LOG_CURRENT_EXCEPTION()
    _hook['original'](self)


def _owns_method():
    return ChatCommandsController.__dict__.get(_METHOD) is _send_reloading_command


def install(get_slots, is_on):
    _hook.update(get_slots=get_slots, is_on=is_on, active=True)
    # Once wrapped, our function stays in the call chain even under another mod's wrapper, so wrapping again would loop.
    if _hook['original'] is not None:
        return
    _hook['original'] = getattr(ChatCommandsController, _METHOD)
    _hook['original_raw'] = ChatCommandsController.__dict__.get(_METHOD)
    setattr(ChatCommandsController, _METHOD, _send_reloading_command)


def uninstall():
    _hook.update(get_slots=None, is_on=None, active=False)
    if _hook['original'] is None or not _owns_method():
        return
    if _hook['original_raw'] is None:
        delattr(ChatCommandsController, _METHOD)
    else:
        setattr(ChatCommandsController, _METHOD, _hook['original_raw'])
    _hook.update(original=None, original_raw=None)
