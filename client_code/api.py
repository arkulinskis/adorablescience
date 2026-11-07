"""Server calls for pages that show their own error state: load(name, ...) returns the reply, or raises LabError
with the server's friendly message ({"__oops__": msg} from server_code/Lab.py @api). router.show() turns a LabError
raised while a page opens into the friendly "Oops" page. Button actions use state.call (a toast instead)."""
import anvil.server


class LabError(Exception):
    pass


def _check(result):
    if isinstance(result, dict) and "__oops__" in result:
        raise LabError(result["__oops__"])
    return result


def load(name, *args, **kwargs):
    """A call with Anvil's spinner (the bubbling beaker). Friendly problems raise LabError."""
    try:
        return _check(anvil.server.call(name, *args, **kwargs))
    except LabError:
        raise
    except Exception as e:  # (the validator's stubs have no anvil.server.SessionExpiredError)
        if type(e).__name__ == "SessionExpiredError":
            raise LabError("Your session expired. Reload the page to continue.")
        raise
