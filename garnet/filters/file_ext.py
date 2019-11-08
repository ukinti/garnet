from typing import Sequence
import operator

from ..helpers import var
from .base import Filter


class ExtensionCollection:
    """
    List of known exceptions
    """
    png: str = var.Var()
    jpeg: str = var.Var()
    webp: str = var.Var()
    gif: str = var.Var()
    bmp: str = var.Var()
    tga: str = var.Var()
    tiff: str = var.Var()
    psd: str = var.Var()
    pic_ext: Sequence[str] = (png, jpeg, webp, gif, bmp, tga, tiff, psd, )

    mp4: str = var.Var()
    mov: str = var.Var()
    avi: str = var.Var()
    vid_ext: Sequence[str] = (mp4, mov, avi, )

    mp2: str = var.Var()  # a.k.a. ISO/IEC 13818-2
    mp3: str = var.Var()
    m4a: str = var.Var()
    aac: str = var.Var()
    ogg: str = var.Var()
    flac: str = var.Var()
    mus_ext: Sequence[str] = (mp3, m4a, aac, ogg, flac, mp2, )

    exe: str = var.Var()


class File:
    Extensions = ExtensionCollection()

    @classmethod
    def between(cls, *extensions: str):
        extensions = [str(ext) for ext in extensions]
        for n, ext in enumerate(extensions):
            if not ext.startswith("."):
                extensions[n] = "." + ext
        return Filter(
            lambda event:
            event.file is not None
            and
            operator.contains(extensions, event.file.ext)
        )
