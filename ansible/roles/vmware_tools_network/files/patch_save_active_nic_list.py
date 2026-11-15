#!/usr/bin/env python3
"""Patch open-vm-tools network script so suspend does not flush Docker bridges."""

from __future__ import annotations

import pathlib
import sys

MARKER = "skipping container interface"

OLD = (
    '   if [ -n "$ip_cmd" ]; then\n'
    "      for nic in $($ip_cmd link show up | egrep '\\bUP\\b' | awk -F: '{print $2}'); do\n"
    "         $ip_cmd link show ${nic%@*} | grep -iq 'link/ether' && echo ${nic%@*} >> $activeList\n"
    "      done\n"
)

NEW = (
    '   if [ -n "$ip_cmd" ]; then\n'
    "      for nic in $($ip_cmd link show up | egrep '\\bUP\\b' | awk -F: '{print $2}'); do\n"
    "         nic_name=${nic%@*}\n"
    '         nic_name=$(echo "$nic_name" | awk \'{print $1}\')\n'
    "         # Managed by Ansible role vmware_tools_network:\n"
    "         # do not suspend/flush Docker bridges and veth pairs.\n"
    '         # The stop path of this script runs "ip addr flush" on every name\n'
    "         # recorded here, which removes Docker bridge gateway addresses.\n"
    '         case "$nic_name" in\n'
    "            docker0|br-*|veth*|virbr*)\n"
    '               log "[save_active_NIC_list] skipping container interface $nic_name"\n'
    "               continue\n"
    "               ;;\n"
    "         esac\n"
    '         $ip_cmd link show "$nic_name" | grep -iq \'link/ether\' && echo "$nic_name" >> $activeList\n'
    "      done\n"
)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch_save_active_nic_list.py <script-path>", file=sys.stderr)
        return 2

    path = pathlib.Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")

    if MARKER in text:
        print("already_patched")
        return 0

    if OLD not in text:
        print("upstream pattern not found", file=sys.stderr)
        return 1

    path.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print("patched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
