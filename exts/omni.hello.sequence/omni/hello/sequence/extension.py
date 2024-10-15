import omni.ext
import omni.ui as ui
import carb 
import time
from pxr import Usd, Sdf, Tf, UsdGeom, UsdLux, Gf, UsdShade, Vt
import omni.kit.viewport.utility as vu
omni.kit.pipapi.install("GPUtil")
import GPUtil

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
            carb.log_warn(f"load {loop_val}: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB used")
def print_gpu_memory_unload(loop_val):
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            carb.log_warn(f"unload {loop_val}: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB used")

class SequenceExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        stage = omni.usd.get_context().get_stage()
        world_path = Sdf.Path("/World")
        default_prim = UsdGeom.Xform.Define(stage, world_path)

        stage.SetDefaultPrim(default_prim.GetPrim())
        base_directory = "omniverse://localhost/Users/admin/LB_test/low_res_test/ns_converted/ns_00000_thd_0"
        self._window = ui.Window("My Window", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                label = ui.Label("")
                
                def on_click():
                    label.text = f"start"
                    for i in range(1, 9):
                        context: omni.usd.UsdContext = omni.usd.get_context()
                        path = f"{base_directory}{i}_stl.usd"
                        payload_prim: Usd.Prim = create_payload(context, Sdf.Path("/World/payload_prim"), path)
                        payload_prim.Load()
                        print_gpu_memory(str(i))

                def on_reset():
                    world_path = Sdf.Path("/World")
                    for prim in stage.TraverseAll():
                        prim.Unload()
                        print_gpu_memory(str(prim))

                with ui.HStack():
                    ui.Button("Start", clicked_fn=on_click)
                    ui.Button("Reset", clicked_fn=on_reset)


    def on_shutdown(self):
        print("[omni.hello.sequence] SequenceExtension shutdown")
