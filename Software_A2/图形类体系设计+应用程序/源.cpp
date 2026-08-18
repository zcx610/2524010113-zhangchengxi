#include <iostream>
#include <cmath>
#include <vector>

using namespace std;

// 常量 π
const double PI = 3.141592653589793;

/*
 * 抽象基类 Shape
 * 至少包含一个纯虚函数
 */
class Shape {
public:
    virtual double area() const = 0;          // 面积（纯虚函数）
    virtual double perimeter() const = 0;     // 周长（纯虚函数）
    virtual void print() const = 0;           // 输出信息
    virtual ~Shape() {}                       // 虚析构函数（多态必备）
};

/*
 * 圆形
 */
class Circle : public Shape {
private:
    double radius;

public:
    explicit Circle(double r) : radius(r) {}

    double area() const override {
        return PI * radius * radius;
    }

    double perimeter() const override {
        return 2 * PI * radius;
    }

    void print() const override {
        cout << "[Circle]    radius = " << radius
            << ", area = " << area()
            << ", perimeter = " << perimeter() << endl;
    }
};

/*
 * 矩形
 */
class Rectangle : public Shape {
private:
    double width;
    double height;

public:
    Rectangle(double w, double h) : width(w), height(h) {}

    double area() const override {
        return width * height;
    }

    double perimeter() const override {
        return 2 * (width + height);
    }

    void print() const override {
        cout << "[Rectangle] width = " << width
            << ", height = " << height
            << ", area = " << area()
            << ", perimeter = " << perimeter() << endl;
    }
};

/*
 * 三角形（海伦公式）
 */
class Triangle : public Shape {
private:
    double a, b, c;

public:
    Triangle(double x, double y, double z) : a(x), b(y), c(z) {}

    double area() const override {
        double p = perimeter() / 2;
        return sqrt(p * (p - a) * (p - b) * (p - c));
    }

    double perimeter() const override {
        return a + b + c;
    }

    void print() const override {
        cout << "[Triangle]  sides = " << a << ", " << b << ", " << c
            << ", area = " << area()
            << ", perimeter = " << perimeter() << endl;
    }
};

/*
 * 主函数：演示动态绑定
 */
int main() {
    vector<Shape*> shapes;

    // 用户输入
    double r, w, h, a, b, c;

    cout << "请输入圆的半径: ";
    cin >> r;
    shapes.push_back(new Circle(r));

    cout << "请输入矩形的宽和高: ";
    cin >> w >> h;
    shapes.push_back(new Rectangle(w, h));

    cout << "请输入三角形的三边长: ";
    cin >> a >> b >> c;
    shapes.push_back(new Triangle(a, b, c));

    cout << "\n====== 图形信息（动态绑定） ======\n";
    for (Shape* shape : shapes) {
        shape->print();   // 运行时多态
    }

    // 释放内存
    for (Shape* shape : shapes) {
        delete shape;
    }

    return 0;
}