#!/usr/bin/env python3
"""FIR surgery v2: replace extmodule SimDTM with top-level TestHarness ports.
Correctly distinguishes SimDTM wiring lines (DELETE) from SimDTM output
consumers (REWRITE SimDTM.exit -> dtm_exit)."""
import re, sys

def surgery(path_in, path_out):
    lines = open(path_in).readlines()
    n = len(lines)

    # Locate extmodule SimDTM declaration
    extmod_start = extmod_end = None
    for i, l in enumerate(lines):
        if l.strip() == 'extmodule SimDTM :':
            extmod_start = i
            extmod_end = i + 1
            while extmod_end < n:
                s = lines[extmod_end].strip()
                if s == '' or s.startswith('module ') or s.startswith('extmodule '):
                    break
                extmod_end += 1
            break

    # Locate TestHarness
    th_start = th_port_end = None
    for i, l in enumerate(lines):
        if l.strip() == 'module TestHarness :':
            th_start = i
            th_port_end = i + 1
            while th_port_end < n:
                if lines[th_port_end].strip() == '':
                    break
                th_port_end += 1
            break

    if extmod_start is None or th_start is None:
        print("ERROR: SimDTM or TestHarness not found"); sys.exit(1)

    # Classify SimDTM lines in TestHarness body
    to_delete = set()
    for i in range(th_start, min(th_start + 500, n)):
        ls = lines[i].strip()
        if not ls: continue
        if 'inst SimDTM of SimDTM' in ls or \
           re.match(r'SimDTM\.\w+\s*<=', ls) or \
           '<- SimDTM' in ls:
            to_delete.add(i)

    # New top-level ports
    new_ports = [
        "    input dtm_req_valid : UInt<1>\n",
        "    input dtm_req_bits_addr : UInt<7>\n",
        "    input dtm_req_bits_data : UInt<32>\n",
        "    input dtm_req_bits_op : UInt<2>\n",
        "    input dtm_exit : UInt<32>\n",
        "    output dtm_req_ready : UInt<1>\n",
        "    output dtm_resp_valid : UInt<1>\n",
        "    output dtm_resp_ready : UInt<1>\n",
        "    output dtm_resp_bits_data : UInt<32>\n",
        "    output dtm_resp_bits_resp : UInt<2>\n",
    ]

    # Individual connects replacing the aggregate bidir connect
    replacement_connects = [
        "    dtm_req_ready <= ldut.debug.clockeddmi.dmi.req.ready\n",
        "    dtm_resp_valid <= ldut.debug.clockeddmi.dmi.resp.valid\n",
        "    dtm_resp_bits_data <= ldut.debug.clockeddmi.dmi.resp.bits.data\n",
        "    dtm_resp_bits_resp <= ldut.debug.clockeddmi.dmi.resp.bits.resp\n",
        "    ldut.debug.clockeddmi.dmi.req.valid <= dtm_req_valid\n",
        "    ldut.debug.clockeddmi.dmi.req.bits.addr <= dtm_req_bits_addr\n",
        "    ldut.debug.clockeddmi.dmi.req.bits.data <= dtm_req_bits_data\n",
        "    ldut.debug.clockeddmi.dmi.req.bits.op <= dtm_req_bits_op\n",
        "    ldut.debug.clockeddmi.dmi.resp.ready <= dtm_resp_ready\n",
    ]

    # Build output
    out = []
    first_deleted = min(to_delete) if to_delete else th_port_end
    inserted_ports = False
    inserted_connects = False

    for i in range(n):
        # Skip extmodule declaration
        if extmod_start is not None and extmod_start <= i < extmod_end:
            continue

        # Skip deleted SimDTM wiring
        if i in to_delete:
            if not inserted_connects:
                for c in replacement_connects:
                    out.append(c)
                out.append('\n')
                inserted_connects = True
            continue

        line = lines[i]

        # Rewrite SimDTM.exit references in node definitions
        if 'SimDTM.exit' in line:
            line = line.replace('SimDTM.exit', 'dtm_exit')

        out.append(line)

        # Insert new ports after existing port block
        if i == th_port_end - 1 and not inserted_ports:
            for p in new_ports:
                out.append(p)
            inserted_ports = True

    with open(path_out, 'w') as f:
        f.writelines(out)
    print(f"OK: deleted {extmod_end - extmod_start} extmodule lines + "
          f"{len(to_delete)} wiring lines; "
          f"added {len(new_ports)} ports + {len(replacement_connects)} connects; "
          f"rewrote SimDTM.exit -> dtm_exit")

if __name__ == '__main__':
    surgery(sys.argv[1], sys.argv[2])
