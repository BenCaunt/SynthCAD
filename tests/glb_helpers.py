import json
import struct
from pathlib import Path


def glb_material_colors(path: Path) -> set[tuple[float, float, float, float]]:
    data = path.read_bytes()
    offset = 12
    while offset < len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type != 0x4E4F534A:
            continue
        document = json.loads(chunk.rstrip(b" \t\r\n\x00"))
        colors = set()
        for material in document.get("materials", []):
            color = material.get("pbrMetallicRoughness", {}).get("baseColorFactor")
            if color:
                colors.add(tuple(round(float(component), 4) for component in color))
        return colors
    raise AssertionError(f"{path} does not contain a glTF JSON chunk")
