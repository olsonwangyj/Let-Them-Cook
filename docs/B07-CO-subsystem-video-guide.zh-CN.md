# B07 CO：Individual Full Subsystem Test 录制操作单

文件名：**`B07_CO_subsystem.mp4`**。使用英文口播，不需要幻灯片。本文提供中文操作说明、实际运行命令和可直接照读的简短英文稿。

本文于 2026-09-28 按仓库 `258aa64` 的代码核对。本文编写期间没有连接 ESP、登录板端或执行新的实物测试；视频中的结论必须以你录制当天的结果为准。完整原理见[中文版技术报告](week7-system-technical-report.zh-CN.md)，完整检查字段和首次配置见[中文版测试指南](week7-testing-and-demo-guide.zh-CN.md)。

## 1. 这次视频需要证明什么

主线是：**两块真实 ESP 上电 → 已认证的 BLE 连接 → Windows 同时接收并转发两路数据 → Ultra96 接纳并返回 ACK → iPhone 独立接收结果 → 核对本次实际计数**。

“从零开始”指实际展示一次新的运行过程。固件、驱动、Python 依赖、受信任证书、已认证绑定和 iPhone 应用可以预先配置好，并在片头说明；不必每次录制都擦除绑定、重新烧录或重装应用。若 Ultra96 服务已经运行，明确说明正在复用；如果要拍到板端服务也从停止状态启动，按第 4 节先核实归属并正常停止本项目服务，再录制启动过程。

建议录制 **18–25 分钟**，按实际等待时间自然延长。你没有时长限制，可以再附一段新的 **600 秒连续测试**。不要为了凑时间截掉核心测试中间的错误或断开。

| 段落 | 画面和动作 | 需要保留的证据 |
|---|---|---|
| 开场和源码 | 两块 ESP、笔记本、iPhone；展示固件和双设备代码 | 设备 ID 1/2、每台 10 Hz、32 字节包、两套独立任务 |
| 从未运行状态启动 | ESP 上电；板端检查/启动；隧道启动；BLE 绑定检查；手机 Connect | 命令与真实输出、`authenticated_bond: true`、`Subscribed, Received: 0` |
| 双设备基线 60 秒 | 新启动 `laptop.dual_bridge`，电脑与手机同时可见 | 两行接收/ACK 计数持续增加；手机出现 `1:` 和 `2:` 两类 ID |
| 最终核对 | 正常结束后展示保存的 JSON 和汇总表 | 每台源端生成数＝接收数＝ACK 数；手机增量匹配；退出码 0 |
| 空闲及恢复 | 保持手机前台，不发送至少 120 秒，再发送 60 秒 | 不重新 Connect，订阅保持；第二次手机增量匹配 |
| 单 ESP 故障 | 单独的 120 秒运行，断一台电约 20 秒再恢复 | 健康设备继续推进；故障设备停顿后恢复；保留非 clean 报告 |
| 故障后正常运行 | 再开独立 60 秒运行 | 用新的源端边界重新得到 clean 报告 |
| 手机锁屏恢复 | 无发送时锁屏约 20 秒，再解锁并手动 Connect；发送 30 秒 | `Paused`、重新订阅、恢复后计数匹配 |
| 长时间证据和结尾 | 新的 600 秒运行，或明确标注以前的测试 | 日期、持续时间、源端计数和手机观察；总结测试范围 |

这些实验验证通信子系统。输入是**确定性模拟数据**，不是实际传感器读数或训练模型的真实识别结果。不要在片尾声称任意断网、断电或后台状态下都保证零丢失。

## 2. 录制前准备：先彩排，再从起点正式录

1. 两块 ESP 贴上 **ESP 1 / left** 和 **ESP 2 / right** 标签。历史验证地址分别为 `38:18:2B:19:82:AE`、`38:18:2B:18:9D:6A`；设备更换后须核实映射。固件必须分别使用 `firebeetle32-left` 和 `firebeetle32-right`。
2. Windows 和 iPhone VPN 均可用，Windows 蓝牙开启。iPhone 已安装更新后的接收应用。Mac 只在重新构建/安装 iPhone 应用时需要，日常演示不需要 Mac 转发数据。
3. 完成首次配对、证书配置和依赖安装后再录。现有电脑检查到的是 Python 3.12.7、Bleak 3.0.1；以后仍以你的实际检查为准。
4. 正式开场时，双 ESP 可以处于断电状态，笔记本桥接程序未运行，手机尚未 Connect。关闭你自己之前启动的发送/订阅程序；不要批量结束所有 Python 或 SSH 进程。
5. 笔记本录屏使用清晰画质，例如 1920×1080；编辑器和终端放大字体。展示源码时一次只展示约 20–35 行，隐藏不必要的侧栏。别用四个缩得很小的窗口来满足“所有画面都在屏幕上”。
6. 用外部摄像头/另一台设备拍到两块 ESP 和 iPhone 屏幕，与电脑录屏同步。手机若使用自身录屏，提前启动，再返回 Unity 建立正式测试会话；中途打开系统控制界面可能使 Unity 暂停。开始时口播段落名称，便于后期对齐画面。
7. 录制时不打开凭据文件、不点击密码显示、不录原始串口或配对口令。输入密码的准备画面可以遮挡；正常数据测试过程保持连续。如果剪辑准备等待过程，明确保留测试的起止和实际持续时间。

**不要打开串口监视器作为主测试的必要步骤。** 打开串口可能重置 ESP，原始输出也可能包含配对口令。固件公开的源端统计和最终核对可以证明这次订阅期间实际生成、提交了多少样本。ESP 的蓝灯闪烁本身不是成功收发证据。

### Windows 共用设置：在终端 B 粘贴一次

以下 Windows 命令使用 **PowerShell 7.3+（`pwsh`）**。在 `D:\LetThemCook` 根目录运行。当前电脑可以使用已安装依赖的 `python`；如果你使用虚拟环境，把 `$py` 换成它的 `python.exe`。

```powershell
Set-Location D:\LetThemCook
if ($PSVersionTable.PSVersion -lt [version]'7.3') { throw 'Use PowerShell 7.3 or newer.' }
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$py = (Get-Command python).Source
& $py --version
& $py -c 'import importlib.metadata; print("bleak", importlib.metadata.version("bleak"))'
if ($LASTEXITCODE -ne 0) { throw 'Install the documented laptop dependencies before recording.' }
git rev-parse HEAD
$ca = Join-Path $env:USERPROFILE '.codex\private\cg4002-week7-20260906\ca-cert.pem'
if (-not (Test-Path -LiteralPath $ca)) { throw 'Locate the existing trusted public CA.' }
$left = '38:18:2B:19:82:AE'
$right = '38:18:2B:18:9D:6A'
$port = 18889
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$outRoot = Join-Path (Get-Location) ('.week7-local\B07-video-' + $stamp)
New-Item -ItemType Directory -Path $outRoot -ErrorAction Stop | Out-Null
git rev-parse HEAD | Set-Content -LiteralPath (Join-Path $outRoot 'revision.txt')
Write-Host "Evidence: $outRoot"
```

缺依赖时，在正式录制前运行 `python -m pip install -r laptop/requirements.txt`；软件回归检查另外需要 `requirements-dev.txt`。不要为了通过连接而生成新 CA、关闭证书检查或降级到不受保护的 BLE 模式。

不同终端不共享 PowerShell 变量。终端 A/C 的独立命令下文会明确说明；不要以为 B 中的 `$py` 已自动存在于 A。

### 可复用采集函数：仍在终端 B 粘贴

这个函数调用现有双 ESP 程序，把实时日志同时显示在屏幕并保存，另外保存独立、可解析的最终 JSON。它不会启动手机模拟器。每次使用新名称，避免覆盖旧证据。

```powershell
function Invoke-B07Capture {
    param([string]$Name, [int]$Seconds = 60)
    $caseDir = Join-Path $outRoot $Name
    New-Item -ItemType Directory -Path $caseDir -ErrorAction Stop | Out-Null
    $reportPath = Join-Path $caseDir 'report.json'
    $logPath = Join-Path $caseDir 'live.log'
    Write-Host "CASE=$Name DURATION=$Seconds REPORT=$reportPath"
    & $py -m laptop.dual_bridge `
        --ca $ca --port $port --session-id week7-demo `
        --left-address $left --right-address $right `
        --duration $Seconds --ack-window 32 --progress-interval 1 `
        --report $reportPath `
        2>&1 | ForEach-Object { $_.ToString() } |
        Tee-Object -FilePath $logPath | Out-Host
    $exitCode = $LASTEXITCODE
    $exitCode | Set-Content -LiteralPath (Join-Path $caseDir 'exit-code.txt')
    Write-Host "Exit code: $exitCode"
    [pscustomobject]@{ Directory=$caseDir; Report=$reportPath; ExitCode=$exitCode }
}
```

**直播日志里的 received 是 BLE 回调到达数，processed 是已处理数，acked 是已验证的板端确认数。** 最终 JSON 的 `received` 则沿用“已处理”的含义；`callback_received` 才是回调数。短暂 received > acked 不一定是漏包，需要等正常收尾对账。

## 3. 开场：设备、数据生成和并发代码

录到两块 ESP 的标签及供电方式。可以用充电宝供电，以直观表明通信不依赖 USB 数据；若使用电脑 USB，也说明 USB 只提供电源，业务数据通过 BLE。

**English:**

> This is B07's communication subsystem. Two physical ESP32s generate test packets at ten hertz each. The laptop receives and forwards both streams to Ultra96, and the iPhone receives results directly from the board.
>
> The firmware, authenticated bonds and certificates were provisioned earlier. I will now start a new run and establish fresh BLE connections.

先显示以下短代码段，具体源码阅读清单见第 11 节：

- `firmware/esp32/platformio.ini`：左右设备 ID 1、2。
- `firmware/esp32/src/main.cpp` 的 `loop()`：100 ms 门限，分配序号、生成 32 字节包、调用 BLE notification、记录成功/失败。
- `laptop/dual_bridge.py` 的任务创建段：左右各自的 input/writer task。

**English:**

> Each packet carries a device ID, a boot ID and a sequence number. The values are deterministic dummy data, so we can validate the communication path without using real sensors.
>
> Each device has its own BLE input, queue and TLS connection. Asynchronous tasks allow both streams to make progress while another task is waiting for I/O.

这里的并行是两条独立路径在同一时段并发推进；不要解释为无线电在完全相同的纳秒发射，或 Python 使用了两个 CPU 核心。

## 4. Ultra96：检查并展示真实启动

在 Windows **终端 C** 打开板端控制连接；两跳都保持严格主机密钥验证，交互式输入密码：

```powershell
Set-Location D:\LetThemCook
$b07Proxy = 'ssh -o StrictHostKeyChecking=yes -o BatchMode=no -o ConnectTimeout=20 -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -W "[%h]:%p" yanjie@stujump.comp.nus.edu.sg'
$b07SshOptions = @('-o','Port=22','-o','StrictHostKeyChecking=yes','-o','BatchMode=no','-o','ConnectTimeout=60','-o',"ProxyCommand=$b07Proxy")
ssh @b07SshOptions xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg
```

以下命令在 **Ultra96 的 shell** 执行：

```sh
week7_root=/var/tmp/cg4002-week7-yanjie-20260907
id
hostname
ss -ltnp
ps -u "$(id -u)" -o pid=,args=
```

检查 `127.0.0.1:8888` 和 `127.0.0.1:9999` 是否由本项目的 `ultra96.server` 持有。最后核实的源码目录是 `$week7_root/source-observer-20260921T080754Z`。旧文档里的 PID 不能直接拿来停止进程。

**若服务已运行：** 可以复用并在视频中说明。若确实要拍完整服务冷启动，先按[完整指南的进程身份检查](week7-testing-and-demo-guide.zh-CN.md#5-check-the-board-without-redeploying-or-stopping-it)，核实实际 PID 的属主、`/proc/PID/cwd`、`/proc/PID/cmdline`、证书路径、日志位置和监听端口；仅对核实属于本项目的进程发送 `kill -TERM "$week7_pid"`。先确认正常停止回执及诊断记录完成，再确认两个端口已释放。不要停止他人的共享进程，也不要同时运行两个服务器。

**只在本项目服务已停止且两个端口空闲时启动：**

```sh
week7_root=/var/tmp/cg4002-week7-yanjie-20260907
week7_source="$week7_root/source-observer-20260921T080754Z"
if ! week7_listeners=$(ss -ltnH); then
    printf '%s\n' 'Listener inspection failed; do not start.'
elif printf '%s\n' "$week7_listeners" |
    awk '$4 ~ /:(8888|9999)$/ {found=1} END {exit !found}'; then
    printf '%s\n' 'Port occupied: inspect the existing owner before starting.'
else
    week7_stamp=$(date -u +%Y%m%dT%H%M%SZ)
    cd "$week7_source" &&
    /usr/bin/python3 -u -m ultra96.server \
        --cert "$week7_root/tls/server-cert.pem" \
        --key "$week7_root/tls/server-key.pem" \
        --session-id week7-demo --ingest-port 8888 --gateway-port 9999 \
        --event-log-dir "$week7_root/evidence/B07-video-$week7_stamp"
fi
```

看到 `listening`、`host: 127.0.0.1`、`tls: true`、两个正确端口。前台启动后保持终端 C 打开。目录或证书缺失时停止排查，不要随意改成旧目录或关闭验证。这个前台命令不会替你更新旧 PID 文件。

**English:**

> Ultra96 exposes SSH on port twenty-two. The ingestion and result services listen on loopback ports eight eight eight eight and nine nine nine nine. The laptop and phone use separate authenticated SSH routes and verified TLS connections.

如果实际复用了服务，加一句：

> The board service was already running. Here I am verifying its process and listening ports before connecting the clients.

## 5. 笔记本隧道、BLE 绑定和手机准备

### 5.1 在终端 A 启动笔记本隧道

先在 **终端 B** 检查本地端口是否已有监听：

```powershell
$existingTunnel = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object LocalPort -eq 18889)
$existingTunnel | Select-Object LocalAddress,LocalPort,OwningProcess
```

没有输出才在终端 A 执行下面的启动命令。若已有监听，先核实 `OwningProcess` 对应的命令和目标端口；确实是预期隧道才复用，否则先解决端口冲突。不要盲目启动第二个隧道。

```powershell
Set-Location D:\LetThemCook
python -c 'import subprocess; from tools.ssh_tunnel import tunnel_command; raise SystemExit(subprocess.run(tunnel_command("yanjie@stujump.comp.nus.edu.sg","xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg",18889,8888)).returncode)'
```

使用已验证依赖的 Python；若 B 中选择了专用解释器，在 A 中也使用同一个绝对路径。输入两跳密码，保持终端 A 打开。成功后没有持续输出属于正常情况。`python -m tools.ssh_tunnel` 默认只打印命令；不要把“打印了一条 SSH 命令”当作已启动隧道。`--run` 需要密钥/agent，不能代替这次交互式密码流程。

在 **终端 B** 验证监听和 TLS；本地端口统一使用 18889：

```powershell
Get-NetTCPConnection -State Listen -LocalPort 18889 |
    Select-Object LocalAddress,LocalPort,OwningProcess
& $py -c 'import socket,sys; from common.tls import client_context,TLS_SERVER_NAME; raw=socket.create_connection(("127.0.0.1",18889),timeout=8); tls=client_context(sys.argv[1]).wrap_socket(raw,server_hostname=TLS_SERVER_NAME); print("Verified ingestion TLS:",tls.version()); tls.close()' $ca
if ($LASTEXITCODE -ne 0) { throw 'TLS preflight failed; do not start the capture.' }
```

这个 TLS 探测不发送传感器数据，也不会抢走手机订阅。

### 5.2 两块 ESP 上电，并核实受保护绑定

拍到两块 ESP 上电，然后在 **终端 B** 执行：

```powershell
& $py -m laptop.windows_pairing --address $left
if ($LASTEXITCODE -ne 0) { throw 'ESP 1 authenticated bond check failed.' }
& $py -m laptop.windows_pairing --address $right
if ($LASTEXITCODE -ne 0) { throw 'ESP 2 authenticated bond check failed.' }
```

两条输出都应包含 `authenticated_bond: true` 和各自地址。若尚未绑定，程序会要求配对；先在镜头外完成首次配对，再开始新一轮录制，不要把口令拍进视频。

**绑定成功不是新的 BLE 数据订阅证明。** 下一节启动桥接程序时，才建立新的接收连接并订阅通知；随后用 `ble_connections`、两路实时数据及源端核对共同证明连接正常。

**English:**

> Both ESP32s have authenticated Bluetooth bonds. This check confirms the stored protection level. The next command will establish the actual data connections and subscribe to both streams.

### 5.3 iPhone 建立新的计数会话

保持 iPhone VPN 开启。打开 Unity，点击 **Week 7 Connect / Week 7 Settings**，输入两跳凭据并 Connect。录到 **`Subscribed`、`Received: 0`**。之后保持 Unity 前台，不锁屏、不切应用、不再点击 Connect，直到本段计数记录完毕。

原生应用、板端和笔记本使用 **`week7-demo`**；不要为了给录像命名而改 `session_id`。录像段落用输出目录名区分。

不要同时运行 `laptop.phone_simulator`、`phone.receiver` 或 `tools.rehearse_remote_week7`。它们会作为另一个结果订阅者，替换正在演示的 iPhone。

**English:**

> The iPhone is now subscribed with a received count of zero. It receives results directly from Ultra96 through its own connection; the laptop does not relay results to the phone.

## 6. 核心：两块 ESP 同时发送、电脑同时接收和转发

在 **终端 B** 输入手机当前计数，再运行 60 秒：

```powershell
$phoneBefore = [long](Read-Host 'Phone Received BEFORE this capture')
$capture = Invoke-B07Capture -Name '01-dual-baseline-60s' -Seconds 60
```

不要在 B 中按 Ctrl+C；允许启动、60 秒共同观测和正常排空全部结束。启动和关闭阶段会让总耗时略长于 60 秒。

屏幕中的实际格式如下；这里的数值只是示例，视频里使用真实运行输出：

```text
progress mode=physical phase=observation device=1 received=100 processed=100 acked=98 queue=0 drops=0 errors=0
progress mode=physical phase=observation device=2 received=100 processed=100 acked=99 queue=0 drops=0 errors=0
```

拍到并口述：

1. `mode=physical`，没有 `--mock` 或 `--diagnostic-unprotected`。
2. **device=1 和 device=2 在同一运行期间持续增长**，不需要轮流运行两个接收程序。
3. `received` 增长证明电脑收到了回调；`acked` 增长证明相应数据已转发且板端确认。
4. iPhone 的 `Received` 增长，结果中能看到分别以 **`1:` 和 `2:`** 开头的 ID。标签是 `REST/FIST/OPEN/POINT` 的模拟映射；显示最新值可能跳过中间标签，不能靠逐帧盯屏来数包。
5. `drops=0`、`errors=0` 应持续为零，但最终仍须看报告；`queue=0` 本身不表示所有 ACK 都回来了。

**English:**

> Both device counters are increasing during the same observation period. Received counts show BLE input, and ACK counts show that Ultra96 has accepted the forwarded messages.
>
> The phone is also receiving results from both device IDs. These are live physical inputs, not software-generated mock packets on the laptop.

### 正常结束后：读报告、核对手机，再进行下一段

在 **终端 B** 粘贴以下块。每一次新的正常采集结束后，都重复执行此块；它读取当前 `$capture`，并使用采集前记录的 `$phoneBefore`。

```powershell
$r = Get-Content -LiteralPath $capture.Report -Raw | ConvertFrom-Json
$r | Select-Object clean,mock_input,report_saved,progress_error,common_observation_seconds
$deviceRows = @($r.devices.PSObject.Properties | ForEach-Object {
    $d = $_.Value
    [pscustomobject]@{
        Device=$_.Name; Clean=$d.clean; Protected=$d.protected_ble
        BLEConnections=$d.ble_connections; TLSConnections=$d.transport_connections
        Generated=$d.source.generated; Submitted=$d.source.source_submitted
        BLECallbacks=$d.callback_received; Received=$d.received
        Sent=$d.sent; ACKed=$d.acked
        MissingBLE=$d.source.missing_received; MissingACK=$d.source.missing_acked
        QueueDrops=$d.queue_dropped; StaleDrops=$d.stale_dropped
        Disconnects=$d.disconnects; Unfinished=$d.unfinished
    }
})
$deviceRows | Format-Table Device,Clean,Protected,BLEConnections,TLSConnections,Unfinished -AutoSize
$deviceRows | Format-Table Device,Generated,Submitted,Received,Sent,ACKed -AutoSize
$deviceRows | Format-Table Device,BLECallbacks,MissingBLE,MissingACK,QueueDrops,StaleDrops,Disconnects -AutoSize
$phoneAfter = [long](Read-Host 'Phone Received AFTER final delivery settles')
$phoneDelta = $phoneAfter - $phoneBefore
$eligible = ($capture.ExitCode -eq 0 -and $r.clean -eq $true -and
    $r.mock_input -eq $false -and $r.report_saved -eq $true -and
    $r.devices.'1'.source.complete -eq $true -and
    $r.devices.'2'.source.complete -eq $true)
$expected = $null
if ($eligible) {
    $expected = [long]$r.devices.'1'.source.generated + [long]$r.devices.'2'.source.generated
}
$observation = [pscustomobject]@{
    UTC=(Get-Date).ToUniversalTime().ToString('o')
    ExitCode=$capture.ExitCode; CleanPhysicalCapture=$eligible
    SourceTotal=$expected; PhoneBefore=$phoneBefore; PhoneAfter=$phoneAfter
    PhoneIncrease=$phoneDelta; CountMatch=($eligible -and $phoneDelta -eq $expected)
    PhoneStatus=(Read-Host 'Observed phone status')
    ForegroundNotes=(Read-Host 'Stayed foregrounded? Any interruption?')
}
$observation | Format-List
$observation | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $capture.Directory 'phone-observation.json') -Encoding utf8
```

上面按连接、计数、异常分成三个小表。如果窗口仍太窄，把 `$r.devices.'1' | Format-List` 和 `$r.devices.'2' | Format-List` 分别展示，或把 JSON 在编辑器中格式化查看。不要为了把所有列塞进画面而缩小到不可读。

正常采集要求：退出码 0、`clean: true`、`mock_input: false`、两台 `protected_ble: true`、完整源端审计、所有错误/丢弃/重复/缺口为零、`unfinished: false`。通常每台 BLE/TLS 连接数均为 1。所有验收字段详见[完整测试指南第 7 节](week7-testing-and-demo-guide.zh-CN.md#7-capture-a-complete-physical-run-and-save-its-outcome)。

分别核对每台的 **source.generated = source.source_submitted = source.received = source.acked**，且电脑接收、发送、ACK 计数对应一致。随后核对：

**手机结束计数 − 手机开始计数 = 本次两台 source.generated 之和。**

不要预填“60 秒恰好 1,200”。订阅启动和收尾可能贡献额外样本，实际源端计数才是分母。错误报告、空报告或 `generated: null` 不能按零处理并宣布通过。

**English（用本次实际数值填空）：**

> Device one generated [N1] packets, and device two generated [N2]. For each device, the generated, received and acknowledged counts match, with no missing samples reported.
>
> The phone count increased by [N], matching the combined source total. No packet loss was detected in this connected capture. The phone evidence is an aggregate count, not a saved receipt for every individual result ID.

## 7. 空闲后恢复：不用重新 Connect

保存基线计数后，不再运行发送程序。保持 iPhone 前台和同一订阅至少 **120 秒**，不要按 Connect。这段时间可以放大展示并发代码和报告。记录停止发送和恢复发送的实际时间。

约两秒后显示 `No live result` 是正常的显示过期；状态仍应为 `Subscribed`，计数不减少。它不等于 BLE、SSH 或手机订阅失败。

```powershell
Get-Date -Format o
# Keep the phone foregrounded for at least 120 seconds before the next command.
$phoneBefore = [long](Read-Host 'Phone count before idle-resume capture')
$capture = Invoke-B07Capture -Name '02-idle-resume-60s' -Seconds 60
```

结束后再次执行第 6 节报告/手机核对块。使用手机**增量**，不要把两次运行的累计值直接与第二次源端数量比较。

**English:**

> No data has been sent for at least two minutes. The live label has expired, but the subscription remains active. I will restart the sender without pressing Connect on the phone.
>
> New results have resumed, and the increase in the phone count matches this second capture.

## 8. 单 ESP 断电：单独录故障，再录干净恢复

先保存前两次成功结果。下面是**预期会产生非 clean 报告的故障实验**，不能和正常零丢失验收混为一谈。

```powershell
$capture = Invoke-B07Capture -Name '03-left-power-fault-120s' -Seconds 120
```

1. 等到两行都进入 `phase=observation` 且计数增长。
2. 约 20 秒时，拍到你移除 **ESP 1 的唯一电源**；ESP 2 保持供电。
3. 保持约 20 秒，展示 ESP 1 的输入停顿、错误/重连记录，以及 ESP 2 持续增长。ESP 1 的 ACK 可能短暂排空已有数据，不能把这段排空误认为它断电后还在采样。
4. 恢复 ESP 1 电源，观察它重新出现、接收/ACK 继续增长。不要声称一定在固定秒数内恢复；根据本次实际结果说明。
5. 等 120 秒采集正常结束，保存退出码与报告。**120 秒是采集时长，不是要求断电 120 秒。**

可以查看故障字段，不用这一段计算“无丢失的手机总数”：

```powershell
$fault = Get-Content -LiteralPath $capture.Report -Raw | ConvertFrom-Json
$fault | Select-Object clean,mock_input
$fault.devices.'1' | Format-List clean,ble_connections,disconnects,ble_errors,transport_errors,acked,source_issue,unfinished
$fault.devices.'1'.source | Format-List
$fault.devices.'2' | Format-List clean,ble_connections,disconnects,received,acked
```

断电会改变 boot ID。起止快照不属于同一次启动时，`source.generated` 等字段可能为 `null`，并记录中断/boot 不一致。这是审计拒绝把两个启动混成一次 clean 采集，不是让你把 `null` 当成零。

**English:**

> I am now removing power from ESP one. Its input stops, while the laptop continues receiving acknowledgements for ESP two. This demonstrates independent progress during a device failure.
>
> The interrupted run is expected to fail the clean-capture check. The system reports the interruption instead of hiding it, and it does not replay all outage data.

故障运行结束、两台供电稳定后，开一个全新的正常采集。先记手机开始计数，结束后再执行第 6 节核对块：

```powershell
$phoneBefore = [long](Read-Host 'Phone count before fresh post-fault capture')
$capture = Invoke-B07Capture -Name '04-post-fault-clean-60s' -Seconds 60
```

**English:**

> Both devices are powered again. This fresh capture establishes new source boundaries and verifies normal operation after recovery.

## 9. 手机锁屏恢复，以及可选 VPN 恢复

在**没有发送端运行**时操作：记录计数，锁屏约 20 秒，解锁并返回 Unity，展示 `Paused`。然后点击 Week 7 Settings/Connect，重新输入凭据并 Connect，确认新会话 `Subscribed, Received: 0`。

```powershell
$phoneBefore = [long](Read-Host 'Fresh phone count after manual Connect')
$capture = Invoke-B07Capture -Name '05-after-lock-30s' -Seconds 30
```

结束后执行第 6 节核对块。

**English:**

> Locking the phone intentionally pauses reception and clears the credentials. After returning to the app, I reconnect explicitly. This test verifies manual foreground recovery, not reception while the phone is locked.

如果还要录 VPN 恢复：停止发送后，记录时间，关闭并恢复 iPhone VPN，返回 Unity，按需手动 Connect，再开名为 `06-after-vpn-30s` 的新采集。进入设置同时会使应用失活，所以这一段属于**网络切换与应用生命周期组合操作**，不要描述成“纯网络中断后自动恢复”。最后仍用新的实际计数核对。Windows 隧道中断也可以另开一个故障段，停止你自己的终端 A 隧道再重建，保留非 clean 报告，随后另做正常采集；不要把多种故障同时施加。

## 10. 长时间运行和软件检查

没有时长限制时，建议另外录一段本次 **600 秒连续实物运行**。手机保持前台，镜头/录屏保持连续，可以在运行中讲解源码，但不要切走 iPhone 应用。

```powershell
$phoneBefore = [long](Read-Host 'Phone count before the new 600-second soak')
$capture = Invoke-B07Capture -Name '07-soak-600s' -Seconds 600
```

结束后执行同一核对块。若仅展示历史证据，要明确日期：2026-09-21 更新后十分钟运行是 **6,002 + 6,001 = 12,003**，操作者报告手机 **12,003**；不能说刚才现场完成了十分钟，也不要使用更早运行的 12,004 代替本次数据。原始范围和限制见[更新后实物验收报告](phone-post-update-test-2026-09-21.md)。历史报告也保留了早期未解释的 109 结果短缺及另一项修复前的 16 结果缺失，不能用后来的通过抹去它们。

**English：新测试时**

> This is a new ten-minute physical run. Both devices are currently active. After normal shutdown, I will compare the final source, acknowledgement and phone counts.

**English：只引用旧测试时**

> This is previously recorded evidence from September twenty-first. The ten-minute test generated twelve thousand and three packets, and the operator reported the same total on the phone. It is separate from today's live demonstration.

正式录制前，建议运行并保存软件回归检查。它们补充协议、边界条件和清理逻辑证据，不替代实体设备测试；跳过项要保留原因：

```powershell
& $py -m pytest laptop/tests tests phone/tests -q -ra
pwsh -NoProfile -File phone/tests/run_core_tests.ps1
```

Swift/Apple 相关检查要在 Mac 上执行；固件构建命令和前置依赖见[完整测试指南](week7-testing-and-demo-guide.zh-CN.md)。不要把 Windows 上没有运行的 Apple 测试宣布为通过。

## 11. 源码怎么展示才看得清、讲得明白

在编辑器打开下面的文件，搜索函数名；行号仅作为本次代码版本的定位提示。每次放大一个代码区域，先停留让观众看清，再讲 1–2 句。展示自己的通信逻辑，不必遍历 Unity 生成文件或全部测试文件。

| 画面 | 定位 | 英文口播 |
|---|---|---|
| 固件产生和提交样本 | [main.cpp](../firmware/esp32/src/main.cpp#L397)，`loop()`，尤其传感器分支 | “The firmware allocates a sequence number, serializes the sample and submits a BLE notification. Successful and failed submissions are counted separately.” |
| 包身份和字节格式 | [week7_packet.h](../firmware/esp32/include/week7_packet.h#L16) / [sensor.py](../common/sensor.py#L12) | “The fixed packet format preserves the device, boot and sequence identity across the pipeline.” |
| BLE 接收及保护检查 | [bridge.py](../laptop/bridge.py#L623)，`ble_loop`，随后 `start_notify` | “The receiver checks the device, authenticated bond and MTU before subscribing. The callback copies the bytes into that device's bounded queue.” |
| 两套并发任务 | [dual_bridge.py](../laptop/dual_bridge.py#L83)，两组 `asyncio.create_task` | “There are separate input and writer tasks for both devices. One device waiting for I/O does not require the other device to stop.” |
| 网络发送及 ACK 流水线 | [bridge.py](../laptop/bridge.py#L458)，`_pipeline_epoch` | “Each device can have up to thirty-two messages awaiting acknowledgements. Each ACK must match the expected packet identity.” |
| 源端与接收核对 | [source_audit.py](../laptop/source_audit.py#L149)，`report` | “Source snapshots define the full generated interval, including the first and last samples. We compare that interval with reception and acknowledgements.” |
| 板端接入与模拟结果 | [server.py](../ultra96/server.py#L232)，`_ingest` | “The board validates each message, creates a deterministic test result, and returns an ingestion acknowledgement. That ACK is not a phone receipt.” |
| 手机接收和空闲修复 | [Subscriber.swift](../ios-visualizer/Week7Native/Sources/Week7Transport/Subscriber.swift#L37) | “A complete subscribed connection can remain idle. A partially received frame still has a deadline.” |
| 锁屏暂停 | [IntegrationController.swift](../ios-visualizer/Week7Native/Sources/Week7Bridge/IntegrationController.swift#L20) | “When the app becomes inactive, the client stops and credentials are cleared. Returning to the foreground requires an explicit Connect.” |

若要讲原始字节，可在单独的说明段运行 `python -m tools.week7_demo packet`，但必须说 **“This is an illustrative packet example, not a live hardware capture.”** 主验收不要换成 `--mock`，也不要把单设备 `tools.week7_demo sender` 当作双设备性能测试；它的旧发送路径使用不同的 ACK 窗口。

## 12. 结束、上传和章节

所有采集完成后，拍到本次 `$outRoot` 中每段的 `report.json`、`live.log`、`exit-code.txt` 和正常采集的 `phone-observation.json`。失败段也保留。停止你自己的终端 A 隧道时只在该终端按 Ctrl+C。若本次专门在 C 中启动了板端前台服务，结束它时在 C 中按 Ctrl+C，并核实正常停止和观测记录完成；若复用了已有服务，交接时说明是否继续运行，不要随意结束它。

**English 结尾：**

> The clean runs demonstrate concurrent reception and forwarding from two physical ESP32s, with matching source and acknowledgement counts and a matching aggregate phone count. Separate fault tests show visible interruption and recovery. These results apply to the tested conditions; outage replay and real sensor inference are outside this subsystem demonstration.

最终文件名使用 **`B07_CO_subsystem.mp4`**，视频标题可用 **`B07_CO_subsystem`**。上传 YouTube 时设置 **Unlisted（不公开列出）**，再提交视频链接。Unlisted 允许持链接者观看和转发，不等同于 Private；上传后用未登录窗口核对能播放、源码文字可读、声音清楚。[YouTube 官方隐私设置说明](https://support.google.com/youtube/answer/157177?hl=en)。

可在视频描述添加章节。下面仅为时间模板，**录完后必须换成实际时间**：

```text
00:00 B07 communication subsystem overview
00:45 Firmware and parallel architecture
02:30 Ultra96 and SSH startup
04:00 Authenticated BLE and iPhone subscription
05:00 Concurrent two-ESP live test
06:30 Source, ACK and phone count verification
07:30 Idle and resume test
10:30 Single-ESP power failure and recovery
14:00 Fresh clean capture after recovery
16:00 Phone lock and manual reconnection
18:00 Source-code walkthrough and soak evidence
21:00 Results and limitations
```

YouTube 手动章节要求首项从 `00:00` 开始，至少三个按时间升序排列的章节，每章至少十秒；具体时长以成片为准，章节功能可用性还取决于账号功能权限。[YouTube 官方章节说明](https://support.google.com/youtube/answer/9884579?hl=en)。课程给出的要求是不用幻灯片且源码可读，本文的时长和段落安排是录制建议，不是额外评分规则。
