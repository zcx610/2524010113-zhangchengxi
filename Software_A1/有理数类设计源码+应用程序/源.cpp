#include <iostream>
#include <stdexcept>
using namespace std;
// 手写 gcd 函数
int gcd(int a, int b) {
    return b == 0 ? abs(a) : gcd(b, a % b);
}

class Rational {
private:
    int numerator;     // 分子
    int denominator;   // 分母（始终为正数）

    // 化简分数
    void reduce() {
        if (denominator == 0) {
            throw invalid_argument("分母不能为 0");
        }
        if (denominator < 0) {   // 规范化：分母为正
            numerator = -numerator;
            denominator = -denominator;
        }
        int g = gcd(abs(numerator), denominator);
        numerator /= g;
        denominator /= g;
    }

public:
    // 默认构造函数：0/1
    Rational() : numerator(0), denominator(1) {}

    // 带参构造函数（构造函数重载）
    Rational(int num, int den = 1)
        : numerator(num), denominator(den) {
        reduce();
    }

    // 只读访问接口（数据安全性）
    int getNumerator() const {
        return numerator;
    }

    int getDenominator() const {
        return denominator;
    }

    // 加法
    Rational operator+(const Rational& rhs) const {
        return Rational(
            numerator * rhs.denominator + rhs.numerator * denominator,
            denominator * rhs.denominator
        );
    }

    // 减法
    Rational operator-(const Rational& rhs) const {
        return Rational(
            numerator * rhs.denominator - rhs.numerator * denominator,
            denominator * rhs.denominator
        );
    }

    // 乘法
    Rational operator*(const Rational& rhs) const {
        return Rational(
            numerator * rhs.numerator,
            denominator * rhs.denominator
        );
    }

    // 除法
    Rational operator/(const Rational& rhs) const {
        if (rhs.numerator == 0) {
            throw invalid_argument("不能除以 0");
        }
        return Rational(
            numerator * rhs.denominator,
            denominator * rhs.numerator
        );
    }

    // 规范化输出
    friend ostream& operator<<(ostream& os, const Rational& r) {
        if (r.denominator == 1) {
            os << r.numerator;
        }
        else {
            os << r.numerator << "/" << r.denominator;
        }
        return os;
    }
};

int main() {
    try {
        int x, y;
        cout << "请输入两个整数：";
        cin >> x >> y;
        int z, w;
        cout << "请输入两个整数：";
        cin >> z >> w;
        Rational a(x, y);
        Rational b(z, w);

        cout << "a = " << a << endl;
        cout << "b = " << b << endl;
        cout << "a + b = " << a + b << endl;
        cout << "a - b = " << a - b << endl;
        cout << "a * b = " << a * b << endl;
        cout << "a / b = " << a / b << endl;

        Rational c(6, -8);   // 自动规范化
        cout << "c = " << c << endl;
    }
    catch (const exception& e) {
        cerr << "错误：" << e.what() << endl;
    }

    return 0;
}