import omni.ext # type: ignore
import omni.ui as ui # type: ignore
import carb  # type: ignore
import time
import datetime
from pxr import Usd, Sdf, Tf, UsdGeom, UsdLux, Gf, UsdShade, Vt # type: ignore
import omni.kit.viewport.utility as vu # type: ignore
omni.kit.pipapi.install("GPUtil")
import GPUtil # type: ignore
import omni.timeline # type: ignore
from .menu import MenuEntry
import asyncio
from typing import Union

def create_payload(usd_context: omni.usd.UsdContext, path_to: Sdf.Path, asset_path: str) -> Usd.Prim:
    omni.kit.commands.execute("CreatePayload",
        usd_context=usd_context,
        path_to=path_to,
        asset_path=asset_path, 
    )
    return usd_context.get_stage().GetPrimAtPath(path_to)



def print_gpu_memory(loop_val):
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            carb.log_warn(f"load {loop_val}: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB used  Chris Fowler")
def print_gpu_memory_unload(loop_val):
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            carb.log_warn(f"unload {loop_val}: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB used")
#aaa
class Simulation:
    def __init__(self):
        carb.log_warn(f"Simulation Init")
        self.step = 1
        self.start_time = 0
        self.state = f"Uninitialized"
        self.last_valid_frame = 5

        self.path = None
        self.path2 = None

        self.old_payload_prim = None
        self.payload_prim = None
        self.old_payload_prim2 = None
        self.payload_prim2 = None

        self.base_directory = "C:/Users/ovlaunch1/Downloads/ns_prod_converted/ns_00000_thd_"
        self.base_directory2 = "C:/Users/ovlaunch1/Downloads/wn_prod_converted/wn_00000_thd_0"

        self.stage = omni.usd.get_context().get_stage()
        world_path = Sdf.Path("/World")
        default_prim = UsdGeom.Xform.Define(self.stage, world_path)
        self.stage.SetDefaultPrim(default_prim.GetPrim())

    def getstate(self):
        return self.state

    async def async_run_step_load(self):
        context: omni.usd.UsdContext = omni.usd.get_context()
        self.path = f"{self.base_directory}{self.step:0>2}_stl.usd"
        self.payload_prim: Usd.Prim = create_payload(context, Sdf.Path(f"/World/payload_prim_{self.step}"), self.path)
        self.payload_prim.Load()
        context2: omni.usd.UsdContext = omni.usd.get_context()
        self.path2 = f"{self.base_directory2}{self.step}_stl.usd"
        self.payload_prim2: Usd.Prim = create_payload(context2, Sdf.Path(f"/World/payload_prim2_{self.step}"), self.path2)
        self.payload_prim2.Load()




    async def async_run_step_unload(self):
        #context: omni.usd.UsdContext = omni.usd.get_context()
        #path = f"{self.base_directory}{self.step:0>2}_stl.usd"
        self.payload_prim.Unload()
        mystep = self.step - 1
        carb.log_warn(f'Removing: /World/payload_prim_{mystep}') 
        foo_prim_path = Sdf.Path(f"/World/payload_prim_{mystep}")
        self.stage.RemovePrim(foo_prim_path)
        #context2: omni.usd.UsdContext = omni.usd.get_context()
        #path2 = f"{self.base_directory2}{self.step}_stl.usd"
        self.payload_prim2.Unload()
        foo_prim_path = Sdf.Path(f"/World/payload_prim2_{mystep}")
        self.stage.RemovePrim(foo_prim_path)

    async def async_on_update(self,dt):
        # test
        #carb.log_warn(f"Upate Time Step")
        if self.state != f"Running":
            return
        if self.step > self.last_valid_frame:
            # for now we are going to loop, for dev reasons
            # When we are done, switch to just return
            await self.async_run_step_unload()
            self.step = 1


        time_difference = time.time() - self.start_time
        if time_difference > 2.0:
            if self.step > 1:
                await self.async_run_step_unload()  # unloads the existing payload-prim
            carb.log_warn(f"time_difference={time_difference}")
            self.start_time = time.time()
            await self.async_run_step_load()
            self.step = self.step + 1


    def start(self):
        carb.log_warn(f"Simulation Start")
        self.state = f"Running"
        self.start_time = time.time() 
        self.step = 1

    def stop(self):
        carb.log_warn(f"Simulation Stop")                        
        self.state = f"Stopped"
        
    def close(self):  # This is not serviced from window yet
        carb.log_warn(f"Simulation Closed")
        self.stop()

#bbb
class LBPMUNCDemo(MenuEntry):
    async def async_on_start(self):
        if self.simulation:
            self.simulation.start()

    async def async_on_update(self,dt):
        if self.simulation: 
            await self.simulation.async_on_update(dt)
            self.label.text = self.simulation.getstate()
        else:
            self.label.text = f"Simulation Not Created"

    def update(self,dt):
        #carb.log_warn(f" calling update(self,dt) in LBPMUNCDemo class")
        asyncio.ensure_future(self.async_on_update(dt))

    async def async_on_stop(self):
        if self.simulation:
            self.simulation.stop()


    async def window_create_async(self):
        self.simulation = Simulation()

        # this is required to set self._window

        self._window = ui.Window(self.tool_name, width=500,height=500)
        with self._window.frame:
            with ui.VStack():   #GLOBAL_STYLE):
                self.label = ui.Label("?????????", height=20)

                def on_start():
                    asyncio.ensure_future(self.async_on_start())
                        
                def on_stop():
                    asyncio.ensure_future(self.async_on_stop())

                with ui.HStack( height=30):
                    ui.Button("Start", clicked_fn=on_start)
                    ui.Button("Stop", clicked_fn=on_stop)

    def window_close(self):
        MenuEntry.window_close(self)
        if self.simulation:
            self.simulation.close()
            self.simulation = None                    

#ccc
class SequenceExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self._windows = [LBPMUNCDemo('Lattice Boltzmann Porous Medium Demo', 'Lattice Boltzmann Porous Medium Demo/Show Window')]
        # App provides common event bus. It is event queue which is popped every update (frame).
        self._bus = omni.kit.app.get_app().get_update_event_stream()
        self._sub = self._bus.create_subscription_to_push(self.on_update, name=f"SequenceExtension OnUpdate")

    def on_shutdown(self):
        self._bus = None
        self._sub = None
        for window in self._windows:
            window.shutdown()
        self._windows = None
        # Explicitly shut down window
        # Need callback for visibility change

    # This event fires very frequently. A callback with long-running code will block the
    # UI and make the app unresponsive.
    def on_update(self, e: carb.events.IEvent):
        # carb.log_warn(f"def on_update in SequenceExtension")
        if self._windows:  # if even init
            for window in self._windows:
                #carb.log_warn(f"def on_update within window for loop 156")
                window.on_update(e.payload["dt"])





