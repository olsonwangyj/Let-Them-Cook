# B07 CO 录像操作稿：先拍实物，再录电脑

**日常只用两个入口：`flash.py` 负责固件，`demo.py` 负责隧道、Video / Live 和报告。** `run` 完成后自动显示报告与两台匹配的 sensor/ACK；手机接收情况直接拍摄同次运行的开始、增长和结束画面，不输入手机计数。原来的通信实现在 bridge/server 中继续复用。

每新开一个 PowerShell，先进入仓库：

```powershell
Set-Location D:\LetThemCook
```

## 常用命令与最短录制顺序

| 展示稿入口 | 在 PowerShell 运行 | 什么时候用 |
|---|---|---|
| [R01 Flash，第 1767 行](./B07-CO-video-presentation.en.md#r01) | `python flash.py` | 一次命令先构建两份，再提示用同一根烧录 USB 线接左板、换右板，依次检测并上传 |
| [R02 Tunnel，第 1780 行](./B07-CO-video-presentation.en.md#r02) | `python demo.py tunnel` | 终端 A 开 SSH 隧道并保持运行 |
| [R03 Video run，第 1791 行](./B07-CO-video-presentation.en.md#r03) | `python demo.py run` | 终端 B 默认采集 60 秒、每台 10 Hz，结束自动显示报告和匹配数据 |
| [R04 Live，第 1802 行](./B07-CO-video-presentation.en.md#r04) | `python demo.py live` | 默认 120 秒、每台 10 Hz，开放键盘 1 / 2 命令；见后面的 Live 小节 |

**Video 用 `run`，Live 用 `live`，同一场景只选一个。** 报告自动显示；首次配对、串口监视和服务维护见文末按需功能。

**常规录像：** A1 首次拍真实 `flash.py` 编译/上传 → 断开 laptop USB、两板独立供电 → A2 拍 ID/包格式源码 → 终端 A `demo.py tunnel` → 手机 Connect / Subscribed → 终端 B `demo.py run` → 自动报告和匹配数据、拍清手机结束画面 → A7 改 JSON、再 `flash.py`、拔 USB 后再 `demo.py run` → B 阶段讲图与代码。固件未改、setup 已录好的后续采集，从隧道和手机连接开始，不重复刷板或配对。

串口识别只在首次或 COM 变化时用 `python flash.py --ports`；查看端口不会烧录。隧道、串口监视和前台服务占用各自当前终端，不在这些终端里输入下一条采集命令。

**本次使用两个主文档：**

| 文件 | 用途 | 怎么打开 |
|---|---|---|
| [B07-CO-video-presentation.en.md](./B07-CO-video-presentation.en.md) | 投屏展示稿：G01–G11 图解、英文旁白、带英文注释的 C01–C40 源码和 R01–R08 操作说明 | VS Code 打开，Ctrl+Shift+V 预览；Ctrl+F 找 Gxx/Cxx/Rxx，点内部代码链接跳转，再点 Back to Gxx 返回 |
| [B07-CO-video-operator-script.zh-CN.md](./B07-CO-video-operator-script.zh-CN.md) | 本操作稿：中文步骤、短命令、英文口播、源码定位 | 放在旁边参考，不必把整篇投屏 |

**录像顺序固定为 A → B。** 第一阶段用**摄影手机**拍 FireBeetle 的真实设置、同一台 Windows laptop 上的 USB 烧录操作、电脑屏幕里的 ID/包格式源码，以及实际通信现象；第二阶段才用电脑屏幕录制图解、加密和并发源码。**“手机录像”也包括用相机拍电脑屏幕，不是只拍硬件外观。** 摄影手机和 **Visualizer iPhone** 是不同设备。Visualizer iPhone 全程运行 Unity，摄影手机负责相机和收音；不要在 Visualizer iPhone 打开相机、锁屏或切出 Unity。

A、B 可以分两次、不同时间录制。B 阶段重看 A 阶段保存的报告和日志时，要明确说是 **the recorded capture**；不需要重跑实体采集，也不能把文件重放说成新的现场通信。建议先录好 A 的完整证据，再一次性录完 B。成片时长按内容需要安排，下面不是老师规定的分钟数。

## 本稿对应的 Video 要求

| 老师的要求 | 必录实物段 | 必录电脑段 |
|---|---|---|
| Laptop ↔ Ultra96 — Live + Video | A3、A5、A6：真正发送与接收 ACK | B6 / G06 分帧；B7 / G07 协议 FSM |
| Ultra96 ↔ phone Visualizer — Live + Video | A4–A6：订阅、结果、实际手机计数 | B8 / G08 订阅 FSM；B1 / G01 独立结果路径 |
| **FireBeetle setup — Video only** | **A1：打开项目/配置，真实编译烧录及 SUCCESS，两块板标签、独立供电、通电和认证绑定** | B2 / G02 是图解回顾，不替代 A1 实操 |
| **Explain FireBeetle: Device IDs / packet types / packet format — Live + Video** | **A2：直接拍电脑打开 platformio.ini、sensor.py、control.py、protocol.py 并讲字段**；A6 对照实际日志 | B3–B4 / G03–G04 图解回顾；B5 / G05 BLE FSM |
| Encryption walkthrough in every channel — Video only | A1 的绑定结果作为实物佐证 | B9 / G09：BLE、laptop–Ultra96、Ultra96–iPhone 三条通道源码 |
| Laptop + Ultra96 concurrency/threading walkthrough — Video only | A5 两路进度同时增长 | B10 / G10、B11 / G11：两张框图和任务/队列源码 |
| General：修改 dummy packets 并 recompile/rerun | **A7：现场改 JSON、重新构建/上传、独立供电后新采集、对照两台设备的更新值** | B3 回顾修改前后已保存的证据；英文展示稿 D01 提供对应说明 |

General 要求放在相应段落：实际格式的多组随机 dummy 数据、可修改后重跑、FSM、并发框图、清楚的解码日志/两路颜色、无 relay laptop USB、服务器在 Ultra96、无 message broker、TCP 消息可能分段。本稿主体按 Video 要求录像；末尾给出同一入口的 Live 快捷用法。最大速率、文件传输及故障/鲁棒性演示另行安排，10 Hz 不是最大速率；60 秒只是 Video 通信镜头的采集长度。

## 开录前准备：不计入口播

1. Windows 的 Python 应能运行项目；本机核实过 Python 3.12.7 和 Bleak 3.0.1。打开 PowerShell，执行开头的 `Set-Location D:\LetThemCook`。在 VS Code 打开 `D:\LetThemCook\docs\B07-CO-video-presentation.en.md`，按 Ctrl+Shift+V 预览；把此操作稿放旁边参考。
2. 本机已准备 PlatformIO 和串口驱动；本次在 A1 用**同一台 laptop** 拍真实构建/上传过程。**USB 只用于 setup；用一根烧录 USB 线依次烧录两板；另一口一直接鼠标，无需拔鼠标，实际 BLE 通信前两板都断开 laptop USB、改独立供电。** Ultra96 和已安装的原生 iPhone App 都支持匹配的 v2。更新仓库不等于更新已经烧录/安装的程序；不要为了录像无理由清除既有认证绑定。
3. Windows 蓝牙开启；Windows 和 Visualizer iPhone 均开启所需 VPN。关闭连接这两块板子的其他 BLE 客户端。
4. Ultra96 当前服务需监听板端 `127.0.0.1:8888` 和 `127.0.0.1:9999`。需要确认状态时按附录运行 `python demo.py service`；仅不存在且端口空闲时加 `--start`。当前部署源码目录为 `/var/tmp/cg4002-week7-yanjie-20260907/source-co-v2-20260928T122047Z`；历史 PID 不能当作当天状态。
5. 手机是本次唯一结果订阅者。不要另跑 `phone.receiver`、`laptop.phone_simulator`、`tools.rehearse_remote_week7`；新订阅者会替换旧订阅者。
6. 准备两个独立电源，例如不会因低电流自动关机的充电宝。A1 烧录/首次串口配对时可以 USB 接这台 laptop；A5 开始实体 BLE 采集前，两块板都必须**完全断开 laptop USB**，各自使用独立电源，即使另有电源也不能保留 laptop USB 线。
7. 默认 CA 是 `C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\ca-cert.pem`。这是已有可信公开证书，不为普通录像重新生成 PKI；不打开任何私钥文件。
8. 密码输入和首次配对口令放在镜头外完成。电脑终端字号调到手机能拍清，关闭通知；摄影手机试拍一次，确认无反光且能读清 Visualizer 的计数。

| 窗口名称 | 机器 | 本次用途 |
|---|---|---|
| 终端 A | Windows relay laptop，自己打开的 PowerShell | `demo.py tunnel`；真实采集时保持运行 |
| 终端 B | 同一 Windows laptop，另一 PowerShell | `flash.py` 构建/上传；`demo.py run/live`；需要时 `report` |
| 串口终端 | 首次配对时按需另开一个，一次连接一块板 | `flash.py --monitor 实际COM` 读取当前板口令；完成后退出，再换下一板 |
| Ultra96 服务终端 | 需要维护时另开 PowerShell | `demo.py service` 检查；`service --start` 启动后保持运行 |
| VS Code 编辑器 + Markdown 预览 | 同一 laptop；A 阶段相机拍屏，B 阶段电脑录屏 | 图解、英文注释代码、A 阶段保存的日志 |

## 第一阶段 A：摄影手机拍 setup、包格式说明与真实通信

**这阶段要拍电脑上的 setup 和 packet 源码操作。** A1/A2 先做设置和包格式解释，A3–A6 连续完成数据链路；实际采集开始后不再穿插源码讲解。图解、加密和并发 walkthrough 留到 B 阶段。英文块可以现场说或后配音；成功结论必须等实际核对后再录。

### A0｜摆好机位与开场

**画面：** 摄影手机横拍，两块带标签的 FireBeetle、电源、relay laptop 和 Visualizer iPhone 同框。Ultra96 可通过部署说明交代位置，不把笔记本说成服务器。

**操作：** 电脑显示 VS Code 的展示稿预览，终端 B 已进入仓库；确认尚无采集程序运行。摄影手机开始录像，先停留 5 秒拍清各设备。此时不要切换 Visualizer iPhone 去拍其他东西。

**英文口播：**

> This is B07's communication subsystem. I will first show the FireBeetle setup, actual firmware upload and packet-format code with this camera, followed by a physical communication run. Later, a computer screen recording will explain the diagrams, encryption and concurrency. The filming phone and Visualizer iPhone are different devices.

**简述两个入口：**

> Flash builds and uploads the firmware. Demo opens the tunnel, runs the Video or Live capture, and displays the saved evidence. The report appears automatically after a capture. I film the phone directly to show its actual reception.

### A1｜FireBeetle setup — [Video only]：真实编译、上传、供电与绑定

**本段用摄影手机拍电脑屏幕和板子；真的执行构建/上传并拍成功结果，不只展示命令。** 这是 setup 阶段，尚未运行 BLE 采集。同一台 Windows laptop 可接 USB 烧录；本段使用同一根烧录 USB 线依次连接左板和右板；末尾拍清两板均已断开 laptop USB、各自独立供电。

**A1.1 打开固件项目并指出左右环境。** 在编辑器按 Ctrl+O，打开 `D:\LetThemCook\firmware\esp32\platformio.ini`，Ctrl+F 搜索 `firebeetle32-left`。拍清 `board = firebeetle32`、`framework = arduino`、left/right 两个环境和 `WEEK7_DEVICE_ID=1/2`，不要选择 `firebeetle32-unprotected-diagnostic`。

> I am setting up both FireBeetle ESP32 boards. PlatformIO builds Arduino firmware for the firebeetle32 board. The left environment assigns device ID one, and the right environment assigns device ID two. I will program them in turn using one programming USB cable, then power both independently for the BLE demonstration.

**A1.2 贴好 left / right 标签，使用一根烧录 USB 线。** 不需要同时连接两块板，也不用预先填写一对 COM。确认串口监视已退出，接线按下一步脚本提示进行；如果需要单独辨认串口，可用 `python flash.py --ports` 只读查看。

**A1.3 R01：一条命令依次烧录两块板。** 在终端 B 运行：

```powershell
python flash.py
```

| 提示阶段 | 你实际做什么 | 镜头保留什么 |
|---|---|---|
| 生成与构建 | 等 fixture 头生成、左右环境都构建成功 | 两个 profile 的构建结果；失败就停止 |
| 接 LEFT | 把烧录 USB 线接到标签 left 的板，按 Enter | 当前检测到的 COM、device 1 环境、左板 upload 成功 |
| 换 RIGHT | 拔掉左板，把同一 USB 线接到 right，再按 Enter | 重新检测的 COM、device 2 环境、右板 upload 成功 |
| 两次完成 | 拔掉右板；两块板各接独立电源 | 两板均不再连接 laptop USB |

每个上传阶段都重新检测当前串口：只有一个候选时自动选择，有多个时才按提示选当前板的实际 COM。**两次可以是同一个 COM 号**，由物理 left/right 标签与脚本阶段区分；没有保存端口映射的步骤。

> This script regenerates the fixture table and builds both device profiles. I connect the left board, then swap it for the right board when prompted. The script detects the serial port for each upload and stops if a step fails.

脚本使用本机已安装的 PlatformIO。拍清左/右 profile、各自 upload 成功以及实际换板；可以剪去构建等待，不能剪掉失败后宣称成功。

**预期：** 对应环境显示 `SUCCESS` 且退出码 0；失败不能接着口播已烧录成功。此时不需要打开 server 私钥或串口 dump。

> The left and right uploads have completed successfully. Each board now contains the firmware built for its assigned device ID. A successful upload proves programming completed; the authenticated BLE checks and data capture will establish communication next.

**A1.4 首次配对或绑定恢复才做；正常已有绑定略过。** 不清除绑定，也不在每次刷板后重新配对。`demo.py run` 会在连接时自动检查认证，A5 拍到 `BLE_connected`、`authenticated=True` 才继续成功口播。

> This setup option opens the selected serial port at one hundred and fifteen thousand two hundred baud. I keep pairing passkeys off camera and close the monitor before uploading or starting the wireless demonstration.

一根烧录 USB 线的首次配对仍是一次一板。暂停拍摄口令屏幕，终端 B 和一个独立串口终端都先进入仓库；按下表完成左板，再重复右板：

| 阶段 | 接线/终端操作 |
|---|---|
| 只接左板 USB | 终端 B 用 `python flash.py --ports` 查看当前 COM |
| 左板口令 | 串口终端运行 `python flash.py --monitor COM4`；COM4 只是示例，换成左板实际 COM，保持此终端运行 |
| 左板认证 | 终端 B 运行 `python flash.py --pair left`，在隐藏提示输入左板串口显示的真实口令 |
| 换板 | 串口终端 Ctrl+C 退出；左板换独立电源，同一根烧录 USB 线接右板 |
| 右板口令/认证 | 用 `--ports` 查看当前 COM，再在串口终端运行 `--monitor 实际COM`；终端 B 运行 `python flash.py --pair right` |
| 结束 | 退出右板 monitor，拔右板 USB，右板也换独立电源 |

> This setup option uses the existing authenticated pairing tool for the selected board. I use left and right in turn during first-time setup; existing authenticated bonds are reused.

左右地址分别为 `38:18:2B:19:82:AE` 和 `38:18:2B:18:9D:6A`。成功应显示 `authenticated_bond: true`。不录 `PAIR LOCALLY`、不保存串口日志；若先运行配对才发现未开 monitor，Ctrl+C 取消后按上表重试，不猜口令。无参数的 `--pair` 会检查两板，一根烧录 USB 线的首次流程使用上面的显式 left/right，避免等待另一块尚未读取的口令。

**A1.5 拍清两板均已独立供电。** 最后一块板烧录/必要配对后，摄影手机拍到它从 laptop USB 拔下并换独立电源；同时拍清另一块已独立供电。沿电源线拍到两个电源，laptop 的 USB 口不再连接任何 FireBeetle。此时不再运行额外配对或串口命令；A5 启动时的认证连接日志是正常检查证据。

> USB setup is finished. Both boards are now disconnected from the relay laptop and powered independently. The capture checks their authenticated Bluetooth connections before streaming application data.

### A2｜Explain FireBeetle: Device IDs / packet types / packet format — [Live + Video]

**本段仍由摄影手机拍电脑屏幕，必须打开实际代码片段指出字段，不能只说有这些文件。** 在 VS Code 打开展示稿并按 Ctrl+Shift+V 预览。Ctrl+F 找 G02/G03/G04，点击对应的 Cxx 内部链接到代码区；每行的 `L原行号` 标记对应原文件，英文注释帮助解释。Ctrl+F 也可直接找 Cxx，再点 **Back to Gxx** 返回图解。此时尚未开始实际采集。

| 镜头顺序 | 在 Markdown 预览中定位 | 当场指给镜头的内容 |
|---|---|---|
| Device IDs | G02 → **C02 Board + IDs** → L21 / L26 | left / right 的 ID=1 / 2；L6 / L7 为板型和 Arduino |
| Sensor format | G03 → **C05 Sensor fields** → L11；返回后 **C06 Sensor codec** → L73 / L75 | struct、32-byte 长度校验、字段解码 |
| Random dummy | G03 → **C07 Fixtures** → L2–L5；**C40 Random source** → L94；**C08 Sensor send** → L507 / L508 | 多组八通道数据、esp_random、真实发送路径 |
| BLE packet types | G04 → **C09 BLE types** → L10–L16；**C10 Control codec** → L90 / L98 | opcode、响应位、14-byte 头、B7/version=1 |
| 网络类型/源端统计 | G04 → **C11 JSON types** → L8–L12；**C12 Source counters** → L49–L52 | SENSOR_BATCH/ACK/订阅/结果、source counters |

以上是生成投屏文件时保存的源码快照，**不会随着仓库修改自动更新**。若刚才改过 fixture/代码，改动部分应在编辑器打开实际文件并配新日志说明，不能用旧展示稿快照证明已更新。实际文件定位如下，编辑器 Ctrl+O 输入完整路径、Ctrl+F 输入定位词即可：

| 要讲什么 | 实际打开的文件 | Ctrl+F 定位并指给镜头 |
|---|---|---|
| Device IDs | `D:\LetThemCook\firmware\esp32\platformio.ini` | `WEEK7_DEVICE_ID=1` 和 `WEEK7_DEVICE_ID=2` |
| Sensor packet format | `D:\LetThemCook\common\sensor.py` | `_PACKET`、`decode_packet`、`to_message` |
| 多组随机 dummy payload | `D:\LetThemCook\common\dummy_fixtures.json` | 四组、每组八个数；无需搜索 |
| 随机序列化源码 | `D:\LetThemCook\firmware\esp32\include\week7_packet.h` | `serializeFixturePacket` |
| 固件随机数来源 | `D:\LetThemCook\firmware\esp32\src\main.cpp` | `fixtureRandomWord`、`esp_random` |
| BLE packet types / control header | `D:\LetThemCook\common\control.py` | `_HEADER`、`COMMAND`、`SET_RATE`、`RESPONSE_FLAG` |
| 网络 message types | `D:\LetThemCook\ultra96\protocol.py` | `SENSOR_BATCH`、`INGEST_ACK`、`SUBSCRIBE`、`GESTURE_RESULT` |

**先讲 Device IDs：** left 环境对应 device 1 / `38:18:2B:19:82:AE`；right 对应 device 2 / `38:18:2B:18:9D:6A`。地址选择硬件，应用 ID 标识数据，两者不是同一个字段。

> The left firmware is device one and the right firmware is device two. Their Bluetooth addresses select the physical boards. The device ID inside each packet identifies the application source. A boot ID distinguishes different startups, and the sequence number identifies a sample within that boot.

**再讲 Sensor packet format。** 在 `sensor.py` 指 `<2sBBIII8h`，按字节依次说明：

| 字节 | 长度 | 字段/类型 |
|---|---:|---|
| 0–1 | 2 | Magic `W7` |
| 2 | 1 | Version，当前 2 |
| 3 | 1 | Device ID，1 或 2 |
| 4–7 | 4 | Boot ID，uint32 |
| 8–11 | 4 | Sequence，uint32 |
| 12–15 | 4 | Uptime ms，uint32 |
| 16–31 | 16 | 八个 signed int16 values |

> This struct defines a thirty-two-byte sensor packet. It contains the W7 marker, version, device ID, boot ID, sequence, uptime and eight signed sixteen-bit values. Multi-byte fields use little-endian encoding. Version two randomly selects from these editable fixtures while preserving the real sensor packet format. Repeating a fixture is allowed. The decoded logs later show the actual transmitted values.

**最后讲 Packet types 和 control format。** 指 `control.py` 的 `<2sBBBBII>`：Magic 2 + version 1 + opcode 1 + device 1 + status 1 + ID 4 + offset 4 = 14 bytes。它是 `B7`、控制 version=1，和 sensor version=2 分开编号。Opcode 1 command、2 rate、16–19 file begin/chunk/end/abort；响应置 bit 7。

| 通道/方向 | 类型 | 镜头里怎么解释 |
|---|---|---|
| ESP → laptop | `W7` notification | 32-byte sensor 样本，独立 characteristic |
| Laptop 读取 ESP | `W7S1` source counters | 源端生成/提交统计，用于最终对账 |
| Laptop ↔ ESP | `B7` request / response | command、rate、file 控制，匹配 request ID |
| Laptop → Ultra96 → laptop | `SENSOR_BATCH` / `INGEST_ACK` | JSON 样本与 accepted / duplicate 接入确认 |
| Phone ↔ Ultra96 | `SUBSCRIBE` / `SUBSCRIBED` / `GESTURE_RESULT` | 订阅及结果，手机走自己的连接 |

> The sensor stream uses W7 notifications. The laptop reads W7S1 source counters for reconciliation. Bidirectional controls use a separate B7 header carrying the opcode, device, status, request ID and offset. A response sets bit seven of the opcode. A command contains a complete sensor packet; our upcoming run uses the rate request and response to set ten hertz.
>
> After decoding, the laptop sends SENSOR_BATCH JSON to Ultra96 and validates INGEST_ACK. The phone sends SUBSCRIBE, receives SUBSCRIBED, and then receives GESTURE_RESULT messages. These are distinct message types with different roles. I will show a real decoded sensor and matching acknowledgement from this capture at the end.

**修改 dummy packets 的实际演示安排在 A7。** 先完成 A3–A6，保存修改前的真实数据；然后拍下编辑、重新编译/上传和新采集的完整过程。本稿把这项 General 要求安排为独立实操，不只口头介绍。第二组第一项 `1200 → 1500` 是可直接使用的示例；若老师指定其他值，仍保持每组八个 int16、总共 2–64 组。

### A3｜启动或展示本次 SSH 隧道

**R02 操作：** 自己打开终端 A，进入仓库后运行：

```powershell
python demo.py tunnel
```

> This command opens the existing SSH route to Ultra96. I keep this terminal open during the demonstration.

在**当前终端 A** 输入两跳密码，随后保持它运行；它不另开窗口。A5 要切到终端 B，不能在隧道终端输入下一条采集命令。

若需输入两跳密码，暂时把镜头移开；也可以录前私下启动，镜头中说明它已运行。已有确认属于本项目、使用本地 18889 的隧道就直接复用，不开第二个实例。

**预期：** 提示 `Opening SSH tunnel on 127.0.0.1:18889`；完成认证后安静等待正常，窗口保持打开。隧道存在不等于应用通信成功，后面必须看到 ACK。路径为 laptop `127.0.0.1:18889` → SSH → Ultra96 `127.0.0.1:8888`。

**英文口播：**

> The laptop's SSH tunnel is running. It forwards this local port to the private ingestion service on Ultra96. I entered the credentials outside the recording. Successful application communication will be shown by the correlated acknowledgements in the next step.

### A4｜Visualizer iPhone 先订阅，拍清开始画面

**机器：** Visualizer iPhone；摄影手机拍它，不在 Visualizer 上打开相机。

1. Unity → **Week 7 Connect / Settings**，保持 **Use campus jump host** 开启。使用已有 verified public CA；必要时点击 **Import verified public CA** 导入那张公开证书。
2. 在镜头外填 Board / Jump 登录信息，点 **Connect**。等待 `Subscribed, Received: 0`。
3. 摄影手机拍清 `Subscribed`、开始时的 `Received` 和结果区域。已有订阅的计数可以不是 0；保留此画面，用于和同次运行结束画面对照，无需输入电脑。
4. 之后保持 Unity 前台、不锁屏、不再点 Connect。手机自己连接 Ultra96 的 9999 服务，不连接 Windows 18889。

**未到 Subscribed 不开始 A5。** 先查 VPN、两跳凭据、CA、版本及有无竞争订阅者。

**英文口播：**

> The Visualizer has established its own SSH and TLS connection to Ultra96 and completed the subscription handshake. The camera records its starting received count. I will keep the app in the foreground while the laptop sends data.

### A5｜跑一次真实双设备采集，拍两条链路的现象

**R03 操作：** 先确认两板都已断开 laptop USB、两板独立供电、手机已 Subscribed 并拍好开始画面；终端 A 的隧道保持运行。在终端 B 执行：

```powershell
python demo.py run
```

> This command captures both physical boards for sixty seconds at ten hertz each, then automatically shows the report and matching sensor and acknowledgement records. The camera records the phone reception.

Video 默认 60 秒、每台目标 10 Hz。启动时拍清两台 `BLE_connected` 与 `authenticated=True`，之后才进入共同观察时段。程序不会询问手机计数；不需要额外报告步骤。不要 Ctrl+C，让命令自然结束；初始化和收尾会让总等待略长。保留结束输出的 **`Saved in: ...` 完整路径**。

**摄影手机在这一运行内依次拍：**

1. 电脑进入 `mode=physical phase=observation`，`device=1` 和 `device=2` 的 `received` / `acked` 都递增，正常 `drops=0 errors=0`。两路终端通常显示青色/紫色。
2. 暂停移动镜头，拍清几条抽样解码记录。`sensor` 显示设备、boot、seq、values；`sensor_ack` 显示对应身份与 `validation=accepted` 等状态。控制台抽样不减少文件内的记录。
3. 镜头转到 Visualizer iPhone，拍清 `Received` 增长，结果 ID 中出现 `1:` / `2:`，以及 dummy gesture。两台可以交错显示；刷新可能只显示最新结果，不必逐包停留。
4. 全景再拍两块板子仍独立供电。不要插拔电源或做超距、锁屏试验。

**预期进度格式；下面数字不是本次结果：**

```text
progress mode=physical phase=observation device=1 received=100 processed=100 acked=98 ... drops=0 errors=0 ...
progress mode=physical phase=observation device=2 received=100 processed=100 acked=99 ... drops=0 errors=0 ...
```

**看到实际递增后说：**

> Both physical BLE streams are arriving at the laptop during the same capture. The received counters show laptop input. The acknowledged counters increase when Ultra96 returns a valid acknowledgement with matching identifiers. The decoded records show the packet identities and sensor values.
>
> On the Visualizer, the received count is also increasing. The result IDs identify device one or device two, the boot, and the sequence. These gestures are simulated results selected from REST, FIST, OPEN and POINT. They are not predictions from a trained model. Results travel directly from Ultra96 to the phone over the phone's own connection.

### A6｜自动报告、手机结束画面与本次证据

1. 等 `demo.py run` 自然结束。终端自动显示最终报告、两设备匹配 sensor/ACK，并打印 **`Saved in: ...` 完整目录**；无需再运行一个脚本或输入手机数字。
2. 摄影手机拍清 `CAPTURE PASSED`、两台最终计数、`Phone expected increase` 和本次路径。等待手机 Received 稳定，拍清手机结束画面及最后结果。停止发送约两秒后出现 `No live result` 是最新标签过期，Received 仍可观察。
3. 对照同一次录像的手机开始/结束画面和报告的预期增量。脚本只统计源端、laptop 接收与 Ultra96 ACK；**手机实际收到了多少由手机画面证明**，不能用报告的预期值代替手机读数。

| 要看什么 | 在哪里看 | 成功依据 |
|---|---|---|
| [N1] / [N2] | 报告 Device 1 / 2 的 Generated | 每台 Generated = Received = ACKed；MissingBLE / MissingACK 均 0 |
| 手机预期增量 | `Phone expected increase` | Video 未开 keyboard，预期为 N1 + N2；这是计算值 |
| 手机实际接收 | 同次录像的开始、增长及结束画面 | Received 真实增长，出现两个设备的结果；可读时与预期增量比较 |
| [CAPTURE] | 本次 `Saved in` 完整目录 | 默认 `D:\LetThemCook\.week7-local\B07-...`，保留该次全部文件 |
| 采集摘要 | 同一份报告 | `Exit=0 clean=True mock_input=False report_saved=True`，且 `CAPTURE PASSED` |

运行中收到数与 ACK 数暂时不同可以正常；最终排空后再比较。手机画面不清楚或增量不符时，不能宣称手机计数一致。程序不读取 iPhone 屏幕，也不生成手机逐条收据或自动手机通过结论。

**报告通过、手机画面也核对后口播：**

> Device one generated [N1] packets and device two generated [N2]. Each device's generated, received and acknowledged counts match. The filmed phone shows its actual reception during this same capture. The report's expected phone increase is a comparison value, not a receipt from the phone.

**若失败：** 保存原报告/视频，不读成功结论。可说：

> This capture did not meet the acceptance checks. I will retain these results, investigate the mismatch, and record a new capture before claiming successful communication.

**展示自动打印的 packet。** 拍清两台设备各自匹配 sensor/ACK 的 device_id / boot_id / seq、**完整八个 values** 和 ACK 的 `validation=accepted`。找不到匹配时不借别次记录凑数。需要逐行查看时，用编辑器打开该目录下的 `packets.log`。

> These decoded records show each sample's device, boot, sequence and eight values, followed by its matching acknowledgement. That confirms ingestion by Ultra96. The camera footage separately shows what the iPhone received.

用文件资源管理器把摄影手机的本段视频、手机开始/结束画面及必要备注放入**这个目录**的 `camera-clips` 子目录。保留原始 `live.log`、`packets.jsonl`、`packets.log`、`report.json`、`report-readable.json`、`exit-code.txt`，不覆盖失败尝试。把本次完整 Saved in 路径写入录像笔记，另一天录 B 时仍指定它。

**R05 仅在稍后需要重看时运行。** 引号内换成刚才保存的实际完整目录；不是自动选择最近或成功的一次：

```powershell
python demo.py report "D:\LetThemCook\.week7-local\B07-本次目录"
```

> This command reopens the exact saved capture and displays its report and matching packets. The phone observation remains in the corresponding camera footage.

完成 A6 后继续 A7；终端 B 的采集已结束，终端 A 的隧道暂时保留。先保存修改前证据，再接 USB 做下一轮 setup。

### A7｜修改 dummy packets → 重新编译/上传 → 重新运行并核对

**本段继续用摄影手机拍电脑和硬件。** 它对应 General Guidelines 的 “change the dummy packets … recompile/rerun”。英文投屏提示见[展示稿 D01，第 1869 行](./B07-CO-video-presentation.en.md#d01)。沿用已有脚本，不需要新增命令工具；修改和烧录由你在录制时实际执行。

**A7.1 留下修改前证据，再现场编辑。** 把 A6 的准确 Saved in 目录记为“修改前”，保留该次手机开始/结束画面。用资源管理器把当前 `common/dummy_fixtures.json` 复制到这个目录留档。在编辑器打开该次 `packets.log`，搜索完整的 `values=[1200, -300, 850, 40, -20, 15, 600, 250]`，记录对应 `device_id`、`boot_id`、`seq`；这是后面对照的基准。

**哪些值可以改：** 任意一组、任意一项都可以修改；每组必须正好 **8 个整数**，各值范围 **−32768～32767**，整份文件保留 **2～64 组**。保持合法 JSON，不写小数、字符串或注释。下面的 1200 → 1500 只是容易对照的演示例子；若现场选了其他值，就同步替换口播中的数字和日志搜索的完整八项。固件随机抽取整组，不保证每个包都出现修改值；非法内容会在 `flash.py` 生成阶段报错，后续构建/上传停止。

在 VS Code 打开 [common/dummy_fixtures.json 第 3 行](../common/dummy_fixtures.json#L3)，按本稿示例只把第二组第一项 **1200 改成 1500**，其他七项和其他三组保持不变，按 Ctrl+S 保存。拍清修改过程。以下是同一组修改前后的内容；不是把整份 JSON 换成单独一组：

| 状态 | 第二组的完整八个 values |
|---|---|
| 修改前 | `[1200, -300, 850, 40, -20, 15, 600, 250]` |
| 修改后 | `[1500, -300, 850, 40, -20, 15, 600, 250]` |

**英文口播：**

> I am changing the first channel of the second dummy fixture from twelve hundred to fifteen hundred. Each fixture still contains eight signed sixteen-bit values, and the thirty-two-byte packet format remains unchanged. The firmware will continue selecting randomly from the four fixtures.

**A7.2 重新编译并上传，两块都要更新。** 确认 `demo.py run` 已结束且串口监视已关闭；准备好用同一根烧录 USB 线依次连接左板和右板。终端 A 的隧道可以继续复用。

| 顺序 | 在终端 B 运行 / 操作 | 必须观察到的结果 |
|---|---|---|
| 1 | `python flash.py`；按提示接左板，左板成功后拔左换右 | fixture 头重新生成；左右构建和上传都成功；失败即停 |
| 2 | 打开 [week7_fixtures.h 第 9 行](../firmware/esp32/include/week7_fixtures.h#L9) | 第二组为 `{1500, -300, 850, 40, -20, 15, 600, 250}`；这是生成结果，不直接编辑 |
| 3 | 右板上传后也拔掉 USB，确认两板均恢复独立供电 | 镜头拍清真实采集前两板均已断开 laptop USB；已有绑定不用再 pair |
| 4 | Visualizer 保持前台且 Subscribed；必要时重连，拍本轮开始画面 | 本轮手机开始状态清楚，不借修改前那次画面 |
| 5 | `python demo.py run` | 两台认证连接通过；新 60 秒采集结束后自动报告、匹配记录和新 Saved in 目录 |
| 6 | 拍本轮手机结束画面，与本轮报告比较 | 电脑与手机证据都属于修改后的这一次 |

如果隧道此前已结束，按 A3 在终端 A 重开 `demo.py tunnel`；否则复用。认证失败才按 A1 的少用选项排查，不能降级安全。只修改合法 payload 数值时，重新构建两块 FireBeetle 即可，不需要重编译 Ultra96 或 iPhone App。

**英文口播：**

> I run the same flash script again, using one programming USB cable for the two boards in turn. After restoring independent power, I start a new capture with demo.py. It displays the report automatically, while the camera records the phone's received count.

**A7.3 在新日志里证明修改已生效。** 把新 Saved in 目录记为“修改后”，用资源管理器将修改后的 JSON、生成的 `week7_fixtures.h` 及本轮手机开始/结束画面复制到该目录留档。在 VS Code 打开**新目录的 `packets.log`**，Ctrl+F 搜索完整的 `values=[1500, -300, 850, 40, -20, 15, 600, 250]`。找到 device 1 和 device 2 各至少一条 `type=sensor`、`direction=ESP->laptop`、`validation=decoded` 的记录，拍清八个 values 和该条的 boot/seq。

再按各自 `device_id`、`boot_id`、`seq` 找到同一文件中的 `type=sensor_ack`、`direction=Ultra96->laptop`、`validation=accepted` 记录。可以搜索 `packets.jsonl` 中同一身份辅助定位；不能拿另一台或另一条 seq 的 ACK 配对。修改前后不要求 boot/seq 相同，重新上电会建立新的启动身份。

**注意随机选择：** 自动报告只展示每台设备找到的首个匹配样本，那条不一定抽到第二组；终端输出也会抽样显示。用保存的 `packets.log` / `packets.jsonl` 查找，不能因首个样本没有 1500 就认定失败，也不能未找到就宣称成功。若任一设备找不到更新后的完整组，保留此次记录并排查其固件/上传/采集，确认后再录新的采集。

**核对完成后才说：**

> The earlier capture contains the original fixture starting with twelve hundred. In this new capture, both devices have transmitted the updated fixture starting with fifteen hundred. Each displayed sample has a matching Ultra96 acknowledgement. The new report passes its checks. The corresponding camera footage shows the phone receiving results and its count increasing.

手机展示的是结果事件和接收数，不一定直接显示这八个 sensor values；不能要求手机出现数字 1500，也不能把随机 AI 事件变化当作 payload 已更新的证明。修改证据是新采集中的实际 sensor values，ACK 和手机计数分别说明接入及结果接收。

**A7 完成后再停止摄影手机。** 保留“修改前/修改后”两套目录和各自计数；B 阶段只回看它们。展示稿 C07 是原 fixture 快照，不会自动变成 1500；讲修改时点击 Source 打开实际 JSON，并展示保存的两次日志。若之后恢复 1200，也需要重新运行 `python flash.py` 烧录才能恢复硬件数据，不能只改回 JSON 就宣称两板已恢复。现在可在自己运行的终端 A 按 Ctrl+C 结束隧道，不停止共享 Ultra96 服务。

## 第二阶段 B：电脑录屏，图解、加密与并发源码

**先打开哪个文件：** B 阶段始终以 `D:\LetThemCook\docs\B07-CO-video-presentation.en.md` 为投屏主文件，在 VS Code 按 Ctrl+Shift+V 打开预览；这份中文操作稿只在旁边指路。先找对应 Gxx 图解，再点表内 Cxx 的“展示稿”链接进入带英文注释的代码。片段后的 **Read aloud:** 就是可直接朗读的英文台词。代码中的 `L行号` 对应原源文件，不是 Markdown 行号。

**Source 链接什么时候点：** 它打开真实项目文件，适合临时核对实现或展示已经修改的 fixture。正常讲解留在英文展示稿；那里同时有代码、注释和 Read aloud，不必切去源文件再找台词。核对完回到预览，用 **Back to Gxx** 返回图解。

**展示稿快速定位：** 下表数字是 `B07-CO-video-presentation.en.md` 的标题行。需要精确跳转时，先点回 VS Code 的 Markdown **编辑器标签页**，Ctrl+G 输入行号；再用 Ctrl+Shift+V 看预览。它和代码注释里的原源码 `L行号` 是两套行号，不要混用。

| 章节 | 内容 | Markdown 标题行 |
|---|---|---|
| G01 | 系统架构 | [展示稿第 38 行](./B07-CO-video-presentation.en.md#g01) |
| G02 | FireBeetle setup / IDs | [展示稿第 92 行](./B07-CO-video-presentation.en.md#g02) |
| G03 | Sensor packet / fixtures | [展示稿第 224 行](./B07-CO-video-presentation.en.md#g03) |
| G04 | Packet types / control | [展示稿第 445 行](./B07-CO-video-presentation.en.md#g04) |
| G05 | BLE FSM | [展示稿第 613 行](./B07-CO-video-presentation.en.md#g05) |
| G06 | TCP frame / fragmentation | [展示稿第 672 行](./B07-CO-video-presentation.en.md#g06) |
| G07 | Laptop–Ultra96 FSM | [展示稿第 769 行](./B07-CO-video-presentation.en.md#g07) |
| G08 | Phone FSM | [展示稿第 880 行](./B07-CO-video-presentation.en.md#g08) |
| G09 | 三条通道加密 | [展示稿第 978 行](./B07-CO-video-presentation.en.md#g09) |
| G10 | Laptop 并发 | [展示稿第 1247 行](./B07-CO-video-presentation.en.md#g10) |
| G11 | Ultra96 并发 | [展示稿第 1496 行](./B07-CO-video-presentation.en.md#g11) |

**每个主讲片段按这个顺序：** 展示 G 图解并读该图旁白 → 点本节表中“主讲”的 C 链接 → 按表指出原源码 L 行和函数 → 向下看同一 C 代码块紧接的 **Read aloud:**，直接读那段英文 → Back to Gxx → 下一个主讲 C。不是只读代码注释，也不是回这份中文稿寻找逐段台词。

**选读规则：** “备查”片段只在需要展开时打开；B2–B4 的 setup/格式已在 A 拍过，按需回顾即可。下面保留的“合并讲解备选”是压缩版：只有不逐个展开 C 时才选读，已经读过各 C 的 Read aloud 就跳过，避免重复。B 阶段不运行 hardware/bridge；重看 A 的报告只读取那次已保存的证据。

展示稿中的代码保留源文件路径和原始行号，并添加英文解释注释。它是生成文档时的源码快照，讲解注释不代表项目源文件已被修改。若 A 之后改过代码，应展示相应实际文件/记录版本差异，不把快照说成自动同步编辑器；展示片段用于讲解，实际运行上面的 flash/demo 命令。

**开头声明：**

> The physical demonstration was recorded earlier. I will now explain the implemented protocols, setup and source code. When I reopen a report or packet log, it is saved evidence from that recorded capture, not a new live run.

### B1 / G01｜系统架构：服务器和两条结果路径

**文件分工：** `demo.py`（C01）的 `capture_command()` 组装双设备 bridge 的启动参数、session、ACK window 和证据路径；`flash.py` 的固件准备只作背景说明，不在此重跑。

**本节怎么讲：** G01 → C01：指出 `capture_command()` 和表中的原行号，再读 C01 代码下方的 **Read aloud**。

**投屏英文旁白（与展示稿一致）：**

> Two FireBeetles send structured dummy sensor packets to the relay laptop over protected Bluetooth Low Energy. The laptop forwards both streams to Ultra96 and receives ingestion acknowledgements. The Visualizer iPhone has its own SSH and TLS connection to the board. Ultra96 sends gesture results directly to that phone. The application servers run on Ultra96. We use SSH for the deployed campus access route and do not use a message broker.

**代码讲解顺序（范围是原文件行号，标题与展示稿相同）：**

| 用法 | 代码标题/内部链接 | 展示稿标题行（Ctrl+G） | 源文件与片段范围 | 要指出的原行号 |
|---|---|---|---|---|
| 主讲 | **C01 Launcher** | [展示稿第 47 行](./B07-CO-video-presentation.en.md#c01) | [demo.py](../demo.py#L71)，71–88 | L74 / L76 / L79 |

**投屏 G01：** 指 FireBeetle → laptop → Ultra96，再指独立的 Ultra96 → iPhone；读图解英文说明。指出应用服务运行在 Ultra96，未使用 message broker；SSH 是当前校园访问路线，不是 TCP 固有要求。

**代码画面：** G01 → C01，指 `demo.py` 的 capture_command() 启动 laptop.dual_bridge、传入 session / ACK window、保存 report / evidence。`flash.py` 管固件，`demo.py` 复用既有桥接和报告实现；展示稿 R01–R08 说明 Video、Live 和少用维护选项。本阶段不重新运行实体操作。

| 入口 | 复用职责；这里只讲解 |
|---|---|
| `demo.py tunnel` | 打开 SSH 路由并保持当前终端 |
| `demo.py run` / `live` | 同一双设备采集；Video 默认 60 秒，Live 默认 120 秒并启用键盘 |
| `demo.py report "准确目录"` | 重看指定采集的报告和匹配数据，无手机输入 |
| `flash.py` | 生成 fixtures、构建两份固件，用同一根烧录线依次检测并上传左右板 |

**合并讲解备选（不逐段展开 C 时选读；已读 Read aloud 就略过）：**

> Demo opens the tunnel, launches the existing dual-device bridge and displays the resulting evidence. Run provides the Video defaults; Live enables the keyboard demonstration. Report reopens an explicit saved directory. Flash handles firmware preparation. The bridge and server modules implement the actual communication.

### B2 / G02｜FireBeetle setup 和 Device IDs 图解回顾

**文件分工：** `platformio.ini`（C02）定义板型和左右 ID；`main.cpp`（C03，备查）执行启动设置；`windows_pairing.py`（C04，备查）检查认证绑定。

**本节怎么讲：** 先回顾 G02；若需要展开配置或首次绑定实现，再按 C02 / C03 / C04 定位原行号，并读所打开片段下方的 **Read aloud**。

**投屏英文旁白（与展示稿一致）：**

> PlatformIO builds our Arduino firmware for the firebeetle32 board. The left profile assigns device ID one, and the right profile assigns device ID two. We use one USB cable to upload to the left board and then the right board, and disconnect the laptop USB after programming. During the BLE demonstration, each board uses its own power source. We complete authenticated pairing before streaming. The BLE address selects the physical board, while the device ID identifies its application packets.

**代码讲解顺序（范围是原文件行号，标题与展示稿相同）：**

| 用法 | 代码标题/内部链接 | 展示稿标题行（Ctrl+G） | 源文件与片段范围 | 要指出的原行号 |
|---|---|---|---|---|
| A 已讲；本段回顾/备查 | **C02 Board + IDs** | [展示稿第 101 行](./B07-CO-video-presentation.en.md#c02) | [firmware/esp32/platformio.ini](../firmware/esp32/platformio.ini#L4)，4–26 | L6 / L7 / L21 / L26 |
| setup 细节备查 | **C03 Boot setup** | [展示稿第 147 行](./B07-CO-video-presentation.en.md#c03) | [firmware/esp32/src/main.cpp](../firmware/esp32/src/main.cpp#L404)，404–423 | L406 / L421 |
| 配对实现备查 | **C04 Pairing** | [展示稿第 188 行](./B07-CO-video-presentation.en.md#c04) | [laptop/windows_pairing.py](../laptop/windows_pairing.py#L116)，116–127 | L119 / L120 / L123 / L125 |


**投屏 G02：** 回顾 A1 已由摄影手机拍到的两份构建、同一根烧录 USB 线依次上传、双板 ID，以及 setup → 拔线 → 独立供电的切换；认证证据使用 A5 启动时的连接日志，首次配对才补 A1 的绑定画面。这里不再执行上传，也不把 setup 第一次放到本段才解释。

**画面：** 指 left / right profile 与 device 1 / 2 映射；必要时暂停到 A1 两次 upload 的成功画面。原始配置位置为 [platformio.ini](../firmware/esp32/platformio.ini)，搜索 firebeetle32-left / firebeetle32-right。

**简短回顾备选（未展开 C 片段时选读）：**

> The camera recording already showed both actual uploads and the authenticated bond checks. This diagram summarizes that setup and the distinct device identities. USB was used for programming and removed from both boards before the BLE communication capture.

### B3 / G03｜Sensor packet format 图解回顾

**文件分工：** `sensor.py`（C05/C06）定义并编解码 32-byte 样本，`dummy_fixtures.json`（C07）提供可编辑的八通道数据；`main.cpp`（C40/C08）提供随机数并走实际发送路径。

**本节怎么讲：** 先回顾 G03；需要展开时按 C05 → C06 → C07 → C40 → C08，指出字段、fixture、随机数和发送调用，再读各片段下方的 **Read aloud**。

**投屏英文旁白（与展示稿一致）：**

> Each sensor notification contains thirty-two bytes. The fields are the W7 marker, version, device ID, boot ID, sequence number, uptime and eight signed sixteen-bit channel values. Multi-byte fields use little-endian encoding. Version two randomly selects from several editable fixtures. Device, boot and sequence identify the sample. The packet has no custom application CRC field. Our dummy values follow the sensor packet schema, and the decoded log shows the actual values transmitted.

**代码讲解顺序（范围是原文件行号，标题与展示稿相同）：**

| 用法 | 代码标题/内部链接 | 展示稿标题行（Ctrl+G） | 源文件与片段范围 | 要指出的原行号 |
|---|---|---|---|---|
| A 已讲；本段回顾/备查 | **C05 Sensor fields** | [展示稿第 233 行](./B07-CO-video-presentation.en.md#c05) | [common/sensor.py](../common/sensor.py#L11)，11–38 | L11 / L12 / L23 / L27 |
| A 已讲；本段回顾/备查 | **C06 Sensor codec** | [展示稿第 286 行](./B07-CO-video-presentation.en.md#c06) | [common/sensor.py](../common/sensor.py#L63)，63–80 | L67 / L73 / L75 / L78 |
| A 已讲；本段回顾/备查 | **C07 Fixtures** | [展示稿第 327 行](./B07-CO-video-presentation.en.md#c07) | [common/dummy_fixtures.json](../common/dummy_fixtures.json#L1)，1–6 | L2 / L3 / L4 / L5 |
| A 已讲；本段回顾/备查 | **C40 Random source** | [展示稿第 414 行](./B07-CO-video-presentation.en.md#c40) | [firmware/esp32/src/main.cpp](../firmware/esp32/src/main.cpp#L87)，87–96 | L89 / L94 |
| A 已讲；本段回顾/备查 | **C08 Sensor send** | [展示稿第 357 行](./B07-CO-video-presentation.en.md#c08) | [firmware/esp32/src/main.cpp](../firmware/esp32/src/main.cpp#L483)，483–511 | L500 / L503 / L507 / L508 |


**投屏 G03：** 用清晰图解回顾 A2 相机镜头里的 _PACKET / decode_packet，顺着 32 个 byte 的位置讲，不需要重复上传或生成数据。源码为 [sensor.py](../common/sensor.py)、[dummy_fixtures.json](../common/dummy_fixtures.json)、[week7_packet.h](../firmware/esp32/include/week7_packet.h)。

**回顾 A7 修改结果：** 打开[展示稿 D01](./B07-CO-video-presentation.en.md#d01)，展示修改前后保存的 JSON 和实际日志，读其中最后一段英文结论（仅在 A7 已全部核对成功时）。此处不重新烧录或运行 `demo.py run`；C07 仍是原始数据快照，1500 的依据是 A7 保存的文件和真实新采集。

**要指到：** W7、v2、ID、boot、seq、uptime、八个 int16，little-endian；fixture 是随机抽取，允许连续重复，真正的 values 已保存在 A6 的解码日志。没有 custom application CRC，不把校验或加密说成不存在的 CRC 字段。

### B4 / G04｜Packet types 与 BLE control format 图解回顾

**文件分工：** `control.py`（C09/C10）定义 BLE opcode 和控制包编解码，`ultra96/protocol.py`（C11）定义网络消息类型，`week7_source_stats.h`（C12）序列化源端对账计数。

**本节怎么讲：** 先回顾 G04；需要展开时按 C09 → C10 → C11 → C12，指出类型常量、header 和统计字段，再读各片段下方的 **Read aloud**。

**投屏英文旁白（与展示稿一致）：**

> The sensor characteristic sends W7 notifications. The laptop reads W7S1 source counters for reconciliation. Commands use a separate B7 control header containing the opcode, device ID, status, request ID and offset. A response sets bit seven of the opcode. The command payload carries a complete version-two sensor packet. The control header itself remains version one. The laptop then uses SENSOR_BATCH and INGEST_ACK messages with Ultra96, while the phone uses subscription and gesture-result messages.

**代码讲解顺序（范围是原文件行号，标题与展示稿相同）：**

| 用法 | 代码标题/内部链接 | 展示稿标题行（Ctrl+G） | 源文件与片段范围 | 要指出的原行号 |
|---|---|---|---|---|
| A 已讲；本段回顾/备查 | **C09 BLE types** | [展示稿第 454 行](./B07-CO-video-presentation.en.md#c09) | [common/control.py](../common/control.py#L8)，8–17 | L10 / L11 / L12 / L15 |
| A 已讲；本段回顾/备查 | **C10 Control codec** | [展示稿第 488 行](./B07-CO-video-presentation.en.md#c10) | [common/control.py](../common/control.py#L88)，88–101 | L90 / L97 / L98 / L100 |
| A 已讲；本段回顾/备查 | **C11 JSON types** | [展示稿第 525 行](./B07-CO-video-presentation.en.md#c11) | [ultra96/protocol.py](../ultra96/protocol.py#L3)，3–13 | L7 / L8 / L9 / L10 |
| A 已讲；本段回顾/备查 | **C12 Source counters** | [展示稿第 562 行](./B07-CO-video-presentation.en.md#c12) | [firmware/esp32/include/week7_source_stats.h](../firmware/esp32/include/week7_source_stats.h#L34)，34–53 | L41 / L44 / L45 / L49 |


**投屏 G04：** 回顾 A2 已实际打开的 [control.py](../common/control.py) 和 [protocol.py](../ultra96/protocol.py)。指 W7 notification、W7S1 source counters、B7 control request / response，再指网络消息类型。控制头为 14 bytes；响应置 bit 7；控制 version=1 与 sensor version=2 分开。

**需要进一步说明 source counters 时：** 在英文展示稿打开 C12，指出 serializeSourceStats 并读代码下方的 Read aloud；只有核对原文件时才点 [week7_source_stats.h](../firmware/esp32/include/week7_source_stats.h)。24-byte W7S1 记录包含 device、boot、next sequence、submitted、failures，为 A6 的源端对账提供边界。它不等于手机的结果收据。

### B5 / G05｜BLE 协议 FSM

**文件分工：** `week7_security.h`（C13）把连接、认证、订阅和 MTU 状态转为允许通知或控制的具体条件，对应图中的状态门槛。

**本节怎么讲：** G05 → C13：指出 `canNotify`、`sensorFitsMtu`、`canAcceptControl`，再读 C13 下方的 **Read aloud**。

**投屏英文旁白（与展示稿一致）：**

> On power-up, the FireBeetle advertises its BLE service. After the laptop connects, the firmware checks authenticated encryption. A valid peer can enable notifications. Sensor streaming requires a subscription and an ATT MTU of at least thirty-five. Our rate-control operation additionally requires an MTU of at least sixty-four. On disconnection, the device clears connection state and advertises again. This diagram summarizes the implemented control flow.

**代码讲解顺序（范围是原文件行号，标题与展示稿相同）：**

| 用法 | 代码标题/内部链接 | 展示稿标题行（Ctrl+G） | 源文件与片段范围 | 要指出的原行号 |
|---|---|---|---|---|
| 主讲 | **C13 BLE gates** | [展示稿第 622 行](./B07-CO-video-presentation.en.md#c13) | [firmware/esp32/include/week7_security.h](../firmware/esp32/include/week7_security.h#L7)，7–25 | L10 / L11 / L14 / L16 |


**投屏 G05：** 广播 → 连接/认证 → ready → 通知发送；断开后重新广播/重连。这是行为概括，不声称源码存在同名 enum。读图解英文说明。

**代码画面：** G05 → C13，指 canNotify、sensorFitsMtu、canAcceptControl，把图里的安全/订阅/MTU 门槛对应到真实条件。

**合并讲解备选（不逐段展开 C 时选读；已读 Read aloud 就略过）：**

> These checks connect the state diagram to the implementation. Sensor notification requires a connected, subscribed and authenticated peer in the normal protected profile. Thirty-two bytes require an ATT MTU of at least thirty-five. This capture also used the control channel, which requires at least sixty-four. The laptop checks the bond, establishes notifications and retries after a disconnect. Historical MTU observations are not a guarantee of every future connection.

### B6 / G06｜TCP 分帧与 fragmentation

**文件分工：** `common/wire.py` 用 `encode_frame()`（C14）给 JSON 添加长度头，再用 `read_frame()`（C15）跨多次 TCP 接收读齐并解析完整消息。

**本节怎么讲：** G06 → C14 → C15：先讲长度头，再讲 `readexactly` 和长度校验；每段指出表内原行号后，读该段下方的 **Read aloud**。

**投屏英文旁白（与展示稿一致）：**

> TCP delivers a byte stream, so one application frame can arrive in several pieces. Our encoder prefixes the JSON body with its four-byte big-endian byte length. The receiver first reads exactly four bytes, checks that the length is between one and sixteen thousand three hundred and eighty-four, and then reads exactly that many body bytes. It parses and validates the complete JSON object. TLS provides encryption around these application frames.

**代码讲解顺序（范围是原文件行号，标题与展示稿相同）：**

| 用法 | 代码标题/内部链接 | 展示稿标题行（Ctrl+G） | 源文件与片段范围 | 要指出的原行号 |
|---|---|---|---|---|
| 主讲 | **C14 Frame encode** | [展示稿第 681 行](./B07-CO-video-presentation.en.md#c14) | [common/wire.py](../common/wire.py#L35)，35–46 | L43 / L45 / L46 |
| 主讲 | **C15 Partial reads** | [展示稿第 714 行](./B07-CO-video-presentation.en.md#c15) | [common/wire.py](../common/wire.py#L49)，49–76 | L53 / L58 / L59 / L62 |


**投屏 G06：** 4-byte big-endian 长度 + UTF-8 JSON；读图解英文说明，指一个应用帧跨多个 TCP chunk 的图。

**源码：** [wire.py](../common/wire.py) 的 `encode_frame()` / `read_frame()`，指出 `struct.pack("!I", ...)`、`readexactly(4)`、`readexactly(length)` 和 1..16384 限制。

**合并讲解备选（不逐段展开 C 时选读；已读 Read aloud 就略过）：**

> TCP provides a byte stream, not application-message boundaries. One read may contain part of a message or bytes from multiple messages. The sender prefixes the UTF-eight JSON body with a four-byte big-endian byte count. The receiver first reads exactly four bytes, validates the length, and then reads exactly that body length.
>
> It rejects malformed UTF-eight, duplicate JSON keys and invalid JSON objects. Message-schema validation follows at the endpoint. Notice the different byte orders: the BLE packet fields are little-endian, while the TCP length prefix is big-endian. Framing is not encryption.

### B7 / G07｜Laptop ↔ Ultra96 协议 FSM 和录制证据

**文件分工：** `laptop/bridge.py` 在 C16 建立经过验证的 TLS 连接，在 C17 核对 ACK 身份；C39 是错误重试间隔的备查实现。

**本节怎么讲：** G07 → C16 → C17：先讲 TLS，再讲 ACK 身份；各读对应 **Read aloud**。C39 只在需要解释重试时展开。

**投屏英文旁白（与展示稿一致）：**

> The laptop connects through the configured SSH route and verifies Ultra96's TLS certificate and hostname. In the active state it sends SENSOR_BATCH messages and validates matching INGEST_ACK messages. Sending and acknowledgement reading progress concurrently, with up to thirty-two outstanding messages per device. A connection failure retires the transport before retrying with a capped delay. Sent but unconfirmed packets are recorded as ambiguous drops, so reconnection does not imply complete outage replay.

**代码讲解顺序（范围是原文件行号，标题与展示稿相同）：**

| 用法 | 代码标题/内部链接 | 展示稿标题行（Ctrl+G） | 源文件与片段范围 | 要指出的原行号 |
|---|---|---|---|---|
| 主讲 | **C16 TLS connect** | [展示稿第 778 行](./B07-CO-video-presentation.en.md#c16) | [laptop/bridge.py](../laptop/bridge.py#L349)，349–353 | L351 / L352 / L353 |
| 主讲 | **C17 ACK identity** | [展示稿第 804 行](./B07-CO-video-presentation.en.md#c17) | [laptop/bridge.py](../laptop/bridge.py#L375)，375–386 | L376 / L379 / L381 / L382 |
| 备查 | **C39 Retry delay** | [展示稿第 839 行](./B07-CO-video-presentation.en.md#c39) | [laptop/bridge.py](../laptop/bridge.py#L656)，656–670 | L660 / L667 / L669 |


**投屏 G07：** 建连/验证 TLS → active → 匹配 ACK；错误关闭重试与正常 drain 分开。读图解英文说明。

**代码画面：** G07 → C16 看 TLS 建连 → 返回 → C17 看 ACK 身份检查；需要讲故障重试时再点 C39，退避间隔有上限，不是重试次数有固定上限。v2 request_id：stream 为 null，command 为非零 ID；本次只运行 stream。流水线的实际任务创建在 B10 / G10 展示，板端接入代码在 B11 / G11 展示。

**合并讲解备选（不逐段展开 C 时选读；已读 Read aloud 就略过）：**

> The bridge opens a verified TLS connection through the SSH route. For each acknowledgement, it checks the version, session, device, boot and sequence, plus the version-two request ID. An acknowledgement with the wrong identity is rejected. On Ultra96, the ingestion handler validates the SENSOR_BATCH and replies with accepted or duplicate status. A duplicate does not create another independent result.
>
> The active state uses pipelined sending and acknowledgement reading, with up to thirty-two outstanding messages per device. This is not a stop-and-wait protocol. When the capture ends, the bridge drains pending work before producing its final source audit.

**重开 A 阶段证据，明确不是重跑：** 在终端 B 用 `python demo.py report "准确 Saved in 目录"` 指定 A6 的实际目录；若讲 A7 修改结果，则指定 A7 的新目录。先拍清输出路径与对应那次录像一致，再展示报告和两台匹配数据。此处不运行 `run` 或 `live`，它们会开始新的实体采集。

报告直接打印结果，不询问手机数字。手机证据播放对应 A 阶段保存的开始/结束画面，不能用今天的手机画面或另一轮素材代替。停在同一身份的 sensor / sensor_ack，指出八个 values 和 accepted；找不到匹配就解释本次问题，不拼接别次记录。`_clean_capture()` / `show_report()` 检查源端、接收和 ACK；手机接收仍由同次摄像画面独立说明。

> This is saved evidence from the physical capture shown earlier. These decoded sensor and acknowledgement records share the same device, boot and sequence. The final report reconciles source generation, laptop reception and board acknowledgements. The phone's actual reception was checked separately using its observed count increase.

### B8 / G08｜Ultra96 ↔ phone 订阅 FSM

**文件分工：** `Subscriber.swift`（C18）完成订阅握手并调用结果校验；`IntegrationController.swift`（C19）处理 App 失活后的暂停状态。

**本节怎么讲：** G08 → C18 → C19：先讲订阅/结果接收，再讲失活暂停；各指出原行号并读对应 **Read aloud**。

**投屏英文旁白（与展示稿一致）：**

> After Connect, the iPhone verifies the SSH hosts and establishes verified TLS to the board's result service. It sends SUBSCRIBE and waits for SUBSCRIBED. It then validates GESTURE_RESULT messages and updates the received count and display. Version-two results use simulated random gesture labels. If the application becomes inactive, it pauses and requires an explicit Connect after returning. The filming phone is a different device, allowing this iPhone to remain in the foreground.

**代码讲解顺序（范围是原文件行号，标题与展示稿相同）：**

| 用法 | 代码标题/内部链接 | 展示稿标题行（Ctrl+G） | 源文件与片段范围 | 要指出的原行号 |
|---|---|---|---|---|
| 主讲 | **C18 Phone subscribe** | [展示稿第 889 行](./B07-CO-video-presentation.en.md#c18) | [ios-visualizer/Week7Native/Sources/Week7Transport/Subscriber.swift](../ios-visualizer/Week7Native/Sources/Week7Transport/Subscriber.swift#L24)，24–50 | L28 / L31 / L37 / L41 |
| 主讲 | **C19 Phone pause** | [展示稿第 941 行](./B07-CO-video-presentation.en.md#c19) | [ios-visualizer/Week7Native/Sources/Week7Bridge/IntegrationController.swift](../ios-visualizer/Week7Native/Sources/Week7Bridge/IntegrationController.swift#L24)，24–37 | L26 / L27 / L28 |


**投屏 G08：** Connect → SSH/TLS 验证 → SUBSCRIBE / SUBSCRIBED → 收结果；失活进入 Paused，需要用户重连。读图解英文说明。

**代码画面：** G08 → C18 指 TLS handshake 后调用 Week7Protocol.subscribe、收 SUBSCRIBED 后调用 result 校验；返回 → C19 指 willResignActiveNotification 导致 Paused。校验函数的完整定义在 Protocol.swift；当前投屏片段显示调用点，不冒充整段解析器。随机 gesture 的生成在 B11 的 C35 显示。

**合并讲解备选（不逐段展开 C 时选读；已读 Read aloud 就略过）：**

> The phone sends a version-one subscription envelope for the selected session, then validates SUBSCRIBED before receiving results. The native parser accepts version-two gesture results, checks the session and allowed fields, and verifies the result ID against the device, boot and sequence. Version-two stream results have a null request ID.
>
> Ultra96 selects a simulated gesture for each new accepted input. The app receives results through its own connection. Leaving the app pauses reception, and returning requires an explicit connection step. Matching the phone's total count demonstrates aggregate reception in our recorded capture; it is not a saved per-result receipt ledger from the phone.

### B9 / G09｜Every channel：三条通道加密源码

**文件分工：** `main.cpp`（C20/C22，C21 备查）落实 BLE 认证加密与 GATT 权限；`common/tls.py`（C23）设置 Python 的证书验证；`Week7Client.swift`（C24/C25）建立 iPhone 自己的 TLS 链路；`Trust.swift`（C26）核对 SSH host key。

**本节怎么讲：** G09 → C20 → C22 → C23 → C24 → C25 → C26：按 BLE、Python TLS、iPhone TLS/SSH 三条通道依次讲；每个 C 的 **Read aloud** 就在其代码下面。C21 和已在 B7 讲过的 C16 按需回看。

**投屏英文旁白（与展示稿一致）：**

> The FireBeetle link uses BLE Secure Connections with authenticated pairing and bonding. Its stack provides link encryption. The laptop independently verifies the Ultra96 TLS certificate against our CA and checks the expected hostname. The native iPhone performs its own TLS verification and pins the SSH host keys for its route. Both TLS clients require version one point two or newer. These are separate protected connections. We will now inspect the enforcement points in the source code.

**代码讲解顺序（范围是原文件行号，标题与展示稿相同）：**

| 用法 | 代码标题/内部链接 | 展示稿标题行（Ctrl+G） | 源文件与片段范围 | 要指出的原行号 |
|---|---|---|---|---|
| 主讲 | **C20 BLE security** | [展示稿第 987 行](./B07-CO-video-presentation.en.md#c20) | [firmware/esp32/src/main.cpp](../firmware/esp32/src/main.cpp#L243)，243–262 | L251 / L253 / L254 / L255 |
| 主讲 | **C22 GATT access** | [展示稿第 1068 行](./B07-CO-video-presentation.en.md#c22) | [firmware/esp32/src/main.cpp](../firmware/esp32/src/main.cpp#L391)，391–398 | L396 / L397 |
| 备查 | **C21 Peer check** | [展示稿第 1032 行](./B07-CO-video-presentation.en.md#c21) | [firmware/esp32/src/main.cpp](../firmware/esp32/src/main.cpp#L196)，196–208 | L198 / L200 / L201 / L208 |
| 主讲 | **C23 Python TLS** | [展示稿第 1095 行](./B07-CO-video-presentation.en.md#c23) | [common/tls.py](../common/tls.py#L4)，4–19 | L9 / L10 / L11 / L12 |
| B7 已讲；需要时回看 | **C16 TLS connect** | [展示稿第 778 行](./B07-CO-video-presentation.en.md#c16) | [laptop/bridge.py](../laptop/bridge.py#L349)，349–353 | L351 / L352 / L353 |
| 主讲 | **C24 iPhone TLS** | [展示稿第 1137 行](./B07-CO-video-presentation.en.md#c24) | [ios-visualizer/Week7Native/Sources/Week7Transport/Week7Client.swift](../ios-visualizer/Week7Native/Sources/Week7Transport/Week7Client.swift#L88)，88–95 | L89 / L91 / L92 / L94 |
| 主讲 | **C25 Phone route** | [展示稿第 1169 行](./B07-CO-video-presentation.en.md#c25) | [ios-visualizer/Week7Native/Sources/Week7Transport/Week7Client.swift](../ios-visualizer/Week7Native/Sources/Week7Transport/Week7Client.swift#L128)，128–150 | L138 / L140 / L142 / L144 |
| 主讲 | **C26 SSH pins** | [展示稿第 1217 行](./B07-CO-video-presentation.en.md#c26) | [ios-visualizer/Week7Native/Sources/Week7Transport/Trust.swift](../ios-visualizer/Week7Native/Sources/Week7Transport/Trust.swift#L4)，4–10 | L7 / L8 / L9 |


**投屏 G09：** 读图解英文说明，依次指 BLE、laptop–Ultra96、Ultra96–phone 的保护边界。以下三段源码都录，不能只投一张图结束。

**① FireBeetle ↔ laptop。** 在 G09 点击 **C20 BLE security**，指 `ESP_LE_AUTH_REQ_SC_MITM_BOND`；Back to Gxx 返回后点 **C22 GATT access**，指两个 `ENC_MITM` 权限。如果展开认证结果如何用于当前连接，再点 **C21 Peer check**，指 `currentPeer`。Windows 的首次绑定按需在 A1 完成，正常认证连接日志已在 A5 拍到；需要看实现可回 G02 的 C04。

**合并讲解备选（本通道/本节未逐段读 Read aloud 时选读）：**

> BLE uses authenticated Secure Connections with bonding and man-in-the-middle protection. These permissions require authenticated encryption for the protected GATT operations. The authentication callback applies the result only to the current peer, and the laptop requires an authenticated bond. Encryption is implemented by the Bluetooth stack; the application packet has no separate custom encryption function or CRC field.

**② Laptop ↔ Ultra96。** 在 G09 点击 **C23 Python TLS**，指 `minimum_version`、`CERT_REQUIRED`、`check_hostname`、`load_verify_locations` 和服务端的 `load_cert_chain()`。需要回顾连接调用时再点 **C16 TLS connect**。外层 SSH 路由已经在 A3 展示；此处核心源码是应用 TLS 的验证入口，不必另外跳编辑器。

**合并讲解备选（本通道/本节未逐段读 Read aloud 时选读）：**

> The Python client requires TLS one point two or newer. It verifies the server certificate against our configured CA and checks the hostname ultra96 dot week7 dot internal. The server loads its certificate and private key here, while the bridge supplies the verified context and hostname when connecting. In this deployment, TLS runs inside an SSH tunnel with host-key verification on both hops. SSH provides the route and authenticates the SSH hosts; TLS authenticates the application server.

**③ Ultra96 ↔ iPhone。** G09 → **C24 iPhone TLS** 指 `trustRoots`、`.fullVerification`、`.tlsv12`；返回 → **C25 Phone route** 指 `NIOSSLClientHandler` 的 `serverHostname`；返回 → **C26 SSH pins** 指 `validateHostKey()` 的匹配和拒绝分支。三段都在同一 Markdown 展示稿，逐个读各自代码下方的 Read aloud；以下压缩版仅作为备选。

**合并讲解备选（本通道/本节未逐段读 Read aloud 时选读）：**

> The native iPhone transport performs its own full certificate verification using the configured CA, TLS one point two or newer, and the same expected application hostname. Its SSH connections check pinned host keys, including the jump host. This protects the result connection independently of the laptop's ingestion connection. JSON serialization, length prefixes and SHA-two-fifty-six digests are not themselves encryption.

只展示源码如何加载证书/密钥，不打开私钥。不要说 mutual TLS，也不要说三条通道共用一个 AES 密钥。

### B10 / G10｜Laptop concurrency / threading

**文件分工：** `dual_bridge.py`（C27）创建两设备任务；`bridge.py`（C29/C30/C31）接收线程安全回调、限制在途数量并并行发送/读 ACK；`evidence.py`（C32）用真实后台线程写日志，C28 队列状态按需备查。

**本节怎么讲：** G10 → C27 → C29 → C30 → C31 → C32：从两设备任务讲到回调队列、ACK 窗口和日志线程；每个 C 指原行号后读对应 **Read aloud**，C28 只作备查。

**投屏英文旁白（与展示稿一致）：**

> Each device has its own BLE input task, bounded inbox and TLS sender. Its acknowledgement reader validates replies and releases slots in the thirty-two-message window. Waiting for one device's I/O allows the other device's tasks to progress. BLE callbacks enter through a thread-safe queue boundary. A separate worker thread writes packet evidence from another bounded queue. The main network concurrency uses asyncio tasks, while logging uses an actual operating-system thread.

**代码讲解顺序（范围是原文件行号，标题与展示稿相同）：**

| 用法 | 代码标题/内部链接 | 展示稿标题行（Ctrl+G） | 源文件与片段范围 | 要指出的原行号 |
|---|---|---|---|---|
| 主讲 | **C27 Device tasks** | [展示稿第 1256 行](./B07-CO-video-presentation.en.md#c27) | [laptop/dual_bridge.py](../laptop/dual_bridge.py#L91)，91–111 | L94 / L106 / L109 |
| 主讲 | **C29 Callback queue** | [展示稿第 1334 行](./B07-CO-video-presentation.en.md#c29) | [laptop/bridge.py](../laptop/bridge.py#L122)，122–147 | L125 / L128 / L135 / L137 |
| 主讲 | **C30 ACK window** | [展示稿第 1386 行](./B07-CO-video-presentation.en.md#c30) | [laptop/bridge.py](../laptop/bridge.py#L533)，533–544 | L535 / L541 |
| 主讲 | **C31 Send / ACK tasks** | [展示稿第 1417 行](./B07-CO-video-presentation.en.md#c31) | [laptop/bridge.py](../laptop/bridge.py#L632)，632–642 | L633 / L634 / L637 |
| 主讲 | **C32 Log thread** | [展示稿第 1451 行](./B07-CO-video-presentation.en.md#c32) | [laptop/evidence.py](../laptop/evidence.py#L13)，13–34 | L17 / L33 / L34 |
| 备查 | **C28 Inbox state** | [展示稿第 1298 行](./B07-CO-video-presentation.en.md#c28) | [laptop/bridge.py](../laptop/bridge.py#L87)，87–101 | L91 / L92 / L93 |


**投屏 G10：** 指两套 input → RawInbox → TLS sender / ACK reader；再指独立日志线程，读图解英文说明。

**源码顺序：** [dual_bridge.py](../laptop/dual_bridge.py) 的 `DualBridge.run()`：`writers` / `inputs` 的 `asyncio.create_task()`；[bridge.py](../laptop/bridge.py) 的 `RawInbox` / `call_soon_threadsafe`、`_pipeline_epoch()` 内 `sender()` / `receiver()` / `asyncio.Semaphore`；C32 展示 evidence.py 的有界 queue.Queue 和真实 threading.Thread。

**合并讲解备选（本通道/本节未逐段读 Read aloud 时选读）：**

> Each device has its own BLE input task, bounded queue and TLS writer. Both streams can make progress during I/O waits. Within each stream, sending and acknowledgement reading are separate asyncio tasks. The semaphore bounds outstanding messages at thirty-two, and a valid acknowledgement releases a slot.
>
> BLE callbacks enter through a thread-safe queue boundary. Evidence records go to another bounded queue and are written by the packet-evidence worker thread. Main network concurrency uses asynchronous tasks; it does not mean one CPU core or operating-system thread per device. Queue overflow is recorded instead of silently counted as success. The two advancing streams in the earlier physical capture showed the observable behavior of this design.

### B11 / G11｜Ultra96 concurrency / threading

**文件分工：** `ultra96/server.py` 在 C33/C34 创建监听与连接任务，C35 处理样本及 ACK，C36 分开运行手机发送与连接监控，C38 管理结果队列；C37 容量配置按需备查。

**本节怎么讲：** G11 → C33 → C34 → C35 → C36 → C38：从监听任务讲到接入处理、手机网关和结果队列；各读对应 **Read aloud**，C37 只作备查。

**投屏英文旁白（与展示稿一致）：**

> Ultra96 has separate accept tasks for ingestion and the phone gateway. Each client connection gets a task. Ingestion validates and deduplicates a message, creates a simulated result for a new input and returns an acknowledgement. The phone gateway runs a result sender and a connection monitor. A bounded result queue connects the two paths. An ingestion acknowledgement does not confirm phone receipt, which is why the physical demonstration separately compares the phone's received-count increase.

**代码讲解顺序（范围是原文件行号，标题与展示稿相同）：**

| 用法 | 代码标题/内部链接 | 展示稿标题行（Ctrl+G） | 源文件与片段范围 | 要指出的原行号 |
|---|---|---|---|---|
| 主讲 | **C33 Two listeners** | [展示稿第 1505 行](./B07-CO-video-presentation.en.md#c33) | [ultra96/server.py](../ultra96/server.py#L136)，136–153 | L139 / L150 / L151 |
| 主讲 | **C34 Client task** | [展示稿第 1544 行](./B07-CO-video-presentation.en.md#c34) | [ultra96/server.py](../ultra96/server.py#L179)，179–188 | L187 / L188 |
| 主讲 | **C35 Ingest + ACK** | [展示稿第 1573 行](./B07-CO-video-presentation.en.md#c35) | [ultra96/server.py](../ultra96/server.py#L246)，246–275 | L248 / L265 / L266 / L272 |
| 主讲 | **C36 Gateway tasks** | [展示稿第 1631 行](./B07-CO-video-presentation.en.md#c36) | [ultra96/server.py](../ultra96/server.py#L309)，309–337 | L310 / L331 / L334 / L336 |
| 主讲 | **C38 Queue freshness** | [展示稿第 1716 行](./B07-CO-video-presentation.en.md#c38) | [ultra96/server.py](../ultra96/server.py#L56)，56–77 | L58 / L62 / L72 / L73 |
| 备查 | **C37 Queue capacity** | [展示稿第 1685 行](./B07-CO-video-presentation.en.md#c37) | [ultra96/server.py](../ultra96/server.py#L32)，32–41 | L35 |


**投屏 G11：** 两个 accept tasks、每个连接的 client task、订阅结果队列、结果发送与 EOF/额外输入监控，读图解英文说明。

**源码：** [server.py](../ultra96/server.py) 的 `start()` / `_accept()` / `_client()`；再 `_ingest()`、`_gateway()`、`_send_results()`、`ResultQueue`。在 `_gateway()` 指到发送任务与 `reader.read(1)` 监控任务。

**合并讲解备选（本通道/本节未逐段读 Read aloud 时选读）：**

> Ultra96 has independent accept tasks for ingestion and the phone gateway. Each accepted connection gets a client task. The ingestion handler validates and deduplicates incoming messages, creates a simulated result for a new input, queues it for the subscriber, and sends an acknowledgement to the laptop.
>
> The gateway runs separate result-sending and connection-monitoring tasks. The bounded result queue separates ingestion from phone transmission and rejects stale or excessive backlog. These tasks allow both laptop connections and the phone connection to progress during I/O waits. An ingestion acknowledgement does not wait for phone receipt, which is why the earlier demonstration checked the phone separately.

板端主通信是 asyncio；可选诊断日志可以有后台线程。不声称每条链路各占一个 CPU 核心、无限缓存或中断期间全量重放。

### B12｜结束与成片检查

停在本次保存的成功报告和 A6 手机最终计数画面，明确是同一已录制采集的证据，然后说：

> We have shown the physical FireBeetle setup and successful communication with Ultra96 and the Visualizer. We then explained the device IDs, packet types and formats, protocol state machines, encryption boundaries, and concurrency in the implemented laptop and Ultra96 code.

- [ ] A1 拍到真实编译、同一根烧录 USB 线先左后右两次上传成功及两板独立供电；A5 拍到两台认证连接通过，不是只展示命令。
- [ ] A2 用摄影手机拍电脑实际打开 ID / sensor / control / protocol 源码并讲字段；B2–B4 的图解只是回顾。
- [ ] A 段先拍完，再录 B 段；没有录代码时打断实体采集。
- [ ] 两块板子只在 setup 时通过 USB 连接 laptop，正式 BLE 采集前已全拔掉并独立供电；两台手机角色清楚。
- [ ] A 阶段真实计数、ACK、手机结果/增量和保存目录可辨；B 阶段重看证据没有冒充新运行。
- [ ] 三条通道的加密源码、laptop 和 Ultra96 两套并发源码均可读。
- [ ] FSM、TCP 分段与帧边界、random fixtures、修改流程都解释过。
- [ ] A7 实际拍到修改 JSON、重新编译/两板上传、拔 USB 后新采集；两台新日志均找到完整更新值和匹配 ACK，前后目录及各自手机开始/结束画面分开保存。
- [ ] 两路颜色/设备标签及至少一对完整解码 sensor/ACK 可读；秘密未录入。

项目已有的视频文件名约定是 `B07_CO_subsystem.mp4`；最终以实际提交页面为准。不要用旧 `tools.week7_demo packet` 的 v1 离线示例替换这次 v2 实物证据。

## 同一入口用于 Live：修改后直接重新演示

Live 复用 Video 的固件和连接方式，不需要另一套脚本。正常已有绑定无需再 pair；隧道已在终端 A 运行就复用，Visualizer 保持前台并已订阅。

在终端 B 运行：

```powershell
python demo.py live
```

> This command starts a two-minute live capture with keyboard input enabled. Pressing one or two sends a command to the corresponding board. The same launcher saves the evidence and displays the report.

默认 **120 秒、每台 10 Hz**；采集中按 **1** 或 **2** 分别向对应 ESP 发命令，**不需要 Enter**。拍清对应设备的命令/响应、结果及最终报告。Video 的 `run` 默认不启用键盘；两者支持同一组采集选项，可用 `--duration`、`--rate` 调整时长和目标速率。

老师要求修改 dummy 数据时，按 A7 编辑并保存 JSON → `python flash.py` 自动构建，按提示用同一根烧录 USB 线依次换左/右板上传 → 断开 laptop USB、两板独立供电 → 手机已订阅 → `python demo.py live` 开新运行。用新目录的完整八个 values 和同身份 ACK 证明修改，不能用旧报告。Live 中手机预期增量还包含成功完成的命令，不能只把两个 source generated 相加。

本段是 Live 的快捷入口；**10 Hz 不是最大速率**。最大速率、文件传输、断电/超距和其他故障专项演示需按各自要求单独安排，不在普通 Video 运行中临时混做。

## 按需功能：无需每次演示执行

| 展示稿入口 | 命令 | 什么时候用 |
|---|---|---|
| [R05 Report，第 1815 行](./B07-CO-video-presentation.en.md#r05) | `python demo.py report "完整 Saved in 目录"` | 可选：稍后重看明确那次报告；引号内换成本次实际路径 |
| [R06 First pairing，第 1828 行](./B07-CO-video-presentation.en.md#r06) | `python flash.py --pair left` / `right` | 只在首次配对或绑定恢复时按当前接 USB 的那一板操作 |
| [R07 Private serial，第 1841 行](./B07-CO-video-presentation.en.md#r07) | `python flash.py --monitor COM4` | 仅首次口令读取；COM4 是示例，换成核实的实际 COM，独立终端运行 |
| [R08 Service maintenance，第 1854 行](./B07-CO-video-presentation.en.md#r08) | `python demo.py service`；需要启动才加 `--start` | 录前需要时检查/启动已有 Ultra96 部署；不强制重启 |

## 附录：少用维护选项，正常运行不用重复做

**R08 只读检查。** 需要确认 Ultra96 服务状态时，另开 PowerShell 进入仓库，运行：

```powershell
python demo.py service
```

> This command checks the Ultra96 service. If no service is running, the start option checks that both ports are free before starting the existing deployment.

按当前终端的 SSH 提示输入两跳密码。查看端口、属主、进程和部署，正常为 `xilinx` 的同一个 `ultra96.server` 持有 `127.0.0.1:8888` / `127.0.0.1:9999`。

**只有服务不存在、两端口空闲且部署匹配才启动：**

```powershell
python demo.py service --start
```

密码只输入当前终端提示，避开镜头。使用已有证书及 `/var/tmp/cg4002-week7-yanjie-20260907/source-co-v2-20260928T122047Z`；端口被占时不启动、不终止占用者。预期出现 `listening`，**保留此服务终端运行**。需要复查时用另一个终端运行 `service`。目录缺失或版本不符先解决部署，不退回旧部署。

2026-09-28 的 PID `105159` 是历史记录，不照抄操作当天进程。服务维护不会替代隧道或手机 Connect；不要为结束录像停止共享服务。

| 问题 | 处理 |
|---|---|
| 隧道静止不输出 | 正常等待；后续 ACK 才证明通信，不重复占用同端口 |
| 串口不确定 | `flash.py` 每阶段重新检测；多候选时选择当前板 COM，也可 `--ports` 单独查看 |
| 认证连接失败 | 核实地址/固件；首次按 A1 一次一板，先 `--monitor 实际COM` 再 `--pair left/right`，不用每轮重配 |
| 手机 Paused | 显式 Connect，拍本轮新的开始画面，再开新采集 |
| ACK 增长但手机不增 | 查订阅、VPN、竞争接收器、v2 App；ACK 不能当手机收据 |
| 报告失败或手机画面不匹配 | 保留本次完整证据，排查后开新采集；不混用两轮素材 |
| 稍后要看报告 | `demo.py report "本次准确目录"`；不挑“最新成功的一次”代替 |

来源：[当前 CO v2 协议](./co-protocol-v2.md)、[2026-09-28 部署与实体测试记录](./co-live-deployment-2026-09-28.md)及上述当前源码。本文是录制步骤，编写时没有重跑硬件测试。
