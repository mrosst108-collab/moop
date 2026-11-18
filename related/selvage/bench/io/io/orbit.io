truncate := method(x, if(x < 0, x ceil, x floor))
orbit := method(k, steps, q, p,
    steps repeat(
        p = p - truncate(k * q / 2000)
        q = q + p
        p = p - truncate(k * q / 2000)
    )
    list(q, p)
)
orbitInverse := method(k, steps, q, p,
    steps repeat(
        p = p + truncate(k * q / 2000)
        q = q - p
        p = p + truncate(k * q / 2000)
    )
    list(q, p)
)
s := orbit(10, 100000, 100000, 0)
s println
orbitInverse(10, 100000, s at(0), s at(1)) println
