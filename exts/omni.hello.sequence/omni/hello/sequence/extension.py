import omni.ext
import omni.ui as ui
import carb 
import time
from pxr import Usd, Sdf, Tf, UsdGeom, UsdLux, Gf, UsdShade, Vt
import omni.kit.viewport.utility as vu
omni.kit.pipapi.install("GPUtil")
import GPUtil
import omni.timeline
from .menu import MenuEntry


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


# Define a callback function to handle timeline events
# def on_timeline_events(event):
# 	if event.type == omni.timeline.TimelineEventType.CURRENT_TIME_TICKED.value:
# 		# Difference between the last current time and the new one
# 		# Clamped to zero if it would be negative
# 		dt = event.payload['dt']
# 		# Retrieve the new current time
# 		current_time = event.payload['currentTime']
# 		carb.log_warn(f'Current time changed, dt = {dt}s, end of frame = {current_time}s')
# 	if event.type == omni.timeline.TimelineEventType.PLAY.value:
# 		carb.log_warn(f'Timeline is now playing')
# 	if event.type == omni.timeline.TimelineEventType.STOP.value:
# 		carb.log_warn(f'Timeline is now stopped')
# 	if event.type == omni.timeline.TimelineEventType.PAUSE.value:
# 		carb.log_warn(f'Timeline is now paused')
# 	if event.type == omni.timeline.TimelineEventType.START_TIME_CHANGED.value:
# 		start_time = event.payload['startTime']
# 		carb.log_warn(f'Timeline has a new start time: {start_time}s')
# 	# For more events, please consult the TimelineEventType documentation

# def on_time_update(event):
# 	# Frame duration (dt)
# 	frame_duration = event.payload['dt']
#     # End time of the frame
# 	end_time_of_frame = event.payload['currentTime']

# 	# Perform custom computations for the frame, such as simulation, animation, UI updates etc.


# # Define event callbacks
# def subsystem_A(event):
#     if event.type == omni.timeline.TimelineEventType.CURRENT_TIME_TICKED.value: 
#        tick = event.payload['tick']
#        carb.log_warn(f'Subsystem A was executed, tick index is {tick}')

# def subsystem_B(event):
#     if event.type == omni.timeline.TimelineEventType.CURRENT_TIME_TICKED.value: 
#        tick = event.payload['tick']
#        carb.log_warn(f'Subsystem B was executed, tick index is {tick}')



class Simulation:
    def __init__(self):
        carb.log_warn(f"Simulation Init")
        self.step = 0
        self.base_directory = "C:/Users/ovlaunch1/Downloads/ns_prod_converted/ns_00000_thd_"
        self.base_directory2 = "C:/Users/ovlaunch1/Downloads/wn_prod_converted/wn_00000_thd_0"

        stage = omni.usd.get_context().get_stage()
        world_path = Sdf.Path("/World")
        default_prim = UsdGeom.Xform.Define(stage, world_path)
       
        stage.SetDefaultPrim(default_prim.GetPrim())

        self.start_time = 0
        self.state = f"Uninitialized"

    def run_step(self):
        context: omni.usd.UsdContext = omni.usd.get_context()
        path = f"{self.base_directory}{self.step:0>2}_stl.usd"
        payload_prim: Usd.Prim = create_payload(context, Sdf.Path(f"/World/payload_prim_{self.step}"), path)
        payload_prim.Load()
        context2: omni.usd.UsdContext = omni.usd.get_context()
        path2 = f"{self.base_directory2}{self.step}_stl.usd"
        payload_prim2: Usd.Prim = create_payload(context2, Sdf.Path(f"/World/payload_prim2_{self.step}"), path2)
        payload_prim2.Load()

    async def async_on_update(self,dt):
        carb.log_warn(f"Upate Time Step")
        if self.state != f"Running":
            return
        if now.time() - self.start_time > 1000:
            self.start_time = now.time()
            self.run_step()
            self.step = self.step + 1
            
    def start(self):
        carb.log_warn(f"Simulation Start")
        self.state = f"Running"
        self.start_time = now.time() 
        self.step = 0
    def stop(self):
        carb.log_warn(f"Simulation Stop")                        
        self.state = f"Stopped"
        
    def close(self):
        self.stop()
        carb.log_warn(f"Simulation Closed")


class MenuEntryDemoLLM(MenuEntry):
    async def async_on_start(self):
        self.label.text = f"Start"

    async def async_on_update(self,dt):
        if self.simulation:
            await self.simulation.async_update(dt)

    async def async_on_stop():
        world_path = Sdf.Path("/World")
        for prim in stage.TraverseAll():
            prim.Unload()
            print_gpu_memory(str(prim))

    async def window_create_async(self):
        self.simulation = Simulation()

        # this is required to set self._window

        self._window = ui.Window(self.tool_name, width=500,height=500)
        with self._window.frame:
            with ui.VStack(style=GLOBAL_STYLE):
                self.label = ui.Label("Select Model", height=20)

                with ui.HStack():
                    ui.Button("Start", clicked_fn=on_start)
                    ui.Button("Stop", clicked_fn=on_stop)

                def on_start():
                    asyncio.ensure_future(self.async_on_start())
                        
                def on_stop():
                    asyncio.ensure_fiture(self.async_on_stop())
                        


class SequenceExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self._windows = [MenuEntryDemoLLM('LLM Demo', 'SA Demos/LLM Demo')]

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
        if self._windows:  # if even init
            for window in self._windows:
                window.on_update(e.payload["dt"])





