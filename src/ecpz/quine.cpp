#include "ecpz/subprocess.hpp"
int main(int i, char** a) {
    using b = std::istreambuf_iterator<char>; using c = std::string;
    auto d = [](auto e){ std::ifstream f(e, std::ios::binary); return c(b(f), b()); };
    std::vector<c> e(i+3, a[i-1]); e[0]="ecpz"; e[1]="run";
    auto f = i%2 == 0 ? subprocess::run(e).output : d(a[i-1]);
    subprocess::set_bin(); std::cout<<f;
}
