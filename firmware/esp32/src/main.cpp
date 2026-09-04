#include <Arduino.h>
#include <esp_system.h>

namespace {

constexpr uint32_t kReportIntervalMs = 1000;

uint32_t bootId = 0;
uint32_t sequence = 0;
uint32_t lastReportMs = 0;

}  // namespace

void setup() {
  Serial.begin(115200);
  bootId = esp_random();
  lastReportMs = millis();
}

void loop() {
  const uint32_t nowMs = millis();

  if (static_cast<uint32_t>(nowMs - lastReportMs) >= kReportIntervalMs) {
    lastReportMs = nowMs;
    Serial.printf("alive boot_id=%lu sequence=%lu uptime_ms=%lu\n",
                  static_cast<unsigned long>(bootId),
                  static_cast<unsigned long>(sequence),
                  static_cast<unsigned long>(nowMs));
    ++sequence;
  }

  delay(1);
}
