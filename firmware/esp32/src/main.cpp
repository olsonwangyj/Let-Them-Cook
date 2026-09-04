#include <Arduino.h>
#include <BLE2902.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <esp_system.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>

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
bool notificationsEnabled = false;
bool restartAdvertising = false;
bool bleReady = false;
SemaphoreHandle_t connectionStateMutex = nullptr;

BLEAdvertising* advertising = nullptr;
BLECharacteristic* counterCharacteristic = nullptr;
BLE2902* counterCccd = nullptr;

class ServerCallbacks final : public BLEServerCallbacks {
  void onConnect(BLEServer*) override {
    xSemaphoreTake(connectionStateMutex, portMAX_DELAY);
    clientConnected = true;
    notificationsEnabled = false;
    restartAdvertising = false;
    counterCccd->setNotifications(false);
    const uint32_t counter = notificationCounter;
    xSemaphoreGive(connectionStateMutex);
    Serial.printf("ble_connected boot_id=%lu counter=%lu uptime_ms=%lu\n",
                  static_cast<unsigned long>(bootId),
                  static_cast<unsigned long>(counter),
                  static_cast<unsigned long>(millis()));
  }

  void onDisconnect(BLEServer*) override {
    xSemaphoreTake(connectionStateMutex, portMAX_DELAY);
    clientConnected = false;
    notificationsEnabled = false;
    counterCccd->setNotifications(false);
    restartAdvertising = true;
    const uint32_t counter = notificationCounter;
    xSemaphoreGive(connectionStateMutex);
    Serial.printf("ble_disconnected boot_id=%lu counter=%lu uptime_ms=%lu\n",
                  static_cast<unsigned long>(bootId),
                  static_cast<unsigned long>(counter),
                  static_cast<unsigned long>(millis()));
  }
};

class CccdCallbacks final : public BLEDescriptorCallbacks {
  void onWrite(BLEDescriptor*) override {
    xSemaphoreTake(connectionStateMutex, portMAX_DELAY);
    notificationsEnabled = clientConnected && counterCccd->getNotifications();
    xSemaphoreGive(connectionStateMutex);
  }
};

}  // namespace

void setup() {
  Serial.begin(115200);
  bootId = esp_random();
  lastReportMs = millis();
  lastNotificationMs = lastReportMs;
  connectionStateMutex = xSemaphoreCreateMutex();
  if (connectionStateMutex == nullptr) {
    Serial.println("ble_state_mutex_create_failed");
    return;
  }

  BLEDevice::init(kDeviceName);
  BLEServer* server = BLEDevice::createServer();
  server->setCallbacks(new ServerCallbacks());

  BLEService* service = server->createService(kServiceUuid);
  counterCharacteristic = service->createCharacteristic(
      kCounterCharacteristicUuid, BLECharacteristic::PROPERTY_NOTIFY);
  counterCccd = new BLE2902();
  counterCccd->setCallbacks(new CccdCallbacks());
  counterCharacteristic->addDescriptor(counterCccd);
  service->start();

  advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(kServiceUuid);
  advertising->setScanResponse(true);
  advertising->start();
  bleReady = true;
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

  if (!bleReady) {
    delay(1);
    return;
  }

  bool shouldRestartAdvertising = false;
  uint32_t advertisingCounter = 0;
  xSemaphoreTake(connectionStateMutex, portMAX_DELAY);
  if (restartAdvertising && !clientConnected) {
    restartAdvertising = false;
    shouldRestartAdvertising = true;
    advertisingCounter = notificationCounter;
  }
  xSemaphoreGive(connectionStateMutex);
  if (shouldRestartAdvertising) {
    advertising->start();
    Serial.printf("ble_advertising_restarted boot_id=%lu counter=%lu uptime_ms=%lu\n",
                  static_cast<unsigned long>(bootId),
                  static_cast<unsigned long>(advertisingCounter),
                  static_cast<unsigned long>(nowMs));
  }

  bool notificationSubmitted = false;
  uint32_t submittedCounter = 0;
  xSemaphoreTake(connectionStateMutex, portMAX_DELAY);
  if (clientConnected && notificationsEnabled &&
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
    submittedCounter = notificationCounter;
    ++notificationCounter;
    lastNotificationMs = nowMs;
    notificationSubmitted = true;
  }
  xSemaphoreGive(connectionStateMutex);
  if (notificationSubmitted) {
    Serial.printf("ble_notify_submitted boot_id=%lu counter=%lu uptime_ms=%lu\n",
                  static_cast<unsigned long>(bootId),
                  static_cast<unsigned long>(submittedCounter),
                  static_cast<unsigned long>(nowMs));
  }

  delay(1);
}
