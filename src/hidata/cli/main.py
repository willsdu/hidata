# -*- coding: utf-8 -*-
from __future__ import annotations


import logging
import click
from hidata.config.utils import read_last_api
from hidata.cli.app_cmd import app_cmd
from hidata.__version__ import __version__


logger = logging.getLogger(__name__)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="hidata")
@click.option("--host", default=None, help="API 地址（Host）")
@click.option(
    "--port",
    default=None,
    type=int,
    help="API 端口（Port）",
)
@click.pass_context
def cli(ctx: click.Context, host: str|None=None, port: int|None=None) -> None:
    last=read_last_api()
    if host is None or port is None:
        if last:
            host=host or last[0]
            port=port or last[1]
        host=host or "127.0.0.1"
        port=port or 8088
    
    ctx.ensure_object(dict)
    ctx.obj["host"] = host
    ctx.obj["port"] = port

cli.add_command(app_cmd)