#include <Arduino.h>
#include <BLE2902.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <esp_system.h>

namespace {

constexpr uint32_t kReportIntervalMs = 1000;
constexpr uint32_t kNotificationIntervalMs = 100;
constexpr char kDeviceName[] = "LTC-W7";
constexpr char kServiceUuid[] = "6e1c0001-7a45-4dc4-b678-3f2d5a9c1001";
constexpr char kCounterCharacteristicUuid[] =
    "6e1c0002-7a45-4dc4-b678-3f2d5a9c1001";

uint32_t bootId = 0;
uint32_t sequence = 0;
uint32_t lastReportMs = 0;
uint32_t notificationCounter = 0;
uint32_t lastNotificationMs = 0;
bool clientConnected = false;
bool restartAdvertising = false;

BLEAdvertising* advertising = nullptr;
BLECharacteristic* counterCharacteristic = nullptr;
BLE2902* counterCccd = nullptr;

class ServerCallbacks final : public BLEServerCallbacks {
  void onConnect(BLEServer*) override {
    clientConnected = true;
    Serial.printf("ble_connected boot_id=%lu counter=%lu uptime_ms=%lu\n",
                  static_cast<unsigned long>(bootId),
                  static_cast<unsigned long>(notificationCounter),
                  static_cast<unsigned long>(millis()));
  }

  void onDisconnect(BLEServer*) override {
    clientConnected = false;
    restartAdvertising = true;
    Serial.printf("ble_disconnected boot_id=%lu counter=%lu uptime_ms=%lu\n",
                  static_cast<unsigned long>(bootId),
                  static_cast<unsigned long>(notificationCounter),
                  static_cast<unsigned long>(millis()));
  }
};

}  // namespace

void setup() {
  Serial.begin(115200);
  bootId = esp_random();
  lastReportMs = millis();
  lastNotificationMs = lastReportMs;

  BLEDevice::init(kDeviceName);
  BLEServer* server = BLEDevice::createServer();
  server->setCallbacks(new ServerCallbacks());

  BLEService* service = server->createService(kServiceUuid);
  counterCharacteristic = service->createCharacteristic(
      kCounterCharacteristicUuid, BLECharacteristic::PROPERTY_NOTIFY);
  counterCccd = new BLE2902();
  counterCharacteristic->addDescriptor(counterCccd);
  service->start();

  advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(kServiceUuid);
  advertising->setScanResponse(true);
  advertising->start();
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

  if (restartAdvertising) {
    restartAdvertising = false;
    advertising->start();
    Serial.printf("ble_advertising_restarted boot_id=%lu counter=%lu uptime_ms=%lu\n",
                  static_cast<unsigned long>(bootId),
                  static_cast<unsigned long>(notificationCounter),
                  static_cast<unsigned long>(nowMs));
  }

  if (clientConnected && counterCccd->getNotifications() &&
      static_cast<uint32_t>(nowMs - lastNotificationMs) >=
          kNotificationIntervalMs) {
    uint8_t payload[4] = {
        static_cast<uint8_t>(notificationCounter & 0xFF),
        static_cast<uint8_t>((notificationCounter >> 8) & 0xFF),
        static_cast<uint8_t>((notificationCounter >> 16) & 0xFF),
        static_cast<uint8_t>((notificationCounter >> 24) & 0xFF),
    };
    counterCharacteristic->setValue(payload, sizeof(payload));
    counterCharacteristic->notify();
    Serial.printf("ble_notify_submitted boot_id=%lu counter=%lu uptime_ms=%lu\n",
                  static_cast<unsigned long>(bootId),
                  static_cast<unsigned long>(notificationCounter),
                  static_cast<unsigned long>(nowMs));
    ++notificationCounter;
    lastNotificationMs = nowMs;
  }

  delay(1);
}
