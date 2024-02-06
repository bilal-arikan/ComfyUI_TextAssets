
from server import PromptServer
import folder_paths
import hashlib
import os
import sys

try:
    import aiohttp
    from aiohttp import web
except ImportError:
    print("Module 'aiohttp' not installed. Please install it via:")
    print("pip install aiohttp")
    print("or")
    print("pip install -r requirements.txt")
    sys.exit()

input_sub_folder = "textassets"

class LoadTextAsset:
    @classmethod
    def INPUT_TYPES(s):
        if not(os.path.exists(os.path.join(folder_paths.get_input_directory(), input_sub_folder))):
            os.makedirs(os.path.join(folder_paths.get_input_directory(), input_sub_folder))
        input_dir = os.path.join(folder_paths.get_input_directory(), input_sub_folder)
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]

        return {"required": {
                    "textasset": (sorted(files), {"save_textasset": True}),
                    "overwrite": ("INT", {"default": 0, "min": 0, "max": 1, "step": 1}),
                    "show_content": ("INT", {"default": 1, "min": 0, "max": 1, "step": 1})
                }
            }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "load_asset"
    CATEGORY = "utils/LoadTextAsset"

    def load_asset(self, textasset, overwrite, show_content):
        text_path = os.path.join(folder_paths.get_input_directory(), input_sub_folder, textasset)
        file = open(text_path,'r')
        textasset_value = file.read()
        file.close()
        return {"ui": {"textasset": (textasset_value,)}, "result": (textasset_value,)}
    
    @classmethod
    def IS_CHANGED(self, textasset, overwrite, show_content):
        received_file_path = os.path.join(folder_paths.get_input_directory(), input_sub_folder, textasset)
        file = open(received_file_path,'r')
        textasset_value = file.read()
        file.close()
        return textasset_value

    @classmethod
    def VALIDATE_INPUTS(self, textasset, overwrite, show_content):
        if not os.path.join(folder_paths.get_input_directory(), input_sub_folder, textasset):
            return "Invalid file file: {}".format(textasset)
        return True


@PromptServer.instance.routes.post("/upload/textasset")
async def upload_textasset(request):
    post = await request.post()
    response = save_received_textasset(post)
    return response

def get_dir_by_type(dir_type):
    if dir_type is None:
        dir_type = "input"

    if dir_type == "input":
        type_dir = folder_paths.get_input_directory()
    elif dir_type == "temp":
        type_dir = folder_paths.get_temp_directory()
    elif dir_type == "output":
        type_dir = folder_paths.get_output_directory()

    return type_dir, os.path.join(dir_type, input_sub_folder)

def save_received_textasset(post, received_file_save_function=None):
    received_file = post.get("textasset")
    overwrite = post.get("overwrite")

    received_file_upload_type = post.get("type")
    upload_dir, received_file_upload_type = get_dir_by_type(received_file_upload_type)

    if received_file and received_file.file:
        filename = received_file.filename
        if not filename:
            return web.Response(status=400)

        subfolder = post.get("subfolder", "")
        # print("# subfolder", subfolder)
        full_output_folder = os.path.join(upload_dir, input_sub_folder, os.path.normpath(subfolder))
        # print("# full_output_folder", full_output_folder)
        filepath = os.path.abspath(os.path.join(full_output_folder, filename))
        # print("# filepath", filepath)

        if os.path.commonpath((upload_dir, filepath)) != upload_dir:
            return web.Response(status=400)

        if not os.path.exists(full_output_folder):
            os.makedirs(full_output_folder)

        split = os.path.splitext(filename)

        if overwrite is not None and (overwrite == "true" or overwrite == "1"):
            pass
        else:
            i = 1
            while os.path.exists(filepath):
                filename = f"{split[0]}_({i}){split[1]}"
                filepath = os.path.join(full_output_folder, filename)
                i += 1

        if received_file_save_function is not None:
            received_file_save_function(received_file, post, filepath)
        else:
            with open(filepath, "wb") as f:
                f.write(received_file.file.readline())

        return web.json_response({"name" : filename, "subfolder": subfolder, "type": received_file_upload_type})
    else:
        return web.Response(status=400)


NODE_CLASS_MAPPINGS = {
    "LoadTextAsset": LoadTextAsset,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadTextAsset": "Load Text Asset File",
}