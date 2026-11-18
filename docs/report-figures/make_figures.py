import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams["font.family"] = "DejaVu Sans"
BLUE, GREEN, ORANGE, PURPLE, GREY = "#dbe8f6", "#e2f0d9", "#fde9d4", "#ece3f4", "#f2f2f2"
EDGE = "#3a3a3a"

def box(ax, x, y, w, h, title, lines=(), fc=GREY, fs=10):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=fc, ec=EDGE, lw=1.2))
    ax.text(x + w / 2, y + h - 0.22, title, ha="center", va="top", fontsize=fs, weight="bold")
    for i, line in enumerate(lines):
        ax.text(x + w / 2, y + h - 0.62 - i * 0.34, line, ha="center", va="top", fontsize=fs - 2)

def arrow(ax, x1, y1, x2, y2, both=False, color=EDGE, lw=1.6, ls="-"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="<|-|>" if both else "-|>", color=color, lw=lw, ls=ls,
                                shrinkA=2, shrinkB=2))

# Figure 7a: architecture
fig, ax = plt.subplots(figsize=(11, 7.2))
ax.set_xlim(0, 16); ax.set_ylim(-0.5, 10.5); ax.axis("off")

box(ax, 4.2, 7.1, 7.6, 3.2, "Ultra96 (PYNQ board)", fc=BLUE, fs=11)
box(ax, 4.5, 7.35, 3.5, 2.3, "Communications service", ["one asyncio event loop, TLS", "ingest :8888, gateway :9999", "bound to 127.0.0.1 only"], fc="white", fs=9.5)
box(ax, 8.6, 7.35, 2.9, 2.3, "AI worker process", ["model on the FPGA", "connects to the", "service's socket"], fc="white", fs=9.5)
arrow(ax, 8.6, 8.5, 8.0, 8.5)
ax.text(8.3, 8.25, "samples →"+chr(10)+"← results", ha="center", va="top", fontsize=6.5, color="#555")
ax.text(8.3, 8.75, "Unix\nsocket", ha="center", va="bottom", fontsize=7.5)

box(ax, 5.6, 4.3, 4.8, 1.6, "NUS jump host (SSH)", ["reached only with the NUS VPN", "relays ciphertext only"], fc=GREY, fs=10)

box(ax, 0.2, 0.3, 2.9, 3.0, "Two sensor gloves", ["FireBeetle ESP32", "left = device 1", "right = device 2", "50 samples/s each"], fc=GREEN, fs=10)
box(ax, 4.0, 0.3, 4.2, 3.0, "Laptop", ["BLE central: connects to each glove", "one relay per glove: link, queue, TLS", "OpenSSH local forwards", "127.0.0.1:18889 → board :8888"], fc=ORANGE, fs=10)
box(ax, 10.6, 0.3, 5.2, 3.0, "Phone (iOS)", ["Swift client: SwiftNIO SSH + TLS", "nested SSH channels, no listening port", "Unity game polls C functions", "each frame (CommsNextHandEvent)"], fc=PURPLE, fs=10)

arrow(ax, 4.0, 1.8, 3.1, 1.8)
ax.text(3.55, 2.0, "BLE"+chr(10)+"samples →", ha="center", va="bottom", fontsize=8)
ax.text(3.55, 1.5, "LE Secure\nConnections", ha="center", va="top", fontsize=7.5, color="#555")

arrow(ax, 7.0, 3.3, 7.0, 4.3); arrow(ax, 7.0, 5.9, 6.6, 7.35)
ax.text(4.75, 3.8, "SSH (2 hops) + TLS\nSENSOR_BATCH  ↑\nINGEST_ACK  ↓", ha="center", va="center", fontsize=8.5)
arrow(ax, 12.0, 3.3, 9.6, 4.3); arrow(ax, 9.0, 5.9, 7.4, 7.35)
ax.text(13.0, 4.6, "SSH (2 hops) + TLS\nSUBSCRIBE  ↑\nGESTURE_RESULT, HAND_EVENT  ↓", ha="center", va="center", fontsize=8.5)

ax.text(8.0, -0.35, "Arrows point from the side that opens each connection; labels give the data direction."+chr(10)+"The laptop and the phone both open their remote connections towards the Ultra96.",
        ha="center", fontsize=8, style="italic", color="#444")
fig.savefig(r"D:\LetThemCook\docs\report-figures\fig7a-comms-architecture.png", dpi=220, bbox_inches="tight")

# Figure 7b: one sample, end to end
lanes = ["Glove", "Laptop relay", "Ultra96 service", "AI worker (FPGA)", "Phone / Unity"]
xs = [0.9, 3.9, 7.1, 10.3, 13.5]
fig, ax = plt.subplots(figsize=(11, 7.6))
ax.set_xlim(-0.4, 15.4); ax.set_ylim(-1.0, 10.6); ax.axis("off")
cols = [GREEN, ORANGE, BLUE, BLUE, PURPLE]
for x, name, c in zip(xs, lanes, cols):
    ax.add_patch(FancyBboxPatch((x - 1.25, 9.6), 2.5, 0.7, boxstyle="round,pad=0.02", fc=c, ec=EDGE))
    ax.text(x, 9.95, name, ha="center", va="center", fontsize=9.5, weight="bold")
    ax.plot([x, x], [0.0, 9.6], color="#999", lw=1, ls="--")

def msg(y, a, b, text, dashed=False):
    arrow(ax, xs[a], y, xs[b], y, ls="--" if dashed else "-")
    ax.text((xs[a] + xs[b]) / 2, y + 0.12, text, ha="center", va="bottom", fontsize=8.5)

def note(y, i, text):
    ax.text(xs[i], y, text, ha="center", va="center", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.25", fc="#fffbe6", ec="#b8a96a"))

msg(9.0, 0, 1, "notification: 1–6 × 40-byte packets")
note(8.45, 0, "seq given when the\nsample leaves the queue")
msg(7.6, 1, 2, "SENSOR_BATCH (device_id, boot_id, seq)")
msg(6.8, 2, 3, "sample line (nonblocking enqueue)")
msg(6.0, 2, 1, "INGEST_ACK accepted / duplicate")
note(5.35, 2, "ACK = accepted by the service,\nnot processed by the AI")
msg(4.55, 3, 2, "prediction → GESTURE_RESULT", dashed=True)
note(3.95, 2, "GESTURE_RESULT check: known glove and boot,"+chr(10)+"seq ≤ highest accepted, new result ID")
msg(3.0, 3, 2, "HAND_EVENT", dashed=True)
note(2.3, 2, "HAND_EVENT check: worker epoch, exact source"+chr(10)+"sample, prediction source ≤ 0.5 s old,"+chr(10)+"rising event_seq, state lease and transitions")
msg(1.35, 2, 4, "GESTURE_RESULT / HAND_EVENT")
note(0.6, 4, "phone drops repeated result IDs and"+chr(10)+"repeated or out-of-order events;"+chr(10)+"expires states without refresh")
ax.text(7.3, -0.55, "The (device_id, boot_id, seq) triple names the sample on every hop; the ACK path and the result path are independent;"+chr(10)+"dashed arrows are asynchronous.",
        ha="center", fontsize=8, style="italic", color="#444")
fig.savefig(r"D:\LetThemCook\docs\report-figures\fig7b-sample-sequence.png", dpi=220, bbox_inches="tight")
print("ok")
