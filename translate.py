#!/usr/bin/env python3

from colorama import Fore, Style
import os
import sys

REPO_UNSTABLE = 'github:NixOS/nixpkgs/nixos-unstable'

def parse_atom(atom):
    tmp = atom.split('/', 2)
    tmp2 = tmp[1].split(':', 2)
    slot = tmp2[1] if len(tmp2) == 2 else '0'
    return (tmp[0], tmp2[0], slot)

class PkgState:
    def __init__(self, base):
        self.base = base
        with open(os.path.join(base, '.pkgignore')) as f:
            self.deny = [l.split('/') for l in f]
        self.pkgs = []
        self.from_overlays = {}
        self.confls = []
        self.warn_pkgs = []

    def lookup(self, atom):
        categ, pkgname, slot = parse_atom(atom)
        p_categ = os.path.join(self.base, categ)
        if os.path.isdir(p_categ):
            p_pkg = os.path.join(p_categ, pkgname)
            if os.path.isfile(p_pkg):
                return (p_pkg, pkgname)
            else:
                return None
        elif os.path.isfile(p_categ):
            return (p_categ, pkgname)
        else:
            return None

    def append(self, atom):
        p = self.lookup(atom)
        if not p:
            print(f'{atom}:\t{Fore.RED}unknown{Style.RESET_ALL}')
            return
        p, pkgname = p

        with open(p, 'r') as f:
            for l in f:
                l = l.strip()
                lp = l.split(' ')
                x = (': ' + ' '.join(lp[1:])) if len(lp) > 1 else ''
                if l == '' or lp[0] == '#':
                    pass
                elif lp[0] == 'skip':
                    return
                elif lp[0] == 'force-manual':
                    print(f'{atom}:\t{Fore.BLUE}force-manual{x}{Style.RESET_ALL}')
                    return
                elif lp[0] == 'unavailable':
                    print(f'{atom}:\t{Fore.RED}unavailable{x}{Style.RESET_ALL}')
                    return
                elif lp[0] == 'warn':
                    if lp[1] == 'pkg':
                        self.warn_pkgs.append(lp[2])
                    elif lp[1] == 'msg':
                        x = ' '.join(lp[2:])
                        print(f'{atom}:\t{Fore.YELLOW}{x}{Style.RESET_ALL}')
                elif lp[0] == 'pkg':
                    rpn = lp[1] if (len(lp) > 1 and lp[1] != '_') else pkgname
                    self.pkgs.append(rpn)
                    if len(lp) > 2:
                        overlay = None
                        if lp[2] == 'unstable':
                            overlay = REPO_UNSTABLE
                        elif lp[2] == 'PR':
                            overlay = lp[4]
                        elif lp[2] == 'overlay':
                            overlay = lp[3]
                        else:
                            x = ' '.join(lp[2:])
                            print(f'{atom}:\t{Fore.RED}unknown package source spec{Style.RESET_ALL}: {x}')
                            return
                        self.from_overlays[rpn] = overlay
                elif lp[0] == 'module':
                    if len(lp) > 1:
                        if lp[1] == 'manual':
                            x = ' '.join(lp[2:])
                            print(f'{atom}:\t{Fore.BLUE}manual service module: {x}{Style.RESET_ALL}')
                elif lp[0] == '>':
                    self.confls.append(' '.join(lp[1:]))
                else:
                    print(f'{atom}:\t{Fore.RED}unknown directive{Style.RESET_ALL}: {l}')

pkgst = PkgState(os.path.realpath(sys.path[0]))

with open(sys.argv[1], 'r') as wf:
    for l in wf:
        pkgst.append(l.strip())

pkgst.pkgs.sort()
pkgst.warn_pkgs.sort()

for p in pkgst.warn_pkgs:
    if p in pkgst.pkgs:
        print(f'WARNING: {Fore.YELLOW}probably unwanted package in pkgs set{Style.RESET_ALL}: {p}')

print(f'PKGS: {pkgst.pkgs}')
print(f'FROM_OVERLAYS: {pkgst.from_overlays}')
print(f'CONFLS:')
for l in pkgst.confls:
    print(f'  {l}')
print(f'WARN_PKGS: {pkgst.warn_pkgs}')
