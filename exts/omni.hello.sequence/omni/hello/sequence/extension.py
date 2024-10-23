import omni.ext
import omni.ui as ui
import carb
import asyncio
from pxr import Sdf, UsdGeom, UsdShade, Gf

from pxr import Usd, Sdf, UsdGeom

def create_perspective_35mm_camera(stage: Usd.Stage, prim_path: str="/World/MyPerspCam") -> UsdGeom.Camera:
    camera_path = Sdf.Path(prim_path)
    usd_camera: UsdGeom.Camera = UsdGeom.Camera.Define(stage, camera_path)
    usd_camera.CreateProjectionAttr().Set(UsdGeom.Tokens.perspective)
    usd_camera.CreateFocalLengthAttr().Set(35)
    # Set a few other common attributes too.
    usd_camera.CreateHorizontalApertureAttr().Set(20.955)
    usd_camera.CreateVerticalApertureAttr().Set(15.2908)
    usd_camera.CreateClippingRangeAttr().Set((0.1,100000))
    translate_op = usd_camera.AddTranslateOp()
    translate_op.Set(value=(123.43060339597056, 89.90841433124608, 1490.475525864984))

    return usd_camera


def create_material(stage, mat_name):
    """Create a red material."""
    material_path = f"/World/{mat_name}"
    
    # Create a material
    material = UsdShade.Material.Define(stage, Sdf.Path(material_path))
    shader = UsdShade.Shader.Define(stage, Sdf.Path(material_path + "/Shader"))
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set((1.0, 0.0, 0.0))  # Red color
    
    # Bind the shader to the material
    material.CreateSurfaceOutput().ConnectToSource(shader.CreateOutput('surface', Sdf.ValueTypeNames.Token))
    
    return material

def create_payload(context, prim_path, payload_path):
    """Create a payload prim in the USD stage."""
    stage = context.get_stage()
    payload_prim = stage.DefinePrim(prim_path, 'Xform')
    payload_prim.GetPayloads().AddPayload(payload_path)
    imageable_prim = UsdGeom.Imageable(payload_prim)
    visibility_attr = imageable_prim.GetVisibilityAttr()
    visibility_attr.Set(UsdGeom.Tokens.invisible)
    return payload_prim

async def smooth_transition(current_ns, current_wn, overlap_duration):
    """Transition from the current prim to the next prim."""
    if current_ns and current_wn:
        imageable_ns = UsdGeom.Imageable(current_ns)
        imageable_wn = UsdGeom.Imageable(current_wn)

        # Make both visible
        if imageable_ns:
            imageable_ns.MakeVisible()
        if imageable_wn:
            imageable_wn.MakeVisible()

        # Wait for the overlap duration
        await asyncio.sleep(overlap_duration)

        # Optionally hide both after waiting
        if imageable_ns:
            imageable_ns.MakeInvisible()
        if imageable_wn:
            imageable_wn.MakeInvisible()

async def sequential_visibility_change(prims_ns, prims_wn, overlap_duration):
    """Sequentially change visibility for a list of prims."""
    for current_ns, current_wn in zip(prims_ns, prims_wn):
        await smooth_transition(current_ns, current_wn, overlap_duration)

class SequenceExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        stage = omni.usd.get_context().get_stage()
        world_path = Sdf.Path("/World")
        default_prim = UsdGeom.Xform.Define(stage, world_path)
        stage.SetDefaultPrim(default_prim.GetPrim())

        base_directory_wn = "omniverse://localhost/Users/admin/std_res_prod/wn_prod_converted/wn_00000_thd_"
        base_directory_ns = "omniverse://localhost/Users/admin/std_res_prod/ns_prod_converted/ns_00000_thd_"

        self.loaded_prims_wn = [] 
        self.loaded_prims_ns = [] 

        cam_path = default_prim.GetPath().AppendPath("MyPerspCam")
        camera = create_perspective_35mm_camera(stage, cam_path)

        self._window = ui.Window("My Window", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                label = ui.Label("")

                async def on_load_payloads(): 
                    label.text = "Loading payloads..."
                    context = omni.usd.get_context()
                    
                    # Create a red material for NS prims
                    red_material = create_material(context.get_stage(), "RedMaterial")

                    for i in range(1, 6):
                        val = f"{i:02}"
                        path_wn = f"{base_directory_wn}{val}_stl.usd"
                        prim_path_wn = f"/World/payload_prim_wn_{val}"
                        create_payload(context, Sdf.Path(prim_path_wn), path_wn)
                        self.loaded_prims_wn.append(prim_path_wn)

                        path_ns = f"{base_directory_ns}{val}_stl.usd"
                        prim_path_ns = f"/World/payload_prim_ns_{val}"
                        create_payload(context, Sdf.Path(prim_path_ns), path_ns)
                        self.loaded_prims_ns.append(prim_path_ns)

                        node_path = prim_path_ns + "/node_/mesh_"
                        ns_prim = context.get_stage().GetPrimAtPath(Sdf.Path(node_path))
                        material_binding_api = UsdShade.MaterialBindingAPI(ns_prim)

                        material_binding_api.Bind(red_material)

                        if len(self.loaded_prims_wn) % 5 == 0:  # Load 5 prims at a time.
                            await asyncio.sleep(0.25)  # Simulate loading delay.

                    # Make the first prim visible after loading.
                    if self.loaded_prims_ns and self.loaded_prims_wn:
                        first_prim_ns = context.get_stage().GetPrimAtPath(self.loaded_prims_ns[0])
                        first_prim_wn = context.get_stage().GetPrimAtPath(self.loaded_prims_wn[0])


                        imageable_prim_ns = UsdGeom.Imageable(first_prim_ns)
                        if imageable_prim_ns:
                            imageable_prim_ns.MakeVisible()

                        imageable_prim_wn = UsdGeom.Imageable(first_prim_wn)
                        if imageable_prim_wn:
                            imageable_prim_wn.MakeVisible()

                    label.text = "Payloads loaded as invisible."
                
                async def on_show_prims_sequentially():
                    label.text = "Starting visibility sequence..."
                    prims_wn = [omni.usd.get_context().get_stage().GetPrimAtPath(path_wn) for path_wn in self.loaded_prims_wn]
                    prims_ns = [omni.usd.get_context().get_stage().GetPrimAtPath(path_ns) for path_ns in self.loaded_prims_ns]

                    await sequential_visibility_change(prims_ns, prims_wn, 0.1)
                    label.text = "All prims have been shown and hidden."

                def call_async(fn):
                    asyncio.ensure_future(fn())

                with ui.HStack():
                    ui.Button("Load Payloads", clicked_fn=lambda: call_async(on_load_payloads))
                    ui.Button("Show Prims Sequentially", clicked_fn=lambda: call_async(on_show_prims_sequentially))

    def on_shutdown(self):
        print("[omni.hello.sequence] SequenceExtension shutdown")
