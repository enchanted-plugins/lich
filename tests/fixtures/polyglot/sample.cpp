// Polyglot fixture — use-after-move.
// `s` is moved into `sink` on line 11; read again on line 12 is undefined.
// Parses clean; clang-tidy bugprone-use-after-move would flag line 12.

#include <string>
#include <iostream>
#include <utility>

void sink(std::string) {}

int main() {
    std::string s = "hello";
    sink(std::move(s));
    std::cout << s.size() << "\n";
    return 0;
}
