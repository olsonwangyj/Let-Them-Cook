#include <cassert>
#include <cstdint>
#include <cstdio>
#include "week7_gatts_control.h"

struct FakeWrite {
  uint16_t conn_id, handle, offset, len;
  bool is_prep;
  uint8_t* value;
};
union FakeParams {
  FakeWrite write;
  struct { uint16_t conn_id; uint8_t flag; } exec_write;
};

int main() {
  using week7::ProbeWriteStatus;
  // The parser must not inspect write fields for another union variant or null.
  FakeParams execute = {};
  execute.exec_write.conn_id = 2;
  execute.exec_write.flag = 1;
  assert(week7::parseMtuControlWrite(false, &execute, 123).status == ProbeWriteStatus::Ignored);
  assert(week7::parseMtuControlWrite(false, static_cast<FakeParams*>(nullptr), 123).status == ProbeWriteStatus::Ignored);
  assert(week7::parseMtuControlWrite(true, static_cast<FakeParams*>(nullptr), 123).status == ProbeWriteStatus::Ignored);

  uint8_t payload[] = {2, 2};  // 514 bytes, little endian.
  FakeParams request = {};
  request.write = {7, 123, 0, 2, false, payload};
  // Even bytes that resemble a valid write must not be parsed for another event.
  assert(week7::parseMtuControlWrite(false, &request, 123).status == ProbeWriteStatus::Ignored);
  auto parsed = week7::parseMtuControlWrite(true, &request, 123);
  assert(parsed.status == ProbeWriteStatus::Valid);
  assert(parsed.connectionId == 7 && parsed.requestedLength == 514 && parsed.inputLength == 2);
  assert(week7::parseMtuControlWrite(true, &request, 124).status == ProbeWriteStatus::Ignored);
  request.write.is_prep = true;
  assert(week7::parseMtuControlWrite(true, &request, 123).status == ProbeWriteStatus::Malformed);
  request.write.is_prep = false; request.write.offset = 1;
  assert(week7::parseMtuControlWrite(true, &request, 123).status == ProbeWriteStatus::Malformed);
  request.write.offset = 0; request.write.len = 1;
  assert(week7::parseMtuControlWrite(true, &request, 123).status == ProbeWriteStatus::Malformed);
  request.write.len = 3;
  assert(week7::parseMtuControlWrite(true, &request, 123).status == ProbeWriteStatus::Malformed);
  request.write.len = 2; request.write.value = nullptr;
  assert(week7::parseMtuControlWrite(true, &request, 123).status == ProbeWriteStatus::Malformed);
  std::puts("PASS GATT event/union and malformed-write regression");
}
