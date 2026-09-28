# B07 CO：本机演示简短版

**用 `demo.py` 启动隧道、采集两块 ESP，并自动保存日志和报告。** 以下用于已经配置好的 `D:\LetThemCook`，普通 **Windows PowerShell 5.1 或 PowerShell 7** 均可，无需粘贴辅助函数。

视频文件名：**`B07_CO_subsystem.mp4`**；英文口播，无需幻灯片，上传 YouTube 时选择 **Unlisted**。源码放大到清楚可读。

**覆盖范围：** 本清单演示现有双 ESP 传输基线，尚未覆盖老师新提供的全部要求。新增功能、当前状态及验收标准见[英文需求文档](B07-CO-subsystem-requirements.md)。最终视频还须补齐每条通道的加密源码讲解、电脑与 Ultra96 的并发源码讲解，以及并发框图和协议状态机；新增功能实现后再更新对应操作。

录制顺序：**开场讲脚本和数据流程 → 启动并完成双 ESP 基线测试 → 分别演示恢复能力 → 最后讲重点源码**。下面的“录制前准备”在开录前完成；首次安装与部署仍参考完整指南。

### 录制前准备

- 电脑和 iPhone 连接 VPN，电脑蓝牙开启。使用已安装的新版 iPhone 应用。
- Ultra96 的 `ultra96.server` 服务需在运行，监听板端 `127.0.0.1:8888/9999`。如果还没启动，先按[完整指南的板端步骤](week7-testing-and-demo-guide.zh-CN.md#5-check-the-board-without-redeploying-or-stopping-it)检查并启动，不要重复启动。
- 正式开场时，电脑桥接程序未运行，两块 ESP 可以断电；镜头中再给两块 ESP 通电。按老师要求，演示时两块 ESP 都不能通过 USB 连接中继电脑，即使另有电源也不能保留 USB 数据线；使用两个独立电源，例如两块不会因低电流自动关机的充电宝，方便单独拿走一块 ESP 做超距测试。业务数据通过 BLE。
- 这是新的运行演示，固件、配对、证书和依赖已经预先配置好。输入为确定性模拟数据，10 Hz 表示每台每秒约 10 个包。
- 同时拍到电脑与手机。不要运行手机模拟器；它会替换真实 iPhone 的订阅。不要打开原始串口监视器，避免重置 ESP 或录入配对口令。

## 1. 开场：先讲脚本的基本逻辑（约 1 分钟）

**画面与讲解顺序：** 先拍两块 ESP、电脑和 iPhone，再打开 [demo.py](../demo.py#L212)，搜索 `main()`，展示三个命令的分支。这里只概括流程，底层通信代码留到第 7 节。

| 命令 | 先用中文理解它的作用 | 对应函数 |
|---|---|---|
| `python demo.py tunnel` | 建立电脑到板端的数据接入隧道，密码由 SSH 提示输入 | `run_tunnel()` |
| `python demo.py run` | 填好两块 ESP 的参数，启动现有双设备桥接程序；同时显示并保存日志，结束后显示报告 | `capture_command()`、`run_capture()` |
| `python demo.py report` | 重新读取最近一次已保存的结果，显示计数与通过/失败状态 | `latest_report()`、`show_report()` |

可以顺手定位 [capture_command()](../demo.py#L58)，指出它调用 `laptop.dual_bridge`。**`demo.py` 是启动和记录入口；实际的并发接收、转发在双设备桥接程序里。** `run` 默认 60 秒，每次新建证据目录；它不负责启动板端服务，也不操作 iPhone 的 Connect。

接着用一句话介绍数据方向：**ESP 1/2 → BLE → 电脑双设备桥接 → SSH 隧道内的 TLS → Ultra96；Ultra96 → 手机自己的 SSH/TLS 连接 → iPhone。** 板端另向电脑返回接入 ACK。

**English（设备介绍）：**

> This is B07's communication subsystem. Two physical ESP32s send dummy data at ten hertz each. The laptop receives and forwards both streams to Ultra96, and the iPhone receives results directly from the board. The devices and certificates were configured earlier; I will now start a fresh run.

**English（指着脚本讲）：**

> This launcher provides three commands: tunnel, run and report. Tunnel opens the laptop's SSH connection. Run starts the existing two-device bridge, saves live logs and prints the final counts. Report reads the saved evidence again. The bridge handles the concurrent data streams; the launcher makes the demonstration easier to run.

## 2. 终端 A：启动隧道

在 PowerShell 中执行，按提示输入两跳密码，然后保持此窗口打开。已有确认属于本项目、使用 `18889` 的隧道时直接复用，不重复启动。

```powershell
cd D:\LetThemCook
python demo.py tunnel
```

脚本使用交互式 SSH，沿用已有主机信任配置，不保存密码。启动后安静等待属于正常情况；是否真正通信成功，要看后面的 ACK 和报告。输入密码时不要显示或录入口令。

## 3. 终端 B：检查两台 BLE，然后连接手机

两块 ESP 通电后，在第二个 PowerShell 窗口执行：

```powershell
cd D:\LetThemCook
python -m laptop.windows_pairing --address 38:18:2B:19:82:AE
python -m laptop.windows_pairing --address 38:18:2B:18:9D:6A
```

两台均应显示 `authenticated_bond: true`；这确认已有认证绑定。若失败或要求首次配对，先完成配置再录制。**下一步桥接程序才建立实际数据连接并订阅通知。** 上述地址对应当前 ESP 1/2，换设备后须重新核实。

iPhone 打开 Unity → **Week 7 Connect / Settings → Connect**。确认 **`Subscribed, Received: 0`**。保持应用前台，不锁屏、不再次 Connect，直到本次计数记录完。

**English:**

> Both devices have authenticated Bluetooth bonds. The phone is subscribed with a count of zero. I will now connect to both ESP32s and start receiving their notifications.

## 4. 终端 B：运行 60 秒，显示并保存日志

手机显示 `Subscribed, Received: 0` 后执行：

```powershell
python demo.py run
```

默认运行 **60 秒**，使用第 3 节的两台地址、端口 `18889`，以及当前用户主目录下的 `.codex\private\cg4002-week7-20260906\ca-cert.pem`。如需换地址、CA 或端口，执行 `python demo.py run --help` 查看选项。

脚本会新建本次目录，实时显示并保存日志，结束后显示每台计数和采集通过/失败。让程序自然结束，不要中途按 Ctrl+C；连接准备及最终排空会使总耗时略长于 60 秒。默认每秒显示两路进度，ACK 窗口为每台 32，使用 `week7-demo` 会话。

你会看到类似以下格式，数值以实际运行结果为准：

```text
progress mode=physical phase=observation device=1 received=100 processed=100 acked=98 queue=0 drops=0 errors=0
progress mode=physical phase=observation device=2 received=100 processed=100 acked=99 queue=0 drops=0 errors=0
```

观察这三件事：

1. `device=1` 和 `device=2` 的 `received`、`acked` 在同一运行期间都持续增加。
2. `drops=0`、`errors=0`；手机 `Received` 增加，并出现以 `1:` 和 `2:` 开头的结果 ID。
3. 日志是每秒的累计计数，不是逐包内容。`received` 表示 BLE 回调数，`processed` 表示已处理数，`acked` 表示电脑收到的板端确认数；运行时暂时不同可以正常，结束后必须对账。

**English:**

> Both device counters are increasing during the same run. Received counts show BLE input, and ACK counts show that Ultra96 has accepted the forwarded messages. The phone is displaying results from both device IDs.

## 5. 终端 B：看报告、核对手机

`run` 结束时会自动显示摘要。之后要重新查看最近一次采集，只需：

```powershell
python demo.py report
```

它按目录修改时间选择最近一次采集；即使最近一次未完成，也不会退回旧的成功报告。本次正常测试通过需要：

- 退出码为 `0`、`clean=true`、`mock_input=false`、`report_saved=true`；两台受保护连接正常，`unfinished=false`。正常无重连时 BLE/TLS 连接数各为 1。
- 每台 **`generated = source_submitted = received = acked`**，两项 `missing` 均为 0。这里的 `received` 是源端审计中的已接收样本数。
- 等手机计数稳定后，手动核对 **手机结束计数 − 开始计数 = 两台 `generated` 之和**。只有有效、clean 的实体采集，脚本才会显示预期手机增量。**脚本不会读取 iPhone 屏幕**；初始为 0 时直接比较手机结束计数，并记录画面。

不要固定要求“一分钟恰好 1,200 包”，连接启动和收尾也可能产生样本。未完成报告、`clean=false` 或源端 `null` 都不能算通过。`clean` 汇总了源端核对及错误/丢弃等检查；全部字段见[完整验收说明](week7-testing-and-demo-guide.zh-CN.md#7-capture-a-complete-physical-run-and-save-its-outcome)。

文件保存在 **`D:\LetThemCook\.week7-local\B07-时间戳\`**：

| 文件 | 用途 |
|---|---|
| `live.log` | 本次电脑进度、错误及最终输出 |
| `report.json` | 原始结构化报告，包含两台设备计数和源端审计 |
| `exit-code.txt` | 本次退出码，正常通过为 0 |
| `report-readable.json` | 原始报告是有效 JSON 时，自动保存的缩进版本 |

**English（核对通过后，用实际数字替换）：**

> Device one generated [N1] packets, and device two generated [N2]. The generated, received and acknowledged counts match. The phone count increased by [N], matching the combined source total. No packet loss was detected in this connected capture.

手机的证据是总计数，不能把板端 ACK 当作每个结果已被手机接收的证明。停止发送约两秒后，手机显示 `No live result` 属于正常显示过期。

## 6. 恢复能力：按操作、观察、核对分别录

先保存第 5 节的成功基线。以下命令均在**终端 B**运行，终端 A 的隧道保持打开；一次只改变一个条件。每段口播名称，并记录脚本打印的 `Saved in:` 路径和手机开始/结束计数，避免把不同测试混在一起。`python demo.py report` 默认只显示最近一次结果，旧结果从各自目录查看。

### 6.1 空闲后继续发送：手机不重新 Connect

1. 等基线运行自然结束，记录手机当前计数，保持 Unity 前台。两块 ESP、VPN 和隧道都保持原状。
2. **至少 120 秒不运行新的采集命令**，用电脑上的时钟或秒表计时；不要切走手机应用。约两秒后出现 `No live result` 正常，连接状态仍应是 `Subscribed`，计数应保持不变。
3. 等待结束后，再记录一次手机计数，然后执行：

```powershell
python demo.py run
```

4. 拍到两台 `received/acked` 重新增加、手机出现新结果；全程不点手机 Connect。
5. 结束后应显示 `CAPTURE PASSED`。用**本次手机结束计数减去第 3 步的开始计数**，核对 `Phone expected increase`；不要直接拿累计计数比较。

**English：**

> I have stopped sending for two minutes while keeping the phone in the foreground. The live label has expired, and the phone still shows Subscribed. I will restart the capture without pressing Connect. I will then compare the increase in the phone count with this run's source total.

### 6.2 一块 ESP 断电：观察另一块是否继续工作

1. 两台正常供电、手机仍订阅时，启动独立的故障段：

```powershell
python demo.py run --duration 120
```

2. 等两行进入 `phase=observation` 且计数增加，再开始用秒表计时。约 **20 秒**时，拍到你拔掉 **ESP 1 的唯一电源**。确认它没有同时从另一根线供电；保留 ESP 2 的供电、VPN 和隧道。
3. 持续观察约 **20 秒**：ESP 1 的 `received` 停顿，ESP 2 的 `received/acked` 应继续增加。ESP 1 的 ACK 可能先排空已有数据；蓝灯状态本身不是数据收发证据。
4. 约 **40 秒**时恢复 ESP 1 电源，**不重启电脑程序**。拍到后续重连与 `device=1` 输入恢复，同时 ESP 2 继续推进。按本次实际等待时间说明，不承诺固定几秒内恢复。
5. 等 120 秒采集自然结束，保存故障日志。预期显示 **`CAPTURE NOT PASSED`**；在 `report-readable.json` 查看设备 1 的 `disconnects`、`ble_connections` 和 `source` 中断记录。重启会改变 boot ID，源端数可能显示 `null`（摘要为 `N/A`），不能当作 0 或据此计算“无丢失”的手机总数。

**English：**

> I am removing power from ESP one. Its input stops, while the laptop continues receiving ESP two's data and acknowledgements from Ultra96. I will restore power without restarting the bridge. This interrupted capture is expected to be marked as not passed; it records the failure rather than counting it as a clean run.

**恢复后再做正常验收：** 等故障段自然结束、两台供电和手机计数都稳定，记录手机当前计数，执行一次新的 `python demo.py run`。它会建立新的源端统计边界；要求新报告 `CAPTURE PASSED`，且手机增量匹配。故障段的计数不要并入这次对账。

若本次 ESP 1 没有在故障段结束前恢复，保留该结果并如实说明；重新检查供电和 BLE 后再做新的正常采集，不能把手动重启后的结果描述成“同一运行中自动恢复”。

### 6.3 手机锁屏后恢复：明确演示手动重新连接

1. 等上一段采集结束、手机计数稳定并记录后，**没有采集程序运行时**锁屏约 20 秒。ESP、电脑 VPN 和终端 A 均保持运行。
2. 解锁并返回 Unity，拍到 `Paused`。这是应用失活后的暂停行为，不要求锁屏期间继续接收。
3. 点击 **Week 7 Connect / Settings**，重新输入凭据并 Connect。等新会话显示 **`Subscribed, Received: 0`**，再开始下面这段：

```powershell
python demo.py run --duration 30
```

4. 拍到新结果出现；结束后要求 `CAPTURE PASSED`，且手机计数等于此次 `Phone expected increase`。输入密码时不显示口令。

**English：**

> I will lock the phone while no capture is running. On returning to Unity, the app shows Paused. I reconnect manually, start a new thirty-second capture, and verify that results and matching counts return. This demonstrates foreground recovery after an explicit reconnection.

### 6.4 可选：再录一次十分钟连续运行

记录手机开始计数，执行 `python demo.py run --duration 600`。保持手机前台、两台 ESP 供电以及 VPN/隧道稳定，中途不施加故障。结束后仍按第 5 节核对实际源端总数与手机增量；这是稳定运行测试。

以上口播和通过结论都以本次实际观察为准。系统不承诺补回断电、断网或手机暂停期间的全部数据。

## 7. 最后展示重点源码（约 3–5 分钟）

先结束测试并保存手机计数画面，再放大编辑器。每次展示约 **20–35 行**，按下面顺序定位函数，停留让观众看清；不必从文件第一行一路滚到最后。行号是当前版本提示，优先用函数名搜索。

### 7.1 ESP 怎样生成、发送测试包

打开 [week7_packet.h 的 dummyValue()](../firmware/esp32/include/week7_packet.h#L16)，说明八个值按序号计算；再打开 [main.cpp 的 loop() 发送分支](../firmware/esp32/src/main.cpp#L398)，指出 100 ms 门限、`allocateSampleSequence()`、`serializeDummyPacket()` 和 `recordSensorSubmission()`。只有通知条件和 MTU 满足时才生成/提交样本。

**English：**

> The ESP generates deterministic dummy values from the sequence number. When the BLE connection is ready, it creates a packet about every hundred milliseconds and records whether submission succeeded. The device, boot and sequence IDs let us identify each sample.

### 7.2 电脑怎样连接 BLE 并接收数据

打开 [bridge.py 的 ble_loop()](../laptop/bridge.py#L600)，分别定位设备发现/认证绑定检查，以及 `start_notify()` 附近的回调。指出两台按地址选择，回调将数据放入该设备的有界队列；断开后的重试也在这个循环中。

**English：**

> The bridge discovers the selected ESP, checks the protected connection requirements and subscribes to notifications. The callback queues incoming bytes for processing. After a disconnect, this loop attempts to connect again.

### 7.3 为什么两台 ESP 可以同时推进

打开 [dual_bridge.py 的任务创建段](../laptop/dual_bridge.py#L83)，指出 `writers` 和 `inputs` 中两台各自的 `asyncio.create_task()`。再定位 [bridge.py 的 _pipeline_epoch()](../laptop/bridge.py#L458)，展示独立的发送和 ACK 接收任务、待确认消息窗口。开场脚本把窗口配置为每台 32。

**English：**

> Each ESP has its own input task, queue and TLS writer. Asynchronous I/O lets both streams progress during the same period. Each device can have up to thirty-two messages awaiting acknowledgements, so sending does not wait for one round trip after every packet.

这是 I/O 并发；不需要声称无线电在完全相同瞬间发射，或 Python 使用两个 CPU 核心。

### 7.4 怎样证明本次计数对得上

打开 [source_audit.py 的 report()](../laptop/source_audit.py#L149)，指出起止源端快照、同一 boot 检查，以及 `generated/received/acked` 比较。然后打开 [demo.py 的 _clean_capture()](../demo.py#L103) 和 [show_report()](../demo.py#L122)，解释它只在有效的 clean 实体结果下显示通过和预期手机增量，手机实际增量由操作者核对。

**English：**

> Source snapshots define how many samples were generated during the capture. We compare that total with received packets and validated acknowledgements. An interruption or incomplete report cannot pass. The phone's actual count must still be checked separately.

### 7.5 板端和手机分别负责什么

打开 [server.py 的 _ingest()](../ultra96/server.py#L232)，指出校验、去重、模拟结果与 ACK；再定位 [_gateway()](../ultra96/server.py#L260)，说明手机使用独立订阅连接。

**English：**

> Ultra96 validates each message, creates a deterministic test result and returns an ingestion acknowledgement to the laptop. Results use the phone's separate subscribed connection. A laptop ACK alone does not prove delivery to the phone.

若要对应刚才的两种手机行为，补充展示 [Subscriber.swift 的 channelRead()](../ios-visualizer/Week7Native/Sources/Week7Transport/Subscriber.swift#L37) 中完整帧后取消计时器的逻辑，以及 [IntegrationController.swift 的失活通知处理](../ios-visualizer/Week7Native/Sources/Week7Bridge/IntegrationController.swift#L26)。

**English：**

> A subscribed connection can remain idle between complete frames. When the app becomes inactive, it deliberately pauses and requires an explicit Connect after returning.

**English 结尾（正常测试和观察符合后）：**

> The clean captures demonstrate concurrent reception and forwarding from both ESP32s, with matching source and acknowledgement counts and a matching aggregate phone count. The separate recovery tests show what happens during interruption and how normal operation is restored.

结束时，在终端 A 按 Ctrl+C 停止本次启动的隧道。完整原理见[技术报告](week7-system-technical-report.zh-CN.md)，首次配置和故障排查见[完整测试指南](week7-testing-and-demo-guide.zh-CN.md)。本次仅更新录制清单，没有重新执行实体测试。
