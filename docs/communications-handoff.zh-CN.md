# Let Them Cook（CG4002 B07）通讯与集成交接文档

**读者：** 负责人本人（olsonwangyj，队内叫 Yoz），以及以后接手这个仓库的每一个 agent。
**用途：** 读完就知道这个项目是什么、通讯模块怎么工作、为什么这样设计、现在做到哪一步、哪些事不能做、下一步做什么。
**最后更新：** 2026-10-14（更新记录见第 14 节）。

---

## 0. 怎么用这份文档

1. 先读第 1 到 3 节（项目、角色、边界），再读第 6 节（当前进度）和第 9 节（禁止事项）。动手改通讯代码之前读第 4、5、8 节。要找某个文件夹或文件是做什么的，看第 12 节的代码地图。
2. 事实以谁为准：**代码 > 本文档 > 负责人自己的其他文档 > 队友的 README 和文档**。队友的文档有和代码不一致的地方（见 4.9 节和各细节章节），遇到冲突信代码，并把冲突写进本文档。
3. 这份文档要持续维护。每次发生下面任何一件事，都要更新第 6 节和第 14 节：通讯代码合并了改动；板子、Ultra96 服务、手机 App 的实际部署状态变了；和队友定下了一个接口；负责人纠正了一个理解。
4. 更细的逐常量、逐状态字符串、逐条设计出处的内容在 `docs/handoff-details/` 下的六个章节里（见 12.5 节的索引）。本文档自身已经包含接手所需的全部要点。
5. 历史材料在 `docs/archive/`。那里的文件保留当时的名字（`week7`、`W7`），不更新，只用来查设计决定的出处。

---

## 1. 一分钟概览

- **项目：** NUS CG4002 毕业设计，B07 组，“Let Them Cook”。一个单人 AR 烹饪游戏（类似 Overcooked）。玩家戴两只传感手套做手势，手势由跑在 Ultra96 FPGA 板上的模型识别，识别结果驱动 iPhone 上的 Unity AR 游戏。
- **负责人的两个身份：** 通讯子系统的负责人（主要技术工作）；2026-10-13 起兼任集成负责人。集成的 V1 要在 **2026-10-20（周二）** 前跑通，最终版在第 13 周前后。
- **通讯做的事：** 把每个模块的数据发出去，并确保下一个模块准确收到。手套 → 笔记本 → Ultra96 → iPhone 这条链路已经用假数据在实机上完整跑通并留有证据。
- **还没接通的三个接口：** 手套真实采集模块（Siqiang）、板上模型入口和出口（Wen Ree）、游戏里调用通讯桥的脚本（Jie Ling）。
- **现在最要紧的两件事：** 板上的服务器证书已在 2026-10-06 过期，重新部署时必须先续签（第 6.3 节）；三位队友的接口要尽快定下来（第 7 节）。

---

## 2. 项目是什么

### 2.1 目标形态

```text
两只手套（各一块 FireBeetle ESP32 + IMU + 2 个弯曲传感器）
   │  每只手套每秒约 50 个样本，每个样本 11 个值
   ▼
Windows 笔记本（中继）
   │  经 NUS 跳板机的 SSH 通道
   ▼
Ultra96 FPGA 板：手势模型（两只手套各 11 个值 × 50 个时间步 = 50×22 的窗口 → 6 类手势）
   │  识别结果
   ▼
iPhone 上的 Unity AR 游戏（切菜、洗菜、拿起、放下、扔、灭火）
```

通讯负责图里所有的箭头。箭头两端的方框里面发生什么，由各自的负责人决定。

### 2.2 团队与代码归属

| 人 | GitHub | 负责 | 仓库路径 |
|---|---|---|---|
| 负责人（Yoz） | `olsonwangyj` | 通讯；集成牵头 | `firmware/` `common/` `laptop/` `ultra96/` `phone/` `ios-visualizer/` `tests/` `tools/` `demo.py` `flash.py` `requirements-dev.txt` `docs/` `AGENTS.md` `CLAUDE.md` |
| Siqiang | `siqiangz` | 手套硬件与传感器 | `hardware/` |
| Wen Ree | `Wrooi` | AI 模型与 FPGA | `src/` `models/` `data/` `reports/` `fpga/` `export_fpga_reference.py` `requirements.txt` |
| Jie Ling | `gohjieling834` | Unity AR 游戏 | `vis/` |

队友的路径**只读**。规则全文在仓库根目录的 `AGENTS.md`。

### 2.3 各子系统的现状（2026-10-14，以代码为准）

**手套（Siqiang，`hardware/`）**

- 参考固件是 `hardware/gloves/29_sept/imu_v7.ino`。它自带 `setup()`/`loop()`，启动时做陀螺仪校准。
- 每个样本 11 个浮点数，顺序是 `ax, ay, az, gx, gy, gz, yaw, pitch, roll, flex1, flex2`：加速度（g，已去重力，量程 ±2 g）、角速度（°/s，已去零偏，量程 ±250 °/s）、欧拉角（度）、两个弯曲值（12 位 ADC 除以 4095，范围 0.0 到 1.0）。
- 硬件占用：I2C SDA 21 / SCL 22 / 400 kHz，ADC 引脚 34 和 35。
- 输出方式是 **Bluetooth Classic 串口**（`BluetoothSerial`）发 CSV 文本，约 50 Hz。仓库里有三个草图变体，分别输出 11、12、13 个字段。
- 它和通讯固件**不能原样链接在一起**：两边都有自己的 `setup()`/`loop()`，而且通讯固件用的是 BLE，不是 Bluetooth Classic。

**模型与 FPGA（Wen Ree，`src/` `models/` `fpga/`）**

- 模型是一个 CNN，输入是 50×22 的窗口（50 个时间步；每步是左手 11 个值加右手 11 个值），输出 6 个类别。类别在 `models/class_names.json`：`PICKUPHOLD`、`PLACEDOWN`、`CHOP`、`WASH`、`THROW`、`FIREEXT`。输入不做归一化。
- `src/live_inference.py` 现在自己从 Windows 的两个 COM 口（Bluetooth Classic 串口）读数据，在笔记本上打印预测。置信度阈值是 0.70。**它没有可以被板上服务调用的入口。**
- FPGA 侧（`fpga/`）目前是一个测试模块加第一层卷积。`fpga/README_FPGA_PYNQ.md` 写的是加载 overlay 需要 `sudo` 和另一个解释器。
- 负责人曾用 NumPy 复现前向计算，30 组黄金输出全部一致；把 11 个值按 4.2 节的倍率转成 int16 再转回，预测结果不变。这只是通讯这边为了确认“定点传输不影响模型”做的核对。**怎么实现推理是 Wen Ree 的事。**

**游戏（Jie Ling，`vis/`）**

- Unity 6000.5.10f1 的 iOS AR 工程。动作入口是 `OnSelectPressed`、`OnGrabPressed`、`OnDropPressed`、`OnChopPressed`、`OnWashPressed`。
- `vis/Assets/Scripts/Network/TlsDataReceiver.cs` 是在手机上监听 5005 端口的 TLS 服务端，只把收到的文本显示出来。`vis/README.md` 也这样描述。**这个方向和 NUS 网络模型相反**（手机不能被连入），通讯代码里没有任何连接 5005 的实现。
- `vis/Assets/Scripts` 里现在没有任何调用通讯桥（`CommsStart` 等）的代码。游戏逻辑没有网络输入。

**通讯（负责人）**

- 整条链路用假数据在实机上跑通：两块 ESP32 → 笔记本 → Ultra96 → iPhone。细节见第 4 节，实测数据见 6.1 节。
- 固件发的是假数据，不读传感器。板上服务不调用模型，自己随机给一个假标签。iPhone 上只把结果显示成文字，不触发游戏动作。这三处就是要和队友接通的三个接口。

### 2.4 时间线

| 日期 | 事件 |
|---|---|
| 2026-09-06 起 | 通讯 Week 7 设计与实现 |
| 2026-09-19 至 09-28 | 双板实机测试、iPhone 测试、v2 协议与控制功能上线 |
| 2026-10-01 | 最后一次有记录的实机全链路采集 |
| 2026-10-06 | 板上服务器证书到期 |
| 2026-10-08 | 标识从 `W7` 改为 `LC`、会话从 `week7-demo` 改为 `ltc-comms`（当时保留了兼容） |
| 2026-10-13 | 负责人被推为集成负责人；PR #15 合入团队主分支 |
| 2026-10-14 | 删除 Week 7 兼容代码；整理文档；写本交接文档 |
| **2026-10-20** | **集成 V1 截止** |
| 第 13 周前后 | 最终版 |

团队期望写在团队 Google 文档的 “Integration formulation” 页：<https://docs.google.com/document/d/1P3-7mIIms9bHz4wJCk0NqZe7pYlBCBmjCKYXMzWKqlc>（URL 末尾加 `/mobilebasic` 可免登录阅读）。

---

## 3. 负责人的角色与边界

负责人自己的原话（2026-10-14）：

> I'm responsible for leading the integration, while my main technical responsibility is the communications subsystem. Each teammate remains responsible for the quality and performance of their own component. My role is to ensure that the components communicate correctly and to coordinate the team's work toward a functioning integrated system.

同一天的进一步说明：作为通讯负责人，只负责把每个模块的数据发出去，并确保下一个模块准确收到；其余都不是负责人的事。队友怎么实现自己的部分，负责人不过问。

**通讯负责：**

- 固件里的打包、BLE 发送、配对安全、连接管理（合并真实采集后，仍由负责人写这份固件）。
- 笔记本上的 BLE 接收、排队、转成网络消息、经 SSH 通道送到板上、核对 ACK。
- 板上的收样本、去重、回 ACK、把结果推给订阅的手机。
- iPhone 上的 SSH/TLS 客户端、结果校验、交给 Unity 的三个 C 函数。
- 每一段的身份标识、计数和证据。

**通讯不负责（不要列成负责人的任务，也不要替负责人去问）：**

- 传感器采集算法、校准、传感器故障 → Siqiang。
- 左右手样本配对、组 50×22 窗口、判断发生了手势还是空闲、模型精度和速度 → Wen Ree。
- 标签到游戏动作的映射、冷却和连发、`vis/` 里的任何脚本 → Jie Ling。

**集成牵头的含义：** 把跨模块的接口定清楚（格式、频率、标签、传输方式、时序、谁连谁），协调谁在哪天交付什么。不替队友承担他们组件的质量。

---

## 4. 通讯子系统详解

### 4.1 全链路

```text
左手 FireBeetle ESP32 (device_id=1) ─┐ BLE GATT 通知，每个样本一个 32 字节包
右手 FireBeetle ESP32 (device_id=2) ─┴──────────► Windows 笔记本（BLE 中心端）

笔记本 ─TCP→ 本机 127.0.0.1:18889 ─SSH -L→ stujump:22 → Ultra96:22 → 板内 127.0.0.1:8888（输入服务）
        TLS 内：SENSOR_BATCH →        ← INGEST_ACK

iPhone ─App 内置 SSH→ stujump:22 → Ultra96:22 → 板内 127.0.0.1:9999（结果服务）
        TLS 内：SUBSCRIBE →   ← SUBSCRIBED   ← GESTURE_RESULT

iPhone 内：Swift 客户端 ─三个 C 函数，被 Unity 主线程每帧轮询→ Unity
```

| 跳 | 谁发起，谁监听 | 传输 | 保护 |
|---|---|---|---|
| ESP32 ↔ 笔记本 | 笔记本连 ESP32；每块板同时只接受一个连接 | BLE GATT。样本走通知特征 `6e1c0005`；控制写 `6e1c0007`、响应 `6e1c0008`；源统计读 `6e1c0006` | LE Secure Connections + MITM + 绑定；特征和 CCCD 都要求加密且认证；固件在认证完成前不发任何通知 |
| 笔记本 → 板内 8888 | 笔记本连本机转发口，OpenSSH 两跳到板内回环 | TCP → SSH 本地转发 → TLS → 4 字节大端长度 + JSON | 两跳 SSH 都严格校验主机密钥；TLS ≥ 1.2，校验 CA 和主机名 `ultra96.week7.internal` |
| iPhone → 板内 9999 | App 内的 SwiftNIO SSH 连跳板，`direct-tcpip` 到板子 22，再 `direct-tcpip` 到板内回环；**手机不监听任何端口** | 嵌套 SSH 通道 → TLS → 同一种帧 | 两把 SSH 主机公钥和 CA 指纹固定在 App 源码里；校验主机名和有效期 |
| Swift → Unity | Unity 主线程每帧调用 C 函数 | 进程内 C ABI | 不经过网络 |

要点：

- **所有连接都是主动连出。** 板上两个服务只绑 `127.0.0.1`，只能经 SSH 通道到达。笔记本和手机都不接受连入。
- **输入和结果走两条互不相干的连接。** ACK 只回给笔记本，结果只推给订阅的手机。笔记本不转发结果。
- VPN 只提供网络可达条件，代码里没有任何 VPN 逻辑。**开着 VPN 也仍然经 `stujump` 走。** V1 保持跳板路线。

### 4.2 数据格式

**BLE 传感器包：32 字节，小端，Python 格式 `<2sBBIII8h`**

| 偏移 | 长度 | 字段 | 取值 |
|---|---|---|---|
| 0 | 2 | 标识 | ASCII `LC`（`4C 43`）。2026-10-14 起只接受这一个 |
| 2 | 1 | 版本 | 2 = 任意合法 int16（默认，值取自假数据表）；1 = 确定性公式假数据（编译开关 `COMMS_LEGACY_DUMMY=1`） |
| 3 | 1 | `device_id` | 1 = 左手，2 = 右手（编译期常量） |
| 4 | 4 | `boot_id` | 每次上电取一次随机数 |
| 8 | 4 | `seq` | 每次上电从 0 起，每个样本加 1；提交失败也不复用 |
| 12 | 4 | `uptime_ms` | 这块板自己的 `millis()`；两块板不同步 |
| 16 | 16 | 8 个 int16 | 现在是假数据 |

32 字节的通知需要 ATT MTU ≥ 35。实测协商到的 MTU 是 517。

**源统计：24 字节，`<4sB3xIIII`**：标识 `LCS1`、`device_id`、`boot_id`、`next_seq`、`submitted`（提交成功数）、`failures`（提交失败数）。笔记本在订阅前和停止后各读一次，用来对账“板上产生数 = 笔记本收到数 = Ultra96 确认数”。

**BLE 控制帧：14 字节头，标识 `B7`**（B07 的队号，不是 Week 7）：版本 1、操作码、`device_id`、状态、`id`、`offset`，后跟最多 180 字节载荷。操作码：命令（1）、调速（2，1 到 200 Hz）、文件开始/分块/结束/中止（`0x10` 到 `0x13`，最大 65536 字节，SHA-256 校验）。控制通道要求 MTU ≥ 64。

**网络帧：** 4 字节大端长度 + 严格 UTF-8 JSON 对象，正文 1 到 16384 字节。字段集合必须完全相等。**没有错误消息，出错就关连接。**

| `type` | 板内端口 | 方向 | 除 `v`、`type`、`session_id` 外的字段 |
|---|---|---|---|
| `SENSOR_BATCH` | 8888 | 笔记本 → 板 | `device_id`、`boot_id`、`seq`、`uptime_ms`、`values`（8 个 int16）；v2 加 `request_id` |
| `INGEST_ACK` | 8888 | 板 → 笔记本 | `device_id`、`boot_id`、`seq`、`status`（`accepted` 或 `duplicate`）；v2 加 `request_id` |
| `SUBSCRIBE` | 9999 | 手机 → 板 | 无（只允许 `v=1`） |
| `SUBSCRIBED` | 9999 | 板 → 手机 | 无 |
| `GESTURE_RESULT` | 9999 | 板 → 手机 | `device_id`、`boot_id`、`seq`、`result_id`、`gesture`、`confidence`；v2 加 `request_id` |

- `session_id` 默认处处是 `ltc-comms`。笔记本、板上服务、手机三方必须一致，不一致时板子直接关连接。它是配置，不是密码。
- `request_id`：v2 必须有这个键；普通样本是 `null`；键盘命令是 1 到 4294967295 且等于 `seq`。
- `result_id` 是 `device_id:boot_id:seq`；命令的结果加前缀 `cmd:`。手机用它去重。

**真实手套数据包（已决定，尚未实现）：38 字节 = 现有 16 字节头 + 11 × int16**

| 序 | 字段 | 采集模块给出的单位 | 倍率 | int16 可表示范围 |
|---|---|---|---|---|
| 0–2 | `ax` `ay` `az` | g | ×10000 | ±3.2767 g |
| 3–5 | `gx` `gy` `gz` | °/s | ×100 | ±327.67 °/s |
| 6–8 | `yaw` `pitch` `roll` | 度 | ×100 | ±327.67° |
| 9–10 | `flex1` `flex2` | 0.0–1.0 | ×10000 | 上限 3.2767 |

38 字节的通知需要 ATT MTU ≥ 41。应用层字节量是 38 × 50 Hz × 2 块板 = 30.4 kbps；32 字节包实测过 33.8 kbps 干净，38 字节还没有任何实测。

### 4.3 固件（`firmware/esp32/`）

- PlatformIO + Arduino 框架，板型 `firebeetle32`。构建环境 `firebeetle32-left`（ID 1）、`firebeetle32-right`（ID 2）、一个显式命名的非保护诊断环境。已验证的组合是 Espressif32 7.1.0 + Arduino-ESP32 2.0.17（`platformio.ini` 没有锁版本）。
- 广播名 `LTC-COMMS`，两块板相同；区分靠蓝牙地址和包内 `device_id`。服务 UUID `6e1c0001-7a45-4dc4-b678-3f2d5a9c1001`，共 7 个特征。
- 安全：LE Secure Connections + MITM + 绑定，板子只能显示（DisplayOnly）。6 位配对码只打印到本地串口，由操作者在 Windows 上输入。应用层再加一道闸门：认证模式三位（SC、MITM、绑定）都具备才发通知。
- 主循环每圈：读串口命令 → 按速率节拍判断 → 已认证且已订阅且 MTU 够才分配 `seq`、打包、提交通知、记成功或失败 → 每圈最多处理一帧控制请求 → 每秒打印 `alive` 和 `comms_stats`。
- **产生样本的位置在 `firmware/esp32/src/main.cpp` 调用 `serializeFixturePacket` 的那一段（约第 503 到 510 行）。** 真实采集模块的“读一个样本”就接在这里。
- 断开期间不产生样本，`seq` 不前进，没有离线缓存。速率在断开后保持不变，重启才回到默认 10 Hz。
- 串口命令只有一个：`erase-bonds`（清除绑定，恢复配对用）。
- 策略逻辑都在可移植的 C++11 头文件里（`include/comms_*.h`），不烧板就能在主机上编译测试（`test/host_*.cpp`，由 pytest 调 g++ 运行）。

**`flash.py`：** 先生成假数据头文件并构建左右两份固件，再提示接板。**先接的那块烧成 LEFT（ID 1），后接的烧成 RIGHT（ID 2）。** 它读出厂 MAC，加 2 得到蓝牙地址，写进 `.comms-local/boards.json`。其他用法：`--ports`、`--boards`、`--pair [left|right|both]`、`--monitor COMx`。只能在 Windows 上用。

### 4.4 笔记本（`laptop/`、`demo.py`、`tools/`）

- `laptop/bridge.py` 是单只手套的整条路径；`laptop/dual_bridge.py` 同时跑两条互不耦合的 `Bridge`，`demo.py` 实际调用它。**每块板一套独立的 BLE 连接、队列、TLS 连接**，一块板卡住不影响另一块。
- 每块板的流程：扫描（按服务 UUID 和地址，限 8 秒）→ 连接（不用缓存的 GATT 表，限 20 秒）→ 确认 MTU ≥ 35 → 确认 Windows 绑定是“加密且认证” → 读源统计起点 → 订阅通知。两块板必须在 30 秒内都就绪。
- BLE 回调只做两件事：记到达时刻，把字节拷进这块板的有界队列（64 条，满了丢最旧）。回调里不做网络操作。
- 写任务：解码 → 核对 `device_id`、序号、连接代次 → **在笔记本滞留超过 2 秒的样本丢弃** → 写出 `SENSOR_BATCH` → 按发送顺序逐条核对 `INGEST_ACK`。同时在途最多 32 帧（ACK 窗口）。
- **不重传。** TLS 断开、写超时、ACK 超时或对不上时，这条 TLS 作废，已经尝试写出的帧记为“不确定”（`ambiguous_dropped`），不重发；退避（0.5 秒起翻倍，上限 5 秒）后重连。
- 关闭时的尾包处理：先在远端关通知并保留本地回调，再读一次源统计，等最后几个包到齐，再读一次确认没变。这样首尾的丢包也能对账出来。
- 结束时写 `report.json`（先占位、再原子替换）和 `packets.jsonl`；全部对上才打印 `CAPTURE PASSED`。
- 配对用自己写的 WinRT 流程（`laptop/windows_pairing.py`），因为 Bleak 自带的 `pair()` 可能降低保护级别。**笔记本这一侧只支持 Windows。**
- 控制通道：键盘 `1`/`2` 发命令，`--rate` 调速，`--file` 传文件。命令走单独的 TLS 连接，超时不重试。

`demo.py` 的五个子命令：

| 命令 | 作用 |
|---|---|
| `python demo.py tunnel` | 开两跳 SSH 本地转发：本机 `127.0.0.1:18889` → 板内 `127.0.0.1:8888`。保持这个终端打开 |
| `python demo.py run` | 采集两块板 60 秒（默认 10 Hz），写报告和证据到 `.comms-local/` |
| `python demo.py live` | 同 `run`，并启用键盘命令 |
| `python demo.py report [路径]` | 复核最近一次或指定的采集 |
| `python demo.py service [--start]` | 经 SSH 查看板上服务；`--start` 在两个端口都空闲时启动它 |

### 4.5 Ultra96 服务（`ultra96/`）

- 一个只用标准库的 asyncio 进程：`/usr/bin/python3 -u -m ultra96.server --cert … --key … [--session-id ltc-comms] [--ingest-port 8888] [--gateway-port 9999] [--event-log-dir 新目录]`。以普通用户在一条 SSH 会话的前台运行；不是系统服务，没有自动重启，不用 sudo（板子是共享的）。
- 两个 TLS 监听都只绑 `127.0.0.1`。服务从不主动连出。两个口合计最多 8 个并发连接。
- **输入口 8888：** 读帧 → 校验字段和会话 → 去重 → 新样本生成一条结果并（有订阅者时）放进结果队列 → 回 `INGEST_ACK`。重复样本只回 `duplicate`，不出结果。输入连接空闲 5 秒会被关闭。
- **结果口 9999：** 收到合法的 `SUBSCRIBE` 就把这条连接登记为当前订阅者并回 `SUBSCRIBED`。**同时只有一个订阅者，后来的顶掉先来的。** 结果队列 32 条，满了丢最旧；结果入队满 2 秒就丢弃；没有订阅者时结果直接丢弃，之后不补发。
- **现在的结果是假的。** 生成位置在 `ultra96/server.py:264-267`：v2 从 `REST`、`FIST`、`OPEN`、`POINT` 里随机选一个，置信度写死 1.0。**这里就是将来接模型接口的位置。**
- 去重和防重放只在内存里：v2 对每个 `(device_id, boot_id)` 记一个只增不减的序号高水位，加最近 4096 条指纹；一个进程生命周期内最多 128 个 `(device_id, boot_id)` 和 4096 条命令，用尽后必须重启服务。
- 可选的事件日志（`--event-log-dir`）在后台线程写，上限 50 MiB。它的 `result_write_complete` 只说明板子把结果写进了连接，**不说明手机收到**。
- 证书由 `tools/generate_comms_pki.py` 生成：CA（365 天）和服务器证书（**30 天**，CN 和 SAN 都是 `ultra96.week7.internal`）。服务端只加载服务器证书和私钥；客户端只拿 CA 证书；CA 私钥不离开生成它的机器。只做服务器认证，没有客户端证书（访问控制由 SSH 负责）。

### 4.6 手机端与 Week 7 临时接收端（`ios-visualizer/`、`phone/`）

**现行手机端是 Swift 包 `ios-visualizer/CommsNative`。**

- 用户点 `Communications Connect`，在表单里输入板子和跳板的用户名与密码，首次还要导入 CA 证书。然后 App 自己建立：TCP 到 `stujump:22` → SSH（比对固定的主机公钥，密码认证）→ `direct-tcpip` 到板子 22 → 第二层 SSH → `direct-tcpip` 到 `127.0.0.1:9999` → TLS（验 CA、主机名、有效期）→ 发 `SUBSCRIBE` → 收到 `SUBSCRIBED`。整个过程限 10 秒。
- 之后只收结果：解帧、校验、按 `result_id` 去重（最近 4096 条）、`Received` 加 1、**只保留最新一条**。2 秒没有新结果就清掉显示的标签，计数保留。订阅后空闲不设期限，只对“已经开始但没收完的帧”计 5 秒。
- 错误分两类。网络类（连接断开、超时）自动退避重连并重新订阅。认证、信任、协议类（密码错、主机公钥不符、证书过期、结果没通过校验）**直接终止，不重试，清除密码**，用户必须重新输入密码再连。
- 密码只存内存。**App 锁屏或退到后台就立刻断开并清除密码**，回到前台要手动再连，计数从 0 开始。
- 主机名、两把 SSH 主机公钥、CA 指纹、会话名都编译在 App 里。换板子、换 CA、换会话名都要改源码并重新编译装机。

**给 Unity 的三个 C 函数（`Sources/CommsBridge/DisplayMailbox.swift`）：**

| 函数 | 语义 |
|---|---|
| `void CommsStart(void)` | 安装按钮和前后台通知。**不发起连接**；连接只能由用户点按钮、输入密码发起。调一次即可 |
| `int32_t CommsCopyDisplay(char* buffer, int32_t capacity)` | 取一次快照，拼出四行 UTF-8 文本。文本和上次送出的不同且放得下时，写入缓冲区（带结尾 0）并返回字节数；否则返回 0，不写。不返回负数 |
| `void CommsStop(void)` | 状态立刻变为 `Stopped`，卸载一切并清除密码。只在 App 真正不再使用通讯时调用 |

四行文本：

```text
Communications • DUMMY inference
<状态>
<gesture>  |  <result_id>  |  confidence 1.0        （没有新结果时这一行是 No live result）
Received: <N>
```

调用方必须遵守：只能有一个轮询者；在主线程每帧轮询；缓冲区用 2048 字节；按 UTF-8 解码；**用 `result_id` 判断是不是新结果，不要用标签文字**；桥只给“最新一条”，不能假设看得到每一条；不要在切场景或进后台时调 `CommsStop`。

**“Week 7 receiver” 的准确含义（负责人确认）：** iPhone 上的 `CommsNative` Swift 客户端，加上 Unity 导出工程里调用 `Week7Start` / `Week7CopyDisplay` / `Week7Stop` 的桥接。它是为 Week 7 演示临时做的接收端：

- 当时拿不到 Unity 源工程，所以是对一份特定的 Unity 导出（`ios-visualizer/xcode-export/`，只在 fork 上）的生成代码打补丁：`ios-visualizer/tools/patch_export.py` 把 Jie Ling 的 `TlsDataReceiver` 的四个方法改掉（`Start` 调 `Week7Start()`；`ListenLoop` 清空，5005 监听不再运行；`Update` 每帧调 `Week7CopyDisplay(缓冲区, 2048)` 并把文本写进标签；`OnDestroy` 调 `Week7Stop()`）。`configure_xcode.py` 把 `CommsNative` 链接进 `UnityFramework`。
- 补丁按文件哈希锁定，只认那一份导出；从 `vis/` 重新导出后它会拒绝。
- **它只显示文字，从来不触发游戏动作。**
- **它里面带 `week7` 的名字一律不动**：`Week7*` 三个包装函数、iOS 旧数据目录 `Application Support/Week7`、App 显示名 `Week 7 Visualizer`、补丁脚本里的注释和临时文件前缀。

**`phone/` 下的东西是参考和诊断用的，不是 iPhone 上部署的接收端：** `phone/receiver.py`（Python，Termux/iSH）、`phone/unity/CommsPhoneCore.cs` 和 `CommsPhoneReceiver.cs`（Android 参考，需要手机另外开一条 SSH 本地转发到 `127.0.0.1:19999`）、`phone/ish_control.py`（iSH 路线的临时维护脚本）。

### 4.7 证据等级（互不替代）

| 级 | 证据 | 证明什么 | 不证明什么 |
|---|---|---|---|
| 1 | 板上源统计 `submitted` | 蓝牙协议栈接受了这次通知提交 | 笔记本收到 |
| 2 | 笔记本 `received` | BLE 回调拿到了字节 | 板子收到 |
| 3 | `INGEST_ACK` | 板上服务校验并接受了这条输入 | 手机收到；模型做过推理 |
| 4 | 板上事件 `result_write_complete` | 板子把结果写进了连接 | 手机校验过或显示过 |
| 5 | 手机屏幕上的 `Received: N`（人工读数） | 本次连接内手机接纳了 N 条不重复结果 | 逐条 ID；游戏动作被触发 |

`demo.py` 打印的 `CAPTURE PASSED` 属于第 3 级。手机不回任何应用层确认，也不保存逐条记录；手机那一级要人工把 `Received` 的增量和 `Phone expected increase` 比对。

### 4.8 信任材料

| 材料 | 谁持有 | 备注 |
|---|---|---|
| CA 私钥 `ca-key.pem` | 只在负责人笔记本上（仓库之外） | 不上板，不进手机 |
| CA 证书 `ca-cert.pem` | 笔记本（`--ca`）；iPhone（导入） | 现用 CA 的 SHA-256 是 `4dfba4905c171e68c3623dbc952154149076ed89004b85d475e858cc550760ec`，有效到 2027-09-06；这个指纹固定在 `Configuration.swift` 里 |
| 服务器证书和私钥 | Ultra96 部署目录的 `tls/` | **2026-10-06 已过期，见 6.3 节** |
| 两把 SSH 主机公钥 | 笔记本的 `known_hosts`；iPhone 源码 | 不做“首次信任” |
| SSH 密码 | 只在操作者手里 | 笔记本在 OpenSSH 提示里输入；手机只放内存 |
| BLE 绑定密钥 | ESP32 和 Windows 各一份 | 配对码只显示在板子串口 |

### 4.9 文档与代码不一致的地方（以代码为准）

- `vis/README.md` 写“手机在 5005 端口运行 TLS 服务端”。方向与网络模型相反；Week 7 的导出里这段代码已被清空。
- 归档的架构草案写 `stfjump`，代码和现场是 `stujump`；示例端口写 8888，代码用 18888 和 18889。
- `docs/week7-runbook.md` 里的 `tools.generate_week7_pki`、`tools.rehearse_week7`、`Week7Server` 已改名为 `tools.generate_comms_pki`、`tools.rehearse_comms`、`CommsServer`。
- 归档的 iOS 设计规格写“首条结果等 30 秒”，现行代码在订阅后空闲不设期限。

---

## 5. 为什么这样设计

1. **所有连接都主动连出，板上服务只绑回环，只经 SSH 到达。** NUS 的防火墙规则下，外部只能经 VPN 和跳板机 `stujump` 用 SSH（22 端口）到达 Ultra96。笔记本和手机不在任何白名单上，别人连不进来。所以被否决的做法有：让手机当服务端等别人连入（队友最初的 5005 做法）；笔记本直连手机；对外开放板子的 8888/9999；SSH 反向转发；让笔记本转发结果。
2. **手机自己连板子，不经过笔记本。** 手机拥有自己的整条路线，结果不依赖笔记本在不在线；笔记本只是输入中继。
3. **SSH 里面再套 TLS，主机名固定。** SSH 解决“到得了”；TLS 用专用 CA 和固定名字确认“连的确实是那个服务”，即使 TCP 连的是 `127.0.0.1` 也不放松。不做双向证书，因为 SSH 已经认证了访问者。
4. **不重传、不回放，队列有界，2 秒新鲜度。** 过时的手势如果被补发，会被当成新的游戏动作。所以每一段都宁可丢，也不发旧数据；队列有界，故障时内存不会无限增长。
5. **`device_id` + `boot_id` + `seq` 三元组，序号在提交之前分配，另设只读的源统计。** 板子重启后序号归零也不会和旧数据混淆；提交失败的样本也占一个序号，丢失不会被掩盖；首尾丢的包也能对账出来。
6. **ACK 窗口 32。** 实测远程路线上单条 ACK 等待最长 2.375 秒；逐条停等会让后面的样本超过 2 秒新鲜度而被丢（两次 600 秒测试分别丢 1 条和 33 条）。改成窗口 32 后 600 秒实测全部确认。新鲜度本身不放宽。
7. **每块板一条独立通道。** 一块板断电或卡住，另一块继续（实测断电恢复期间，健康板 111 包 111 ACK）。
8. **BLE 用 Secure Connections + 配对码 + 绑定，不再加一层应用层加密。** 已认证的 BLE 链路加上后面的 SSH/TLS 已覆盖全程；再加一套自己设计的密钥协议只会引入没评审过的东西。
9. **单订阅者，后来者顶替。** V1 只有一部手机，结果流的拥有者始终唯一。
10. **长度前缀 + 严格 JSON，出错就关连接。** TCP 没有消息边界；坏帧之后无法可靠地重新对齐。
11. **主机公钥和 CA 指纹固定在手机源码里。** 手机上没有人工核对 `known_hosts` 的环节，所以不做“首次信任”。代价是换板子或换 CA 要重新编译 App。
12. **密码只放内存，离开前台即断开。** 现场路线用密码认证；不落盘就没有凭据文件要管；也不依赖没验证过的 iOS 后台存活。
13. **板上单进程、只用标准库、不用 sudo、不装系统服务。** 板子是共享的，不动别人的环境。启动脚本只在端口空闲时启动，从不停止或杀掉已有进程。
14. **证据分级。** ACK 和手机结果走两条独立连接，历史上出现过 ACK 全到而手机少收的情况，所以每一级证据只说明它自己那一段。
15. **蓝牙选 BLE 而不是 Bluetooth Classic。** 这是早已定下并测过的选择：50 Hz 和 70 Hz 的设定都在 2026-09-28 实测干净。

每条决定的出处（归档设计记录的条目号）见 `docs/handoff-details/` 各章的“为什么这样设计”。

---

## 6. 现在做到哪一步（2026-10-14）

### 6.1 已完成并在实机上验证过的（全部是 32 字节假数据）

| 项目 | 结果 | 日期 |
|---|---|---|
| 双板 10 Hz 基线 | 左 652、右 653 条全部 ACK；ATT MTU 517 | 09-28 |
| 速率扫描（每块板） | 10、25、50、60、65、70 Hz 通过；75 Hz 和 100 Hz 失败。50 Hz 实测约 49.98 包/秒；70 Hz 设定实测约 66 包/秒，合计 33.8 kbps | 09-28 |
| ACK 窗口 32 | 600 秒：6005 / 6001 条全部确认 | 09-19 |
| 单板断电恢复 | 11 秒重新连上；另一块板不受影响；恢复后第一个包没拿到 ACK（1 次不确定） | 09-28 |
| iPhone 计数 | 60 秒 1202 条、600 秒 12003 条等，与预期一致 | 09-21 |
| 文件传输 | 4096 字节，两块板各一次，摘要一致 | 09-28 |
| 删除兼容后的固件 | 左板烧录当前固件；本机回环 100/100 包；另一次 349 包、源统计对账通过、调速到 20 Hz 得到确认、3 条命令全部往返 | 10-14 |

没有解释清楚的历史问题：2026-09-21 有一次 60 秒运行，手机只收到 1094/1203 条（少 109 条），原因未知。距离测试从未做过。

### 6.2 代码与分支状态

- 团队仓库 `upstream` = <https://github.com/B07-CG4002/Let-Them-Cook>，主分支在 `ec398b6`（PR #15 已合入）。
- 负责人的 fork `origin` = <https://github.com/olsonwangyj/Let-Them-Cook>。本地 `main` 比团队主分支多出只在 fork 上的内容：`docs/`、`ios-visualizer/xcode-export/`、`AGENTS.md`、`CLAUDE.md`、若干工具。
- **2026-10-14 的清理（已合入本地 `main`，分支 `comms/remove-week7-legacy`，等负责人向团队仓库开 PR）：** 删除了对 Week 7 旧版本的兼容。现在只接受 `LC` 包和 `LCS1` 统计；`.week7-local` 目录不再读取；`demo.py service --start` 的会话和 `run`/`live` 一样默认 `ltc-comms`，并新增了 `--session-id`。测试在团队仓库的文件上是 549 通过、3 跳过；在本地 `main`（多了只在 fork 上的测试和证书续签的测试）上是 569 通过、3 跳过。
- **证书续签选项（分支 `comms/renew-server-certificate`）：** `tools/generate_comms_pki.py` 新增 `--renew-server-from <原 CA 目录>`，用原有 CA 只签发新的服务器证书。
- 清理时**有意保留**的 Week 7 名字：

| 保留的名字 | 位置 | 为什么不动 |
|---|---|---|
| TLS 主机名 `ultra96.week7.internal` | `common/tls.py`、证书工具、各接收端 | 写在服务器证书里，每个客户端都按它校验；改名要换证书并重装 App |
| `Week7Start/CopyDisplay/Stop`、iOS 旧目录读取、App 显示名等 | `ios-visualizer/` | 属于 Week 7 临时接收端，负责人明确说不动 |
| 板上部署目录 `/var/tmp/cg4002-week7-…-20260907` | `tools/demo_service.py` | 是板上真实存在的目录 |
| CA 默认路径 `~/.codex/private/cg4002-week7-20260906/ca-cert.pem` | `demo.py` | 是笔记本上真实存在的目录 |
| iSH 的配置文件名 `week7-ish-password.conf` 和主机别名 `week7-ultra96` | `phone/ish_control.py` | 是手机 iSH 里已经存在的文件和别名，仓库里没有任何东西会创建新名字 |
| 协议 v1 和 `COMMS_LEGACY_DUMMY` | 多处 | 是确定性假数据模式，不是旧版本兼容 |

- 清理的副作用：用 Week 7 固件录下的旧采集（都在 `.week7-local/`）里是 `W7` 包，当前的 `demo.py report` 不再判它们通过；要复核旧证据请用提交 `ec398b6`。

### 6.3 实际部署状态，以及“重新部署一轮”

删除兼容之后，三端必须都换成当前源码的版本。**下面凡是要登录跳板机或 Ultra96 的步骤，只能由负责人本人在自己的终端里做**（见第 9 节）。

| 设备 | 现在的状态 | 要做的事 | 谁做 |
|---|---|---|---|
| 左板 | **已烧录当前固件**（10-14，COM3） | 无 | — |
| 右板 | 仍是 Week 7 固件（发 `W7`），当前笔记本程序会拒绝它，报 `invalid source statistics magic; flash this board with the current firmware` | 烧录右板固件 | 负责人或 agent（接上 USB 后） |
| 服务器证书 | **笔记本上的那一份（和 9 月部署到板上的是同一份）已在 2026-10-06 15:11 UTC 过期。** 仓库记录里没有之后换过证书的记录；板上的实际状态没有核对过 | 用原 CA 续签，上传到板上 | 负责人 |
| Ultra96 服务 | 应该还是 9 月 28 日的代码快照，会话 `week7-demo` | 上传 `common/` 和 `ultra96/` 的新快照；核对后停掉旧进程；启动新进程；把 `tools/demo_service.py` 里的 `BOARD_SOURCE` 改成新目录 | 负责人 |
| iPhone App | 装的是 Week 7 那一版，会话 `week7-demo` | 在 Mac 上用当前源码重新构建并安装 | 负责人 |

步骤：

1. **续签服务器证书。** CA 不变，所以手机源码里的 CA 指纹和笔记本的 `--ca` 都不用改。

   ```powershell
   python -m tools.generate_comms_pki --renew-server-from "$HOME\.codex\private\cg4002-week7-20260906" --output-dir <仓库之外的一个新空目录>
   ```

   把新目录里的 `server-cert.pem` 和 `server-key.pem` 放到板上的 TLS 目录（私钥权限 600）。新证书仍然只有 30 天。
2. **板上服务。** 只需要 `common/` 和 `ultra96/` 两个目录。放进一个新目录，不要覆盖正在运行的目录。停旧进程前先用 `ps -p <PID> -o pid=,uid=,args=` 和 `readlink -f /proc/<PID>/cwd` 核对是自己的 `ultra96.server`，再 `kill -TERM <PID>`；不要用 `pkill` 或按端口杀进程。启动后应看到 `{"event": "listening", "host": "127.0.0.1", "tls": true, "ingest_port": 8888, "gateway_port": 9999}`。
3. **右板固件。** 只烧右板：`platformio run -d firmware/esp32 -e firebeetle32-right -t upload --upload-port COMx`。或者跑完整的 `python flash.py`（先接左板，再接右板）。固件换过之后如果 Windows 提示需要认证绑定：在板子串口输入 `erase-bonds`，在 Windows 蓝牙设置里删除这块板，再 `python flash.py --pair right`。
4. **手机 App。** 需要 Mac 和 Xcode：`swift test --package-path ios-visualizer/CommsNative`，然后对 Unity 导出运行 `tools/patch_export.py` 和 `tools/configure_xcode.py`（两者可重复运行；现有的 `xcode-export/` 已经打过补丁），用 Xcode 构建安装。
5. **验收。** `python demo.py tunnel`（终端 A）；手机点 Connect 等到 `Subscribed`；`python demo.py run`（终端 B）。要求 `CAPTURE PASSED`，并且手机 `Received` 的增量等于输出里的 `Phone expected increase`。

核对板上证书是否过期的办法（隧道开着的时候）：

```powershell
openssl s_client -connect 127.0.0.1:18889 -servername ultra96.week7.internal
```

### 6.4 集成进度

- 给三位队友的消息已经起草（只问接口，不问实现，不提替代方案）。接口内容见第 7 节。**是否已经发出、对方怎么答复，由负责人更新到这里。**
- 团队视角的说明文档：<https://claude.ai/code/artifact/b77bebd7-09f4-4c3e-9466-d4e19318359c>（“B07 integration: what to ask, what to tell, and why”）。

---

## 7. 三个要接通的接口

通讯只规定“交接点上需要什么功能、什么字段”。函数名和内部实现由对方定。

### 7.1 向 Siqiang 要：手套采集模块（被通讯固件调用）

已定的分工：Siqiang 交付一个可以运行的采集模块（初始化、读一个样本、数据格式说明）；**负责人**在通讯固件里调用它，并负责缩放成 int16、打包、BLE 发送、连接管理。采集算法、校准、传感器问题仍归 Siqiang。

| 功能 | 建议的形状（名字由他定） | 通讯怎么用 | 必须写清 |
|---|---|---|---|
| 初始化 | `bool begin()` | 在 `setup()` 里调一次 | 成功或失败（失败要返回，不能死循环，否则板子永远不广播）；阻塞多久；期间手套是否要静止 |
| 周期更新（可选） | `void update()` | 主循环每圈调一次 | 只有当姿态滤波需要比发包更密的更新时才需要；对调用间隔的要求；单次最长耗时 |
| 读一个样本 | `bool read(float out[11])` | 在发包时刻调用 | 返回 `true` 时填满 11 个值；当前没有有效样本返回 `false`；不能阻塞 |

11 个值的顺序和单位：`ax, ay, az`（g）、`gx, gy, gz`（°/s）、`yaw, pitch, roll`（度）、`flex1, flex2`（0.0–1.0）。需要他确认每个值的最小值和最大值（要落在 4.2 节的 int16 范围内；例如 yaw 如果是 0 到 360 就会溢出）、坐标轴和正方向、实际采样率、左右手套有没有差别。

通讯固件对模块的约束（来自现有代码）：

- 构建环境是 PlatformIO 的 Arduino 框架，板型 `firebeetle32`；请列出依赖库。
- 模块不定义 `setup()`/`loop()`，不打开任何蓝牙或 Wi-Fi（通讯固件用 BLE），不调用 `Serial.begin`，不读串口输入，不逐样本打印串口（配对码只显示在串口）。
- 不调用 `delay()`。
- `seq`、`uptime_ms`、左右身份都由通讯固件填，模块不用管。
- 以哪个草图为准（`29_sept/imu_v7.ino` 还是别的变体），请他指明。

### 7.2 向 Wen Ree 要：板上模型的入口和出口（被板上通讯服务调用）

接入位置是 `ultra96/server.py:264-267`。

**入口：通讯每接受一条新样本，交给模型侧一次。**

| 字段 | 类型 | 含义 |
|---|---|---|
| `device_id` | 1 或 2 | 1 = 左手，2 = 右手 |
| `boot_id` | uint32 | 这只手套本次上电的随机编号；变了表示手套重启过 |
| `seq` | uint32 | 本次上电内的样本序号，递增 |
| `uptime_ms` | uint32 | 这只手套自己的毫秒计时；两只手套不同步 |
| `values` | 11 个浮点数 | 顺序同 7.1；单位同采集模块的输出 |

通讯这一侧的事实：同一只手套内按 `seq` 递增、不重复；可能有缺口（丢了不补）；两只手套经两条独立连接到达，**没有配对、没有对齐**。配对、组窗口、判断手势或空闲，都在这个入口之后，由模型侧完成。

**出口：模型有结论时交给通讯一次，通讯原样转发给手机。**

| 字段 | 类型 | 含义 |
|---|---|---|
| `gesture` | 字符串 | 标签原文（线路上的字段名就是 `gesture`） |
| `confidence` | 0 到 1 的数 | 置信度 |
| `device_id`、`boot_id`、`seq` | 同入口 | 这个结果用到的**最后一条样本**的身份。通讯用它生成 `result_id`（`device_id:boot_id:seq`），手机靠它去重 |

入口和出口是两个分开的动作：入口只收样本、立即返回；模型什么时候有结论，什么时候再调出口。不要做成“入口同步返回结果”，那样推理耗时会直接加到 ACK 上。

通讯这边的硬约束（来自现有代码，对方需要知道）：

- **入口必须立即返回。** 板上服务是单个 asyncio 事件循环，ACK 在入口返回之后才写出。这里一慢，两只手套的 ACK 都被拖住；笔记本等一条 ACK 的上限是 5 秒，样本新鲜度是 2 秒。推理如果耗时，要放到别的线程或进程里。
- **出口要在服务的事件循环线程里调用。** 通讯的结果队列没有锁。模型如果在别的线程或进程里出结果，要经事件循环转交（通讯会提供一个线程安全的交接函数）。
- **结果消息不能随意加字段。** `GESTURE_RESULT` 的字段集合在板子、iPhone、两个参考接收端四处都是精确匹配的，`result_id` 必须等于 `device_id:boot_id:seq`。所以关联信息只能是一条样本的身份，不能是数组或嵌套对象。

需要他回答的（代码里查不到）：

- 接口形态：现在的 `src/live_inference.py` 自己读 COM 口，没有可调用的入口。
- 运行方式：通讯服务现在以普通用户、`/usr/bin/python3`、只用标准库运行。模型在板上用哪个解释器、哪些依赖、是否需要 root。
- 标签全集（逐字符，含大小写）；空闲或没有手势时是不输出，还是输出某个标签。
- 多久出一个结果（每个样本、每个窗口，还是只在判定出手势时）。

`values` 默认交物理量（通讯把 int16 除以倍率还原，和采集模块的输出同单位，分辨率见 4.2 节的表）。

### 7.3 给 Jie Ling 的：通讯提供的接口（游戏来调用）

已定：手机客户端由 **Jie Ling 在 Unity 工程里加进游戏**，不再用“给导出打补丁”的办法。通讯这边**不需要游戏提供任何 API**；游戏调用通讯的三个 C 函数（4.6 节），做法可以参照 Week 7 临时接收端。

- 游戏里放一个跨场景存活的组件：启动时调一次 `CommsStart()`；每帧调 `CommsCopyDisplay(buffer, 2048)`；App 结束时调 `CommsStop()`。
- 从四行文本的第 3 行取 `gesture` 和 `result_id`，用 `result_id` 判断是不是新结果。拿到之后做什么（映射到哪个动作、冷却、连发），是游戏的事。
- 手机上不能再依赖 5005 端口的监听；结果只从这三个函数进来。
- 屏幕右上角要留给原生的 `Communications Connect` 按钮，它是连接的唯一入口。
- 为了在真机上联调，通讯需要一份由当前 `vis/` 源码导出、并且已经包含上述调用的 Xcode 工程，用来链接 `CommsNative`。
- 参考：<https://github.com/olsonwangyj/Let-Them-Cook/blob/main/ios-visualizer/tools/patch_export.py>（Week 7 是怎么调这三个函数的）和 `configure_xcode.py`（怎么把 Swift 包链接进去）。这两个文件只在 fork 上，团队仓库里没有。

三个函数在 C# 里的声明（按 C 签名推导，还没有在 Unity 里编译验证）：

```csharp
[DllImport("__Internal")] static extern void CommsStart();
[DllImport("__Internal")] static extern int  CommsCopyDisplay(byte[] buffer, int capacity);   // 返回 UTF-8 字节数，不含结尾 0；0 表示没有变化
[DllImport("__Internal")] static extern void CommsStop();
```

符号来自静态库 `CommsNative`，要链接进 `UnityFramework`。缓冲区由调用方分配。

**桥的一个限制，需要负责人拍板（见第 13 节）：** 现有的桥只保存“最新一条”结果，并且文本里的 `confidence 1.0` 是写死的。两次轮询之间如果到了多条结果，游戏只看得到最后一条（`Received` 仍然全部计数）。每帧轮询、结果每秒只有几条时，实际很难碰到；但按“确保下一个模块准确收到”的标准，它不是逐条交付。

---

## 8. 通讯自己的待扩展点（负责人的工作，都还没做）

按顺序做；每一步都先写测试和黄金向量。

1. **38 字节真实数据包。** 定版本号和超范围时的饱和规则，然后同步改：`firmware/esp32/include/comms_packet.h`（8 通道 → 11）、`comms_security.h:19`（MTU 35 → 41）、`comms_control.h`（命令载荷内嵌整包）、`common/sensor.py`、`common/control.py`、`common/dummy_fixtures.json`、`laptop/bridge.py`（MTU 判断）、`laptop/goodput.py`、`ultra96/protocol.py:67`（8 个值）。真实数据不能用版本 1（版本 1 要求值等于假数据公式）。
2. **固件接采集模块。** `main.cpp`：`setup()` 里调初始化；把调用 `serializeFixturePacket` 的那一段换成“读样本 → 缩放 → 打包”。注意这一段运行时持有连接状态互斥量，BLE 回调也要取它，所以这里不能做慢操作。50 Hz 用 `-DCOMMS_INITIAL_RATE_HZ=50` 或 `--rate 50`。
3. **实测。** 两只真实手套、38 字节、50 Hz，不少于 65 秒，两块板源端对账干净。
4. **板上接模型接口。** 替换 `ultra96/server.py:264-267`。
5. **放行模型标签和真实置信度。** 现在四处校验只放行 `REST`/`FIST`/`OPEN`/`POINT` 且置信度必须等于 1.0：`ultra96/protocol.py:4,78-83`、`ios-visualizer/CommsNative/Sources/CommsCore/Protocol.swift:55-60`、`phone/receiver.py`、`phone/unity/CommsPhoneCore.cs`。**不改的话，模型的第一条真实标签就会让手机终止性断开。** 显示文本里的 `DUMMY inference` 和写死的 `confidence 1.0`（`DisplayMailbox.swift`、`SetupViewController.swift`）也在这一步。负责人已明确：这是通讯自己必须支持的，会由负责人来改。
6. **“一条输入一条结果”的判据。** 模型按窗口出结果后，`demo.py` 的 `Phone expected increase` 和两个演练工具（`tools/rehearse_comms.py`、`tools/rehearse_remote_comms.py`）的对账规则要重新定义。
7. **新的 Unity 导出的链接。** `patch_export.py` 不再需要；`configure_xcode.py` 依赖固定的 Xcode 对象 ID，对新导出是否适用没有验证过。
8. 按 6.3 节部署一轮并验收。

---

## 9. 禁止事项与注意事项

### 9.1 不能做的事

1. **不改队友的代码。** `hardware/`、`src/`、`models/`、`data/`、`reports/`、`fpga/`、`vis/`、`export_fpga_reference.py`、`requirements.txt` 只读。包括看起来无害的改动：换行符、格式化、依赖版本、重新生成文件。集成确实需要队友改代码时，写清楚要改什么、为什么，交给负责人去和对方说。
2. **不改通讯的连接方式，不提替代方案或备用路线。** BLE 到笔记本、笔记本和手机各自经 SSH 连到 Ultra96、手机客户端通过三个 C 函数交给游戏，这些已经定了，是按 NUS 防火墙规则设计的。尤其不要提“笔记本连手机 5005”“手机开热点”“共享局域网直连”之类。其他模块来适配通讯。
3. **不越界。** 不以负责人的名义去做或提供队友实现里的任何部分（例如给模型负责人写推理代码、给游戏负责人写 C# 脚本）。不把配对、组窗口、判断手势、标签映射列成负责人的任务。不替负责人评价队友组件的质量。
4. **不碰密码。** 不输入、不保存（文件、记忆、提交信息里都不行）、不复述跳板机或 Ultra96 的密码，即使负责人在对话里贴出来并说允许使用。凡是要登录的步骤，给出命令，由负责人在自己的终端里运行。
5. **不向团队仓库（`upstream`）推送**，除非负责人明确要求。推到 fork（`origin`）可以。
6. **不删除负责人没有纳入版本管理的文件。** 要清理就移到 `D:\LetThemCook-attic\`。`.week7-local/` 里有历史证据和 9 月烧录的固件副本，保留。
7. **不在仓库根目录运行不带路径的 `pytest`。** 它会收集 `fpga/hls/export_conv1d_test.py`，该脚本一导入就改写一个被跟踪的文件。用：`python -m pytest tests laptop/tests phone/tests -q -p no:cacheprovider`。
8. **不动 Week 7 临时接收端里的 `week7` 名字**（见 4.6 和 6.2 节的表）。
9. **演示或联调时不要运行第二个订阅者**（`laptop/phone_simulator.py`、`tools/rehearse_remote_comms.py`）。板上只有一个订阅者位置，它们会把手机顶掉。
10. **提到队友时用名字或“他们/they”，不要根据名字猜性别。**

### 9.2 容易踩的坑

- **证书只有 30 天。** 过期后服务照常启动，但笔记本一条 ACK 都拿不到，手机停在 `SSH, TLS or protocol verification failed`。不带 `--renew-server-from` 运行证书工具会连 CA 一起换掉，那样手机源码里的指纹和笔记本的 `--ca` 都得跟着改。
- **会话名三方必须一致。** 不一致时板子直接关连接，现象是 `received` 在涨、`acked` 一直是 0，或者手机在 `Connecting` 和 `Disconnected` 之间来回跳。
- **端口默认值不统一。** `demo.py` 用 18889；直接运行 `laptop.dual_bridge`、`tools.ssh_tunnel` 等模块时默认 18888。隧道和采集必须用同一个。
- **个人默认值写在代码里。** `demo.py tunnel` 的默认账号、`demo.py --ca` 的默认路径、`tools/demo_service.py` 的账号和板上路径（这个不能用参数改）、`tools/demo_boards.py` 的两块板蓝牙地址。换人、换机器、换板子都要注意。
- **`tools/demo_service.py` 的 `BOARD_SOURCE` 指向 9 月 28 日的快照。** 重新部署后不改它，`demo.py service --start` 启动的仍是旧代码。
- **服务进程的身份容量不回收。** 每次手套重新上电占一个 `(device_id, boot_id)`，一个进程最多 128 个，满了要重启服务。服务重启会清空去重状态。
- **没有订阅者时结果直接丢弃。** 所以要先让手机 `Subscribed`，再开始采集。
- **输入连接空闲 5 秒被板子关闭。** 手套掉线重连后的第一条样本可能没有 ACK，记为一次不确定丢弃。
- **GATT 表变了或固件重烧后，Windows 可能需要重新配对。** 恢复流程是人工的：板子串口 `erase-bonds` → Windows 里删除这块板 → 重新配对。
- **高速率下实际包率低于设定值**（70 Hz 设定约 66 包/秒）；75 Hz 以上会丢。
- **手机只在前台工作。** 锁屏或切走就断开并清密码。
- **没有贯穿全程的时间戳。** 2 秒新鲜度是各段自己的滞留时间，不是端到端延迟。
- **每接受一条输入，板上服务打一行 INFO 日志。** 两只手套各 50 Hz 时约每秒 100 行，全部经前台 SSH 终端输出。
- **`flash.py` 每次都会重写被 Git 跟踪的 `comms_fixtures.h`。** 改了 `common/dummy_fixtures.json` 之后必须重新烧录，板子上的数据才会变。
- **终端里残留的 `LTC_COMMS_SESSION`。** 过渡期的文档教过设 `LTC_COMMS_SESSION=week7-demo`。这个变量同时影响 `demo.py run`、`live` 和 `service --start`，但不影响手机。残留时笔记本和新启动的服务会一起用 `week7-demo`，`CAPTURE PASSED` 照常出现，手机却一直 `Disconnected: connection closed; retrying`。排障时先确认这个变量没有设。
- **两端都不记录“为什么被拒绝”。** 板子对坏帧、会话不符、身份冲突、容量耗尽一律只是关连接并把 `rejected` 加 1，不写日志；指标只在服务停止时打印一次。笔记本对 TLS 握手失败、ACK 超时只增加 `transport_errors`。所以证书过期、会话不一致、端口不通、两端协议版本不一致，在日志里看起来是一样的。做 38 字节迁移时，两端必须一起升级。
- **手机的“自动重试”是反复登录两跳 SSH。** 板上服务没起、会话不一致、被别的订阅者顶掉，手机都当作连接关闭，每隔最多 5 秒用密码重新登录一次跳板机和板子，没有次数上限。服务没准备好时先点 Disconnect，不要让 App 挂在 retrying。
- **`demo.py service --start` 启动的服务是那条 SSH 会话的前台进程。** 关掉那个终端、笔记本睡眠、VPN 掉线，服务都会跟着退出。启动服务的终端要和隧道终端一样保持打开。
- **换一台笔记本要先有 `known_hosts`。** 两跳 SSH 都是严格主机密钥校验，仓库里没有任何代码会写 `known_hosts`。可以用手机源码 `Configuration.swift` 里的两把公钥来核对。
- **单板诊断工具不能选板。** `laptop.ble_counter_receiver`、`laptop.mtu_probe`、`tools.rehearse_comms --ble` 按服务 UUID 扫描，连上先发现的那一块；两块板广播名相同，所以用它们时只给一块板上电。它们也不设速率，板子会沿用上一次的速率。
- **板子还是旧固件时的现象。** 双板采集先读源统计，标识不是 `LCS1` 就报 `invalid source statistics magic; flash this board with the current firmware`，这块板不会被订阅，30 秒后启动超时。
- **`verify-import.py` 只适用于刚导入、还没打补丁的 Unity 导出。** 对现在已经打过补丁的 `xcode-export/` 运行会报 `IMPORT_CHECK_FAILED`，这是正常的。

---

## 10. 负责人纠正过的错误认识（不要再犯）

| 错误 | 正确的 |
|---|---|
| 提议“笔记本经共享网络或热点连到手机的 5005 端口” | 违反 NUS 防火墙规则。手机自己经 `stujump` 用 SSH 连到 Ultra96 的结果服务 |
| 给连接方式提替代方案、备用路线，或承诺去改手机客户端的连接方式 | 通讯的连接方式是正确的做法，不改，不留后路 |
| 以为开了 VPN 就可以直连板子 | 开着 VPN 也仍然经 `stujump`；V1 保持跳板路线 |
| 把 `phone/unity/CommsPhoneReceiver.cs` 当成部署在 iPhone 上的接收端 | 它是 Android 参考实现。“Week 7 receiver”是 iPhone 上的 `CommsNative` 加导出工程里的 `Week7*` 桥接 |
| 提出把 NumPy 推理代码给 Wen Ree、替 Jie Ling 写 C# 脚本 | 越界。负责人只调用对方的接口，对方怎么实现与负责人无关 |
| 把配对、组窗口、每个手势出一个标签、标签映射写成负责人的工作 | 都是对方的工作。通讯止于接口 |
| 说链路只在 10 Hz 测过、蓝牙方案还没定 | 50 Hz 和 70 Hz 在 2026-09-28 实测干净；BLE 早已选定 |
| 在给队友的消息里夹带对他们组件质量的意见（模型精度、陀螺量程、某个路径 bug 等） | 只谈接口和交付时间 |
| 问队友代码里已经有答案的问题 | 先读代码；只问代码回答不了的（物理状态、意图、计划） |
| 用了负责人贴出来的密码 | 从不使用、保存或复述；登录由负责人自己做 |
| 以为固件合并后由 Siqiang 写 | Siqiang 提供采集模块；合并后的固件由负责人写 |
| 想把 TLS 主机名、`Week7*` 函数等也改名 | 这些要么写在证书里，要么属于 Week 7 临时接收端，不动 |
| 用带性别的代词称呼队友 | 用名字或 they |

---

## 11. 运行与验证

**不需要硬件：**

```powershell
python -m pytest tests laptop/tests phone/tests -q -p no:cacheprovider
python -m tools.generate_comms_pki --output-dir <仓库之外的空目录>      # 仅用于本机演练的一次性证书
python -m tools.rehearse_comms --pki-dir <同一目录> --duration 30 --target 100
```

演练在本机起一个板上服务、一个桥、一个订阅者，输出一行 JSON，`passed` 应为 `true`。Swift 测试要在 Mac 上跑：`swift test --package-path ios-visualizer/CommsNative`。

**实机全链路（先连 VPN；登录步骤由负责人做）：**

```powershell
python demo.py service          # 查看板上端口和进程
python demo.py tunnel           # 终端 A，保持打开
# iPhone：点 Communications Connect，等 Subscribed，记下 Received
python demo.py run              # 终端 B
python demo.py report
```

| 要验证的事 | 怎么看 |
|---|---|
| 板子收到（第 3 级） | `CAPTURE PASSED`；每块板 Generated = Received = ACKed |
| 手机收到（第 5 级） | iPhone 上 `Received` 的增量等于输出里的 `Phone expected increase`（人工比对） |
| 服务只绑回环 | `demo.py service` 打印的 `ss -ltnp` 里 8888 和 9999 的本地地址是 `127.0.0.1` |

**烧录与配对：** `python flash.py`（先左后右）、`python flash.py --pair left`、`python flash.py --monitor COMx`、`python flash.py --boards`。

常见故障的现象、原因和恢复办法见 `docs/handoff-details/06-tests-operations-extension.zh-CN.md`。

---

## 12. 代码地图：每个文件夹和文件是做什么的

这一节的目的是让新 agent 不用重读代码就知道东西在哪。要改某个文件之前仍然要读它本身。

### 12.1 顶层一览

| 路径 | 归属 | 是什么 |
|---|---|---|
| `firmware/esp32/` | 通讯 | 两块 FireBeetle ESP32 的 BLE 外设固件（PlatformIO 工程） |
| `common/` | 通讯 | 笔记本和 Ultra96 共用的 Python 模块：包格式、控制帧、网络帧、TLS |
| `laptop/` | 通讯 | Windows 笔记本上的 BLE 接收和转发（中继）程序 |
| `ultra96/` | 通讯 | 跑在 Ultra96 上的服务：收样本、回 ACK、把结果推给手机 |
| `phone/` | 通讯 | 参考和诊断用的接收端（Python、Android C#、iSH 脚本），**不是** iPhone 上部署的那个 |
| `ios-visualizer/` | 通讯 | iPhone 原生客户端 `CommsNative`（Swift）、Week 7 临时接收端的补丁工具、预览 App |
| `tools/` | 通讯 | 运维和演练工具：隧道、板上服务、证书、假数据、演练、证据 |
| `tests/` | 通讯 | 通讯的 Python 测试（也负责编译运行固件的主机测试） |
| `demo.py` | 通讯 | 日常操作入口：`tunnel`、`run`、`live`、`report`、`service` |
| `flash.py` | 通讯 | 构建、烧录两块板，记录蓝牙地址，配对，串口监视 |
| `requirements-dev.txt` | 通讯 | 测试和证书工具的依赖（pytest、cryptography；其中的 pyserial 通讯代码并不使用） |
| `docs/` | 通讯 | 负责人的文档（只在 fork 上） |
| `AGENTS.md`、`CLAUDE.md` | 通讯 | 给 agent 的规则：归属表、角色边界、测试命令（只在 fork 上） |
| `hardware/` | Siqiang | 手套固件草图、录制脚本、原理图。**只读** |
| `src/`、`models/`、`data/`、`reports/`、`fpga/`、`export_fpga_reference.py`、`requirements.txt` | Wen Ree | 模型训练和推理、权重、数据、FPGA 工程。**只读** |
| `vis/` | Jie Ling | Unity AR 游戏工程。**只读** |
| `README.md`、`.gitignore` | 共用 | 只能加或改通讯相关的行 |

### 12.2 通讯代码，逐文件

**`common/`（两端共用，改这里等于同时改笔记本和板上服务）**

| 文件 | 做什么 |
|---|---|
| `sensor.py` | 32 字节传感器包的编码和解码（`SensorPacket`、`encode_packet`、`decode_packet`、`PACKET_MAGIC = b"LC"`）；把包转成 `SENSOR_BATCH` 消息；加载和选择假数据 |
| `control.py` | BLE 控制帧（`B7` 头 14 字节）的编解码和校验；命令对 8 个值的变换规则。与网络 JSON 无关 |
| `wire.py` | 网络帧：4 字节大端长度 + 严格 UTF-8 JSON；上限 16384 字节；读写各 5 秒期限；`ProtocolError` |
| `tls.py` | TLS 客户端和服务端上下文；最低 TLS 1.2；主机名常量 `TLS_SERVER_NAME`；没有“不校验”的分支 |
| `dummy_fixtures.json` | 可编辑的 8 通道假数据表（现有 4 行）；固件头文件由它生成 |

**`firmware/esp32/`**

| 文件 | 做什么 |
|---|---|
| `platformio.ini` | 构建环境：`firebeetle32-left`（ID 1）、`firebeetle32-right`（ID 2）、非保护诊断版 |
| `src/main.cpp` | BLE 外设的全部运行逻辑：GATT 服务和 7 个特征、配对安全、按速率发样本、控制队列、源统计、`erase-bonds` 串口命令 |
| `include/comms_packet.h` | 32 字节包的逐字节序列化；从假数据表取值 |
| `include/comms_fixtures.h` | 由 `common/dummy_fixtures.json` 生成的假数据表（`flash.py` 每次重写） |
| `include/comms_security.h` | 认证位判断、通知闸门、MTU 下限（传感器 35、控制 64）的纯函数 |
| `include/comms_source_stats.h` | 序号分配、提交计数、24 字节源统计的序列化 |
| `include/comms_control.h` | 控制状态机 `ControlEngine`：命令、调速、文件传输、响应缓存 |
| `include/comms_gatts_control.h` | 只在真正的 WRITE 事件上解析写入 |
| `test/host_*.cpp` | 四个在主机上用 g++ 编译运行的测试（包、事件、源统计、控制） |

**`laptop/`**

| 文件 | 做什么 |
|---|---|
| `bridge.py` | 单只手套的整条路径：扫描、连接、MTU 和绑定检查、有界队列、TLS 写出、ACK 核对、指标、关闭时的尾包处理 |
| `dual_bridge.py` | 同时跑两条互不耦合的 `Bridge`，统一观察窗，出总报告。`demo.py` 调的就是它 |
| `source_audit.py` | 解析源统计（`SOURCE_STATS_MAGIC = b"LCS1"`）；对账“产生 = 收到 = ACK” |
| `controls.py` | BLE 控制通道：键盘命令、调速、文件传输 |
| `windows_pairing.py` | Windows 上按“输入配对码 + 加密且认证”配对，并检查绑定等级 |
| `ble_connection.py` | 建 Bleak 客户端时关闭 Windows 的 GATT 缓存 |
| `ble_parameters.py` | 速率高于 10 Hz 时向 Windows 申请吞吐优先的连接参数，并记录实际值 |
| `ble_shutdown.py` | 停止采集时先在远端关通知、保留本地回调，用来收尾包 |
| `evidence.py` | 后台有界地写 `packets.jsonl` 和日志 |
| `goodput.py` | 统计收到的有效传感器字节速率 |
| `reporting.py` | 报告文件的独占占位和原子落盘；源码指纹 |
| `phone_simulator.py` | 桌面版结果订阅者，只用于演练；**连上后会顶掉手机** |
| `mtu_probe.py`、`ble_counter_receiver.py`、`bounded_telemetry_queue.py` | 早期的诊断工具和一个主路径没用到的通用队列 |
| `requirements.txt` | `bleak==3.0.1`（版本必须钉死：关闭尾包保护依赖 Bleak 的内部属性） |
| `tests/` | 上面三个诊断工具的测试 |

**`ultra96/`**

| 文件 | 做什么 |
|---|---|
| `server.py` | 板上服务 `CommsServer`：两个回环 TLS 监听、输入去重和 ACK、单订阅者结果队列、命令行入口。**假结果在第 264 到 267 行生成，模型接口接在这里** |
| `protocol.py` | 五种消息的精确字段和取值范围、`session_id` 规则、`result_id` 生成。**标签白名单 `GESTURES` 和“置信度必须是 1.0”的检查在这里** |
| `diagnostics.py` | 可选的有界事件日志（`--event-log-dir`） |

**`ios-visualizer/`**

| 文件 | 做什么 |
|---|---|
| `CommsNative/Package.swift` | Swift 包定义；依赖固定为 SwiftNIO、NIOSSH、NIOSSL、swift-crypto 的具体版本 |
| `CommsNative/Sources/CommsCore/Protocol.swift` | 订阅帧编码、结果校验（**标签白名单和置信度检查**）、流式分帧 |
| `CommsNative/Sources/CommsCore/DisplayState.swift` | 最新结果、计数、去重（4096）、2 秒过期 |
| `CommsNative/Sources/CommsTransport/CommsClient.swift` | 两跳 SSH + TLS 的建立、错误分类（终止或重试）、退避重连 |
| `CommsNative/Sources/CommsTransport/SSHRoute.swift` | 路线参数、端口和超时常量、失败类型 |
| `CommsNative/Sources/CommsTransport/Trust.swift` | 主机公钥精确比对、密码认证、SSH 通道字节转换 |
| `CommsNative/Sources/CommsTransport/Subscriber.swift` | TLS 握手后发 `SUBSCRIBE`、收帧、帧期限 |
| `CommsNative/Sources/CommsTransport/Credentials.swift` | 可清除的内存密码保管 |
| `CommsNative/Sources/CommsBridge/Configuration.swift` | 固定的主机名、两把 SSH 主机公钥、CA 指纹；CA 导入校验；公开设置存盘 |
| `CommsNative/Sources/CommsBridge/IntegrationController.swift` | 前台会话管理、连接按钮、退后台即断开；会话名 `ltc-comms` 写在这里 |
| `CommsNative/Sources/CommsBridge/SetupViewController.swift` | 设置表单 |
| `CommsNative/Sources/CommsBridge/DisplayMailbox.swift` | 导出给 Unity 的 C 函数 `CommsStart`、`CommsCopyDisplay`、`CommsStop`，以及 `Week7*` 包装；四行文本在这里拼 |
| `CommsNative/Tests/` | Swift 测试（要在 Mac 上跑） |
| `NativePreview/` | 不带 Unity 的预览 App 和界面测试 |
| `tools/patch_export.py` | Week 7 临时接收端：给那一份 Unity 导出的生成代码打补丁（只在 fork 上） |
| `tools/configure_xcode.py` | 把 `CommsNative` 链接进 `UnityFramework`（只在 fork 上） |
| `verify-import.py`、`import-manifest.json` | 核对最初导入的 Unity 导出；只适用于还没打补丁的工程（只在 fork 上） |
| `reference/TlsDataReceiver.cs` | Jie Ling 原始接收脚本的留档（只在 fork 上） |
| `xcode-export/` | Week 7 用的 Unity 导出工程，3479 个文件，大文件走 LFS（只在 fork 上） |
| `README.md`、`NATIVE-INTEGRATION.md` | 源码和集成边界的说明 |

**`phone/`（参考和诊断）**

| 文件 | 做什么 |
|---|---|
| `receiver.py` | 标准库 Python 接收器（Termux/iSH），连本机转发口 19999 |
| `unity/CommsPhoneCore.cs` | 不依赖 Unity 的 C# 协议、TLS 信任、接收循环 |
| `unity/CommsPhoneReceiver.cs` | Android 参考 Unity 组件；需要手机另外开一条 SSH 本地转发 |
| `ish_control.py` | iSH 路线的临时维护通道脚本（该路线已弃用） |
| `tests/` | 上述 Python 的测试，和 C# 自测脚本（需要 PowerShell 7） |

**`tools/`**

| 文件 | 做什么 |
|---|---|
| `ssh_tunnel.py` | 生成两跳、只绑回环的 OpenSSH 本地转发命令（显式 `ProxyCommand`，严格主机密钥） |
| `demo_service.py` | 经 SSH 查看或启动板上服务；板上部署目录常量 `BOARD_ROOT`、`BOARD_SOURCE` 在这里 |
| `demo_boards.py` | 左右板蓝牙地址映射的读写（`.comms-local/boards.json`）；内置默认地址在这里 |
| `generate_comms_pki.py` | 生成 CA 和服务器证书；`--renew-server-from` 用原 CA 只续签服务器证书 |
| `generate_dummy_fixtures.py` | 由 JSON 生成固件头文件 `comms_fixtures.h` |
| `comms_demo.py` | 包示例、单板发送演示、离线日志审计 |
| `rehearse_comms.py` | 本机回环的全流程演练（不碰 SSH 和真机） |
| `rehearse_remote_comms.py` | 经已有隧道的远程演练；**会顶掉手机的订阅** |
| `video_evidence.py` | 从一次采集里取每块板一对样本和 ACK 的示例 |

**`tests/`**：45 个文件（42 个测试 + `fixtures/` 下 3 个黄金向量）。按被测对象命名：`test_sensor.py`（包格式）、`test_source_audit.py`、`test_laptop_controls.py`、`test_bridge_*.py`、`test_dual_*.py`、`test_transport*.py`（TLS、帧、证书工具）、`test_server_*.py`、`test_ssh_trust.py`、`test_demo_*.py`、`test_firmware_*.py`（编译并运行固件主机测试）、`test_rehearsal.py` 等。

### 12.3 队友的代码（只读；了解到能对接的程度即可）

**`hardware/gloves/`（Siqiang）**

| 路径 | 是什么 |
|---|---|
| `README.md` | 两只手套的说明：每只一块 ESP32、一个 MPU-6500、两个弯曲传感器；每个样本 11 个值 |
| `29_sept/imu_v7.ino` | 现在的参考固件草图（Bluetooth Classic 串口输出 CSV） |
| `29_sept/imu_recording_terminal_v14.py`、`how_to_use.txt` | PC 端录制脚本和用法 |
| `imu_v3.ino`、`imu_recording_terminal_v10.py`、`_v11.py` | 较早的版本 |
| `model_threshold_variant_1/` | 在 ESP32 上做“有没有动作”检测的实验（训练脚本、参数头文件、调试草图） |
| `glove_schematic_week7.png` | 原理图 |

**`src/`、`models/`、`data/`、`reports/`、`fpga/`（Wen Ree）**

| 路径 | 是什么 |
|---|---|
| `src/model.py` | CNN 的定义 |
| `src/train_model.py`、`cross_validate_model.py`、`evaluate_model.py`、`check_model.py` | 训练、交叉验证、评估 |
| `src/create_dataset.py`、`preprocess_sensor_data.py` | 数据集构建和预处理 |
| `src/inference.py`、`src/live_inference.py` | 离线推理；从两个 COM 口读手套数据做实时推理（在笔记本上打印结果） |
| `models/class_names.json`、`gesture_cnn*.pth` | 6 个类别名；权重 |
| `data/simulated/` | 模拟数据 |
| `reports/` | 评估结果 |
| `fpga/hls/` | HLS 源码：一个乘加测试模块和第一层卷积的定点实现及测试台。**`export_conv1d_test.py` 一被导入就改写被跟踪的文件，所以不能在根目录跑裸的 pytest** |
| `fpga/pynq/`、`fpga/vivado/`、`fpga/validation/` | 乘加模块的比特流、Vivado 工程、验证数据 |
| `fpga/README_FPGA_PYNQ.md` | 在 PYNQ 上加载 overlay 的说明（需要 sudo） |
| `export_fpga_reference.py` | 导出 FPGA 对照用的参考数据 |

**`vis/`（Jie Ling）**

| 路径 | 是什么 |
|---|---|
| `Assets/Scripts/Core/` | 手部追踪和交互：`HandTrackingManager.cs`（用摄像头和 MediaPipe 取手部关键点）、`GestureButtonController.cs`（动作入口 `OnSelectPressed`、`OnGrabPressed`、`OnDropPressed`、`OnChopPressed`、`OnWashPressed`，其中洗菜还是空的）、`Grabbable.cs` 等 |
| `Assets/Scripts/Kitchen/` | 厨房逻辑：砧板、切菜进度、食材状态、食材箱、锅 |
| `Assets/Scripts/AR/` | AR 相关：二维码生成物品、头显双眼布局、畸变 |
| `Assets/Scripts/UI/` | 菜单和悬停反馈、场景加载 |
| `Assets/Scripts/Network/TlsDataReceiver.cs` | 在手机上监听 5005 的 TLS 服务端，只显示收到的文本（方向与网络模型相反） |
| `Packages/com.github.homuler.mediapipe/` | MediaPipe 的 Unity 插件 |
| `Assets/` 其余、`ProjectSettings/` | 场景、预制体、素材、工程设置 |

### 12.4 Git、只在本机的目录

| 位置 | 内容 |
|---|---|
| `D:\LetThemCook` | 工作副本，本地 `main` |
| `upstream` | 团队仓库 <https://github.com/B07-CG4002/Let-Them-Cook>，公开，主分支没有保护，现在在 `ec398b6`。合并 PR #15 时没有 `gh`，是用 `git commit-tree` 加推送完成的 |
| `origin` | 负责人的 fork <https://github.com/olsonwangyj/Let-Them-Cook>，公开 |
| 只在 fork 上、团队仓库里没有的 | 整个 `docs/`、`AGENTS.md`、`CLAUDE.md`、`.gitattributes`、`ios-visualizer/` 下的 `tools/`、`verify-import.py`、`import-manifest.json`、`reference/`、`xcode-export/`，以及 `tests/test_ios_export_patch.py`。所以队友克隆团队仓库是看不到设计记录的 |
| `.comms-local/` | 本机的板子映射 `boards.json`（左板 `38:18:2B:19:82:AE`，右板 `38:18:2B:18:9D:6A`）和以后的新采集（Git 忽略）。现在还没有采集目录 |
| `.week7-local/` | 17 个历史采集目录（都是 `W7` 包）、9 月的实测结果文件、9 月 29 日烧录固件的留档、以及 9 月用的本地脚本：`co_deploy.py`（带严格 SSH 信任和回滚的板上部署脚本，9 月 28 日的部署就是用它做的）、`co_acceptance.py`、`co_faults.py`、`co_final_check.py`、`co_iphone_capture.py` 等。Git 忽略，没有版本管理，**保留，不要删** |
| `release-tools/`、`output/` | 9 月 30 日提交用的冻结打包工具和 4 个 ZIP（在 `.git/info/exclude` 里，只在本机） |
| `D:\LetThemCook-attic\2026-10-13\` | 整理工作区时移出去的 2.3 GB 文件（没有删除，里面有 README.txt） |
| `D:\LetThemCook-worktrees\comms-cleanup` | 分支 `comms/remove-week7-legacy` 的工作树（基于团队主分支，用来向团队仓库开 PR） |
| `~/.codex/private/cg4002-week7-20260906/` | 现用的 CA（含私钥）和 9 月的服务器证书。不进 Git |

### 12.5 `docs/` 索引

| 文件 | 内容 |
|---|---|
| `communications-handoff.zh-CN.md` | 本文档 |
| `handoff-details/01` 至 `06` | 六个细节章节：架构与网络安全、固件、笔记本、Ultra96、手机与 Week 7 接收端、测试运维与待扩展点 |
| `co-protocol-v2.md` | 负责人的现行协议设计（v2、控制、文件） |
| `B07-CO-protocol-explained.zh-CN.md` | 协议的中文逐字节讲解 |
| `communications-quickstart.md` | 快速上手 |
| `integration-handoff.md` | 给队友看的英文集成说明（PR #15） |
| `week7-runbook.md` | Week 7 的操作手册（部分命令名已过时，见 4.9） |
| `archive/` | 历史：评估材料、报告、实测证据、设计记录、旧手册 |

### 12.6 想改某件事，去哪个文件

| 要改的事 | 文件 |
|---|---|
| 包里放几个值、包多长 | `firmware/esp32/include/comms_packet.h`、`common/sensor.py`、`ultra96/protocol.py`，以及 MTU 闸门 `comms_security.h` 和 `laptop/bridge.py` |
| 固件从哪里取样本 | `firmware/esp32/src/main.cpp`（调用 `serializeFixturePacket` 的那一段） |
| 默认发送速率 | `platformio.ini`（`-DCOMMS_INITIAL_RATE_HZ`）或运行时 `demo.py run --rate` |
| 板上怎么产生结果 | `ultra96/server.py:264-267` |
| 允许哪些标签、置信度 | `ultra96/protocol.py`、`CommsCore/Protocol.swift`、`phone/receiver.py`、`phone/unity/CommsPhoneCore.cs`（四处要一起改） |
| 给 Unity 的文本或函数 | `ios-visualizer/CommsNative/Sources/CommsBridge/DisplayMailbox.swift` |
| 会话名 | 笔记本：`--session-id` 或 `LTC_COMMS_SESSION`；板上：服务的 `--session-id`；手机：`IntegrationController.swift`（要重新编译） |
| 跳板机、板子的主机名和 SSH 主机公钥、CA 指纹 | 笔记本：`tools/ssh_tunnel.py`、`demo.py` 的参数；手机：`Configuration.swift`（要重新编译） |
| 板上部署目录 | `tools/demo_service.py` 的 `BOARD_ROOT`、`BOARD_SOURCE` |
| 两块板的蓝牙地址 | 跑 `python flash.py`，结果在 `.comms-local/boards.json` |
| 队列长度、新鲜度、超时、ACK 窗口 | 笔记本：`laptop/bridge.py` 的 `BridgeConfig`、`demo.py`；板上：`ultra96/server.py`；手机：`SSHRoute.swift`、`DisplayState.swift` |
| 证书 | `tools/generate_comms_pki.py` |

---

## 13. 没有确认的事

- 板上现在的服务器证书、服务进程、代码快照的实际状态（需要负责人登录核对）。
- 右板和左板在重新烧录后是否需要重新配对。
- 38 字节 × 50 Hz × 2 块板在实机上是否干净。
- `configure_xcode.py` 对新的 Unity 导出是否适用。
- 直连模式（手机不经跳板）现场没有验证过，V1 不用。
- 2026-09-21 手机少收 109 条的原因。
- 三位队友对第 7 节接口的答复。

需要负责人拍板的事：

- 游戏通过三个 C 函数拿结果时，只拿“最新一条”和文本是否足够，还是通讯要在桥上加逐条交付和真实置信度（7.3 节末尾）。
- 交给模型的 `values` 是物理量浮点（现在的默认写法）还是 int16 原值。
- 38 字节包的版本号，以及数值超出 int16 范围时怎么处理（饱和还是丢弃）。

---

## 14. 更新记录

| 日期 | 改了什么 |
|---|---|
| 2026-10-14 | 初版。写入：项目与各子系统现状；角色与边界；通讯全链路、格式、各段工作方式和设计理由；删除 Week 7 兼容后的状态；左板已烧录当前固件；发现服务器证书已于 10-06 过期并新增续签选项；三个接口的 API 需求；负责人的各项纠正 |
