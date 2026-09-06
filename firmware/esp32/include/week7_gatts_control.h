#pragma once

#include <stdint.h>

namespace week7 {

enum class ProbeWriteStatus { Ignored, Malformed, Valid };
struct ProbeWrite {
  ProbeWriteStatus status;
  uint16_t connectionId;
  uint16_t requestedLength;
  uint16_t inputLength;
};

// ESP GATTS callbacks use a union: only an actual WRITE event may inspect write.
// Template parameters permit the same guard/parser to run against a host union.
template <typename EventParameters>
ProbeWrite parseMtuControlWrite(bool isWriteEvent, const EventParameters* param,
                               uint16_t controlHandle) {
  if (!isWriteEvent || param == nullptr) {
    return {ProbeWriteStatus::Ignored, 0, 0, 0};
  }
  const auto& write = param->write;
  if (write.handle != controlHandle) {
    return {ProbeWriteStatus::Ignored, 0, 0, 0};
  }
  if (write.len != 2 || write.offset != 0 || write.is_prep || write.value == nullptr) {
    return {ProbeWriteStatus::Malformed, write.conn_id, 0, write.len};
  }
  const uint16_t requested = static_cast<uint16_t>(write.value[0]) |
      (static_cast<uint16_t>(write.value[1]) << 8);
  return {ProbeWriteStatus::Valid, write.conn_id, requested, write.len};
}

}  // namespace week7
