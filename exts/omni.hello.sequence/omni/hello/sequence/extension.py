import omni.ext
import omni.ui as ui
import carb 
import time
from pxr import Usd, Sdf, UsdGeom
import omni.kit.viewport.utility as vu
import omni.kit.pipapi
import GPUtil

def create_payload(context, prim_path, payload_path):
    stage = context.get_stage()
    payload_prim = stage.DefinePrim(prim_path, 'Xform')
    payload_prim.GetPayloads().AddPayload(payload_path)
    imageable_prim = UsdGeom.Imageable(payload_prim)
    visibility_attr = imageable_prim.GetVisibilityAttr()
    visibility_attr.Set(UsdGeom.Tokens.invisible)
    return payload_prim

def set_payloads_visibility(visibility):
    context = omni.usd.get_context()
    stage = context.get_stage()
    for prim in stage.Traverse():
        payloads = prim.GetPayloads()
        if payloads:
            imageable_prim = UsdGeom.Imageable(prim)
            if imageable_prim:
                visibility_attr = imageable_prim.GetVisibilityAttr()
                if visibility_attr:
                    visibility_attr.Set(visibility)
                    print(f"Set visibility of {prim.GetPath()} to {visibility}")
                    print(f"Current visibility of {prim.GetPath()}: {visibility_attr.Get()}")
                else:
                    print(f"Visibility attribute not found for {prim.GetPath()}")
            else:
                print(f"{prim.GetPath()} is not an imageable prim")

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
        base_directory="omniverse://localhost/Users/admin/std_res_prod/ns_prod_converted/ns_00000_thd_"
        # base_directory = "omniverse://localhost/Users/admin/LB_test/low_res_test/ns_converted/ns_00000_thd_"
        self._window = ui.Window("My Window", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                label = ui.Label("")

                def on_load_payloads():
                    label.text = "Loading payload..."
                    context: omni.usd.UsdContext = omni.usd.get_context()

                    for i in range(1, 32): 
                        val = f"{i:02}"
                        path = f"{base_directory}{val}_stl.usd"
                        
                        prim_path = f"/World/payload_prim_{val}" 
                        payload_prim: Usd.Prim = create_payload(context, Sdf.Path(prim_path), path)
                        payload_prim.Load()

                def on_set_visibility():
                    set_payloads_visibility( UsdGeom.Tokens.invisible)
                    label.text = "All prims set to invisible."

                def on_set_visible():
                    set_payloads_visibility( UsdGeom.Tokens.visible)
                    label.text = "All prims set to visible."    

                def on_reset():
                    for prim in stage.TraverseAll():
                        prim.Unload()
                        print_gpu_memory_unload(str(prim))

                with ui.HStack():
                    ui.Button("Reset", clicked_fn=on_reset)
                    ui.Button("Load Payloads", clicked_fn=on_load_payloads)
                    ui.Button("Set All Invisible", clicked_fn=on_set_visibility)
                    ui.Button("Set All Visible", clicked_fn=on_set_visible)


    def on_shutdown(self):
        print("[omni.hello.sequence] SequenceExtension shutdown")
