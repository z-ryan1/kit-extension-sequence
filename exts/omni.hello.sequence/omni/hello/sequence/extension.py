import omni.ext
import omni.ui as ui
import time
from pxr import Usd, Sdf, Tf, UsdGeom, UsdLux, Gf, UsdShade, Vt
import omni.kit.viewport.utility as vu

def create_payload(usd_context: omni.usd.UsdContext, path_to: Sdf.Path, asset_path: str) -> Usd.Prim:
    omni.kit.commands.execute("CreatePayload",
        usd_context=usd_context,
        path_to=path_to,
        asset_path=asset_path, 
    )
    return usd_context.get_stage().GetPrimAtPath(path_to)

def create_perspective_camera(stage: Usd.Stage, prim_path: str="/World/MyPerspCam") -> UsdGeom.Camera:
    camera_path = Sdf.Path(prim_path)
    usd_camera: UsdGeom.Camera = UsdGeom.Camera.Define(stage, camera_path)
    usd_camera.CreateProjectionAttr().Set(UsdGeom.Tokens.perspective)
    return usd_camera

class SequenceExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        stage = omni.usd.get_context().get_stage()
        world_path = Sdf.Path("/World")
        default_prim = UsdGeom.Xform.Define(stage, world_path)

        ## try and create good camera perspective
        # transform_path = '/CameraTransform'
        # camera_transform = UsdGeom.Xform.Define(stage, transform_path)
        # camera_transform.AddTranslateOp().Set(value=Gf.Vec3f(55492, -24886, 64903)) 
        # # Scamera_transform.AddRotateXYZOp().Set(value=(13.19107, 90, 19))

        # camera_path = '/CameraTransform/MyCamera'
        # camera = UsdGeom.Camera.Define(stage, camera_path)
        # camera.CreateFocalLengthAttr(50.0)
        # camera.CreateFocalLengthAttr(50.0)
        # camera.CreateFocusDistanceAttr(400.0)
        # camera.CreateHorizontalApertureAttr(21)    
        # camera.CreateVerticalApertureAttr(15) 
        # camera.CreateClippingRangeAttr((0.1, 1000000.0)) 

        # vp_api = vu.get_active_viewport()
        # vp_api.camera_path = camera_path

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


                def on_reset():
                    pass
                    # prim = stage.GetPrimAtPath("/World/payload_prim")
    
                    # if prim and prim.HasPayload():
                    #     payloads = prim.GetPayloads()
                    #     payload_path = payloads.GetAssetPath()
                    #     # for payload in payloads:
                    #     #     payload_path = payload.GetAssetPath()
                    #     #     print(f"Payload USD path: {payload_path}")
                    #     #     return payload_path 
                    # else:
                    #     return None


                # on_reset()

                with ui.HStack():
                    ui.Button("Start", clicked_fn=on_click)
                    ui.Button("Reset", clicked_fn=on_reset)


    def on_shutdown(self):
        print("[omni.hello.sequence] SequenceExtension shutdown")
