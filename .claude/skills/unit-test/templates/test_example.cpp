// 단위 테스트 작성 예시 (GoogleTest). 모든 테스트 함수는 아래 Doxygen 항목을 갖는다.
#include <gtest/gtest.h>

#include "buffer/buffer.h"

/**
 * @test    Buffer_Write_FillsToExactCapacity
 * @brief   [목적] 용량과 같은 길이(64)의 쓰기가 성공하고 버퍼가 가득 차는지 확인한다.
 *          경계값 분석: 용량 경계(cap)
 * @trace   UT-012 -> DD-004 (SWR-FUN-007)
 *
 * @par 입력값
 *   - 용량 64인 빈 Buffer
 *   - data = 유효한 64바이트 배열, len = 64
 * @par 절차
 *   1. 용량 64로 Buffer를 초기화한다.
 *   2. write(data, 64)를 호출한다.
 *   3. 반환값과 free_space()를 확인한다.
 * @par 예상 출력값
 *   - write()의 반환값 == Status::Ok
 *   - free_space() == 0
 */
TEST(Buffer_Write, FillsToExactCapacity) {
    Buffer buf(64U);
    uint8_t data[64] = {};

    Status st = buf.write(data, 64U);

    EXPECT_EQ(st, Status::Ok);
    EXPECT_EQ(buf.free_space(), 0U);
}
