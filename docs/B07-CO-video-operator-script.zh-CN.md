# B07 CO 录像操作稿：先拍实物，再录电脑

**先双击 [Video-Demo.cmd](D:/LetThemCook/Video-Demo.cmd)。录像时选数字即可，不需要再粘贴长串命令。** 备用方式是在 `D:\LetThemCook` 运行 `python video_demo.py`。启动只显示菜单，不会自动烧录、采集或停止服务。

## 数字菜单与最短录制顺序

| 输入数字 | 做什么 | 你还需要做什么 |
|---|---|---|
| **1** | 生成 fixtures → 编译左右固件 → 上传两块板；失败即停 | 按列出的数字选择已核实的 left / right 串口，不能同口 |
| **2** | 检查两块板的认证绑定；需要时交互输入 PIN | 已绑定直接复用；首次口令按下面的 8 → 2 流程 |
| **3** | 新窗口启动 SSH tunnel | 在新窗口输入密码并保持窗口打开 |
| **4** | 录制 60 秒、每台 10 Hz；结束显示报告、匹配数据与人工计数对账 | 先拔两条 USB、独立供电、手机 Subscribed；按提示填 P0，结束填 P1 |
| **5** | 重新显示准确的本次报告和两设备匹配 sensor/ACK | Enter 用保存的本次目录；也可粘贴明确的历史目录 |
| **6** | 打开图解与源码投屏 HTML | 按 Gxx / Cxx 链接展示即可 |
| **7** | 打开 `dummy_fixtures.json` 编辑 | 保存后回 1，重新生成、编译、上传；再拔 USB 做新采集 |
| **8** | 为选定 COM 开一个 115200 串口监视窗口 | 首次配对时先选 8，再回 2；口令避开镜头，完成后关监视器 |
| **9** | Ultra96 服务子菜单：1 只读检查；2 端口空闲时启动当前部署 | 新 SSH 窗口手输密码；已有正常服务只检查，不重复启动 |
| **0** | 退出主菜单 | 独立的隧道/串口/板端窗口按各段说明处理 |

**最短操作路线：** 录前 `9 → 1` 检查板端、选 `6` 打开图源 → 摄影手机开始 → A1 选 `1` 烧录、需要时 `8 → 2` 配对、拔 USB 独立供电后再选 `2` → A2 拍图源的 ID/包格式代码 → A3 选 `3` → A4 手动连 Visualizer → A5 选 `4`（包含 A6 的报告和对账）→ 保存画面 → B 阶段选 `6` 录图解/代码，B7 选 `5` 重看同次证据。

**本次只使用两个主文件：**

| 文件 | 用途 | 怎么打开 |
|---|---|---|
| [B07-CO-video-visuals.en.html](D:/LetThemCook/docs/B07-CO-video-visuals.en.html) | 独立投屏文件：G01–G11 图解、配套英文说明、可点击跳转的源码片段 | 浏览器打开；左右方向键 / PageUp / PageDown / 空格翻页，Home / End 跳到首尾，F 切换全屏；代码页 Esc / Back 返回图解 |
| [B07-CO-video-operator-script.zh-CN.md](D:/LetThemCook/docs/B07-CO-video-operator-script.zh-CN.md) | 本操作稿：中文步骤、数字菜单操作、英文口播、源码定位 | 放在旁边参考，不必把整篇投屏 |

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

General 要求放在相应段落：实际格式的多组随机 dummy 数据、可修改后重跑、FSM、并发框图、清楚的解码日志/两路颜色、无 relay laptop USB、服务器在 Ultra96、无 message broker、TCP 消息可能分段。本稿不安排 Live-only 的完整键盘 pipeline、测速/极限速率、断电/超距或鲁棒性专项考核；60 秒只是这里通信镜头的采集长度。

## 开录前准备：不计入口播

1. 双击 `D:\LetThemCook\Video-Demo.cmd` 打开主菜单；无需预先设置 PowerShell 变量。Windows 的 Python 应能运行项目；本机核实过 Python 3.12.7 和 Bleak 3.0.1。备用入口是在仓库根目录运行 `python video_demo.py`。
2. 本机已准备 PlatformIO 和串口驱动；本次在 A1 用**同一台 laptop** 拍真实构建/上传过程。**USB 只用于 setup；实际 BLE 通信前拔掉两条 USB，改独立供电。** Ultra96 和已安装的原生 iPhone App 都支持匹配的 v2。更新仓库不等于更新已经烧录/安装的程序；不要为了录像无理由清除既有认证绑定。
3. Windows 蓝牙开启；Windows 和 Visualizer iPhone 均开启所需 VPN。关闭连接这两块板子的其他 BLE 客户端。
4. Ultra96 当前服务需监听板端 `127.0.0.1:8888` 和 `127.0.0.1:9999`。菜单 **9 → 1** 检查并复用正常服务，不重复启动；仅不存在时按附录用 **9 → 2**。当前部署源码目录为 `/var/tmp/cg4002-week7-yanjie-20260907/source-co-v2-20260928T122047Z`；历史 PID 不能当作当天状态。
5. 手机是本次唯一结果订阅者。不要另跑 `phone.receiver`、`laptop.phone_simulator`、`tools.rehearse_remote_week7`；新订阅者会替换旧订阅者。
6. 准备两个独立电源，例如不会因低电流自动关机的充电宝。A1 烧录/首次串口配对时可以 USB 接这台 laptop；A5 开始实体 BLE 采集前，两块板都必须**完全断开 laptop USB**，各自使用独立电源，即使另有电源也不能保留 laptop USB 线。
7. 默认 CA 是 `C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\ca-cert.pem`。这是已有可信公开证书，不为普通录像重新生成 PKI；不打开任何私钥文件。
8. 密码输入和首次配对口令放在镜头外完成。电脑终端字号调到手机能拍清，关闭通知；摄影手机试拍一次，确认无反光且能读清 Visualizer 的计数。

| 窗口名称 | 机器 | 本次用途 |
|---|---|---|
| 主菜单窗口 | Windows relay laptop | 选 1–9；构建/上传、绑定、采集、报告都从这里操作 |
| SSH tunnel 新窗口 | 同一 Windows laptop，菜单 3 打开 | 输入两跳密码；真实采集时保持打开 |
| 串口监视新窗口 | 同一 Windows laptop，菜单 8 打开 | 首次配对读取口令；不拍秘密，完成后关闭再拔 USB |
| Ultra96 SSH 新窗口 | 同一 laptop，菜单 9 打开 | 录前检查/需要时启动当前服务；不是数据桥接 |
| 浏览器 + 编辑器 | 同一 Windows laptop；A 阶段相机拍屏，B 阶段电脑录屏 | HTML 图解 + 源码 + A 阶段保存的日志 |

## 第一阶段 A：摄影手机拍 setup、包格式说明与真实通信

**这阶段要拍电脑上的 setup 和 packet 源码操作。** A1/A2 先做设置和包格式解释，A3–A6 连续完成数据链路；实际采集开始后不再穿插源码讲解。图解、加密和并发 walkthrough 留到 B 阶段。英文块可以现场说或后配音；成功结论必须等实际核对后再录。

### A0｜摆好机位与开场

**画面：** 摄影手机横拍，两块带标签的 FireBeetle、电源、relay laptop 和 Visualizer iPhone 同框。Ultra96 可通过部署说明交代位置，不把笔记本说成服务器。

**操作：** 电脑显示 `Video-Demo.cmd` 的主菜单，录前选 **6** 打开的图源在旁边待用；确认尚无采集程序运行。摄影手机开始录像，先停留 5 秒拍清各设备。此时不要切换 Visualizer iPhone 去拍其他东西。

**英文口播：**

> This is B07's communication subsystem. I will first show the FireBeetle setup, actual firmware upload and packet-format code with this camera, followed by a physical communication run. Later, a computer screen recording will explain the diagrams, encryption and concurrency. The filming phone and Visualizer iPhone are different devices.

**镜头停在主菜单，补一句脚本说明（约 20 秒）：**

> This menu is an operator shortcut. It calls our existing PlatformIO, pairing and demo tools. It builds and uploads in order, stopping on failure, and saves each capture separately with its evidence. It does not replace the BLE or TLS protocols. I enter the phone counts manually.

### A1｜FireBeetle setup — [Video only]：真实编译、上传、供电与绑定

**本段用摄影手机拍电脑屏幕和板子；真的执行构建/上传并拍成功结果，不只展示命令。** 这是 setup 阶段，尚未运行 BLE 采集。同一台 Windows laptop 可接 USB 烧录；本段末尾必须拍两条 USB 均已拔掉，并改独立供电。

**A1.1 打开固件项目并指出左右环境。** 在编辑器按 Ctrl+O，打开 `D:\LetThemCook\firmware\esp32\platformio.ini`，Ctrl+F 搜索 `firebeetle32-left`。拍清 `board = firebeetle32`、`framework = arduino`、left/right 两个环境和 `WEEK7_DEVICE_ID=1/2`，不要选择 `firebeetle32-unprotected-diagnostic`。

> I am setting up both FireBeetle ESP32 boards. PlatformIO builds Arduino firmware for the firebeetle32 board. The left environment assigns device ID one, and the right environment assigns device ID two. I will upload both builds using USB during setup, then remove both USB connections before the BLE communication demonstration.

**A1.2 菜单 1：核实并选择两块板的串口。** 录前只接左板，选 **8** 看串口列表、记下该板的 COM，然后输入 **q** 取消，**不打开 monitor**；拔下左板，只接右板，重复 **8 → 记 COM → q**，贴好 left / right 标签。再将两块都接上本机 USB。主菜单输入 **1**，脚本列出串口后，分别输入列表中 left 和 right 对应的**数字编号**。不能猜默认 COM3，也不能选同一个端口；脚本会拒绝同口。

脚本使用本机已安装的 PlatformIO，不需要你设置 `$b07Pio` 或把 `pio` 加入 PATH。选择前拍清左右标签，选择后拍清实际环境/COM 映射，避免左右刷反。

**A1.3 同一个菜单 1 自动构建并实际上传。** 完成端口选择后，脚本依次生成 fixture 头文件 → 编译 `firebeetle32-left` → 编译 `firebeetle32-right` → 上传左板 → 上传右板。某一步失败即停，不会继续假装全部成功。镜头保持在主菜单窗口；可以剪去等待，但保留左右两次 upload 的环境名和成功结尾。

**预期：** 对应环境显示 `SUCCESS` 且退出码 0；失败不能接着口播已烧录成功。此时不需要打开 server 私钥或串口 dump。

> The left and right uploads have completed successfully. Each board now contains the firmware built for its assigned device ID. A successful upload proves programming completed; the authenticated BLE checks and data capture will establish communication next.

**A1.4 菜单 2：检查两块板的认证绑定。** 回主菜单输入 **2**，脚本依次检查 left `38:18:2B:19:82:AE` 和 right `38:18:2B:18:9D:6A`。每台应打印 `authenticated_bond: true`；正常已有绑定就复用，不清除、不强制重配。

**首次配对的顺序是 8 → 2，仍在 USB setup 阶段完成。** 暂停拍摄敏感屏幕，选 **8** 并选对应 COM，脚本以 115200 打开新的串口监视窗口；需要两块首次配对时，为两块分别打开对应窗口，再回主菜单选 **2**。在隐藏输入提示填入各自串口显示的六位口令。不要保存串口日志或拍到 `PAIR LOCALLY`。

若已经选 2 后才发现需要口令、但尚未开串口，先 Ctrl+C 取消本次等待，再按 8 → 2 重试；不要凭猜测填口令。完成后关闭本次打开的串口监视窗口，再拍两条安全的绑定结果。失败先排查，不能以未认证状态继续。

**A1.5 明确拍到由 USB setup 切换为独立供电。** 摄影手机拍手拔掉两块板与 laptop 之间的 USB 线，然后各接独立电源并上电。沿两根线拍到电源，拍清 laptop 没有再连板子。回主菜单再选 **2**，拍到两台认证绑定检查通过；此时不再选 8、不再开串口。

> USB setup is now finished. I have removed both USB connections to the relay laptop and powered each board independently. Both boards have authenticated Bluetooth bonds. From this point, their application data travels over BLE. The bridge will establish the active connections and subscribe to notifications when the capture starts.

### A2｜Explain FireBeetle: Device IDs / packet types / packet format — [Live + Video]

**本段仍由摄影手机拍电脑屏幕，必须打开实际代码片段指出字段，不能只说有这些文件。** 主菜单选 **6** 打开图解。用页面导航到指定 G 页，点击下面的 C 按钮，代码就出现在**同一 HTML** 内；它显示真实源文件路径、原始行号和高亮行。点行号按钮可定位，Esc 或 **Back to Gxx** 返回图解，再点下一片段。此时尚未开始实际采集。

| 镜头顺序 | 在 HTML 怎么点 | 当场指给镜头的内容 |
|---|---|---|
| Device IDs | G02 → **C02 Board + IDs** → L21 / L26 | left / right 的 ID=1 / 2；L6 / L7 为板型和 Arduino |
| Sensor format | G03 → **C05 Sensor fields** → L11；返回后 **C06 Sensor codec** → L73 / L75 | struct、32-byte 长度校验、字段解码 |
| Random dummy | G03 → **C07 Fixtures** → L2–L5；**C40 Random source** → L94；**C08 Sensor send** → L507 / L508 | 多组八通道数据、esp_random、真实发送路径 |
| BLE packet types | G04 → **C09 BLE types** → L10–L16；**C10 Control codec** → L90 / L98 | opcode、响应位、14-byte 头、B7/version=1 |
| 网络类型/源端统计 | G04 → **C11 JSON types** → L8–L12；**C12 Source counters** → L49–L52 | SENSOR_BATCH/ACK/订阅/结果、source counters |

以上是生成投屏文件时保存的源码快照，**不会随着仓库修改自动更新**。若刚才改过 fixture/代码，改动部分应在编辑器打开实际文件并配新日志说明，不能用旧 HTML 快照证明已更新。实际文件定位如下，编辑器 Ctrl+O 输入完整路径、Ctrl+F 输入定位词即可：

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

**老师临时要求改 dummy 数据时：** 先结束采集，菜单选 **7** 打开 `dummy_fixtures.json`，例如把第二组第一项 `1200` 改为 `1500`；每组仍为八个 int16，数值 −32768..32767、总共 2–64 组。**保存文件后回菜单选 1**，脚本重新生成 fixture 头、构建和上传两块板。按 A1 再次拔掉两条 USB、独立供电，重复 A4–A6；菜单 4 记录新的 P0 和独立采集目录。

在这次新显示的完整 sensor values 中找到更新值，才说明实体数据修改已生效。只改 JSON、只编译未上传、重看旧日志都不能证明 ESP 数据已更新。正常录像可解释此流程；真的执行修改时，把修改前后两次证据分开，HTML 旧快照不会自动更新。

> These fixtures are editable. To change the transmitted dummy values, I edit the JSON, regenerate the firmware table, rebuild and upload both boards, remove USB and start a new BLE capture. The updated decoded values in that new capture show that the change took effect.

### A3｜启动或展示本次 SSH 隧道

**操作：** Windows 主菜单输入 **3**。脚本打开独立的 SSH tunnel 窗口；在那个窗口输入两跳密码，随后保持它打开，主菜单仍可继续选其他项。

若需输入两跳密码，暂时把镜头移开；也可以录前私下启动，镜头中说明它已运行。已有确认属于本项目、使用本地 18889 的隧道就直接复用，不开第二个实例。

**预期：** 提示 `Opening SSH tunnel on 127.0.0.1:18889`；完成认证后安静等待正常，窗口保持打开。隧道存在不等于应用通信成功，后面必须看到 ACK。路径为 laptop `127.0.0.1:18889` → SSH → Ultra96 `127.0.0.1:8888`。

**英文口播：**

> The laptop's SSH tunnel is running. It forwards this local port to the private ingestion service on Ultra96. I entered the credentials outside the recording. Successful application communication will be shown by the correlated acknowledgements in the next step.

### A4｜Visualizer iPhone 先订阅并记录起点

**机器：** Visualizer iPhone；摄影手机拍它，不在 Visualizer 上打开相机。

1. Unity → **Week 7 Connect / Settings**，保持 **Use campus jump host** 开启。使用已有 verified public CA；必要时点击 **Import verified public CA** 导入那张公开证书。
2. 在镜头外填 Board / Jump 登录信息，点 **Connect**。等待 `Subscribed, Received: 0`。
3. 拍清 `Subscribed` 和起点，写下 **[P0]**。若复用已有正常订阅，起点可以不是 0，必须记录实际值。
4. 之后保持 Unity 前台、不锁屏、不再点 Connect。手机自己连接 Ultra96 的 9999 服务，不连接 Windows 18889。

**未到 Subscribed 不开始 A5。** 先查 VPN、两跳凭据、CA、版本及有无竞争订阅者。

**英文口播：**

> The Visualizer has established its own SSH and TLS connection to Ultra96 and completed the subscription handshake. Its starting received count is [P0]. I will keep the app in the foreground while the laptop sends data.

### A5｜跑一次真实双设备采集，拍两条链路的现象

**操作：** SSH tunnel 窗口保持运行，主菜单输入 **4**。按屏幕提示确认已拔掉两条 laptop USB、改独立供电、Visualizer 已 `Subscribed`，再填 A4 看到的起始计数 **[P0]**。脚本不能替你检查供电接线或读取手机屏幕；按提示如实操作。

菜单自动复用现有 `demo.py`，运行 60 秒、每台目标 10 Hz 的实体采集；不是最大速度测试。60 秒是两台都准备好后的共同观察时长，初始化和收尾会让实际等待略长。不要 Ctrl+C，让命令自然结束。结束后菜单会接着询问 **[P1]** 并完成 A6，不需要再输入报告命令。

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

### A6｜看最终报告、核对手机、保存这一次证据

1. 等 A5 自然结束。**菜单 4 会继续处理本次结果**：先显示准确的本次报告和两台匹配 sensor/ACK；等手机计数稳定，在提示处输入最终 **[P1]**，再显示并保存人工计数对账。想重看就回主菜单选 **5**，目录提示处按 Enter。
2. 拍清报告路径、两台最终计数、`CAPTURE PASSED` 和 `Phone expected increase`。记录下面实际数字，不写死 1200。
3. 拍清最终 **[P1]** 和菜单的 `P0=... P1=... delta=... expected=...`。通过时应看到 `MATCH: clean capture total equals the operator-entered phone increase.`；`PHONE OBSERVATION NOT PASSED` 就不是通过。停止发送约两秒后出现 `No live result` 是最新标签过期，计数仍可核对。

| 要记的量 | 从哪里抄 | 成功条件 |
|---|---|---|
| [N1] / [N2] | 报告 Device 1 / 2 的 Generated | 每台 Generated = Received = ACKed；MissingBLE / MissingACK 均 0 |
| [E] | `Phone expected increase` | 本稿未开 keyboard，所以 E = N1 + N2 |
| [P0] / [P1] | A4 / A6 实际手机画面 | P1 − P0 = E |
| [CAPTURE] | 脚本显示的本次完整目录 | 位于 `D:\LetThemCook\.week7-local\video-menu\runs\<unique>\B07-...`，保留全部文件 |
| 摘要状态 | 同一份报告 | `Exit=0 clean=True mock_input=False report_saved=True`，且 `CAPTURE PASSED` |

运行中收到数与 ACK 数暂时不同可以正常；只用最终排空结果做核对。若额外加了 keyboard，预期手机数还要加 completed commands；不要沿用此稿无命令的公式。

**核对全部通过后口播：**

> Device one generated [N1] packets and device two generated [N2]. Each device's generated, received and acknowledged counts match, with no missing records reported. The Visualizer count increased from [P0] to [P1], an increase of [E], matching the expected total. This demonstrates successful ingestion and matching aggregate phone reception during this capture.

**若失败：** 保存原报告/视频，不读上面的成功结论。可说：

> This capture did not meet the acceptance checks. I will retain these results, investigate the mismatch, and record a new capture before claiming successful communication.

**本次路径由菜单保存，不需要复制 PowerShell 变量。** 菜单 4 通过前置检查并收到 P0 后，为实际采集创建独立目录；`last-attempt.json` 在底层采集启动前保存这一次尝试的位置。此后的失败/中断不会自动退回上一次成功报告。若在填写 P0 前就取消或未通过隧道/串口检查，则还没有开始新采集。目录缺失、不完整就显示问题；不要为了得到绿色结论改选别次结果。

**现在仍用摄影手机拍电脑，展示实际可读 packet。** 菜单 4 结束时，以及菜单 **5 → Enter** 重看时，都会显示两台设备各自匹配的 sensor/ACK。拍清 device_id / boot_id / seq、**完整八个 values**，以及同身份 ACK 的 `validation=accepted`。这是实际文件证据，不是教学假数据；找不到匹配时不借别次采集凑数。需要逐行查看时，再用编辑器打开该目录下的 `packets.log`。

> These are decoded records from the capture that just finished. The sensor record shows the device, boot, sequence and eight values. The acknowledgement refers to the same identity and confirms ingestion by Ultra96. The separate iPhone count check establishes the aggregate phone observation.

用文件资源管理器把摄影手机的本段视频副本、P0/P1 画面及 N1/N2/E 的简短备注放入**这个目录**的 `camera-clips` 子目录。保留原始 `live.log`、`packets.jsonl`、`packets.log`、`report.json`、`report-readable.json`、`exit-code.txt` 及菜单保存的手机人工观察信息，不覆盖失败尝试。仍记下完整路径：若之后又开了新尝试，另一天录 B 时可在菜单 5 粘贴明确的旧目录。

至此可停止摄影手机录像。若 B 不接着做实时操作，可在本次自己打开的 SSH tunnel 窗口按 Ctrl+C 结束隧道；菜单 **0** 退出主界面。不为结束录像停止共享 Ultra96 服务，也不需要让实体设备等到代码讲解录完。

## 第二阶段 B：电脑录屏，图解、加密与并发源码

**开始前：** 双击 `Video-Demo.cmd`，选 **6** 打开图解；按 Home 到 G01，F 全屏，左右方向键 / PageUp / PageDown / 空格翻页。代码已内嵌到同一文件，无需切编辑器：点击 **Cxx + 英文名称** 打开片段，再点 **L行号** 按钮定位；Esc 或 **Back to Gxx** 返回所属图解。将浏览器缩放到投屏清楚的字号，本稿放在旁边。

**统一节奏：** 先投 G 页 → 读“投屏英文旁白” → 点击表内标为“主讲”的 C 按钮 → 指定行号 → 读“代码口播” → Back 返回图解 → 下一页。B2–B4 只回顾 A 阶段已经录过的 setup / 格式，不重做操作；“备查”代码只在需要展开时打开，不需要逐条朗读全部 41 个片段。B 阶段不运行 hardware/bridge，不穿插拍实物；重看 A 的报告只读文件。

代码片段标有原文件、原始行号和来源 hash，是生成 HTML 时的真实源码快照。若 A 之后改过代码，应展示相应实际文件/记录版本差异，不把快照说成自动同步编辑器。

**开头声明：**

> The physical demonstration was recorded earlier. I will now explain the implemented protocols, setup and source code. When I reopen a report or packet log, it is saved evidence from that recorded capture, not a new live run.

### B1 / G01｜系统架构：服务器和两条结果路径

**投屏英文旁白（与 HTML 一致）：**

> Two FireBeetles send structured dummy sensor packets to the relay laptop over protected Bluetooth Low Energy. The laptop forwards both streams to Ultra96 and receives ingestion acknowledgements. The Visualizer iPhone has its own SSH and TLS connection to the board. Ultra96 sends gesture results directly to that phone. The application servers run on Ultra96. We use SSH for the deployed campus access route and do not use a message broker.

**点击代码顺序（范围是原文件行号，按钮名与 HTML 相同）：**

| 用法 | 点击按钮 | 源文件与片段范围 | 可点的定位行 |
|---|---|---|---|
| 主讲 | **C41 Video menu** | [video_demo.py](D:/LetThemCook/video_demo.py:358)，358–377 | L359 / L360 / L361 / L377 |
| 底层 launcher 备查 | **C01 Launcher** | [demo.py](D:/LetThemCook/demo.py:64)，64–81 | L67 / L69 / L72 |


**投屏 G01：** 指 FireBeetle → laptop → Ultra96，再指独立的 Ultra96 → iPhone；读图页英文说明。指出应用服务运行在 Ultra96，未使用 message broker；SSH 是当前校园访问路线，不是 TCP 固有要求。

**代码画面：** G01 → **C41 Video menu**，指 L359–L361 的数字到操作映射，再指 L377 调用所选操作。这里只解释菜单如何调用已实现的工具；不在录屏阶段执行烧录、配对、隧道或新采集。

**代码口播（约 10–15 秒）：**

> This table maps menu numbers to upload, pairing, tunnel, capture and review operations. The selected number calls one method, which reuses our existing tools. The menu simplifies operation; the bridge and server implement communication.

**底层 launcher 备查：** 需要展开菜单复用的实现时，G01 → C01，指 `demo.py` 的 capture_command() 启动 laptop.dual_bridge、固定 session / ACK window、保存 report / evidence。这里解释底层 launcher 的职责，不重新运行 tunnel 或 capture。

**底层 launcher 备查口播（可略过）：**

> This launcher has three commands. Tunnel opens the SSH route. Run launches the existing dual-device bridge, saves its logs and report, and prints the outcome. Report reopens saved evidence. The launcher does not start the Ultra96 server or connect the iPhone. The actual concurrent communication is implemented in the bridge and server modules shown later.

### B2 / G02｜FireBeetle setup 和 Device IDs 图解回顾

**投屏英文旁白（与 HTML 一致）：**

> PlatformIO builds our Arduino firmware for the firebeetle32 board. The left profile assigns device ID one, and the right profile assigns device ID two. We upload over USB during setup and then disconnect both USB cables. During the BLE demonstration, each board uses its own power source. We complete authenticated pairing before streaming. The BLE address selects the physical board, while the device ID identifies its application packets.

**点击代码顺序（范围是原文件行号，按钮名与 HTML 相同）：**

| 用法 | 点击按钮 | 源文件与片段范围 | 可点的定位行 |
|---|---|---|---|
| A 已讲；本段回顾/备查 | **C02 Board + IDs** | [firmware/esp32/platformio.ini](D:/LetThemCook/firmware/esp32/platformio.ini:4)，4–26 | L6 / L7 / L21 / L26 |
| setup 细节备查 | **C03 Boot setup** | [firmware/esp32/src/main.cpp](D:/LetThemCook/firmware/esp32/src/main.cpp:404)，404–423 | L406 / L421 |
| 配对实现备查 | **C04 Pairing** | [laptop/windows_pairing.py](D:/LetThemCook/laptop/windows_pairing.py:116)，116–127 | L119 / L120 / L123 / L125 |


**投屏 G02：** 回顾 A1 已由摄影手机拍到的真实构建/上传、双板 ID、认证绑定，以及 USB setup → 拔线 → 独立供电的切换。这里不再执行上传，也不把 setup 第一次放到本段才解释。

**画面：** 指 left / right profile 与 device 1 / 2 映射；必要时暂停到 A1 两次 upload 的成功画面。原始配置位置为 [platformio.ini](D:/LetThemCook/firmware/esp32/platformio.ini)，搜索 firebeetle32-left / firebeetle32-right。

**回顾口播：**

> The camera recording already showed both actual uploads and the authenticated bond checks. This diagram summarizes that setup and the distinct device identities. USB was used for programming and removed from both boards before the BLE communication capture.

### B3 / G03｜Sensor packet format 图解回顾

**投屏英文旁白（与 HTML 一致）：**

> Each sensor notification contains thirty-two bytes. The fields are the W7 marker, version, device ID, boot ID, sequence number, uptime and eight signed sixteen-bit channel values. Multi-byte fields use little-endian encoding. Version two randomly selects from several editable fixtures. Device, boot and sequence identify the sample. The packet has no custom application CRC field. Our dummy values follow the sensor packet schema, and the decoded log shows the actual values transmitted.

**点击代码顺序（范围是原文件行号，按钮名与 HTML 相同）：**

| 用法 | 点击按钮 | 源文件与片段范围 | 可点的定位行 |
|---|---|---|---|
| A 已讲；本段回顾/备查 | **C05 Sensor fields** | [common/sensor.py](D:/LetThemCook/common/sensor.py:11)，11–38 | L11 / L12 / L23 / L27 |
| A 已讲；本段回顾/备查 | **C06 Sensor codec** | [common/sensor.py](D:/LetThemCook/common/sensor.py:63)，63–80 | L67 / L73 / L75 / L78 |
| A 已讲；本段回顾/备查 | **C07 Fixtures** | [common/dummy_fixtures.json](D:/LetThemCook/common/dummy_fixtures.json:1)，1–6 | L2 / L3 / L4 / L5 |
| A 已讲；本段回顾/备查 | **C40 Random source** | [firmware/esp32/src/main.cpp](D:/LetThemCook/firmware/esp32/src/main.cpp:87)，87–96 | L89 / L94 |
| A 已讲；本段回顾/备查 | **C08 Sensor send** | [firmware/esp32/src/main.cpp](D:/LetThemCook/firmware/esp32/src/main.cpp:483)，483–511 | L500 / L503 / L507 / L508 |


**投屏 G03：** 用清晰图解回顾 A2 相机镜头里的 _PACKET / decode_packet，顺着 32 个 byte 的位置讲，不需要重复上传或生成数据。源码为 [sensor.py](D:/LetThemCook/common/sensor.py)、[dummy_fixtures.json](D:/LetThemCook/common/dummy_fixtures.json)、[week7_packet.h](D:/LetThemCook/firmware/esp32/include/week7_packet.h)。

**要指到：** W7、v2、ID、boot、seq、uptime、八个 int16，little-endian；fixture 是随机抽取，允许连续重复，真正的 values 已保存在 A6 的解码日志。没有 custom application CRC，不把校验或加密说成不存在的 CRC 字段。

### B4 / G04｜Packet types 与 BLE control format 图解回顾

**投屏英文旁白（与 HTML 一致）：**

> The sensor characteristic sends W7 notifications. The laptop reads W7S1 source counters for reconciliation. Commands use a separate B7 control header containing the opcode, device ID, status, request ID and offset. A response sets bit seven of the opcode. The command payload carries a complete version-two sensor packet. The control header itself remains version one. The laptop then uses SENSOR_BATCH and INGEST_ACK messages with Ultra96, while the phone uses subscription and gesture-result messages.

**点击代码顺序（范围是原文件行号，按钮名与 HTML 相同）：**

| 用法 | 点击按钮 | 源文件与片段范围 | 可点的定位行 |
|---|---|---|---|
| A 已讲；本段回顾/备查 | **C09 BLE types** | [common/control.py](D:/LetThemCook/common/control.py:8)，8–17 | L10 / L11 / L12 / L15 |
| A 已讲；本段回顾/备查 | **C10 Control codec** | [common/control.py](D:/LetThemCook/common/control.py:88)，88–101 | L90 / L97 / L98 / L100 |
| A 已讲；本段回顾/备查 | **C11 JSON types** | [ultra96/protocol.py](D:/LetThemCook/ultra96/protocol.py:3)，3–13 | L7 / L8 / L9 / L10 |
| A 已讲；本段回顾/备查 | **C12 Source counters** | [firmware/esp32/include/week7_source_stats.h](D:/LetThemCook/firmware/esp32/include/week7_source_stats.h:34)，34–53 | L41 / L44 / L45 / L49 |


**投屏 G04：** 回顾 A2 已实际打开的 [control.py](D:/LetThemCook/common/control.py) 和 [protocol.py](D:/LetThemCook/ultra96/protocol.py)。指 W7 notification、W7S1 source counters、B7 control request / response，再指网络消息类型。控制头为 14 bytes；响应置 bit 7；控制 version=1 与 sensor version=2 分开。

**需要进一步说明 source counters 时：** 打开 [week7_source_stats.h](D:/LetThemCook/firmware/esp32/include/week7_source_stats.h)，搜索 serializeSourceStats。24-byte W7S1 记录包含 device、boot、next sequence、submitted、failures，为 A6 的源端对账提供边界。它不等于手机的结果收据。

### B5 / G05｜BLE 协议 FSM

**投屏英文旁白（与 HTML 一致）：**

> On power-up, the FireBeetle advertises its BLE service. After the laptop connects, the firmware checks authenticated encryption. A valid peer can enable notifications. Sensor streaming requires a subscription and an ATT MTU of at least thirty-five. Our rate-control operation additionally requires an MTU of at least sixty-four. On disconnection, the device clears connection state and advertises again. This diagram summarizes the implemented control flow.

**点击代码顺序（范围是原文件行号，按钮名与 HTML 相同）：**

| 用法 | 点击按钮 | 源文件与片段范围 | 可点的定位行 |
|---|---|---|---|
| 主讲 | **C13 BLE gates** | [firmware/esp32/include/week7_security.h](D:/LetThemCook/firmware/esp32/include/week7_security.h:7)，7–25 | L10 / L11 / L14 / L16 |


**投屏 G05：** 广播 → 连接/认证 → ready → 通知发送；断开后重新广播/重连。这是行为概括，不声称源码存在同名 enum。读图页英文说明。

**代码画面：** G05 → C13，指 canNotify、sensorFitsMtu、canAcceptControl，把图里的安全/订阅/MTU 门槛对应到真实条件。

**代码口播：**

> These checks connect the state diagram to the implementation. Sensor notification requires a connected, subscribed and authenticated peer in the normal protected profile. Thirty-two bytes require an ATT MTU of at least thirty-five. This capture also used the control channel, which requires at least sixty-four. The laptop checks the bond, establishes notifications and retries after a disconnect. Historical MTU observations are not a guarantee of every future connection.

### B6 / G06｜TCP 分帧与 fragmentation

**投屏英文旁白（与 HTML 一致）：**

> TCP delivers a byte stream, so one application frame can arrive in several pieces. Our encoder prefixes the JSON body with its four-byte big-endian byte length. The receiver first reads exactly four bytes, checks that the length is between one and sixteen thousand three hundred and eighty-four, and then reads exactly that many body bytes. It parses and validates the complete JSON object. TLS provides encryption around these application frames.

**点击代码顺序（范围是原文件行号，按钮名与 HTML 相同）：**

| 用法 | 点击按钮 | 源文件与片段范围 | 可点的定位行 |
|---|---|---|---|
| 主讲 | **C14 Frame encode** | [common/wire.py](D:/LetThemCook/common/wire.py:35)，35–46 | L43 / L45 / L46 |
| 主讲 | **C15 Partial reads** | [common/wire.py](D:/LetThemCook/common/wire.py:49)，49–76 | L53 / L58 / L59 / L62 |


**投屏 G06：** 4-byte big-endian 长度 + UTF-8 JSON；读图页英文说明，指一个应用帧跨多个 TCP chunk 的图。

**源码：** [wire.py](D:/LetThemCook/common/wire.py) 的 `encode_frame()` / `read_frame()`，指出 `struct.pack("!I", ...)`、`readexactly(4)`、`readexactly(length)` 和 1..16384 限制。

**代码口播：**

> TCP provides a byte stream, not application-message boundaries. One read may contain part of a message or bytes from multiple messages. The sender prefixes the UTF-eight JSON body with a four-byte big-endian byte count. The receiver first reads exactly four bytes, validates the length, and then reads exactly that body length.
>
> It rejects malformed UTF-eight, duplicate JSON keys and invalid JSON objects. Message-schema validation follows at the endpoint. Notice the different byte orders: the BLE packet fields are little-endian, while the TCP length prefix is big-endian. Framing is not encryption.

### B7 / G07｜Laptop ↔ Ultra96 协议 FSM 和录制证据

**投屏英文旁白（与 HTML 一致）：**

> The laptop connects through the configured SSH route and verifies Ultra96's TLS certificate and hostname. In the active state it sends SENSOR_BATCH messages and validates matching INGEST_ACK messages. Sending and acknowledgement reading progress concurrently, with up to thirty-two outstanding messages per device. A connection failure retires the transport before retrying with a capped delay. Sent but unconfirmed packets are recorded as ambiguous drops, so reconnection does not imply complete outage replay.

**点击代码顺序（范围是原文件行号，按钮名与 HTML 相同）：**

| 用法 | 点击按钮 | 源文件与片段范围 | 可点的定位行 |
|---|---|---|---|
| 主讲 | **C16 TLS connect** | [laptop/bridge.py](D:/LetThemCook/laptop/bridge.py:349)，349–353 | L351 / L352 / L353 |
| 主讲 | **C17 ACK identity** | [laptop/bridge.py](D:/LetThemCook/laptop/bridge.py:375)，375–386 | L376 / L379 / L381 / L382 |
| 备查 | **C39 Retry delay** | [laptop/bridge.py](D:/LetThemCook/laptop/bridge.py:656)，656–670 | L660 / L667 / L669 |


**投屏 G07：** 建连/验证 TLS → active → 匹配 ACK；错误关闭重试与正常 drain 分开。读图页英文说明。

**代码画面：** G07 → C16 看 TLS 建连 → 返回 → C17 看 ACK 身份检查；需要讲故障重试时再点 C39，退避间隔有上限，不是重试次数有固定上限。v2 request_id：stream 为 null，command 为非零 ID；本次只运行 stream。流水线的实际任务创建在 B10 / G10 展示，板端接入代码在 B11 / G11 展示。

**代码口播：**

> The bridge opens a verified TLS connection through the SSH route. For each acknowledgement, it checks the version, session, device, boot and sequence, plus the version-two request ID. An acknowledgement with the wrong identity is rejected. On Ultra96, the ingestion handler validates the SENSOR_BATCH and replies with accepted or duplicate status. A duplicate does not create another independent result.
>
> The active state uses pipelined sending and acknowledgement reading, with up to thirty-two outstanding messages per device. This is not a stop-and-wait protocol. When the capture ends, the bridge drains pending work before producing its final source audit.

**重开 A 阶段证据，明确不是重跑：** 回主菜单选 **5**。如果保存的“本次目录”仍是 A 的那次，目录提示处按 **Enter**；如果后来做过别的尝试，粘贴 A6 记下的准确历史目录。先拍清打印的报告路径与录制那次一致，再看其报告和两设备的匹配数据。不要选菜单 4，那会开始新的实体采集。

停在同一身份的 sensor / sensor_ack，指出完整八个 values 和 accepted。若找不到匹配记录，不拼接其他运行补齐；查看本次报告解释问题。说明原始 `demo.py` 的 `_clean_capture()` / `show_report()` 检查源端/接收/ACK；菜单新增的是操作和人工计数记录，**不会读取 iPhone 屏幕**。

> This is saved evidence from the physical capture shown earlier. These decoded sensor and acknowledgement records share the same device, boot and sequence. The final report reconciles source generation, laptop reception and board acknowledgements. The phone's actual reception was checked separately using its observed count increase.

### B8 / G08｜Ultra96 ↔ phone 订阅 FSM

**投屏英文旁白（与 HTML 一致）：**

> After Connect, the iPhone verifies the SSH hosts and establishes verified TLS to the board's result service. It sends SUBSCRIBE and waits for SUBSCRIBED. It then validates GESTURE_RESULT messages and updates the received count and display. Version-two results use simulated random gesture labels. If the application becomes inactive, it pauses and requires an explicit Connect after returning. The filming phone is a different device, allowing this iPhone to remain in the foreground.

**点击代码顺序（范围是原文件行号，按钮名与 HTML 相同）：**

| 用法 | 点击按钮 | 源文件与片段范围 | 可点的定位行 |
|---|---|---|---|
| 主讲 | **C18 Phone subscribe** | [ios-visualizer/Week7Native/Sources/Week7Transport/Subscriber.swift](D:/LetThemCook/ios-visualizer/Week7Native/Sources/Week7Transport/Subscriber.swift:24)，24–50 | L28 / L31 / L37 / L41 |
| 主讲 | **C19 Phone pause** | [ios-visualizer/Week7Native/Sources/Week7Bridge/IntegrationController.swift](D:/LetThemCook/ios-visualizer/Week7Native/Sources/Week7Bridge/IntegrationController.swift:24)，24–37 | L26 / L27 / L28 |


**投屏 G08：** Connect → SSH/TLS 验证 → SUBSCRIBE / SUBSCRIBED → 收结果；失活进入 Paused，需要用户重连。读图页英文说明。

**代码画面：** G08 → C18 指 TLS handshake 后调用 Week7Protocol.subscribe、收 SUBSCRIBED 后调用 result 校验；返回 → C19 指 willResignActiveNotification 导致 Paused。校验函数的完整定义在 Protocol.swift；当前投屏片段显示调用点，不冒充整段解析器。随机 gesture 的生成在 B11 的 C35 显示。

**代码口播：**

> The phone sends a version-one subscription envelope for the selected session, then validates SUBSCRIBED before receiving results. The native parser accepts version-two gesture results, checks the session and allowed fields, and verifies the result ID against the device, boot and sequence. Version-two stream results have a null request ID.
>
> Ultra96 selects a simulated gesture for each new accepted input. The app receives results through its own connection. Leaving the app pauses reception, and returning requires an explicit connection step. Matching the phone's total count demonstrates aggregate reception in our recorded capture; it is not a saved per-result receipt ledger from the phone.

### B9 / G09｜Every channel：三条通道加密源码

**投屏英文旁白（与 HTML 一致）：**

> The FireBeetle link uses BLE Secure Connections with authenticated pairing and bonding. Its stack provides link encryption. The laptop independently verifies the Ultra96 TLS certificate against our CA and checks the expected hostname. The native iPhone performs its own TLS verification and pins the SSH host keys for its route. Both TLS clients require version one point two or newer. These are separate protected connections. We will now inspect the enforcement points in the source code.

**点击代码顺序（范围是原文件行号，按钮名与 HTML 相同）：**

| 用法 | 点击按钮 | 源文件与片段范围 | 可点的定位行 |
|---|---|---|---|
| 主讲 | **C20 BLE security** | [firmware/esp32/src/main.cpp](D:/LetThemCook/firmware/esp32/src/main.cpp:243)，243–262 | L251 / L253 / L254 / L255 |
| 主讲 | **C22 GATT access** | [firmware/esp32/src/main.cpp](D:/LetThemCook/firmware/esp32/src/main.cpp:391)，391–398 | L396 / L397 |
| 备查 | **C21 Peer check** | [firmware/esp32/src/main.cpp](D:/LetThemCook/firmware/esp32/src/main.cpp:196)，196–208 | L198 / L200 / L201 / L208 |
| 主讲 | **C23 Python TLS** | [common/tls.py](D:/LetThemCook/common/tls.py:4)，4–19 | L9 / L10 / L11 / L12 |
| B7 已讲；需要时回看 | **C16 TLS connect** | [laptop/bridge.py](D:/LetThemCook/laptop/bridge.py:349)，349–353 | L351 / L352 / L353 |
| 主讲 | **C24 iPhone TLS** | [ios-visualizer/Week7Native/Sources/Week7Transport/Week7Client.swift](D:/LetThemCook/ios-visualizer/Week7Native/Sources/Week7Transport/Week7Client.swift:88)，88–95 | L89 / L91 / L92 / L94 |
| 主讲 | **C25 Phone route** | [ios-visualizer/Week7Native/Sources/Week7Transport/Week7Client.swift](D:/LetThemCook/ios-visualizer/Week7Native/Sources/Week7Transport/Week7Client.swift:128)，128–150 | L138 / L140 / L142 / L144 |
| 主讲 | **C26 SSH pins** | [ios-visualizer/Week7Native/Sources/Week7Transport/Trust.swift](D:/LetThemCook/ios-visualizer/Week7Native/Sources/Week7Transport/Trust.swift:4)，4–10 | L7 / L8 / L9 |


**投屏 G09：** 读图页英文说明，依次指 BLE、laptop–Ultra96、Ultra96–phone 的保护边界。以下三段源码都录，不能只投一张图结束。

**① FireBeetle ↔ laptop。** 在 G09 点击 **C20 BLE security**，指 `ESP_LE_AUTH_REQ_SC_MITM_BOND`；Back 返回后点 **C22 GATT access**，指两个 `ENC_MITM` 权限。如果展开认证结果如何用于当前连接，再点 **C21 Peer check**，指 `currentPeer`。Windows 认证绑定的实际检查已在 A1 拍到；需要看实现可回 G02 的 C04。

> BLE uses authenticated Secure Connections with bonding and man-in-the-middle protection. These permissions require authenticated encryption for the protected GATT operations. The authentication callback applies the result only to the current peer, and the laptop requires an authenticated bond. Encryption is implemented by the Bluetooth stack; the application packet has no separate custom encryption function or CRC field.

**② Laptop ↔ Ultra96。** 在 G09 点击 **C23 Python TLS**，指 `minimum_version`、`CERT_REQUIRED`、`check_hostname`、`load_verify_locations` 和服务端的 `load_cert_chain()`。需要回顾连接调用时再点 **C16 TLS connect**。外层 SSH 路由已经在 A3 展示；此处核心源码是应用 TLS 的验证入口，不必另外跳编辑器。

> The Python client requires TLS one point two or newer. It verifies the server certificate against our configured CA and checks the hostname ultra96 dot week7 dot internal. The server loads its certificate and private key here, while the bridge supplies the verified context and hostname when connecting. In this deployment, TLS runs inside an SSH tunnel with host-key verification on both hops. SSH provides the route and authenticates the SSH hosts; TLS authenticates the application server.

**③ Ultra96 ↔ iPhone。** G09 → **C24 iPhone TLS** 指 `trustRoots`、`.fullVerification`、`.tlsv12`；返回 → **C25 Phone route** 指 `NIOSSLClientHandler` 的 `serverHostname`；返回 → **C26 SSH pins** 指 `validateHostKey()` 的匹配和拒绝分支。三段都在同一 HTML，按下列英文逐步讲。

> The native iPhone transport performs its own full certificate verification using the configured CA, TLS one point two or newer, and the same expected application hostname. Its SSH connections check pinned host keys, including the jump host. This protects the result connection independently of the laptop's ingestion connection. JSON serialization, length prefixes and SHA-two-fifty-six digests are not themselves encryption.

只展示源码如何加载证书/密钥，不打开私钥。不要说 mutual TLS，也不要说三条通道共用一个 AES 密钥。

### B10 / G10｜Laptop concurrency / threading

**投屏英文旁白（与 HTML 一致）：**

> Each device has its own BLE input task, bounded inbox and TLS sender. Its acknowledgement reader validates replies and releases slots in the thirty-two-message window. Waiting for one device's I/O allows the other device's tasks to progress. BLE callbacks enter through a thread-safe queue boundary. A separate worker thread writes packet evidence from another bounded queue. The main network concurrency uses asyncio tasks, while logging uses an actual operating-system thread.

**点击代码顺序（范围是原文件行号，按钮名与 HTML 相同）：**

| 用法 | 点击按钮 | 源文件与片段范围 | 可点的定位行 |
|---|---|---|---|
| 主讲 | **C27 Device tasks** | [laptop/dual_bridge.py](D:/LetThemCook/laptop/dual_bridge.py:91)，91–111 | L94 / L106 / L109 |
| 主讲 | **C29 Callback queue** | [laptop/bridge.py](D:/LetThemCook/laptop/bridge.py:122)，122–147 | L125 / L128 / L135 / L137 |
| 主讲 | **C30 ACK window** | [laptop/bridge.py](D:/LetThemCook/laptop/bridge.py:533)，533–544 | L535 / L541 |
| 主讲 | **C31 Send / ACK tasks** | [laptop/bridge.py](D:/LetThemCook/laptop/bridge.py:632)，632–642 | L633 / L634 / L637 |
| 主讲 | **C32 Log thread** | [laptop/evidence.py](D:/LetThemCook/laptop/evidence.py:13)，13–34 | L17 / L33 / L34 |
| 备查 | **C28 Inbox state** | [laptop/bridge.py](D:/LetThemCook/laptop/bridge.py:87)，87–101 | L91 / L92 / L93 |


**投屏 G10：** 指两套 input → RawInbox → TLS sender / ACK reader；再指独立日志线程，读图页英文说明。

**源码顺序：** [dual_bridge.py](D:/LetThemCook/laptop/dual_bridge.py) 的 `DualBridge.run()`：`writers` / `inputs` 的 `asyncio.create_task()`；[bridge.py](D:/LetThemCook/laptop/bridge.py) 的 `RawInbox` / `call_soon_threadsafe`、`_pipeline_epoch()` 内 `sender()` / `receiver()` / `asyncio.Semaphore`；C32 展示 evidence.py 的有界 queue.Queue 和真实 threading.Thread。

> Each device has its own BLE input task, bounded queue and TLS writer. Both streams can make progress during I/O waits. Within each stream, sending and acknowledgement reading are separate asyncio tasks. The semaphore bounds outstanding messages at thirty-two, and a valid acknowledgement releases a slot.
>
> BLE callbacks enter through a thread-safe queue boundary. Evidence records go to another bounded queue and are written by the packet-evidence worker thread. Main network concurrency uses asynchronous tasks; it does not mean one CPU core or operating-system thread per device. Queue overflow is recorded instead of silently counted as success. The two advancing streams in the earlier physical capture showed the observable behavior of this design.

### B11 / G11｜Ultra96 concurrency / threading

**投屏英文旁白（与 HTML 一致）：**

> Ultra96 has separate accept tasks for ingestion and the phone gateway. Each client connection gets a task. Ingestion validates and deduplicates a message, creates a simulated result for a new input and returns an acknowledgement. The phone gateway runs a result sender and a connection monitor. A bounded result queue connects the two paths. An ingestion acknowledgement does not confirm phone receipt, which is why the physical demonstration separately compares the phone's received-count increase.

**点击代码顺序（范围是原文件行号，按钮名与 HTML 相同）：**

| 用法 | 点击按钮 | 源文件与片段范围 | 可点的定位行 |
|---|---|---|---|
| 主讲 | **C33 Two listeners** | [ultra96/server.py](D:/LetThemCook/ultra96/server.py:136)，136–153 | L139 / L150 / L151 |
| 主讲 | **C34 Client task** | [ultra96/server.py](D:/LetThemCook/ultra96/server.py:179)，179–188 | L187 / L188 |
| 主讲 | **C35 Ingest + ACK** | [ultra96/server.py](D:/LetThemCook/ultra96/server.py:246)，246–275 | L248 / L265 / L266 / L272 |
| 主讲 | **C36 Gateway tasks** | [ultra96/server.py](D:/LetThemCook/ultra96/server.py:309)，309–337 | L310 / L331 / L334 / L336 |
| 主讲 | **C38 Queue freshness** | [ultra96/server.py](D:/LetThemCook/ultra96/server.py:56)，56–77 | L58 / L62 / L72 / L73 |
| 备查 | **C37 Queue capacity** | [ultra96/server.py](D:/LetThemCook/ultra96/server.py:32)，32–41 | L35 |


**投屏 G11：** 两个 accept tasks、每个连接的 client task、订阅结果队列、结果发送与 EOF/额外输入监控，读图页英文说明。

**源码：** [server.py](D:/LetThemCook/ultra96/server.py) 的 `start()` / `_accept()` / `_client()`；再 `_ingest()`、`_gateway()`、`_send_results()`、`ResultQueue`。在 `_gateway()` 指到发送任务与 `reader.read(1)` 监控任务。

> Ultra96 has independent accept tasks for ingestion and the phone gateway. Each accepted connection gets a client task. The ingestion handler validates and deduplicates incoming messages, creates a simulated result for a new input, queues it for the subscriber, and sends an acknowledgement to the laptop.
>
> The gateway runs separate result-sending and connection-monitoring tasks. The bounded result queue separates ingestion from phone transmission and rejects stale or excessive backlog. These tasks allow both laptop connections and the phone connection to progress during I/O waits. An ingestion acknowledgement does not wait for phone receipt, which is why the earlier demonstration checked the phone separately.

板端主通信是 asyncio；可选诊断日志可以有后台线程。不声称每条链路各占一个 CPU 核心、无限缓存或中断期间全量重放。

### B12｜结束与成片检查

停在本次保存的成功报告和 A6 手机最终计数画面，明确是同一已录制采集的证据，然后说：

> We have shown the physical FireBeetle setup and successful communication with Ultra96 and the Visualizer. We then explained the device IDs, packet types and formats, protocol state machines, encryption boundaries, and concurrency in the implemented laptop and Ultra96 code.

- [ ] A1 拍到真实编译/左右上传成功、绑定及拔掉 USB 改独立供电；不是只展示命令。
- [ ] A2 用摄影手机拍电脑实际打开 ID / sensor / control / protocol 源码并讲字段；B2–B4 的图解只是回顾。
- [ ] A 段先拍完，再录 B 段；没有录代码时打断实体采集。
- [ ] 两块板子只在 setup 时通过 USB 连接 laptop，正式 BLE 采集前已全拔掉并独立供电；两台手机角色清楚。
- [ ] A 阶段真实计数、ACK、手机结果/增量和保存目录可辨；B 阶段重看证据没有冒充新运行。
- [ ] 三条通道的加密源码、laptop 和 Ultra96 两套并发源码均可读。
- [ ] FSM、TCP 分段与帧边界、random fixtures、修改流程都解释过。
- [ ] 两路颜色/设备标签及至少一对完整解码 sensor/ACK 可读；秘密未录入。

项目已有的视频文件名约定是 `B07_CO_subsystem.mp4`；最终以实际提交页面为准。不要用旧 `tools.week7_demo packet` 的 v1 离线示例替换这次 v2 实物证据。

## 附录：只在录前需要时检查或启动 Ultra96

**不需要复制 SSH 命令。** 主菜单选 **9**，出现 Ultra96 服务子菜单：

1. **子项 1：只读检查状态。** 脚本开新的交互 SSH 窗口，按 SSH 提示输入两跳密码。查看监听端口、属主、进程和部署信息，正常应为 `xilinx` 的同一个 `ultra96.server` 持有 `127.0.0.1:8888` / `127.0.0.1:9999`。已有匹配服务就复用，不选启动。
2. **子项 2：需要时启动当前部署。** 仅当服务不存在且两个端口都空闲时使用。脚本在板端核实端口空闲后，以现有证书和当前部署目录启动服务；端口被占时不启动、不终止占用者。密码仍只输入新 SSH 窗口的交互提示。

当前目录为 `/var/tmp/cg4002-week7-yanjie-20260907/source-co-v2-20260928T122047Z`。预期出现 `listening`；保留启动服务的前台窗口，再用 **9 → 1** 检查实际端口/进程。菜单不会自动停止共享服务，退出主菜单也不能当作远端状态证明。当前目录缺失或版本不符时先解决部署，不退回旧 `source-observer-20260921T080754Z`。

2026-09-28 记录中的 PID `105159` 只是历史信息，不要照抄用来操作当天的进程。菜单 9 用于录前检查/启动；真正采集仍由 **3 → 手机 Connect → 4** 完成。

| 录前/录中问题 | 处理 |
|---|---|
| 隧道静止不输出 | 正常等待；后续 ACK 才证明通信。不要反复选 3 开同端口 |
| Pairing 不通过 | 核地址和固件；首次需要口令时 8 → 2，完成后关监视器；不降级安全 |
| 手机 Paused | 显式重新 Connect，记录新 P0，再开启独立新采集 |
| ACK 增长但手机不增 | 查订阅、VPN、竞争接收器、v2 App；不把 ACK 当手机收据 |
| CAPTURE NOT PASSED / N/A / 手机增量不符 | 保留失败证据，排查后另开新采集；不混用两次计数 |
| 第二阶段找不到这次报告 | 选 5，粘贴 A6 保存的完整目录；不随意取“最新成功的一次” |

来源：[当前 CO v2 协议](D:/LetThemCook/docs/co-protocol-v2.md)、[2026-09-28 部署与实体测试记录](D:/LetThemCook/docs/co-live-deployment-2026-09-28.md)及上述当前源码。本文是录制步骤，编写时没有重跑硬件测试。
