"""Observe/replay a twelve-channel bridge; in socket mode deliver COMPAT results to it.

Socket mode (--socket: the model bridge of ultra96.server --sensor-version 4
--model ultra96.model_bridge) sends results back in the bridge's runner format
(ultra96/model_bridge.py), one compact JSON line per result:
  {"type":"result","gesture":G,"confidence":C,"device_id":D,"boot_id":B,"seq":S}
COMPAT delivery: EventEncoder turns the engine records into hand events; each
pulse, state_start, state_refresh and idle event is one result line, D the hand
and B/S the event's source sample, which the service publishes as one v3
GESTURE_RESULT. state_end and reset events have no v3 form: they are recorded
here and never sent. A second result for one (hand, boot_id, seq) is dropped and
counted, as the service would refuse it. --observe-only keeps the earlier
behaviour (record only, send nothing); --replay never sends.

One HandEngine and one EventEncoder serve both hands. A glove reconnect or
reboot reaches this worker only through its samples: HandWindow resets that hand
alone on a new boot_id, a seq jump, an uptime step outside 0..100 ms or a receive
gap over 0.5 s, and the engine ends its state (source_reset); the other hand is
not touched. An encoder error (ProtocolError) is recorded and resets that hand's
encoder state only. Each worker serves one bridge connection: when it ends (the
service stopped, or another runner connected) both hands are reset, the summary
is written and the worker exits; tools.deploy_service starts the next one.

--out names a new JSONL file, or an existing folder for a new file named from the
UTC start time and the PID. Times are this worker's monotonic clock; source and
host clocks are not synchronized.
"""
import argparse
from collections import Counter,OrderedDict
from datetime import datetime,timezone
import json
import math
import os
from pathlib import Path
import secrets
import socket
import threading
import time

from common.hand_contract import ProtocolError,make_hello
from src.hand_runtime import CHANNELS,ModelBundle,HandEngine,digest
from src.hand_backend import NumpyHandBackend,PynqHandBackend
from src.hand_events import EventEncoder

DELIVERY='compat_v3_gesture_result'
FORWARDED=('pulse','state_start','state_refresh','idle')
ENCODED=('prediction','action','state_start','state_end','idle')  # the records EventEncoder reads
LEASE_MS=1000  # the format-2 hello needs one; a v3 result carries no lease
MEMORY=4096  # sent (hand, boot_id, seq) kept against a second result


def validate_hello(message):
    if not isinstance(message,dict) or message.get('type')!='hello' or message.get('format')!=1 or message.get('channels')!=CHANNELS:
        raise ValueError('Need bridge format 1 with exactly twelve ordered channels. Existing eleven-channel/v3 bridge is incompatible.')


def output_path(value):
    """--out: a new file, or an existing folder for a new file named from the UTC time and PID."""
    path=Path(value)
    if not path.is_dir():return path
    return path/'hand-worker-{}-{}.jsonl'.format(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),os.getpid())


class Recorder:
    def __init__(self,path,backend,synthetic,hello=None):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        self.stream=path.open('x',encoding='utf-8',newline='\n')
        self.counts=Counter();self.devices={1:Counter(),2:Counter()}
        scope=dict(type='scope',backend=backend,synthetic=synthetic,
            gameplay_transport=False,final_gesture_accuracy_validated=False,
            timing_scope='worker processing only; source/host clocks are not synchronized')
        if hello:scope.update(gameplay_transport=True,delivery=DELIVERY,forwarded_kinds=list(FORWARDED),
            logged_only_kinds=['state_end','reset'],session_id=hello['session_id'],worker_epoch=hello['worker_epoch'])
        self.write(scope)
    def write(self,record):
        self.stream.write(json.dumps(record,allow_nan=False)+'\n');self.stream.flush()
        self.counts[record['type']]+=1
        if record.get('device_id') in self.devices:self.devices[record['device_id']][record['type']]+=1
        if record['type'] in ('action','state_start','state_end','idle','hand_event','encoder_error','connection_lost'):
            print(json.dumps(record),flush=True)
    def close(self,**extra):
        summary=dict(type='summary',status='failed' if self.counts['error'] else 'finished',
                     counts=dict(self.counts),hands={str(k):dict(v) for k,v in self.devices.items()},**extra)
        self.stream.write(json.dumps(summary)+'\n');self.stream.close();print(json.dumps(summary),flush=True)


class Delivery:
    """COMPAT: encoder events become bridge result lines; state_end and reset are only recorded.

    consume() takes every engine record in process_due order, on the inference thread.
    """
    def __init__(self,hello,record):
        self.encoder=EventEncoder(hello);self.record=record;self.closed=False
        self.time={1:0.,2:0.}  # as EventEncoder: each hand's local time starts at 0, never decreases
        self.sent=OrderedDict()
        self.counts={d:Counter(dict.fromkeys(('forwarded','collisions','encoder_errors','event_time_raised',
            'state_end_not_forwarded','reset_not_forwarded','unsent'),0)) for d in (1,2)}
    def consume(self,record):
        """One engine record; returns the result lines to send now."""
        device=record.get('device_id')
        if record.get('type') not in ENCODED or device not in (1,2):return []
        now=record.get('elapsed_s')
        if type(now) in (int,float) and now<self.time[device]:
            # HandEngine.add stamps a reset with the sample's ARRIVAL time, which can precede a
            # prediction already handed over; the encoder needs non-decreasing time per hand.
            now=self.time[device];record=dict(record,elapsed_s=now);self.counts[device]['event_time_raised']+=1
        if type(now) in (int,float) and math.isfinite(now):self.time[device]=now
        try:events=self.encoder.consume(record)
        except ProtocolError as error:
            self.counts[device]['encoder_errors']+=1
            self.record(dict(type='encoder_error',device_id=device,record_type=record['type'],error=str(error)))
            events=self.encoder.reset('manual_reset',device=device)
        return [line for line in (self._event(device,event) for event in events) if line]
    def _event(self,device,event):
        kind,source=event['kind'],event['source'];counts=self.counts[device];line=None
        if kind not in FORWARDED:delivery='not_forwarded';counts[kind+'_not_forwarded']+=1
        elif (device,source['boot_id'],source['seq']) in self.sent:delivery='collision';counts['collisions']+=1
        elif self.closed:delivery='unsent';counts['unsent']+=1
        else:
            self.sent[device,source['boot_id'],source['seq']]=None
            if len(self.sent)>MEMORY:self.sent.popitem(last=False)
            delivery='forwarded';counts['forwarded']+=1
            line=dict(type='result',gesture=event['gesture'],confidence=event['confidence'],
                      device_id=device,boot_id=source['boot_id'],seq=source['seq'])
        self.record(dict(type='hand_event',device_id=device,kind=kind,gesture=event['gesture'],
            confidence=event['confidence'],event_id=event['event_id'],state_id=event['state_id'],
            reason=event['reason'],source=source,delivery=delivery))
        return line
    def lost(self,lines):
        """The connection failed before these lines were sent; nothing more is sent."""
        self.closed=True
        for line in lines:
            self.counts[line['device_id']]['forwarded']-=1;self.counts[line['device_id']]['unsent']+=1
    def summary(self):return {str(d):dict(c) for d,c in self.counts.items()}


def run_due(engine,now,record,deliver=None,clock=None):
    """Record every due engine record; with deliver, return the result lines to send."""
    lines=[]
    for event in engine.process_due(now,clock=clock):
        record(event)
        if deliver is not None:lines+=deliver.consume(event)
    return lines


def replay(path,engine,record,initialize=None):
    hello=False;previous=-float('inf');now=0.
    with Path(path).open(encoding='utf-8-sig') as stream:
        for line in stream:
            if not line.strip():continue
            message=json.loads(line)
            if not hello:
                validate_hello(message);hello=True
                if initialize:initialize()
                continue
            if not isinstance(message,dict) or message.get('type')!='sample':raise ValueError('Replay requires sample lines after hello')
            now=message.get('elapsed_s')
            if type(now) not in (float,int) or not 0<=now<float('inf') or now<previous:raise ValueError('Replay times must be finite and ordered')
            previous=now;engine.add(message,float(now))
            for event in engine.process_due(float(now)):record(event)
    if not hello:raise ValueError('Replay is empty')
    for event in engine.process_due(now+1.):record(event)


def connect_bridge(path):
    """Production transport is Unix-domain IPC on Ultra96/Linux, not replay."""
    family=getattr(socket,'AF_UNIX',None)
    if family is None:
        raise RuntimeError('This Python build has no Unix sockets. Use --replay on Windows; run --socket on Ultra96/Linux.')
    client=socket.socket(family,socket.SOCK_STREAM)
    try:
        client.settimeout(1);client.connect(path)
    except BaseException:
        client.close();raise
    return client


def observe_socket(path,engine,record,initialize=None,connection_factory=None,deliver=None):
    """Receiver continues while the single inference thread runs the backend.

    With deliver (a Delivery) the inference thread sends its result lines on the
    bridge connection; without it nothing is ever sent. A failed send ends the
    loop with a connection_lost record."""
    stop=threading.Event();ready=threading.Event();errors=[];lost=[]
    with (connection_factory or connect_bridge)(path) as client:
        def receive():
            pending=b'';hello=False
            try:
                while not stop.is_set():
                    try:data=client.recv(65536)
                    except socket.timeout:continue
                    if not data:break
                    pending+=data
                    while b'\n' in pending:
                        line,pending=pending.split(b'\n',1)
                        if len(line)>4096:raise ValueError('Bridge line too large')
                        if not line.strip():continue
                        message=json.loads(line)
                        if not hello:validate_hello(message);hello=True;ready.set();continue
                        if not isinstance(message,dict) or message.get('type')!='sample':raise ValueError('Unexpected bridge message')
                        engine.add(message,time.monotonic())
                    if len(pending)>4096:raise ValueError('Bridge line too large')
                if pending.strip():raise ValueError('Truncated bridge line')
                if not hello:raise ValueError('Bridge closed before hello')
            except Exception as error:errors.append(error)
            finally:stop.set();engine.reset(time.monotonic())
        receiver=threading.Thread(target=receive,name='hand-receive',daemon=True);receiver.start()
        initialized=False
        try:
            while not stop.wait(.005):
                if not ready.is_set():continue
                if not initialized:
                    if initialize:initialize()
                    initialized=True
                lines=run_due(engine,time.monotonic(),record,deliver,time.monotonic)
                for index,line in enumerate(lines):
                    try:client.sendall((json.dumps(line,separators=(',',':'))+'\n').encode())
                    except OSError as error:
                        lost.append(error);deliver.lost(lines[index:])
                        record(dict(type='connection_lost',error_type=type(error).__name__,message=str(error),
                                    results_unsent=len(lines)-index))
                        break
                if lost:break
        finally:
            stop.set()
            try:client.shutdown(socket.SHUT_RDWR)
            except OSError:pass
            receiver.join(2)
            if deliver is not None:deliver.closed=True  # the connection is closed: nothing more is sent
            run_due(engine,time.monotonic(),record,deliver,time.monotonic)
        # After a lost connection the receiver's failure is its consequence, not a new fault.
        if errors and not lost:raise errors[0]
        for error in errors:record(dict(type='receive_error',error_type=type(error).__name__,message=str(error)))


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',required=True);p.add_argument('--allow-synthetic',action='store_true')
    source=p.add_mutually_exclusive_group(required=True)
    source.add_argument('--replay');source.add_argument('--socket')
    p.add_argument('--observe-only',action='store_true',help='socket mode: record only, send no results')
    p.add_argument('--session-id',default='ltc-comms',help='session of the local hand-event hello; never sent')
    p.add_argument('--backend',choices=('numpy','fpga'),default='numpy')
    p.add_argument('--bit');p.add_argument('--ip-name',default='gesture_cnn_hand_u2_cache_0')
    p.add_argument('--threshold',type=float,default=.7);p.add_argument('--confirmations',type=int,default=3)
    p.add_argument('--interval',type=float,default=.2)
    p.add_argument('--out',required=True,help='a new JSONL file, or an existing folder for a new file')
    a=p.parse_args(argv)
    if a.socket and not hasattr(socket,'AF_UNIX'):
        p.error('This Python build has no Unix sockets. Use --replay on Windows; run --socket on Ultra96/Linux.')
    if a.backend=='fpga' and not a.bit:p.error('FPGA mode requires the NEW matching --bit and .hwh')
    if a.backend=='numpy' and a.bit:p.error('--bit is only meaningful with --backend fpga')
    if a.observe_only and not a.socket:p.error('--observe-only is for --socket; --replay never sends results')
    hello=None
    if a.socket and not a.observe_only:
        try:hello=make_hello(a.session_id,secrets.token_hex(16),LEASE_MS,a.threshold,a.confirmations)
        except ValueError as error:p.error('Compat delivery refuses these settings: '+str(error))
    bundle=ModelBundle(a.bundle,a.allow_synthetic)
    # Validate settings before allocating buffers or downloading an overlay.
    engine=HandEngine(None,a.threshold,a.confirmations,a.interval)
    recorder=Recorder(output_path(a.out),a.backend,bundle.synthetic,hello);backend=None
    delivery=Delivery(hello,recorder.write) if hello else None
    recorder.write(dict(type='bundle_verified',manifest_sha256=digest(bundle.folder/'manifest.json'),
                        model_parameter_sha256={str(d):bundle.models[d]['hash'] for d in (1,2)}))
    def initialize():
        nonlocal backend
        backend=(NumpyHandBackend(bundle) if a.backend=='numpy' else PynqHandBackend(bundle,a.bit,a.ip_name))
        engine.backend=backend
        if a.backend=='fpga':recorder.write(dict(type='hardware_artifacts',**backend.artifacts))
    try:
        if a.replay:replay(a.replay,engine,recorder.write,initialize)
        else:observe_socket(a.socket,engine,recorder.write,initialize,deliver=delivery)
    except BaseException as error:
        recorder.write(dict(type='error',error_type=type(error).__name__,message=str(error)))
        raise
    finally:
        try:
            if backend:backend.close()
        finally:recorder.close(**(dict(delivery=delivery.summary()) if delivery else {}))


if __name__=='__main__':main()
