"""X2-A 离线入口：固定源码包、受管合成 fixture。"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
# -I -S 时仍显式指定本包，拒绝先前加载的异源模块。
for name, module in tuple(sys.modules.items()):
    if name == 'life_engine' or name.startswith('life_engine.'):
        if not Path(getattr(module, '__file__', '')).resolve().is_relative_to(ROOT / 'runtime'):
            raise SystemExit('RUNTIME_ORIGIN_DENIED')
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'runtime')]

from x2_runtime import Controller, X2Error, VERSION, offline_report
from x2_web import make_server


def offline_guard(event, args):
    if event in ('socket.connect', 'socket.getaddrinfo', 'socket.gethostbyaddr', 'socket.gethostbyname'):
        raise X2Error('OFFLINE_NETWORK_DENIED', 'network')
    if event == 'socket.bind' and (type(args[1]) is not tuple or args[1][0] != '127.0.0.1'):
        raise X2Error('OFFLINE_BIND_DENIED', 'network')


def main(argv=None):
    parser = argparse.ArgumentParser(description='X2-A 合成记忆试用；无模型/Host/发送')
    parser.add_argument('command', choices=['start', 'status', 'export'])
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--new', action='store_true')
    target.add_argument('--fixture', help='仅受管的 32 位 fixture ID')
    parser.add_argument('--offline', action='store_true', required=True)
    args = parser.parse_args(argv)
    if args.new and args.command != 'start':
        parser.error('--new 只用于 start')
    controller = None
    server = None
    try:
        sys.addaudithook(offline_guard)
        if args.command != 'start':
            print(json.dumps(offline_report(args.fixture), ensure_ascii=False), flush=True)
            return 0
        controller = Controller(args.fixture)
        server = make_server(controller)
        # 口令仅这次终端启动输出；不写文件/access log/诊断导出。
        print(json.dumps(dict(version=VERSION, fixture=controller.identifier,
                              url=server.launch_url, mode='OFFLINE_REPLAY / MODEL_NOT_CONNECTED'),
                         ensure_ascii=False), flush=True)
        server.serve_forever(poll_interval=.1)
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as error:
        print(json.dumps(dict(ok=False, code=error.code if isinstance(error, X2Error) else
                              ('FIXTURE_BUSY' if isinstance(error, TimeoutError) else 'OPEN_FAILED'),
                              stage=getattr(error, 'stage', 'open')), ensure_ascii=False), flush=True)
        return 1
    finally:
        if server:
            server.server_close()
        if controller:
            controller.close()


if __name__ == '__main__':
    raise SystemExit(main())
