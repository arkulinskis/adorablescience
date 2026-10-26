# api — client Module. Calls server functions and turns friendly server errors into LabError.
import anvil.server


class LabError(Exception):
    pass


def _check(result):
    if isinstance(result, dict) and "__oops__" in result:
        raise LabError(result["__oops__"])
    return result


def load(name, *args, **kwargs):
    """Quiet call (no Anvil spinner). Pages show their own wobbling-beaker loader."""
    try:
        return _check(anvil.server.call_s(name, *args, **kwargs))
    except anvil.server.SessionExpiredError:
        raise LabError("Your session expired. Reload the page to continue.")


def do(name, *args, **kwargs):
    """Call for button actions (shows Anvil's spinner while it runs)."""
    try:
        return _check(anvil.server.call(name, *args, **kwargs))
    except anvil.server.SessionExpiredError:
        raise LabError("Your session expired. Reload the page to continue.")
