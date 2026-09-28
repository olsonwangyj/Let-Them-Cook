# B07 CO：本机演示简短版

**现有功能就能实现：两块 ESP 同时收发、实时日志、保存最终 JSON 报告。** 不用修改程序，也不用粘贴辅助函数。以下用于已经配置好的 `D:\LetThemCook`，使用 **PowerShell 7.3+（pwsh）**。

视频文件名：**`B07_CO_subsystem.mp4`**；英文口播，无需幻灯片，上传 YouTube 时选择 **Unlisted**。源码放大到清楚可读。

## 1. 录制前准备

- 电脑和 iPhone 连接 VPN，电脑蓝牙开启。使用已安装的新版 iPhone 应用。
- Ultra96 的 `ultra96.server` 服务需在运行，监听板端 `127.0.0.1:8888/9999`。如果还没启动，先按[完整指南的板端步骤](week7-testing-and-demo-guide.zh-CN.md#5-check-the-board-without-redeploying-or-stopping-it)检查并启动，不要重复启动。
- 正式开场时，电脑桥接程序未运行，两块 ESP 可以断电；镜头中再给两块 ESP 通电。USB 或充电宝均可，业务数据通过 BLE。
- 这是新的运行演示，固件、配对、证书和依赖已经预先配置好。输入为确定性模拟数据，10 Hz 表示每台每秒约 10 个包。
- 同时拍到电脑与手机。不要运行手机模拟器；它会替换真实 iPhone 的订阅。不要打开原始串口监视器，避免重置 ESP 或录入配对口令。

**English:**

> This is B07's communication subsystem. Two physical ESP32s send dummy data at ten hertz each. The laptop receives and forwards both streams to Ultra96, and the iPhone receives results directly from the board. The devices and certificates were configured earlier; I will now start a fresh run.

## 2. 终端 A：启动隧道

在 PowerShell 中执行，按提示输入两跳密码，然后保持此窗口打开。已有确认属于本项目、使用 `18889` 的隧道时直接复用，不重复启动。

```powershell
cd D:\LetThemCook
python -c 'import subprocess; from tools.ssh_tunnel import tunnel_command; raise SystemExit(subprocess.run(tunnel_command("yanjie@stujump.comp.nus.edu.sg","xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg",18889,8888)).returncode)'
```

这条命令直接使用已有隧道工具，无需粘贴函数。启动后安静等待属于正常情况；是否真正通信成功，要看后面的 ACK 和报告。输入密码时不要显示或录入口令。

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

下面整个小块执行一次即可。每次运行自动使用新目录；重测时再执行同一块。现有程序默认每秒输出两路进度，ACK 窗口为每台 32，使用 `week7-demo` 会话。

```powershell
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$run = ".week7-local\B07-$(Get-Date -Format yyyyMMdd-HHmmss-fff)"
New-Item -ItemType Directory -Path $run -ErrorAction Stop | Out-Null
python -u -m laptop.dual_bridge `
    --ca "$env:USERPROFILE\.codex\private\cg4002-week7-20260906\ca-cert.pem" --port 18889 `
    --left-address 38:18:2B:19:82:AE --right-address 38:18:2B:18:9D:6A `
    --duration 60 --report "$run\report.json" `
    2>&1 | ForEach-Object { $_.ToString() } | Tee-Object -FilePath "$run\live.log"
$runExit = $LASTEXITCODE
$runExit | Set-Content "$run\exit-code.txt"
Write-Host "Exit=$runExit  Saved in: $run"
```

**不需要改代码。** `--report` 是程序已有的报告功能；`Tee-Object` 让日志同时显示并保存。让程序自然结束，不要中途按 Ctrl+C；连接准备及最终排空会使总耗时略长于 60 秒。

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

结束后执行这个短块，显示总状态、连接状态和源端对账表。拉宽终端窗口，避免表格列被截断：

```powershell
$r = Get-Content "$run\report.json" -Raw | ConvertFrom-Json
$r | Format-List clean,mock_input,report_saved
# Connection rows are ESP 1, then ESP 2.
$r.devices.'1', $r.devices.'2' | Format-Table clean,protected_ble,ble_connections,transport_connections,unfinished -AutoSize
$r.devices.'1'.source, $r.devices.'2'.source |
    Format-Table device_id,generated,source_submitted,received,acked,missing_received,missing_acked -AutoSize
```

本次正常测试通过需要：

- `Exit=0`、`clean=True`、`mock_input=False`、`report_saved=True`；两台受保护连接正常，`unfinished=False`。正常无重连时 BLE/TLS 连接数各为 1。
- 每台 **`generated = source_submitted = received = acked`**，两项 `missing` 均为 0。这里的 `received` 是源端审计中的已接收样本数。
- 等手机计数稳定后，核对 **手机结束计数 − 开始计数 = 两台 `generated` 之和**。记录实际手机计数；电脑报告不会自动读取 iPhone 屏幕。初始为 0 时直接比较手机结束计数。

不要固定要求“一分钟恰好 1,200 包”，连接启动和收尾也可能产生样本。未完成报告、`clean=False` 或源端 `null` 都不能算通过。`clean` 汇总了源端核对及错误/丢弃等检查；全部字段见[完整验收说明](week7-testing-and-demo-guide.zh-CN.md#7-capture-a-complete-physical-run-and-save-its-outcome)。

文件保存在 **`D:\LetThemCook\.week7-local\B07-时间戳\`**：

| 文件 | 用途 |
|---|---|
| `live.log` | 本次电脑进度、错误及最终输出 |
| `report.json` | 原始结构化报告，包含两台设备计数和源端审计 |
| `exit-code.txt` | 本次退出码，正常通过为 0 |

想保存一个方便阅读的缩进版本，再运行这一行即可：

```powershell
python -m json.tool "$run\report.json" "$run\report-readable.json"
```

**English（核对通过后，用实际数字替换）：**

> Device one generated [N1] packets, and device two generated [N2]. The generated, received and acknowledged counts match. The phone count increased by [N], matching the combined source total. No packet loss was detected in this connected capture.

手机的证据是总计数，不能把板端 ACK 当作每个结果已被手机接收的证明。停止发送约两秒后，手机显示 `No live result` 属于正常显示过期。

## 6. 再录几段，验证恢复能力

每次重复第 4 节，按表修改 `--duration`；自动得到新的日志和报告目录。记录每次手机开始/结束计数，正常运行后重复第 5 节。

| 测试 | 操作与观察 |
|---|---|
| 空闲恢复 | 手机保持前台，停止发送至少 120 秒，再运行 60 秒；不点 Connect。应保持 `Subscribed`，手机增量匹配第二次源端总数。 |
| 单 ESP 故障 | 单独运行 120 秒；两路开始后约 20 秒给 ESP 1 断电，约 20 秒后恢复。ESP 2 应继续推进，ESP 1 恢复后继续接收。此次故障报告预期不 clean，不能用来宣布零丢失。 |
| 故障后正常运行 | 两台供电稳定后，另做新 60 秒采集，重新核对 clean 和计数。断电改变 boot ID，前一段源端数可能为 `null`，不能当作 0。 |
| 手机锁屏恢复 | 停止发送后锁屏约 20 秒，解锁出现 `Paused`；手动 Connect，确认计数归零，再运行 30 秒并核对。 |
| 十分钟连续运行 | 改为 `--duration 600`，保持手机前台，结束后用实际数值对账。 |

**English：**

> After two minutes of idle time, results resume without reconnecting the phone.
>
> When ESP one loses power, the laptop continues receiving acknowledgements for ESP two. I will then run a fresh clean capture after recovery.
>
> Locking the phone pauses reception. After unlocking, I reconnect manually and verify a new capture.

以上口播以本次观察确实符合为前提。系统不承诺补回断电、断网或手机暂停期间的全部数据。

## 7. 展示源码与结尾

打开下列文件，每次放大一个短代码区域；无需制作幻灯片：

| 文件 | 展示内容 |
|---|---|
| [main.cpp](../firmware/esp32/src/main.cpp#L397) | 固件每 100 ms 生成并提交带序号的 BLE 模拟数据 |
| [dual_bridge.py](../laptop/dual_bridge.py#L83) | 两台设备分别创建 input 和 writer 任务 |
| [bridge.py](../laptop/bridge.py#L458) | 每台独立队列、TLS 发送与 ACK 流水线 |
| [server.py](../ultra96/server.py#L232) | 接纳数据、返回 ACK、向手机发送模拟结果 |

**English：**

> Each device has its own BLE input, queue and TLS connection. Asynchronous tasks allow both streams to make progress independently. The clean captures show matching source and acknowledgement counts, together with a matching aggregate phone count.

保存报告和手机计数画面后，在终端 A 按 Ctrl+C 停止本次启动的隧道。完整原理见[技术报告](week7-system-technical-report.zh-CN.md)，首次配置和故障排查见[完整测试指南](week7-testing-and-demo-guide.zh-CN.md)。本次文档简化只核对命令与代码，没有重新执行实体测试。
