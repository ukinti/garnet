import operator
import itertools

from ..helpers import var
from .base import Filter


class ExtensionCollection:
    png:  str = var.Var()
    jpeg: str = var.Var()
    webp: str = var.Var()
    gif:  str = var.Var()
    bmp:  str = var.Var()
    tga:  str = var.Var()
    tiff: str = var.Var()
    psd:  str = var.Var()

    mp4:  str = var.Var()
    mov:  str = var.Var()
    avi:  str = var.Var()

    mp3:  str = var.Var()
    m4a:  str = var.Var()
    aac:  str = var.Var()
    ogg:  str = var.Var()
    flac: str = var.Var()

    exe:  str = var.Var()


class File:
    class __Extension:
        def __eq__(self, extension: str):
            if not extension.startswith("."):
                extension = "." + extension
            return Filter(lambda event: event.file and operator.eq(event.file.ext, extension))

        def between(*extensions: str):
            extensions = list(itertools.chain(extensions))
            for n, ext in enumerate(extensions):
                if not ext.startswith("."):
                    extensions[n] = ext
            return Filter(lambda event: event.file and operator.contains(extensions, event.file.ext))

        in_ = between

    Extension = __Extension()
