from __future__ import annotations

import multiprocessing as mp
import queue
import time
from typing import TYPE_CHECKING, Literal

import xipppy as xp
from loguru import logger

if TYPE_CHECKING:
    from pathlib import Path

PARALLEL_PORT_INDEX = 4
USE_TCP = True


def _attempt_xipppy_connection(use_tcp: bool, out_q):
    try:
        with xp.xipppy_open(use_tcp=use_tcp):
            out_q.put(True)
            logger.info(
                "Connected to RippleNeuroMed Explorer Summit | {version_info}",
                version_info=xp.get_version(),
            )
    except xp.exception.XippPyException:
        out_q.put(False)
    except Exception:
        out_q.put(False)


def check_xipppy_connection(*, timeout_s: float = 10, use_tcp: bool = USE_TCP) -> bool:
    logger.info("Attempting to connect to RippleNeuroMed sEEG device...")

    ctx = mp.get_context("spawn")  # cross-platform, esp. Windows

    out_q = ctx.Queue(maxsize=1)
    p = ctx.Process(target=_attempt_xipppy_connection, args=(use_tcp, out_q), daemon=True)
    p.start()
    p.join(timeout_s)

    if p.is_alive():
        p.kill()
        p.join()
        logger.error("Failed to connect to RippleNeuroMed sEEG device!")
        return False

    try:
        return bool(out_q.get_nowait())
    except queue.Empty:
        logger.exception("Failed to connect to RippleNeuroMed sEEG device!")
        return False


def send_trigger(trigger_value: int = 0, *, use_tcp: bool = USE_TCP) -> None:
    with xp.xipppy_open(use_tcp=use_tcp):
        try:
            xp.digout(
                outputs=[PARALLEL_PORT_INDEX],
                values=[trigger_value],
            )
            logger.info(
                "Sent trigger {trigger} to parallel port",
                trigger=trigger_value,
            )
        except Exception:
            logger.warning(
                "Failed to send trigger {trigger} to parallel port",
                trigger=trigger_value,
            )


def send_pulse(
    on_value: int = 2**16 - 1,
    *,
    off_value: int = 0,
    duration_in_s: float = 0.015,
    use_tcp: bool = USE_TCP,
) -> None:
    with xp.xipppy_open(use_tcp=use_tcp):
        try:
            send_trigger(on_value, use_tcp=use_tcp)
            time.sleep(duration_in_s)
            send_trigger(off_value, use_tcp=use_tcp)

        except Exception:
            logger.warning(
                "Failed to send pulse to parallel port",
            )


def start_recording(*, operator_id: int = 129, filepath_base: Path, use_tcp: bool = USE_TCP, **kwargs) -> None:
    with xp.xipppy_open(use_tcp=use_tcp):
        if use_tcp:
            xp.add_operator(oper_addr=operator_id)
            logger.info("Added operator {operator_id}", operator_id=operator_id)

        filepath_base.parent.mkdir(exist_ok=True, parents=True)
        status, *_ = xp.trial(
            oper=operator_id,
            status="recording",
            file_name_base=str(filepath_base),
            **kwargs,
        )

        if status == "recording":
            logger.success(
                "sEEG recording started automatically with output saved at {filepath_base}",
                filepath_base=filepath_base,
            )
        else:
            logger.error(
                "sEEG recording was not started automatically. Start the recording manually in the Trellis GUI now, using the filepath: {filepath_base}",
                filepath_base=filepath_base,
            )


def stop_recording(*, operator_id: int = 129, use_tcp: bool = USE_TCP) -> None:
    with xp.xipppy_open(use_tcp=use_tcp):
        xp.trial(oper=operator_id, status="paused")
        status, *_ = xp.trial(oper=operator_id, status="stopped")
        if status == "stopped":
            logger.success("sEEG recording stopped.")
        else:
            logger.warning(
                "sEEG recording may not have been stopped automatically. Stop the recording manually in the Trellis GUI now.",
            )
