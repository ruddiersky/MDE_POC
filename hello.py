print('hello')


def draw_pyramid(height: int) -> None:
    for i in range(1, height + 1):
        stars = '*' * (2 * i - 1)
        print(stars.center(2 * height - 1))


if __name__ == "__main__":
    value = int(input())
    draw_pyramid(value)
