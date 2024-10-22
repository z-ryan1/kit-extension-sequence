import omni.ext
import omni.ui as ui
import asyncio
from pxr import Sdf, UsdGeom

"""
Create a payload prim in the USD stage.
Args:
    context: The current USD context.
    prim_path: The path where the payload prim will be created.
    payload_path: The path to the payload USD file.
Returns:
    The created payload prim.
"""
def create_payload(context, prim_path, payload_path):
    stage = context.get_stage()
    payload_prim = stage.DefinePrim(prim_path, 'Xform')
    payload_prim.GetPayloads().AddPayload(payload_path)
    imageable_prim = UsdGeom.Imageable(payload_prim)
    visibility_attr = imageable_prim.GetVisibilityAttr()
    visibility_attr.Set(UsdGeom.Tokens.invisible)
    return payload_prim

"""
Transition from the current prim to the next prim.

Args:
    current_prim: The prim currently visible.
    next_prim: The prim to be made visible next.
    overlap_duration: The duration to wait before transitioning.
"""
async def smooth_transition(current_prim, next_prim, overlap_duration):
    if current_prim and next_prim:
        imageable_prim = UsdGeom.Imageable(current_prim)
        if imageable_prim:
            imageable_prim.MakeInvisible()
            current_prim.Unload()

    if next_prim:
        imageable_prim = UsdGeom.Imageable(next_prim)
        if imageable_prim:
            imageable_prim.MakeVisible()
            await asyncio.sleep(overlap_duration)

"""
Sequentially change visibility for a list of prims.

Args:
    prims: List of prims to change visibility for.
    overlap_duration: The duration each prim remains visible before transitioning.
"""
async def sequential_visibility_change(prims, overlap_duration):
    for i in range(len(prims) - 1):
        current_prim = prims[i]
        next_prim = prims[i + 1]
        await smooth_transition(current_prim, next_prim, overlap_duration)

class SequenceExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        stage = omni.usd.get_context().get_stage()
        world_path = Sdf.Path("/World")
        default_prim = UsdGeom.Xform.Define(stage, world_path)
        stage.SetDefaultPrim(default_prim.GetPrim())

        base_directory = "omniverse://localhost/Users/admin/std_res_prod/wn_prod_converted/wn_00000_thd_"
        self.loaded_prims = [] 

        self._window = ui.Window("My Window", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                label = ui.Label("")

                async def on_load_payloads(): 
                    """
                        Load payloads into the stage and set them to invisible.
                    """
                    label.text = "Loading payloads..."
                    context = omni.usd.get_context()

                    for i in range(1, 32):
                        val = f"{i:02}"
                        path = f"{base_directory}{val}_stl.usd"
                        prim_path = f"/World/payload_prim_{val}"
                        create_payload(context, Sdf.Path(prim_path), path)
                        self.loaded_prims.append(prim_path)

                        if len(self.loaded_prims) % 5 == 0:  # Load 5 prims at a time.
                            await asyncio.sleep(0.25)  # Simulate loading delay.

                    # Make the first prim visible after loading.
                    if self.loaded_prims:
                        first_prim = omni.usd.get_context().get_stage().GetPrimAtPath(self.loaded_prims[0])
                        imageable_prim = UsdGeom.Imageable(first_prim)
                        if imageable_prim:
                            imageable_prim.MakeVisible()

                    label.text = "Payloads loaded as invisible."

                """
                Show prims sequentially, making each visible for a set duration.
                """
                async def on_show_prims_sequentially():
                    label.text = "Starting visibility sequence..."
                    prims = [omni.usd.get_context().get_stage().GetPrimAtPath(path) for path in self.loaded_prims]
                    await sequential_visibility_change(prims, 0.5)  # Change visibility with a 0.5s overlap.
                    label.text = "All prims have been shown and hidden."

                """
                Helper function to call an async function in the event loop.

                Args:
                    fn: The async function to call.
                """
                def call_async(fn):
                    asyncio.ensure_future(fn())  # Ensure the function runs asynchronously.

                with ui.HStack():
                    ui.Button("Load Payloads", clicked_fn=lambda: call_async(on_load_payloads))
                    ui.Button("Show Prims Sequentially", clicked_fn=lambda: call_async(on_show_prims_sequentially))

    def on_shutdown(self):
        print("[omni.hello.sequence] SequenceExtension shutdown")
