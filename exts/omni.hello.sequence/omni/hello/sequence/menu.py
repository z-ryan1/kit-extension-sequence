# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.




# use this to create a hot reloadable ui window, callable from a menu item
'''

Example usage:

class MenuEntryDemoLLM(MenuEntry) :
    async def window_create_async(self):
        # this is called from the on menu clicked handler
        # this is responsible for creating whatever gui.,
        # this is required to set self._window

        self._window = ui.Window(self.tool_name, width=500,height=500)
        with self._window.frame:
            with ui.VStack(style=GLOBAL_STYLE):
                self.model_label = ui.Label("Select Model", height=20)



class MyExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self._windows = [MenuEntryDemoLLM('LLM Demo', 'SA Demos/LLM Demo')]

    def on_shutdown(self):
        for window in self._windows:
            window.shutdown()
            self._window = None

'''





import asyncio
import carb # type: ignore

import omni.ext # type: ignore
import omni.ui as ui # type: ignore
import omni.kit.ui  # type: ignore # for get_editor_menu

from functools import partial


def obj_shutdown(obj):
    if not obj:
        return
    if hasattr(obj, 'shutdown') and callable(getattr(obj, 'shutdown')):
        getattr(obj, 'shutdown')()




class MenuEntry():
    # UI Callbacks.  No long running events!
    # these typicall should call async routines.
    def on_window_closed(self):
        self.window_close()

    def on_menu_clicked(self, *_arg):
        asyncio.ensure_future(self._window_create_async())

    def on_update(self, delta: float):
        # ignore if we are not initialized yet!  This can and will be called before __init__ is done.
        if hasattr(self, '_window') and self._window:
            if hasattr(self, 'update') and callable(getattr(self, 'update')):
                self.update(delta)

    def on_window_visibility_changed(self, visible: bool):
        if not visible:
            # go async, don't close self in our own callback!
            asyncio.ensure_future(self.window_close_async())
            self.window_close()

    async def window_close_async(self):
        # if in a callback, you should queue this and
        # not call windows_close directly.
        self.window_close()

    async def window_create_async(self):
        # this is called from the on menu clicked handler
        # this is responsible for creating whatever gui.,
        # you should override this with your own implementation.
        pass

    async def _window_create_async(self):
        # calls descendent window create that performs standard setup.
        await self.window_create_async()
        if not self._window:
            return
        # Handles the change in visibility of the window gracefully
        self._window.set_visibility_changed_fn(self.on_window_visibility_changed)

        # , on_close = self.on_window_closed

    def window_close(self):
        # when window closes, we want to get rid of our pointer to it.
        if self._window:
            obj_shutdown(self._window)
            self._window = None

    def __init__(self, tool_name: str, menu_path: str):
        self.simulation = None  # HACK  Should be done by descended class
        self.tool_name = tool_name
        carb.log_info(f"{self.tool_name} menu startup")
        self.menus = omni.kit.ui.get_editor_menu().add_item(menu_path, self.on_menu_clicked, toggle=False, value=False)
        self._window = None

        # The ability to show the window if the system requires it.
        # You use it in QuickLayout.
        def _menu_show_window(menu, value):
            asyncio.ensure_future(self._window_create_async())

        ui.Workspace.set_show_window_fn(tool_name, partial(_menu_show_window, None))
        # super().__init__(tool_name)

    def shutdown(self):
        carb.log_info(f"{self.tool_name} menu shutdown")
        self.window_close()
        self.menus = None

