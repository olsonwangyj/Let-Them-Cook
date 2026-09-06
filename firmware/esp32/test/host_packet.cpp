// Compile/run on a host; expected byte strings live in the independent fixtures.
#include <cassert>
#include <cstdio>
#include "week7_packet.h"
#include "week7_security.h"

static void printPacket(const uint8_t* bytes) {
  for (size_t i = 0; i < week7::kPacketSize; ++i) std::printf("%02x", bytes[i]);
  std::printf("\n");
}

int main() {
  uint8_t output[32] = {};
  assert(week7::serializeDummyPacket(output, sizeof(output), 2, 0x78563412, 42, 0x01020304));
  printPacket(output);
  const int16_t extremes[8] = {-32768, 32767, -1, 0, 1, 255, 256, -256};
  assert(week7::serializePacket(output, sizeof(output), 1, 0xffffffff, 0xffffffff, 0, extremes));
  printPacket(output);
  assert(!week7::serializePacket(output, 31, 1, 0, 0, 0, extremes));
  assert(!week7::serializePacket(output, 32, 0, 0, 0, 0, extremes));
  assert(!week7::serializePacket(output, 32, 3, 0, 0, 0, extremes));
  assert(!week7::serializePacket(nullptr, 32, 1, 0, 0, 0, extremes));
  assert(!week7::serializePacket(output, 32, 1, 0, 0, 0, nullptr));
  assert(week7::dummyValue(0, 0) == -1000);
  assert(week7::dummyValue(1999, 7) == 1069);
  assert(week7::dummyValue(2000, 0) == -1000);
  assert(week7::dummyValue(0xffffffff, 7) == 365);

  // A successful callback lacking either SC, MITM or bonding must stay closed.
  assert(week7::isAuthenticated(true, 0x0d));
  assert(!week7::isAuthenticated(false, 0x0d));
  assert(!week7::isAuthenticated(true, 0x09));
  assert(!week7::isAuthenticated(true, 0x05));
  assert(!week7::isAuthenticated(true, 0x0c));
  assert(!week7::canNotify(true, true, false, false));
  assert(week7::canNotify(true, true, true, false));
  assert(!week7::canNotify(false, true, true, false));
  assert(!week7::canNotify(true, false, true, false));
  assert(week7::canNotify(true, true, false, true));
  assert(!week7::canNotify(false, true, false, true));
  assert(!week7::sensorFitsMtu(34));
  assert(week7::sensorFitsMtu(35));
  assert(week7::sensorFitsMtu(517));
}
