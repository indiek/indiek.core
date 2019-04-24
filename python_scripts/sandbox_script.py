class c:
    def a(self):
        pass

if __name__ == "__main__":
    x = c()
    print(type(x.a))
    print(type(c.a))
    print(c == x)

