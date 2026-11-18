Body := Object clone do(x := 0; y := 0; z := 0; vx := 0; vy := 0; vz := 0; mass := 0)
pi := 3.141592653589793
solar := 4 * pi * pi
year := 365.24
body := method(x, y, z, vx, vy, vz, m,
    b := Body clone
    b x = x; b y = y; b z = z
    b vx = vx * year; b vy = vy * year; b vz = vz * year
    b mass = m * solar
    b
)
bodies := list(
    body(0, 0, 0, 0, 0, 0, 1),
    body(4.84143144246472090e+00, -1.16032004402742839e+00, -1.03622044471123109e-01,
         1.66007664274403694e-03, 7.69901118419740425e-03, -6.90460016972063023e-05, 9.54791938424326609e-04),
    body(8.34336671824457987e+00, 4.12479856412430479e+00, -4.03523417114321381e-01,
         -2.76742510726862411e-03, 4.99852801234917238e-03, 2.30417297573763929e-05, 2.85885980666130812e-04),
    body(1.28943695621391310e+01, -1.51111514016986312e+01, -2.23307578892655734e-01,
         2.96460137564761618e-03, 2.37847173959480950e-03, -2.96589568540237556e-05, 4.36624404335156298e-05),
    body(1.53796971148509165e+01, -2.59193146099879641e+01, 1.79258772950371181e-01,
         2.68067772490389322e-03, 1.62824170038242295e-03, -9.51592254519715870e-05, 5.15138902046611451e-05)
)
sun := bodies at(0)
sun vx = 0; sun vy = 0; sun vz = 0
px := 0; py := 0; pz := 0
bodies foreach(b, px = px + b vx * b mass; py = py + b vy * b mass; pz = pz + b vz * b mass)
sun vx = (px negate) / solar; sun vy = (py negate) / solar; sun vz = (pz negate) / solar

energy := method(
    e := 0
    for(i, 0, 4,
        a := bodies at(i)
        e = e + 0.5 * a mass * (a vx * a vx + a vy * a vy + a vz * a vz)
        for(j, i + 1, 4,
            b := bodies at(j)
            dx := a x - b x; dy := a y - b y; dz := a z - b z
            e = e - a mass * b mass / ((dx * dx + dy * dy + dz * dz) sqrt)
        )
    )
    e
)
advance := method(
    for(i, 0, 4,
        a := bodies at(i)
        for(j, i + 1, 4,
            b := bodies at(j)
            dx := a x - b x; dy := a y - b y; dz := a z - b z
            d2 := dx * dx + dy * dy + dz * dz
            mag := 0.01 / (d2 * d2 sqrt)
            a vx = a vx - dx * b mass * mag; a vy = a vy - dy * b mass * mag; a vz = a vz - dz * b mass * mag
            b vx = b vx + dx * a mass * mag; b vy = b vy + dy * a mass * mag; b vz = b vz + dz * a mass * mag
        )
    )
    bodies foreach(b, b x = b x + 0.01 * b vx; b y = b y + 0.01 * b vy; b z = b z + 0.01 * b vz)
)
energy println
20000 repeat(advance)
energy println
