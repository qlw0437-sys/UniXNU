#!/usr/bin/env python3
import re
from pathlib import Path

def patch_makeinc_def():
    for p in Path(".cache/xnu-work").glob("**/makedefs/MakeInc.def"):
        text = p.read_text(encoding="utf-8")
        if "-mach_msg2" in text:
            p.write_text(text.replace("-mach_msg2", ""), encoding="utf-8")
            print(f"Patched {p}: removed -mach_msg2 for Xcode mig compatibility")

def patch_iorpc_headers():
    inline_impl = """#if defined(__cplusplus)
extern "C" {
#endif
static inline IORPCMessage *
IORPCMessageFromMach(IORPCMessageMach * msg, bool reply)
{
\tmach_msg_size_t idx, count = msg->msgh_body.msgh_descriptor_count;
\tmach_msg_port_descriptor_t * desc = &msg->objects[0];
\tmach_msg_port_descriptor_t * maxDesc = (typeof(maxDesc))(((uintptr_t) msg) + msg->msgh.msgh_size);
\tfor (idx = 0; idx < count; idx++) {
\t\tif (desc >= maxDesc) return (IORPCMessage *)0;
\t\tsize_t size = (desc->type == MACH_MSG_PORT_DESCRIPTOR) ? sizeof(mach_msg_port_descriptor_t) : sizeof(mach_msg_ool_descriptor_t);
\t\tdesc = (typeof(desc))(((uintptr_t) desc) + size);
\t}
\treturn (IORPCMessage *)(uintptr_t) desc;
}
#if defined(__cplusplus)
}
#endif"""

    pattern = re.compile(r"#ifndef\s+KERNEL[\s\S]*?IORPCMessageFromMach[\s\S]*?#endif\s*/\*\s*KERNEL\s*\*/")

    for p in Path(".cache/xnu-work").glob("**/*IORPC.h"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if pattern.search(text):
            new_text = pattern.sub(inline_impl, text)
            p.write_text(new_text, encoding="utf-8")
            print(f"Patched {p}: defined IORPCMessageFromMach as static inline for kernel mode")

def patch_warning_flags():
    search_dirs = [Path("."), Path("device"), Path("../device"), Path("..")]
    for base in search_dirs:
        if not base.exists():
            continue
        for ext in ("*.py", "*.sh"):
            for p in base.rglob(ext):
                try:
                    text = p.read_text(encoding="utf-8")
                    if "-Wno-unnecessary-virtual-specifier" in text:
                        p.write_text(text.replace("-Wno-unnecessary-virtual-specifier", "-Wno-unknown-warning-option"), encoding="utf-8")
                        print(f"Patched {p}: replaced -Wno-unnecessary-virtual-specifier with -Wno-unknown-warning-option")
                except Exception:
                    pass

if __name__ == "__main__":
    patch_makeinc_def()
    patch_iorpc_headers()
    patch_warning_flags()
