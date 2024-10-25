import omni.ext
import omni.ui as ui
import asyncio
from pxr import Sdf, UsdGeom, Gf, UsdShade

def create_material(stage, mat_name):
    """Create a red material."""
    material_path = f"/World/{mat_name}"
    
    material = UsdShade.Material.Define(stage, Sdf.Path(material_path))
    shader = UsdShade.Shader.Define(stage, Sdf.Path(material_path + "/Shader"))
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set((1.0, 0.0, 0.0))  # Red color
    material.CreateSurfaceOutput().ConnectToSource(shader.CreateOutput('surface', Sdf.ValueTypeNames.Token))
    opacity_input = shader.CreateInput("opacity", Sdf.ValueTypeNames.Float)

    # Set the opacity value
    opacity_input.Set(0.5)  # Change this value to set the desired opacity
    
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

def create_camera_on_startup(stage, camera_path="/World/MyCamera"):
    """Create a camera on startup from a specific view."""
    camera_prim = UsdGeom.Camera.Define(stage, camera_path)
    camera_prim.CreateFocalLengthAttr().Set(50.0)
    camera_prim.CreateHorizontalApertureAttr().Set(36.0)
    camera_prim.CreateVerticalApertureAttr().Set(24.0)
    camera_prim.CreateFStopAttr().Set(5.6)
    camera_prim.CreateFocusDistanceAttr().Set(1000.0)
    xform = UsdGeom.Xform(camera_prim.GetPrim())
    ''''
    This is where you can change the starting camera position
    '''
    pos = Gf.Vec3f(123, 126, 1100) # change starting position
    translate_op = xform.AddTranslateOp()

    translate_op.Set(pos)

    return camera_prim, translate_op

def update_camera_position(stage, camera_path, target_prim, translate_op):
    """Update the camera position to look at the target prim."""
    target_pos = translate_op.Get()

    # Set the camera position above the target
    new_camera_pos = Gf.Vec3f(target_pos[0], target_pos[1], target_pos[2] + 10.0) # can change to move camera faster
    translate_op.Set(new_camera_pos)


async def smooth_transition(current_ns, current_wn, overlap_duration, stage, camera_path, translate_op):
    """Transition from the current prim to the next prim."""
    if current_ns and current_wn:
        imageable_ns = UsdGeom.Imageable(current_ns)
        imageable_wn = UsdGeom.Imageable(current_wn)

        if imageable_ns:
            imageable_ns.MakeVisible()
        if imageable_wn:
            imageable_wn.MakeVisible()

        update_camera_position(stage, camera_path, current_ns, translate_op)
        await asyncio.sleep(overlap_duration)

        if imageable_ns:
            imageable_ns.MakeInvisible()

        if imageable_wn:
            imageable_wn.MakeInvisible()

async def sequential_visibility_change(prims_ns, prims_wn, overlap_duration, stage, camera_path, translate_op):
    """Sequentially change visibility for a list of prims."""
    for current_ns, current_wn in zip(prims_ns, prims_wn):
        await smooth_transition(current_ns, current_wn, overlap_duration, stage, camera_path, translate_op)

class SequenceExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        stage = omni.usd.get_context().get_stage()
        world_path = Sdf.Path("/World")
        default_prim = UsdGeom.Xform.Define(stage, world_path)
        stage.SetDefaultPrim(default_prim.GetPrim())

        # Create a camera
        camera_path = "/World/MyCamera"
        self.camera, translate_op = create_camera_on_startup(stage, camera_path )

        base_directory_wn = "/home/zoe/wn_prod_converted/wn_00000_thd_"
        base_directory_ns = "/home/zoe/ns_prod_converted/ns_00000_thd_"

        self.loaded_prims_wn = [] 
        self.loaded_prims_ns = [] 

        self._window = ui.Window("My Window", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                label = ui.Label("")

                async def on_load_payloads(): 
                    label.text = "Loading payloads..."
                    context = omni.usd.get_context()
                    
                    # Create a red material for NS prims
                    red_material = create_material(context.get_stage(), "RedMaterial")

                    for i in range(1, 32):
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

                        if len(self.loaded_prims_wn) % 5 == 0:
                            await asyncio.sleep(0.25)

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

                    await sequential_visibility_change(prims_ns, prims_wn, 0.1, stage, camera_path, translate_op) # change 0.1 to change duration
                    label.text = "All prims have been shown and hidden."

                def call_async(fn):
                    asyncio.ensure_future(fn())

                with ui.HStack():
                    ui.Button("Load Payloads", clicked_fn=lambda: call_async(on_load_payloads))
                    ui.Button("Show Prims Sequentially", clicked_fn=lambda: call_async(on_show_prims_sequentially))

    def on_shutdown(self):
        print("[omni.hello.sequence] SequenceExtension shutdown")