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

# def create_payload(usd_context: omni.usd.UsdContext, path_to: Sdf.Path, asset_path: str) -> Usd.Prim:
#     omni.kit.commands.execute("CreatePayload",
#         usd_context=usd_context,
#         path_to=path_to,
#         asset_path=asset_path, 
#     )
#     return usd_context.get_stage().GetPrimAtPath(path_to)

def create_payload(context, prim_path, payload_path):
    """Create a payload prim in the USD stage."""
    stage = context.get_stage()
    
    payload_prim = stage.DefinePrim(prim_path, 'Xform')
    payload_prim.GetPayloads().AddPayload(payload_path)
    imageable_prim = UsdGeom.Imageable(payload_prim)
    visibility_attr = imageable_prim.GetVisibilityAttr()
    visibility_attr.Set(UsdGeom.Tokens.invisible)
    return payload_prim

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
        self.last_valid_frame = 400

        self.start_frame = 10
        self.num_to_batch = 6
        self.batch_step = 1

        self.path = None
        self.path2 = None

        self.old_payload_prim = None
        self.payload_prim = None
        self.old_payload_prim2 = None
        self.payload_prim2 = None

        self.base_directory = "E:/fowler_keynote/awn_converted/awn_00000_thd_"
        self.base_directory2 = "E:/fowler_keynote/awn_converted/awn_00000_thd_"

        self.stage = omni.usd.get_context().get_stage()
        world_path = Sdf.Path("/World")
        default_prim = UsdGeom.Xform.Define(self.stage, world_path)
        self.stage.SetDefaultPrim(default_prim.GetPrim())

    def getstate(self):
        return self.state

    async def async_run_step_load(self):
        # This function will be a visibility binstead of loading step
        context: omni.usd.UsdContext = omni.usd.get_context()
        
        self.path = f"{self.base_directory}{(self.step):0>3}_stl.usd"
        #self.payload_prim: Usd.Prim = create_payload(context, Sdf.Path(f"/World/payload_prim_{self.step+self.batch_counter}"), self.path)
       
        context2: omni.usd.UsdContext = omni.usd.get_context()
        
        self.path2 = f"{self.base_directory2}{(self.step):0>3}_stl.usd"
        #self.payload_prim2: Usd.Prim = create_payload(context2, Sdf.Path(f"/World/payload_prim2_{self.step+self.batch_counter}"), self.path2)
    
        first_prim_ns = context.get_stage().GetPrimAtPath(Sdf.Path(f"/World/payload_prim_{self.step}"))
        first_prim_wn = context2.get_stage().GetPrimAtPath(Sdf.Path(f"/World/payload_prim2_{self.step}"))
                   
        carb.log_warn(f"Got to changing the visibility of the first item at {self.step}")
        imageable_prim_ns = UsdGeom.Imageable(first_prim_ns)
        if imageable_prim_ns:
            carb.log_warn(f"Just about to change imageable_prim_ns visibility at {self.step}")

            imageable_prim_ns.MakeVisible()

        imageable_prim_wn = UsdGeom.Imageable(first_prim_wn)
        if imageable_prim_wn:
            imageable_prim_wn.MakeVisible()

        for hist in range(2,3): # Don't get the one right behind you...
            foo_prim_path3 = Sdf.Path(f"/World/payload_prim_{self.step-hist}")
            foo_prim_path4 = Sdf.Path(f"/World/payload_prim2_{self.step-hist}")
            
            check_for_valid_prim3 = self.stage.GetPrimAtPath(foo_prim_path3)
            check_for_valid_prim4 = self.stage.GetPrimAtPath(foo_prim_path4)
            
            if (check_for_valid_prim3 is not None):
                self.stage.RemovePrim(foo_prim_path3)

            if (check_for_valid_prim4 is not None):    
                self.stage.RemovePrim(foo_prim_path4)

    async def async_batch_load(self):
        carb.log_warn(f"In batch loading function at step:{self.step}")
        for j in range(self.step, self.step+self.num_to_batch):
            
            self.path = f"{self.base_directory}{j:0>3}_stl.usd"
            self.path2 = f"{self.base_directory2}{j:0>3}_stl.usd"
            
            
            if (self.step < self.num_to_batch):
                    
                #await asyncio.sleep(0.1)

                context: omni.usd.UsdContext = omni.usd.get_context()
                
                self.payload_prim: Usd.Prim = create_payload(context, Sdf.Path(f"/World/payload_prim_{j}"), self.path)
    
                context2: omni.usd.UsdContext = omni.usd.get_context()
                
                self.payload_prim2: Usd.Prim = create_payload(context2, Sdf.Path(f"/World/payload_prim2_{j}"), self.path2)
        
                carb.log_warn(f"Batch loading initial set:{j}")


                first_prim_ns = context.get_stage().GetPrimAtPath(Sdf.Path(f"/World/payload_prim_{j}"))
                first_prim_wn = context.get_stage().GetPrimAtPath(Sdf.Path(f"/World/payload_prim2_{j}"))
                if j is self.step:
                    carb.log_warn(f"Got to changing the visibility of the first item at {self.step}")
                    imageable_prim_ns = UsdGeom.Imageable(first_prim_ns)
                    if imageable_prim_ns:
                        carb.log_warn(f"Just about to change imageable_prim_ns visibility at {self.step}")

                        imageable_prim_ns.MakeVisible()

                    imageable_prim_wn = UsdGeom.Imageable(first_prim_wn)
                    if imageable_prim_wn:
                        imageable_prim_wn.MakeVisible()



            else:
  
                #await asyncio.sleep(0.1)

                foo_prim_path = Sdf.Path(f"/World/payload_prim_{self.step}")
                foo_prim_path2 = Sdf.Path(f"/World/payload_prim2_{self.step}")
                check_for_valid_prim = self.stage.GetPrimAtPath(foo_prim_path)
                check_for_valid_prim2 = self.stage.GetPrimAtPath(foo_prim_path2)
                #carb.log_warn(f"${j} self.path=${self.path}  check_for_prim=${foo_prim_path}")
                if (check_for_valid_prim is not None):
                    context: omni.usd.UsdContext = omni.usd.get_context()
                    
                    self.payload_prim: Usd.Prim = create_payload(context, Sdf.Path(f"/World/payload_prim_{j}"), self.path)
        
            
                if (check_for_valid_prim2 is not None):
                    context2: omni.usd.UsdContext = omni.usd.get_context()
                    self.payload_prim2: Usd.Prim = create_payload(context2, Sdf.Path(f"/World/payload_prim2_{j}"), self.path2)
        
                    carb.log_warn(f"Batch loading: ${j}")


                # for hist in range(1,self.num_to_batch):
                #     foo_prim_path3 = Sdf.Path(f"/World/payload_prim_{self.step-hist}")
                #     foo_prim_path4 = Sdf.Path(f"/World/payload_prim2_{self.step-hist}")
                    
                #     check_for_valid_prim3 = self.stage.GetPrimAtPath(foo_prim_path3)
                #     check_for_valid_prim4 = self.stage.GetPrimAtPath(foo_prim_path4)
                    
                #     if (check_for_valid_prim3 is not None):
                #         self.stage.RemovePrim(foo_prim_path3)

                #     if (check_for_valid_prim4 is not None):    
                #         self.stage.RemovePrim(foo_prim_path4)


    async def async_batch_unload(self):
            carb.log_warn(f"In batch unloading function at step:${self.step}")
            for j in range(self.step-2*self.num_to_batch, self.step-self.num_to_batch):
                
                self.path = f"{self.base_directory}{j:0>3}_stl.usd"
                self.path2 = f"{self.base_directory2}{j:0>3}_stl.usd"
                
                foo_prim_path = Sdf.Path(f"/World/payload_prim_{j}")
                foo_prim_path2 = Sdf.Path(f"/World/payload_prim2_{j}")
                
                check_for_valid_prim = self.stage.GetPrimAtPath(foo_prim_path)
                check_for_valid_prim2 = self.stage.GetPrimAtPath(foo_prim_path2)
                
                if (check_for_valid_prim is not None):
                    self.stage.RemovePrim(foo_prim_path)

                if (check_for_valid_prim2 is not None):    
                    self.stage.RemovePrim(foo_prim_path2)
                
                
                    

    async def async_run_step_unload(self):
 
        carb.log_warn(f"Unloading steps:${self.step-1}")
 
        context: omni.usd.UsdContext = omni.usd.get_context()
        
        first_prim_ns = context.get_stage().GetPrimAtPath(Sdf.Path(f"/World/payload_prim_{self.step-1}"))
        first_prim_wn = context.get_stage().GetPrimAtPath(Sdf.Path(f"/World/payload_prim2_{self.step-1}"))
        

        imageable_prim_ns = UsdGeom.Imageable(first_prim_ns)
        if imageable_prim_ns:
            imageable_prim_ns.MakeInvisible()

        imageable_prim_wn = UsdGeom.Imageable(first_prim_wn)
        if imageable_prim_wn:
            imageable_prim_wn.MakeInvisible()

    async def async_on_update(self,dt):
        # test
        #carb.log_warn(f"Upate Time Step")
        if self.state != f"Running":
            return
        if self.step > self.last_valid_frame:
            # for now we are going to loop, for dev reasons
            # When we are done, switch to just return
            await self.async_run_step_unload()
            self.step = self.start_frame
        time_difference = time.time() - self.start_time
        if time_difference > 1:  # Delay between frames is here
            if self.step == self.start_frame:
                await self.async_batch_load()
                
            #if self.step > 1:
                #await self.async_run_step_unload()  # unloads the existing payload-prim
            if self.step > self.start_frame:
                if self.step%(self.num_to_batch - self.num_to_batch/2)== 0:
                    await self.async_batch_load()
                #await self.async_run_step_unload()
            #if self.step > self.num_to_batch + 1: # just need to be bigger than the num_to_batch for now
                #if self.step%self.num_to_batch == 0:
                    #await self.async_batch_unload()
            carb.log_warn(f"time_difference={time_difference}")
            self.start_time = time.time()
            await self.async_run_step_unload()
            await self.async_run_step_load()
            self.step = self.step + 1
            self.batch_counter = 0


    def start(self):
        carb.log_warn(f"Simulation Start")
        # Get the USD context
        #context = Usd.Context.Get()

# Clear the GPU memory cache
        
        self.state = f"Running"
        self.start_time = time.time() 
        self.step = self.start_frame

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





