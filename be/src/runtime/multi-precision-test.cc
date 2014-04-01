// Copyright 2012 Cloudera Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <string>
#include <gtest/gtest.h>

#include <boost/math/constants/constants.hpp>
#include "runtime/multi-precision.h"

using namespace boost::multiprecision;
using namespace std;

namespace impala {

// Simple example of adding and subtracting numbers that use more than
// 64 bits.
TEST(MultiPrecisionIntTest, Example) {
  int128_t v128;
  v128 += int128_t(numeric_limits<uint64_t>::max());
  v128 += int128_t(numeric_limits<uint64_t>::max());

  v128 -= int128_t(numeric_limits<uint64_t>::max());
  EXPECT_EQ(v128, numeric_limits<uint64_t>::max());

  v128 -= int128_t(numeric_limits<uint64_t>::max());
  EXPECT_EQ(v128, 0);

  int96_t v96;
  v96 += int96_t(numeric_limits<uint64_t>::max());
  v96 += int96_t(numeric_limits<uint64_t>::max());

  v96 -= int96_t(numeric_limits<uint64_t>::max());
  EXPECT_EQ(v96, numeric_limits<uint64_t>::max());

  v96 -= int96_t(numeric_limits<uint64_t>::max());
  EXPECT_EQ(v96, 0);
}

// Example taken from:
// http://www.boost.org/doc/libs/1_55_0/libs/multiprecision/doc/html/boost_multiprecision/tut/floats/fp_eg/aos.html

template<typename T> inline T area_of_a_circle(T r) {
   using boost::math::constants::pi;
   return pi<T>() * r * r;
}

TEST(MultiPrecisionFloatTest, Example) {
  const float r_f(float(123) / 100);
  const float a_f = area_of_a_circle(r_f);

  const double r_d(double(123) / 100);
  const double a_d = area_of_a_circle(r_d);

  const cpp_dec_float_50 r_mp(cpp_dec_float_50(123) / 100);
  const cpp_dec_float_50 a_mp = area_of_a_circle(r_mp);

  stringstream ss;

  // Verify the results at different precisions.
  ss.str("");
  ss << setprecision(numeric_limits<float>::digits10)
     << a_f;
  EXPECT_EQ(ss.str(), "4.75292");

  ss.str("");
  ss << std::setprecision(std::numeric_limits<double>::digits10)
     << a_d;
  EXPECT_EQ(ss.str(), "4.752915525616");

  ss.str("");
  ss << std::setprecision(std::numeric_limits<cpp_dec_float_50>::digits10)
     << a_mp;
  EXPECT_EQ(ss.str(), "4.7529155256159981904701331745635599135018975843146");
}

}

int main(int argc, char **argv) {
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}

