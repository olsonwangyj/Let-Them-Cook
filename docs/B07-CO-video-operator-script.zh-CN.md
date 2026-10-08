# B07 CO 录像操作稿：实物拍摄 + 十分钟以内电脑录屏

**标识更新（2026-10-08）：** 这份录像稿对应原部署，示例中的 `W7`/`W7S1` 与 `week7-demo` 均保留原样。用更新后的 `demo.py` 连接原 Ultra96 和已安装的手机应用时，先在执行 `run`/`live` 的 PowerShell 终端设置 `$env:LTC_COMMS_SESSION = 'week7-demo'`。新刷入的固件会发送 `LC`/`LCS1`；见[快速上手](communications-quickstart.md#source-and-deployment-identifiers)。

**部署说明：** 本稿的固定路径、`demo.py service` 与默认 SSH/CA 配置对应原 B07 实体部署。其他电脑请先按[通信快速上手](communications-quickstart.md)设置自己的 `--jump`、`--target` 和公有 CA `--ca`。已部署手机应用显示 **Week 7 Connect**；本次交接只包含未来重建用的 `CommsNative` 源码，不含 Unity 导出的 Xcode 工程。

**电脑录屏直接看下方“第二阶段 B”：只讲 8 节，目标 8–9 分钟，10 分钟以内；A 实拍另计。**

**日常只用两个入口：`flash.py` 负责固件，`demo.py` 负责隧道、Video 和报告。** `run` 完成后自动显示报告与两台匹配的 sensor/ACK；手机接收情况直接拍摄同次运行的开始、增长和结束画面，不输入手机计数。原来的通信实现在 bridge/server 中继续复用。

每新开一个 PowerShell，先进入仓库：

```powershell
Set-Location D:\LetThemCook
```

## 常用命令与最短录制顺序

| 用途 | 在 PowerShell 运行 | 什么时候用 |
|---|---|---|
| 烧录（A1） | `python flash.py` | 一次命令先构建两份；第一块定义为 LEFT / ID 1，第二块定义为 RIGHT / ID 2，自动保存地址 |
| 隧道（A2） | `python demo.py tunnel` | 终端 A 开 SSH 隧道并保持运行 |
| Video（A4） | `python demo.py run` | 终端 B 默认采集 60 秒、每台 10 Hz，结束自动显示报告和匹配数据 |

**录像使用 `python demo.py run`，报告自动显示。首次配对仅在录前需要时按 A1.4 准备，不额外录维护流程。

**常规录像：** A1 拍真实 `flash.py` 编译/上传，断开 laptop USB、两板独立供电 → A2 终端 A `demo.py tunnel` → A3 手机 Connect / Subscribed → A4 终端 B `demo.py run` → A5 自动报告、匹配数据和手机结束画面 → A6 改 JSON、再 `flash.py`，拔 USB 后新采集 → B 阶段电脑录屏，**B1–B2 完整讲 Device IDs / packet types / packet format**，再讲协议、加密和并发。固件未改、setup 已录好的后续采集，从隧道和手机连接开始，不重复刷板或配对。

串口识别只在首次或 COM 变化时用 `python flash.py --ports`；查看端口不会烧录。隧道、串口监视和前台服务占用各自当前终端，不在这些终端里输入下一条采集命令。

**本次使用两个主文档：**

| 文件 | 用途 | 怎么打开 |
|---|---|---|
| [B07-CO-video-presentation.en.md](./B07-CO-video-presentation.en.md) | 投屏展示稿：8 节必讲内容、短英文口播、必要图和短源码 | VS Code 打开，Ctrl+Shift+V 预览；从 01 讲到 08，只读引用块里的英文；讲完即停止录屏 |
| [B07-CO-video-operator-script.zh-CN.md](./B07-CO-video-operator-script.zh-CN.md) | 本操作稿：中文步骤、短命令、英文口播、源码定位 | 放在旁边参考，不必把整篇投屏 |

**录像顺序固定为 A → B。** 第一阶段用**摄影手机**拍 FireBeetle 的真实设置、同一台 Windows laptop 上的烧录操作、独立供电、实际通信和修改 dummy 数据后重录；拍电脑屏幕也只展示这些实操。**Device IDs / packet types / packet format 的完整源码讲解移到第二阶段电脑录屏的 B1–B2**，再录协议图解、加密和并发。摄影手机和 **Visualizer iPhone** 是不同设备；Visualizer iPhone 全程运行 Unity，摄影手机负责相机和收音，不在 Visualizer iPhone 打开相机、锁屏或切出 Unity。

A、B 可以分两次、不同时间录制。B 阶段重看 A 阶段保存的报告和日志时，要明确说是 **the recorded capture**；不需要重跑实体采集，也不能把文件重放说成新的现场通信。建议先录好 A 的完整证据，再一次性录完 B。成片时长按内容需要安排，下面不是老师规定的分钟数。

## 本稿对应的 Video 要求

| 老师的要求 | 必录实物段 | 必录电脑段 |
|---|---|---|
| Laptop ↔ Ultra96 — Live + Video | A2、A4、A5：真正发送与接收 ACK | B4：协议 FSM 与 readexactly 分帧 |
| Ultra96 ↔ phone Visualizer — Live + Video | A3–A5：订阅、结果、实际手机计数 | B5：订阅 FSM；B1：独立结果路径 |
| **FireBeetle setup — Video only** | **A1：左右 profile 供烧录选用，真实编译上传及 SUCCESS、独立供电；A4 拍认证连接日志** | B1：简述 ID/配置；setup 实操保留在 A1 |
| **Explain FireBeetle: Device IDs / packet types / packet format — Live + Video** | A5/A6 保存实际 sensor/ACK 和修改前后数据，供录屏引用 | **B1：Device IDs；B2：packet format、packet types 和随机 dummy** |
| Encryption walkthrough in every channel — Video only | A4 的认证连接日志；首次配对时另有 A1 的绑定画面 | B6：BLE、laptop–Ultra96、Ultra96–iPhone 三条通道短源码 |
| Laptop + Ultra96 concurrency/threading walkthrough — Video only | A4 两路进度同时增长 | B7、B8：两张并发框图与任务/队列短源码 |
| General：修改 dummy packets 并 recompile/rerun | **A6：现场改 JSON、重新构建/上传、独立供电后新采集、对照两台设备的更新值** | B2：一句话解释随机选择和重新烧录；实际修改证据保留在 A6 |

General 要求放在相应段落：实际格式的多组随机 dummy 数据、可修改后重跑、FSM、并发框图、清楚的解码日志/两路颜色、无 relay laptop USB、服务器在 Ultra96、无 message broker、TCP 消息可能分段。本稿保留标有 Video 的项目及适用的 General Guidelines；60 秒是现有脚本的采集时长。

## 开录前准备：不计入口播

1. Windows 的 Python 应能运行项目；本机核实过 Python 3.12.7 和 Bleak 3.0.1。打开 PowerShell，执行开头的 `Set-Location D:\LetThemCook`。在 VS Code 打开 `D:\LetThemCook\docs\B07-CO-video-presentation.en.md`，按 Ctrl+Shift+V 预览；把此操作稿放旁边参考。
2. 本机已准备 PlatformIO 和串口驱动；本次在 A1 用**同一台 laptop** 拍真实构建/上传过程。**USB 只用于 setup；用一根烧录 USB 线依次烧录两板；另一口一直接鼠标，无需拔鼠标，实际 BLE 通信前两板都断开 laptop USB、改独立供电。** Ultra96 和已安装的原生 iPhone App 都支持匹配的 v2。更新仓库不等于更新已经烧录/安装的程序；不要为了录像无理由清除既有认证绑定。
3. Windows 蓝牙开启；Windows 和 Visualizer iPhone 均开启所需 VPN。关闭连接这两块板子的其他 BLE 客户端。
4. Ultra96 当前服务需监听板端 `127.0.0.1:8888` 和 `127.0.0.1:9999`。需要确认状态时运行 `python demo.py service`；仅不存在且端口空闲时加 `--start`。当前部署源码目录为 `/var/tmp/cg4002-week7-yanjie-20260907/source-co-v2-20260928T122047Z`；历史 PID 不能当作当天状态。
5. 手机是本次唯一结果订阅者。不要另跑 `phone.receiver`、`laptop.phone_simulator`、`tools.rehearse_remote_comms`；新订阅者会替换旧订阅者。
6. 准备两个独立电源，例如不会因低电流自动关机的充电宝。A1 烧录/首次串口配对时可以 USB 接这台 laptop；A4 开始实体 BLE 采集前，两块板都必须**完全断开 laptop USB**，各自使用独立电源，即使另有电源也不能保留 laptop USB 线。
7. 默认 CA 是 `C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\ca-cert.pem`。这是已有可信公开证书，不为普通录像重新生成 PKI；不打开任何私钥文件。
8. 密码输入和首次配对口令放在镜头外完成。电脑终端字号调到手机能拍清，关闭通知；摄影手机试拍一次，确认无反光且能读清 Visualizer 的计数。

| 窗口名称 | 机器 | 本次用途 |
|---|---|---|
| 终端 A | Windows relay laptop，自己打开的 PowerShell | `demo.py tunnel`；真实采集时保持运行 |
| 终端 B | 同一 Windows laptop，另一 PowerShell | `flash.py` 构建/上传；`demo.py run/live`；需要时 `report` |
| 串口终端 | 首次配对时按需另开一个，一次连接一块板 | `flash.py --monitor 实际COM` 读取当前板口令；完成后退出，再换下一板 |
| VS Code 编辑器 + Markdown 预览 | 同一 laptop；A 阶段相机拍屏，B 阶段电脑录屏 | 图解、英文注释代码、A 阶段保存的日志 |

## 第一阶段 A：摄影手机拍 setup、真实通信与修改后重录

**这阶段拍实际操作与现象。** A1 完成 setup，A2–A5 连续展示两条通信链路，A6 修改 JSON、重新编译上传并拍新采集。A1 只简述左右 profile 便于刷入对应板，深入的 ID/包类型/包格式统一在 B1–B2 录屏讲解。实际采集时不穿插源码讲解；英文可以现场说或后配音，成功结论须在证据核对后再录。

### A0｜摆好机位与开场

**画面：** 摄影手机横拍，两块 FireBeetle、待贴的 LEFT / RIGHT 标签、电源、relay laptop 和 Visualizer iPhone 同框。Ultra96 可通过部署说明交代位置，不把笔记本说成服务器。

**操作：** 电脑显示 VS Code 的展示稿预览，终端 B 已进入仓库；确认尚无采集程序运行。摄影手机开始录像，先停留 5 秒拍清各设备。此时不要切换 Visualizer iPhone 去拍其他东西。

**英文口播：**

> This is B07's communication subsystem. I will first show the physical setup, firmware uploads and communication, followed by changing the dummy data and recording another run. The later computer screen recording will explain device IDs, packet types, packet formats, protocols, encryption and concurrency. The filming phone and Visualizer iPhone are different devices.

### A1｜FireBeetle setup — [Video only]：真实编译、上传、供电与绑定

**本段用摄影手机拍电脑屏幕和板子；真的执行构建/上传并拍成功结果，不只展示命令。** 这是 setup 阶段，尚未运行 BLE 采集。同一台 Windows laptop 可接 USB 烧录；本段使用同一根烧录 USB 线依次连接左板和右板；末尾拍清两板均已断开 laptop USB、各自独立供电。

**A1.1 打开固件项目，只确认用于烧录的左右环境。** 在编辑器按 Ctrl+O，打开 `D:\LetThemCook\firmware\esp32\platformio.ini`，Ctrl+F 搜索 `firebeetle32-left`。指出 left / right profile 分别用于本轮第一块/第二块板，确认使用正常保护配置，不选择 `firebeetle32-unprotected-diagnostic`。这里不展开设备 ID 字段或数据包结构，完整说明放到 B1–B2。

> I am setting up both FireBeetle ESP32 boards. The first board will receive the left profile, and the second board will receive the right profile. I will upload them in turn using one programming USB cable, then power both independently for the BLE demonstration.

**A1.2 准备 LEFT / RIGHT 贴纸，使用一根烧录 USB 线。** 首次设置或换新板时，任选第一块作为左手；第二块不同的板作为右手。每块上传成功后再贴对应标签。若只是修改 dummy 后重烧，按已有 LEFT → RIGHT 标签顺序接入以保留手部角色。确认串口监视已退出，接线按提示进行，不预填 COM 或 MAC 地址。

**A1.3 R01：一条命令依次烧录两块板。** 在终端 B 运行：

```powershell
python flash.py
```

| 提示阶段 | 你实际做什么 | 镜头保留什么 |
|---|---|---|
| 生成与构建 | 等 fixture 头生成、左右环境都构建成功 | 两个 profile 的构建结果；失败就停止 |
| 第一块 → LEFT | 接第一块板、按 Enter；上传成功后贴 LEFT / ID 1 | 自动识别的硬件地址、device 1 环境及 upload 成功 |
| 第二块 → RIGHT | 拔第一块，用同一根线连接另一块、按 Enter；成功后贴 RIGHT / ID 2 | 第二块的地址、device 2 环境、upload 成功及 Board mapping saved |
| 两次完成 | 拔掉右板；两块板各接独立电源 | 两板均不再连接 laptop USB |

每个阶段重新检测串口：一个候选自动选择，多个时才选实际 COM。**两次可以是同一 COM 号**，脚本另读硬件身份；第二次仍是第一块板时，第二次上传会被拦截。两次都成功后，更新后的脚本把地址映射写入 `D:\LetThemCook\.comms-local\boards.json`，由采集和配对共用，无需手改 MAC。烧录中途失败/取消时重新完成 `python flash.py`，普通采集会拦截尚未完成的配置。

> This script regenerates the fixture table and builds both device profiles. The first board I program becomes the left hand with device ID one. I then connect a different board, which becomes the right hand with device ID two. The script identifies the hardware and saves both Bluetooth addresses for capture and pairing. I label each board after its upload succeeds.

脚本使用本机已安装的 PlatformIO。拍清左/右 profile、各自 upload 成功以及实际换板；可以剪去构建等待，不能剪掉失败后宣称成功。

**预期：** 对应环境显示 `SUCCESS` 且退出码 0；失败不能接着口播已烧录成功。此时不需要打开 server 私钥或串口 dump。

> The left and right uploads have completed successfully. Each board now contains the firmware built for its assigned device ID. A successful upload proves programming completed; the authenticated BLE checks and data capture will establish communication next.

**A1.4 录前准备，不计口播：首次配对或绑定恢复才做；已有绑定略过。** 不清除绑定，也不在每次刷板后重新配对。`demo.py run` 会在连接时自动检查认证，A4 拍到 `BLE_connected`、`authenticated=True` 才继续成功口播。

一根烧录 USB 线的首次配对仍是一次一板。暂停拍摄口令屏幕，终端 B 和一个独立串口终端都先进入仓库；按下表完成左板，再重复右板：

| 阶段 | 接线/终端操作 |
|---|---|
| 只接左板 USB | 终端 B 用 `python flash.py --ports` 查看当前 COM |
| 左板口令 | 串口终端运行 `python flash.py --monitor COM4`；COM4 只是示例，换成左板实际 COM，保持此终端运行 |
| 左板认证 | 终端 B 运行 `python flash.py --pair left`，在隐藏提示输入左板串口显示的真实口令 |
| 换板 | 串口终端 Ctrl+C 退出；左板换独立电源，同一根烧录 USB 线接右板 |
| 右板口令/认证 | 用 `--ports` 查看当前 COM，再在串口终端运行 `--monitor 实际COM`；终端 B 运行 `python flash.py --pair right` |
| 结束 | 退出右板 monitor，拔右板 USB，右板也换独立电源 |

先完成两次烧录；配对按 `.comms-local/boards.json` 中本次保存的左右地址进行；若还没写入新映射，更新后的脚本会读取旧 `.week7-local/boards.json`。新板需要首次配对，已有认证绑定可复用。成功应显示 `authenticated_bond: true`。不录 `PAIR LOCALLY`、不保存串口日志；若先运行配对才发现未开 monitor，Ctrl+C 取消后按上表重试，不猜口令。无参数的 `--pair` 会检查两板，一根烧录 USB 线的首次流程使用上面的显式 left/right，避免等待另一块尚未读取的口令。

**A1.5 拍清两板均已独立供电。** 最后一块板烧录/必要配对后，摄影手机拍到它从 laptop USB 拔下并换独立电源；同时拍清另一块已独立供电。沿电源线拍到两个电源，laptop 的 USB 口不再连接任何 FireBeetle。此时不再运行额外配对或串口命令；A4 启动时的认证连接日志是正常检查证据。

> USB setup is finished. Both boards are now disconnected from the relay laptop and powered independently. The capture checks their authenticated Bluetooth connections before streaming application data.

### A2｜启动或展示本次 SSH 隧道

**R02 操作：** 自己打开终端 A，进入仓库后运行：

```powershell
python demo.py tunnel
```

> This command opens the existing SSH route to Ultra96. I keep this terminal open during the demonstration.

在**当前终端 A** 输入两跳密码，随后保持它运行；它不另开窗口。A4 要切到终端 B，不能在隧道终端输入下一条采集命令。

若需输入两跳密码，暂时把镜头移开；也可以录前私下启动，镜头中说明它已运行。已有确认属于本项目、使用本地 18889 的隧道就直接复用，不开第二个实例。

**预期：** 提示 `Opening SSH tunnel on 127.0.0.1:18889`；完成认证后安静等待正常，窗口保持打开。隧道存在不等于应用通信成功，后面必须看到 ACK。路径为 laptop `127.0.0.1:18889` → SSH → Ultra96 `127.0.0.1:8888`。

**英文口播：**

> The laptop's SSH tunnel is running. It forwards this local port to the private ingestion service on Ultra96. I entered the credentials outside the recording. Successful application communication will be shown by the correlated acknowledgements in the next step.

### A3｜Visualizer iPhone 先订阅，拍清开始画面

**机器：** Visualizer iPhone；摄影手机拍它，不在 Visualizer 上打开相机。

1. Unity → **Week 7 Connect / Settings**，保持 **Use campus jump host** 开启。使用已有 verified public CA；必要时点击 **Import verified public CA** 导入那张公开证书。
2. 在镜头外填 Board / Jump 登录信息，点 **Connect**。等待 `Subscribed, Received: 0`。
3. 摄影手机拍清 `Subscribed`、开始时的 `Received` 和结果区域。已有订阅的计数可以不是 0；保留此画面，用于和同次运行结束画面对照，无需输入电脑。
4. 之后保持 Unity 前台、不锁屏、不再点 Connect。手机自己连接 Ultra96 的 9999 服务，不连接 Windows 18889。

**未到 Subscribed 不开始 A4。** 先查 VPN、两跳凭据、CA、版本及有无竞争订阅者。

**英文口播：**

> The Visualizer has established its own SSH and TLS connection to Ultra96 and completed the subscription handshake. The camera records its starting received count. I will keep the app in the foreground while the laptop sends data.

### A4｜跑一次真实双设备采集，拍两条链路的现象

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

### A5｜自动报告、手机结束画面与本次证据

1. 等 `demo.py run` 自然结束。终端自动显示最终报告、两设备匹配 sensor/ACK，并打印 **`Saved in: ...` 完整目录**；无需再运行一个脚本或输入手机数字。
2. 摄影手机拍清 `CAPTURE PASSED`、两台最终计数、`Phone expected increase` 和本次路径。等待手机 Received 稳定，拍清手机结束画面及最后结果。停止发送约两秒后出现 `No live result` 是最新标签过期，Received 仍可观察。
3. 对照同一次录像的手机开始/结束画面和报告的预期增量。脚本只统计源端、laptop 接收与 Ultra96 ACK；**手机实际收到了多少由手机画面证明**，不能用报告的预期值代替手机读数。

| 要看什么 | 在哪里看 | 成功依据 |
|---|---|---|
| [N1] / [N2] | 报告 Device 1 / 2 的 Generated | 每台 Generated = Received = ACKed；MissingBLE / MissingACK 均 0 |
| 手机预期增量 | `Phone expected increase` | Video 未开 keyboard，预期为 N1 + N2；这是计算值 |
| 手机实际接收 | 同次录像的开始、增长及结束画面 | Received 真实增长，出现两个设备的结果；可读时与预期增量比较 |
| [CAPTURE] | 本次 `Saved in` 完整目录 | 更新后的默认路径为 `D:\LetThemCook\.comms-local\B07-...`，保留该次全部文件 |
| 采集摘要 | 同一份报告 | `Exit=0 clean=True mock_input=False report_saved=True`，且 `CAPTURE PASSED` |

运行中收到数与 ACK 数暂时不同可以正常；最终排空后再比较。手机画面不清楚或增量不符时，不能宣称手机计数一致。程序不读取 iPhone 屏幕，也不生成手机逐条收据或自动手机通过结论。

**报告通过、手机画面也核对后口播：**

> Device one generated [N1] packets and device two generated [N2]. Each device's generated, received and acknowledged counts match. The filmed phone shows its actual reception during this same capture. The report's expected phone increase is a comparison value, not a receipt from the phone.

**若失败：** 保存原报告/视频，不读成功结论。可说：

> This capture did not meet the acceptance checks. I will retain these results, investigate the mismatch, and record a new capture before claiming successful communication.

**展示自动打印的 packet。** 拍清两台设备各自匹配 sensor/ACK 的 device_id / boot_id / seq、**完整八个 values** 和 ACK 的 `validation=accepted`。找不到匹配时不借别次记录凑数。需要逐行查看时，用编辑器打开该目录下的 `packets.log`。

> These decoded records show each sample's device, boot, sequence and eight values, followed by its matching acknowledgement. That confirms ingestion by Ultra96. The camera footage separately shows what the iPhone received.

用文件资源管理器把摄影手机的本段视频、手机开始/结束画面及必要备注放入**这个目录**的 `camera-clips` 子目录。保留原始 `live.log`、`packets.jsonl`、`packets.log`、`report.json`、`report-readable.json`、`exit-code.txt`，不覆盖失败尝试。把本次完整 Saved in 路径写入录像笔记，供之后核对。

完成 A5 后继续 A6；终端 B 的采集已结束，终端 A 的隧道暂时保留。先保存修改前证据，再接 USB 做下一轮 setup。

### A6｜修改 dummy packets → 重新编译/上传 → 重新运行并核对

**本段继续用摄影手机拍电脑和硬件。** 它对应 General Guidelines 的 “change the dummy packets … recompile/rerun”。录屏时只在[展示稿第 02 节](./B07-CO-video-presentation.en.md#b2)简述原理。沿用已有脚本，不需要新增命令工具；修改和烧录由你在录制时实际执行。

**A6.1 留下修改前证据，再现场编辑。** 把 A5 的准确 Saved in 目录记为“修改前”，保留该次手机开始/结束画面。用资源管理器把当前 `common/dummy_fixtures.json` 复制到这个目录留档。在编辑器打开该次 `packets.log`，搜索完整的 `values=[1200, -300, 850, 40, -20, 15, 600, 250]`，记录对应 `device_id`、`boot_id`、`seq`；这是后面对照的基准。

**哪些值可以改：** 任意一组、任意一项都可以修改；每组必须正好 **8 个整数**，各值范围 **−32768～32767**，整份文件保留 **2～64 组**。保持合法 JSON，不写小数、字符串或注释。下面的 1200 → 1500 只是容易对照的演示例子；若现场选了其他值，就同步替换口播中的数字和日志搜索的完整八项。固件随机抽取整组，不保证每个包都出现修改值；非法内容会在 `flash.py` 生成阶段报错，后续构建/上传停止。

编辑时保持合法输入：2–64 组、每组 8 个 int16，范围 −32768..32767；这次只改一个值，格式解释放在 B2。

在 VS Code 打开 [common/dummy_fixtures.json 第 3 行](../common/dummy_fixtures.json#L3)，按本稿示例只把第二组第一项 **1200 改成 1500**，其他七项和其他三组保持不变，按 Ctrl+S 保存。拍清修改过程。以下是同一组修改前后的内容；不是把整份 JSON 换成单独一组：

| 状态 | 第二组的完整八个 values |
|---|---|
| 修改前 | `[1200, -300, 850, 40, -20, 15, 600, 250]` |
| 修改后 | `[1500, -300, 850, 40, -20, 15, 600, 250]` |

**英文口播：**

> I am changing the first channel of the second dummy fixture from twelve hundred to fifteen hundred. Each fixture still contains eight signed sixteen-bit values, and the thirty-two-byte packet format remains unchanged. The firmware will continue selecting randomly from the four fixtures.

**A6.2 重新编译并上传，两块都要更新。** 确认 `demo.py run` 已结束且串口监视已关闭；准备好用同一根烧录 USB 线依次连接左板和右板。终端 A 的隧道可以继续复用。

| 顺序 | 在终端 B 运行 / 操作 | 必须观察到的结果 |
|---|---|---|
| 1 | `python flash.py`；按已有 LEFT → RIGHT 标签接入，保留手部角色 | fixture 头重新生成；两次上传成功，地址映射自动更新；失败即停 |
| 2 | 打开 [comms_fixtures.h 第 9 行](../firmware/esp32/include/comms_fixtures.h#L9) | 第二组为 `{1500, -300, 850, 40, -20, 15, 600, 250}`；这是生成结果，不直接编辑 |
| 3 | 右板上传后也拔掉 USB，确认两板均恢复独立供电 | 镜头拍清真实采集前两板均已断开 laptop USB；已有绑定不用再 pair |
| 4 | Visualizer 保持前台且 Subscribed；必要时重连，拍本轮开始画面 | 本轮手机开始状态清楚，不借修改前那次画面 |
| 5 | `python demo.py run` | 两台认证连接通过；新 60 秒采集结束后自动报告、匹配记录和新 Saved in 目录 |
| 6 | 拍本轮手机结束画面，与本轮报告比较 | 电脑与手机证据都属于修改后的这一次 |

如果隧道此前已结束，按 A2 在终端 A 重开 `demo.py tunnel`；否则复用。认证失败才按 A1 的少用选项排查，不能降级安全。只修改合法 payload 数值时，重新构建两块 FireBeetle 即可，不需要重编译 Ultra96 或 iPhone App。

**英文口播：**

> I run the same flash script again, using one programming USB cable for the two boards in turn. After restoring independent power, I start a new capture with demo.py. It displays the report automatically, while the camera records the phone's received count.

**A6.3 在新日志里证明修改已生效。** 把新 Saved in 目录记为“修改后”，用资源管理器将修改后的 JSON、生成的 `comms_fixtures.h` 及本轮手机开始/结束画面复制到该目录留档。在 VS Code 打开**新目录的 `packets.log`**，Ctrl+F 搜索完整的 `values=[1500, -300, 850, 40, -20, 15, 600, 250]`。找到 device 1 和 device 2 各至少一条 `type=sensor`、`direction=ESP->laptop`、`validation=decoded` 的记录，拍清八个 values 和该条的 boot/seq。

再按各自 `device_id`、`boot_id`、`seq` 找到同一文件中的 `type=sensor_ack`、`direction=Ultra96->laptop`、`validation=accepted` 记录。可以搜索 `packets.jsonl` 中同一身份辅助定位；不能拿另一台或另一条 seq 的 ACK 配对。修改前后不要求 boot/seq 相同，重新上电会建立新的启动身份。

**注意随机选择：** 自动报告只展示每台设备找到的首个匹配样本，那条不一定抽到第二组；终端输出也会抽样显示。用保存的 `packets.log` / `packets.jsonl` 查找，不能因首个样本没有 1500 就认定失败，也不能未找到就宣称成功。若任一设备找不到更新后的完整组，保留此次记录并排查其固件/上传/采集，确认后再录新的采集。

**核对完成后才说：**

> The earlier capture contains the original fixture starting with twelve hundred. In this new capture, both devices have transmitted the updated fixture starting with fifteen hundred. Each displayed sample has a matching Ultra96 acknowledgement. The new report passes its checks. The corresponding camera footage shows the phone receiving results and its count increasing.

手机展示的是结果事件和接收数，不一定直接显示这八个 sensor values；不能要求手机出现数字 1500，也不能把随机 AI 事件变化当作 payload 已更新的证明。修改证据是新采集中的实际 sensor values，ACK 和手机计数分别说明接入及结果接收。

**A6 完成后再停止摄影手机。** 保留“修改前/修改后”两套目录和各自计数；修改前后对比在本实拍段完成，B 阶段只讲原理，不再重复翻日志。展示实际 JSON 和本次两份日志，不把文档中的代码快照当成现场结果。若之后恢复 1200，也需要重新运行 `python flash.py` 烧录才能恢复硬件数据，不能只改回 JSON 就宣称两板已恢复。现在可在自己运行的终端 A 按 Ctrl+C 结束隧道，不停止共享 Ultra96 服务。

## 第二阶段 B：电脑录屏，只讲 8 节，十分钟以内

**只打开** `D:\LetThemCook\docs\B07-CO-video-presentation.en.md`，按 **Ctrl+Shift+V** 预览，从 **01 → 08** 顺序向下讲。主稿已经替换成短版，没有需要继续讲的长附录。你之前录的实物段仍可使用。

**怎么读：** 顺着页面向下，每个 `>` 引用块内的英文只念一次；它就放在对应图或代码旁。图上的文字、源码、英文注释、文件名和行号只用鼠标指出，**不逐项念、不额外解释**。所有必讲代码已内嵌，不必打开源文件来回切换；Source 链接只是核对入口。

**时长依据：** 全部口播共 **494 个英文词**。按偏慢的每分钟 70 词约 **7 分 03 秒**，另留约 **1 分 30 秒** 滚动和指图，预计 **8 分 33 秒**。下表给出 9 分 05 秒的分段上限，保留到 10 分钟的余量。正式录制前计时一遍；第 08 节最后一句后立即停止。**十分钟限制只针对本电脑录屏段，前面的真实烧录/通信/修改数据实拍另计。**

### 逐节照做：展示哪一行、指什么、说什么

下表的“展示稿行”指英文 Markdown 文件的行号。需要定位时点回该文件编辑器，**Ctrl+G 输入行号**，再打开预览。代码注释中的 `L` 是源文件行号。

| 顺序与累计时间 | 展示稿行 / 画面 | 鼠标指出什么；说什么 |
|---|---|---|
| B1 · 0:00–1:00 | [第 6 行：01 Architecture](./B07-CO-video-presentation.en.md#b1)；G01 架构图、2 行 ID 配置 | 指两块板 → laptop → Ultra96 → phone，以及 ID=1/2。只读本节英文，覆盖架构、ID、独立供电。 |
| B2 · 1:00–2:20 | [第 22 行：02 Packets](./B07-CO-video-presentation.en.md#b2)；G03 字节图、G04 包类型图、2 个短代码块 | 依次指 32 字节字段、14 字节 control header、opcode 和随机选整行。只读本节英文，不逐格念图，不再回放 dummy 修改。 |
| B3 · 2:20–3:00 | [第 55 行：03 BLE](./B07-CO-video-presentation.en.md#b3)；G05 FSM | 顺着连接 → 认证 → 订阅 → 发送箭头，再指断开回广播。只读本节英文。 |
| B4 · 3:00–4:00 | [第 62 行：04 Laptop–Ultra96](./B07-CO-video-presentation.en.md#b4)；G07 FSM、readexactly 代码 | 指 Active / retry，再指 readexactly(4) 和 readexactly(length)。只读本节英文，讲 ACK 与 TCP 分片。 |
| B5 · 4:00–4:45 | [第 82 行：05 Visualizer](./B07-CO-video-presentation.en.md#b5)；G08 FSM | 指 SUBSCRIBE → SUBSCRIBED → result、Paused → Connect。只读本节英文；无需重开手机或报告。 |
| B6 · 4:45–6:55 | [第 89 行：06 Encryption](./B07-CO-video-presentation.en.md#b6)；G09 图和三个通道的小节 | 逐段指 BLE 安全参数/验证、Python TLS 验证、Swift TLS/SSH pin。**三段英文各读一次**；每个通道都让源码出现在录屏里。 |
| B7 · 6:55–8:00 | [第 191 行：07 Laptop concurrency](./B07-CO-video-presentation.en.md#b7)；G10 框图、3 个短源码块 | 图上指每板各自输入/发送、queue、ACK、logger；代码指 create_task、lock、call_soon_threadsafe、Thread。只读本节英文。 |
| B8 · 8:00–9:05 | [第 232 行：08 Ultra96 concurrency](./B07-CO-video-presentation.en.md#b8)；G11 框图、一个合并源码块 | 指 ingest 和 gateway 两路、result queue、返回 ACK，再指 client/sender/monitor tasks。只读本节英文，最后一句后停止录屏。 |

### 源码定位备查：不增加口播

| 录屏段 | 原源文件与必须指出的位置 |
|---|---|
| B1 | `firmware/esp32/platformio.ini` L21 / L26：编译进左右 device ID。 |
| B2 | `common/sensor.py` L11–12：实际 32 字节格式；`firmware/esp32/include/comms_packet.h` L57–60：随机选择完整 fixture。 |
| B4 | `common/wire.py` L53 / L58–62：先读完整长度，再读完整正文，检查长度范围。 |
| B6 · BLE | `firmware/esp32/src/main.cpp` L251–256：Secure Connections / MITM / bonding / key；`comms_security.h` L10–17：认证结果检查和发送门槛。 |
| B6 · laptop–Ultra96 | `common/tls.py` L7–12 / L16–19：客户端 CA+hostname，服务端证书和私钥；`laptop/bridge.py` L350–353：实际 TLS 建连；`tools/ssh_tunnel.py` L26–28：SSH host 验证。 |
| B6 · phone | `CommsClient.swift` L88–92 / L142：完整 TLS 验证、hostname；`Trust.swift` L7–10：SSH host-key pin。 |
| B7 | `laptop/dual_bridge.py` L94–95 / L106：每板任务；`laptop/bridge.py` L128 / L138 / L633–634：lock、线程安全唤醒、send/ACK；`laptop/evidence.py` L33–34：日志线程。 |
| B8 | `ultra96/server.py` L151 / L187：listener/client tasks；L272–275：result/ACK 两条路径；L334–337：sender 与 monitor。 |

**成片核对：** A 段有真实操作和手机接收证据；B 段 8 节全覆盖且计时小于 10 分钟。没有实际录到成功结果时，不用图解或旧日志替代成功证据。
