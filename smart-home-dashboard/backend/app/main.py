"""Smart Home Dashboard API.

Simulates lights, fans, thermostats, doors and cameras, and exposes them over
REST plus a WebSocket stream for real-time updates. Interactive docs live at
/docs (Swagger UI) and /redoc.
"""
from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .events import bus
from .readings_store import ReadingStore
from .routers import devices, history, rules, schedules
from .simulator import Simulator
from .store import DeviceStore, RuleStore, ScheduleStore

DESCRIPTION = """
REST API for a simulated smart home.

**Devices** — lights, fans, thermostats, doors and cameras with per-type state.
**Schedules** — run a device action at a wall-clock time on chosen weekdays.
**Rules** — WHEN a sensor (temperature / humidity / motion) crosses a
threshold, THEN apply an action to another device. Edge-triggered: a rule
fires once per crossing, not continuously.
**History** — sensor readings (temperature, humidity, power, motion) recorded
on every simulation tick.
**Realtime** — connect to `/ws` for `device_updated` / `rule_triggered` events.
"""


def create_app(
    db_path: str | Path = ":memory:",
    simulate: bool = True,
    tick_interval: float = 5.0,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.devices = DeviceStore(seed=True)
        app.state.schedules = ScheduleStore()
        app.state.rules = RuleStore()
        app.state.readings = ReadingStore(db_path)
        app.state.simulator = Simulator(
            app.state.devices,
            app.state.schedules,
            app.state.rules,
            app.state.readings,
            interval=tick_interval,
        )
        if simulate:
            await app.state.simulator.start()
        yield
        await app.state.simulator.stop()
        app.state.readings.close()

    app = FastAPI(
        title="Smart Home Dashboard API",
        description=DESCRIPTION,
        version="1.0.0",
        lifespan=lifespan,
        contact={"name": "Smart Home Sim"},
        license_info={"name": "MIT"},
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(devices.router)
    app.include_router(schedules.router)
    app.include_router(rules.router)
    app.include_router(history.router)

    @app.get("/api/health", tags=["meta"], summary="Health check")
    def health() -> dict:
        return {"status": "ok"}

    @app.websocket("/ws")
    async def websocket(ws: WebSocket) -> None:
        """Streams events: `device_updated`, `rule_triggered`."""
        await ws.accept()
        queue = bus.subscribe()
        try:
            # Send the current snapshot first so clients can hydrate.
            snapshot = [d.model_dump(mode="json") for d in ws.app.state.devices.list()]
            await ws.send_text(json.dumps({"type": "snapshot", "data": snapshot}))
            while True:
                event = await queue.get()
                await ws.send_text(json.dumps(event))
        except WebSocketDisconnect:
            pass
        finally:
            bus.unsubscribe(queue)

    return app


app = create_app(db_path=Path(__file__).resolve().parent.parent / "smarthome.db")
