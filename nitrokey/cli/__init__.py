# -*- coding: utf-8 -*-
#
# Copyright 2019 SoloKeys Developers
#
# Licensed under the Apache License, Version 2.0, <LICENSE-APACHE or
# http://apache.org/licenses/LICENSE-2.0> or the MIT license <LICENSE-MIT or
# http://opensource.org/licenses/MIT>, at your option. This file may not be
# copied, modified, or distributed except according to those terms.

import os

import click

import json

import nitrokey
import nitrokey.operations
from nitrokey.cli.fido2 import fido2
from nitrokey.cli.start import start

from . import _patches  # noqa  (since otherwise "unused")

if (os.name == "posix") and os.environ.get("ALLOW_ROOT") is None:
    if os.geteuid() == 0:
        print("THIS COMMAND SHOULD NOT BE RUN AS ROOT!")
        print()
        print(
            "Please install udev rules and run `nitrokey` as regular user (without sudo)."
        )
        print(
            "We suggest using: https://github.com/solokeys/solo/blob/master/udev/70-solokeys-access.rules"
        )
        print()
        print("For more information, see: https://docs.solokeys.io/solo/udev/")


@click.group()
def solo_cli():
    pass


solo_cli.add_command(fido2)
solo_cli.add_command(start)


@click.command()
def version():
    """Version of python-solo library and tool."""
    print(nitrokey.__version__)


solo_cli.add_command(version)


@click.command()
@click.option("--input-seed-file")
@click.argument("output_pem_file")
def genkey(input_seed_file, output_pem_file):
    """Generates key pair that can be used for Nitrokey signed firmware updates.

    \b
    * Generates NIST P256 keypair.
    * Public key must be copied into correct source location in Nitrokey's bootloader
    * The private key can be used for signing updates.
    * You may optionally supply a file to seed the RNG for key generating.
    """

    vk = nitrokey.operations.genkey(output_pem_file, input_seed_file=input_seed_file)

    print("Public key in various formats:")
    print()
    print([c for c in vk.to_string()])
    print()
    print("".join(["%02x" % c for c in vk.to_string()]))
    print()
    print('"\\x' + "\\x".join(["%02x" % c for c in vk.to_string()]) + '"')
    print()


solo_cli.add_command(genkey)


@click.command()
@click.argument("verifying-key")
@click.argument("app-hex")
@click.argument("output-json")
@click.option("--end_page", help="Set APPLICATION_END_PAGE. Should be in sync with firmware settings.", default=20, type=int)
def sign(verifying_key, app_hex, output_json, end_page):
    """Signs a firmware hex file, outputs a .json file that can be used for signed update."""

    msg = nitrokey.operations.sign_firmware(verifying_key, app_hex, APPLICATION_END_PAGE=end_page)
    print("Saving signed firmware to", output_json)
    with open(output_json, "wb+") as fh:
        fh.write(json.dumps(msg).encode())


solo_cli.add_command(sign)


@click.command()
@click.option("--attestation-key", help="attestation key in hex")
@click.option("--attestation-cert", help="attestation certificate file")
@click.option(
    "--lock",
    help="Indicate to lock device from unsigned changes permanently.",
    default=False,
    is_flag=True,
)
@click.argument("input_hex_files", nargs=-1)
@click.argument("output_hex_file")
@click.option(
    "--end_page",
    help="Set APPLICATION_END_PAGE. Should be in sync with firmware settings.",
    default=20,
    type=int,
)
def mergehex(
    attestation_key, attestation_cert, lock, input_hex_files, output_hex_file, end_page
):
    """Merges hex files, and patches in the attestation key.

    \b
    If no attestation key is passed, uses default Solo Hacker one.  <---- TODO: remove?
    Note that later hex files replace data of earlier ones, if they overlap.
    """
    nitrokey.operations.mergehex(
        input_hex_files,
        output_hex_file,
        attestation_key=attestation_key,
        APPLICATION_END_PAGE=end_page,
        attestation_cert=attestation_cert,
        lock=lock,
    )


solo_cli.add_command(mergehex)


@click.command()
def ls():
    """List Nitrokey keys (in firmware or bootloader mode)"""

    fido2.commands["list"].callback()
    start.commands["list"].callback()

solo_cli.add_command(ls)

from pygments.console import colorize
print(f'*** {colorize("red", "Nitrokey tool for Nitrokey FIDO2 & Nitrokey Start")}')