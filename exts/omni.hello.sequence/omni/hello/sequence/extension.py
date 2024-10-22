import omni.ext
import omni.ui as ui
import asyncio
from pxr import Sdf, UsdGeom

def create_payload(context, prim_path, payload_path):
    stage = context.get_stage()
    payload_prim = stage.DefinePrim(prim_path, 'Xform')
    payload_prim.GetPayloads().AddPayload(payload_path)
    imageable_prim = UsdGeom.Imageable(payload_prim)
    visibility_attr = imageable_prim.GetVisibilityAttr()
    visibility_attr.Set(UsdGeom.Tokens.invisible)
    return payload_prim

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

        base_directory = "omniverse://localhost/Users/admin/std_res_prod/ns_prod_converted/ns_00000_thd_"
        self.loaded_prims = []

        self._window = ui.Window("My Window", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                label = ui.Label("")

                async def on_load_payloads(): 
                    label.text = "Loading payloads..."
                    context = omni.usd.get_context()

                    for i in range(1, 32):
                        val = f"{i:02}"
                        path = f"{base_directory}{val}_stl.usd"
                        prim_path = f"/World/payload_prim_{val}"
                        create_payload(context, Sdf.Path(prim_path), path)
                        self.loaded_prims.append(prim_path)

                        if len(self.loaded_prims) % 5 == 0:
                            await asyncio.sleep(0.25)

                    if self.loaded_prims:
                        first_prim = omni.usd.get_context().get_stage().GetPrimAtPath(self.loaded_prims[0])
                        imageable_prim = UsdGeom.Imageable(first_prim)
                        if imageable_prim:
                            imageable_prim.MakeVisible()

                    label.text = "Payloads loaded as invisible."

                async def on_show_prims_sequentially():
                    label.text = "Starting visibility sequence..."
                    prims = [omni.usd.get_context().get_stage().GetPrimAtPath(path) for path in self.loaded_prims]
                    await sequential_visibility_change(prims, 0.5)
                    label.text = "All prims have been shown and hidden."

                def call_async(fn):
                    asyncio.ensure_future(fn())

                with ui.HStack():
                    ui.Button("Load Payloads", clicked_fn=lambda: call_async(on_load_payloads))
                    ui.Button("Show Prims Sequentially", clicked_fn=lambda: call_async(on_show_prims_sequentially))

    def on_shutdown(self):
        print("[omni.hello.sequence] SequenceExtension shutdown")
