#include <Arduino.h>
#include <BLE2902.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <esp_gatt_common_api.h>
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
constexpr char kMtuProbeControlCharacteristicUuid[] =
    "6e1c0003-7a45-4dc4-b678-3f2d5a9c1001";
constexpr char kMtuProbeCharacteristicUuid[] =
    "6e1c0004-7a45-4dc4-b678-3f2d5a9c1001";
constexpr uint16_t kAttValueOverheadBytes = 3;
constexpr size_t kMtuProbePayloadCapacity =
    ESP_GATT_MAX_MTU_SIZE - kAttValueOverheadBytes;

uint32_t bootId = 0;
uint32_t sequence = 0;
uint32_t lastReportMs = 0;
uint32_t notificationCounter = 0;
uint32_t lastNotificationMs = 0;
bool clientConnected = false;
bool notificationsEnabled = false;
bool mtuProbeNotificationsEnabled = false;
bool restartAdvertising = false;
bool bleReady = false;
bool mtuProbeRequestPending = false;
uint16_t pendingMtuProbeLength = 0;
uint16_t negotiatedMtu = ESP_GATT_DEF_BLE_MTU_SIZE;
uint16_t mtuConnectionId = 0;
SemaphoreHandle_t connectionStateMutex = nullptr;

BLEAdvertising* advertising = nullptr;
BLECharacteristic* counterCharacteristic = nullptr;
BLE2902* counterCccd = nullptr;
BLECharacteristic* mtuProbeControlCharacteristic = nullptr;
BLECharacteristic* mtuProbeCharacteristic = nullptr;
BLE2902* mtuProbeCccd = nullptr;

class ServerCallbacks final : public BLEServerCallbacks {
  void onConnect(BLEServer*) override {
    xSemaphoreTake(connectionStateMutex, portMAX_DELAY);
    clientConnected = true;
    notificationsEnabled = false;
    mtuProbeNotificationsEnabled = false;
    mtuProbeRequestPending = false;
    pendingMtuProbeLength = 0;
    negotiatedMtu = ESP_GATT_DEF_BLE_MTU_SIZE;
    restartAdvertising = false;
    counterCccd->setNotifications(false);
    mtuProbeCccd->setNotifications(false);
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
    mtuProbeNotificationsEnabled = false;
    mtuProbeRequestPending = false;
    pendingMtuProbeLength = 0;
    negotiatedMtu = ESP_GATT_DEF_BLE_MTU_SIZE;
    counterCccd->setNotifications(false);
    mtuProbeCccd->setNotifications(false);
    restartAdvertising = true;
    const uint32_t counter = notificationCounter;
    xSemaphoreGive(connectionStateMutex);
    Serial.printf("ble_disconnected boot_id=%lu counter=%lu uptime_ms=%lu\n",
                  static_cast<unsigned long>(bootId),
                  static_cast<unsigned long>(counter),
                  static_cast<unsigned long>(millis()));
  }

  void onMtuChanged(BLEServer*, esp_ble_gatts_cb_param_t* param) override {
    xSemaphoreTake(connectionStateMutex, portMAX_DELAY);
    negotiatedMtu = param->mtu.mtu;
    mtuConnectionId = param->mtu.conn_id;
    xSemaphoreGive(connectionStateMutex);
    Serial.printf("ble_mtu_changed conn_id=%u negotiated_mtu=%u uptime_ms=%lu\n",
                  static_cast<unsigned int>(param->mtu.conn_id),
                  static_cast<unsigned int>(param->mtu.mtu),
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

class MtuProbeCccdCallbacks final : public BLEDescriptorCallbacks {
  void onWrite(BLEDescriptor*) override {
    xSemaphoreTake(connectionStateMutex, portMAX_DELAY);
    mtuProbeNotificationsEnabled =
        clientConnected && mtuProbeCccd->getNotifications();
    xSemaphoreGive(connectionStateMutex);
  }
};

class MtuProbeControlCallbacks final : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic*, esp_ble_gatts_cb_param_t* param) override {
    const uint16_t requestLength = param->write.len;
    if (param->write.len != sizeof(uint16_t)) {
      Serial.printf("mtu_probe_rejected reason=malformed request_bytes=%u\n",
                    static_cast<unsigned int>(requestLength));
      return;
    }

    const uint16_t requestedLength =
        static_cast<uint16_t>(param->write.value[0]) |
        (static_cast<uint16_t>(param->write.value[1]) << 8);
    xSemaphoreTake(connectionStateMutex, portMAX_DELAY);
    const bool ready = clientConnected && mtuProbeNotificationsEnabled;
    const bool pending = mtuProbeRequestPending;
    if (ready && !pending) {
      pendingMtuProbeLength = requestedLength;
      mtuProbeRequestPending = true;
    }
    xSemaphoreGive(connectionStateMutex);

    if (!ready) {
      Serial.printf("mtu_probe_rejected reason=not_ready requested_length=%u\n",
                    static_cast<unsigned int>(requestedLength));
    } else if (pending) {
      Serial.printf("mtu_probe_rejected reason=pending requested_length=%u\n",
                    static_cast<unsigned int>(requestedLength));
    }
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
  const esp_err_t localMtuResult = BLEDevice::setMTU(ESP_GATT_MAX_MTU_SIZE);
  Serial.printf("ble_local_mtu_configured mtu=%u return_code=%d\n",
                static_cast<unsigned int>(ESP_GATT_MAX_MTU_SIZE),
                static_cast<int>(localMtuResult));
  BLEServer* server = BLEDevice::createServer();
  server->setCallbacks(new ServerCallbacks());

  BLEService* service = server->createService(kServiceUuid);
  counterCharacteristic = service->createCharacteristic(
      kCounterCharacteristicUuid, BLECharacteristic::PROPERTY_NOTIFY);
  counterCccd = new BLE2902();
  counterCccd->setCallbacks(new CccdCallbacks());
  counterCharacteristic->addDescriptor(counterCccd);
  mtuProbeControlCharacteristic = service->createCharacteristic(
      kMtuProbeControlCharacteristicUuid, BLECharacteristic::PROPERTY_WRITE);
  mtuProbeControlCharacteristic->setCallbacks(new MtuProbeControlCallbacks());
  mtuProbeCharacteristic = service->createCharacteristic(
      kMtuProbeCharacteristicUuid, BLECharacteristic::PROPERTY_NOTIFY);
  mtuProbeCccd = new BLE2902();
  mtuProbeCccd->setCallbacks(new MtuProbeCccdCallbacks());
  mtuProbeCharacteristic->addDescriptor(mtuProbeCccd);
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

  bool processMtuProbeRequest = false;
  uint16_t requestedMtuProbeLength = 0;
  uint16_t observedMtu = ESP_GATT_DEF_BLE_MTU_SIZE;
  bool probeReady = false;
  xSemaphoreTake(connectionStateMutex, portMAX_DELAY);
  if (mtuProbeRequestPending) {
    processMtuProbeRequest = true;
    requestedMtuProbeLength = pendingMtuProbeLength;
    observedMtu = negotiatedMtu;
    probeReady = clientConnected && mtuProbeNotificationsEnabled;
    mtuProbeRequestPending = false;
  }
  xSemaphoreGive(connectionStateMutex);

  if (processMtuProbeRequest) {
    const uint16_t mtuAllowedLength =
        observedMtu > kAttValueOverheadBytes
            ? observedMtu - kAttValueOverheadBytes
            : 0;
    const uint16_t allowedLength =
        min<uint16_t>(mtuAllowedLength, kMtuProbePayloadCapacity);
    if (!probeReady) {
      Serial.printf("mtu_probe_rejected reason=not_ready requested_length=%u "
                    "negotiated_mtu=%u allowed_length=%u\n",
                    static_cast<unsigned int>(requestedMtuProbeLength),
                    static_cast<unsigned int>(observedMtu),
                    static_cast<unsigned int>(allowedLength));
    } else if (requestedMtuProbeLength > allowedLength) {
      Serial.printf("mtu_probe_rejected requested_length=%u negotiated_mtu=%u "
                    "allowed_length=%u\n",
                    static_cast<unsigned int>(requestedMtuProbeLength),
                    static_cast<unsigned int>(observedMtu),
                    static_cast<unsigned int>(allowedLength));
    } else {
      uint8_t payload[kMtuProbePayloadCapacity];
      for (uint16_t index = 0; index < requestedMtuProbeLength; ++index) {
        payload[index] = static_cast<uint8_t>(index & 0xFF);
      }
      xSemaphoreTake(connectionStateMutex, portMAX_DELAY);
      const bool stillReady = clientConnected && mtuProbeNotificationsEnabled;
      if (stillReady) {
        mtuProbeCharacteristic->setValue(payload, requestedMtuProbeLength);
        mtuProbeCharacteristic->notify();
      }
      xSemaphoreGive(connectionStateMutex);
      if (stillReady) {
        Serial.printf("mtu_probe_submitted requested_length=%u negotiated_mtu=%u "
                      "allowed_length=%u boot_id=%lu uptime_ms=%lu\n",
                      static_cast<unsigned int>(requestedMtuProbeLength),
                      static_cast<unsigned int>(observedMtu),
                      static_cast<unsigned int>(allowedLength),
                      static_cast<unsigned long>(bootId),
                      static_cast<unsigned long>(nowMs));
      } else {
        Serial.printf("mtu_probe_rejected reason=not_ready requested_length=%u "
                      "negotiated_mtu=%u allowed_length=%u\n",
                      static_cast<unsigned int>(requestedMtuProbeLength),
                      static_cast<unsigned int>(observedMtu),
                      static_cast<unsigned int>(allowedLength));
      }
    }
  }

  delay(1);
}
